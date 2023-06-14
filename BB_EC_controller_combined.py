#!/usr/bin/env python

# Script for GUI for chamber control using the TPS
# Environmental Chamber's Watlow F4T panel

# Utilizes ethernet to
# control F4T with Telnet

# Author: Austin Martinez, Christian Secular


from pymodbus.client import ModbusTcpClient
from pymodbus.payload import BinaryPayloadDecoder
from pymodbus.payload import BinaryPayloadBuilder
from pymodbus.constants import Endian
import pymodbus

import customtkinter as ctk

import numpy as np
import time



MAX_TEMP = 180
MIN_TEMP = -45
# declare and open a Modbus connection to the EC
client = ModbusTcpClient("169.254.18.153", port=502, timeout=3)
paused = False
disconnected = False
remaining_time = 0 #variable for monitoring how much time is left in step
remaining_time_total = 0

global startTemp
global endTemp
global begin
global end
global step
global delay
global outfile
global temps

# subroutine to read in starting temperature and validate it
def read_startTemp(lbl_dispStartTemp, ent_startTemp):
	global startTemp
	startTemp = int(ent_startTemp.get())
	if startTemp < 0:
		lbl_dispStartTemp.configure(text = "Minimum start temperature is 0")
		#lbl_dispStartTemp["text"] = "Minimum start temperature is 0"
	elif startTemp > 100:
		lbl_dispStartTemp.configure(text = "Maximum start temperature is 100")
		#lbl_dispStartTemp["text"] = "Maximum start temperature is 100"
	else:
		lbl_dispStartTemp.configure(text = f"{startTemp}\N{DEGREE CELSIUS}")
        
# subroutine to read in end temperature and validate it
def read_endTemp(lbl_dispEndTemp, ent_endTemp, startTemp):
	global endTemp
	endTemp = int(ent_endTemp.get())
	if endTemp < startTemp+1:
		lbl_dispEndTemp.configure(text = "End temperature must be larger than start temp")
	elif endTemp > 100:
		lbl_dispEndTemp.configure(text = "Exceeded maximum end temperature of 100")
	else:
		lbl_dispEndTemp.configure(text = f"{endTemp}\N{DEGREE CELSIUS}")
        
# subroutine to read in temperature step and validate it
def read_step(lbl_dispStep, ent_step):
	global step
	step = int(ent_step.get())
	if step < 1:
		lbl_dispStep.configure(text = "Temperature step must be at least 1")
	else:
		lbl_dispStep.configure(text = f"{step}\N{DEGREE CELSIUS}")
        
# subroutine to read in delay time and validate it
def read_delay(lbl_dispDelay, ent_delay):
	global delay
	delay = int(ent_delay.get())
	if delay < 5:
		lbl_dispDelay.configure(text = "Time delay must be at least 5 minutes")
	else:
		lbl_dispDelay.configure(text = f"{delay} minutes")
        
# subroutine to read in outfile and validate it
def read_outfile(lbl_dispOutfile, ent_outfile):
	global outfile
	try:
		outfile = ent_outfile.get()
	except ValueError:
		lbl_dispOutfile.configure(text = "Please type a filename")
	if len(outfile) < 1:
		lbl_dispOutfile.configure(text = "Please type a filename")
	else:
		lbl_dispOutfile.configure(text = f"{outfile}.txt")
		outfile = outfile + ".txt"
        
def compute(lbl_dispSweep):
    # initialize temperature array
    global temps
    temps = np.arange(startTemp, endTemp, step)  # temps in [C]
    temps = np.append(25, temps)  # make sure the script leaves the BB at 25C
    lbl_dispSweep.configure(text = f"{temps}\nSweep will be done in reverse order, ending on 25C")
    
def BB_serial(temps, delay, outfile, lbl):
    print("Starting Blackbody in serial mode...")
    lbl.configure(text = "Starting Blackbody in serial mode...")
    
    # initialize a serial instance
    ser = serial.Serial(
            port='/dev/ttyS0', # Connect to port
            baudrate = 115200,   # baud rate per the manual
            parity=serial.PARITY_NONE,    # parity per the manual
            stopbits=serial.STOPBITS_ONE, # stop bits per the manual
            bytesize=serial.EIGHTBITS,    # byte size per the manual
            timeout=1
    )

    command = ("\n").encode('ascii')
    print(ser.read_until(command))  # needs to say connected to acc controler

    start_time = time.ctime()
    print(start_time)
    bb_temp = []
    for t in range(1, temps.shape[0] + 1):
        # print(t)
        # print(temps[-t])
        print("Temp:" + format(temps[-t], '.1f') + "C")  # keep track of what temp its on

        # DAxx.x sets the absolute temperature
        # ex: DA25.0 sets the abs. temp. to 25 C
        command = ("DA" + format(temps[-t], '.1f') + "\n").encode('ascii')  # set temp
        ser.write(command)

        # hold this temperature for the given amount of minutes
        time.sleep(delay*60)  # delay for how ever long you want [s]

        # MDA gets the absolute temperature from the BB
        command = ("MDA\n").encode('ascii')  # get temp
        ser.write(command)

        command = ("\n").encode('ascii')  # print temp
        bb_t = ser.read_until(command)

        print(bb_t)  # check that its reading temps
        bb_temp.append(bb_t)

    file = open(outfile, "w")  # change file name each time
    file.write(start_time + "\n")

    for i in range(len(bb_temp)):
        split = bb_temp[i].split()
        file.write(str(np.float64(split[-1])) + "\n")

    file.close()
    ser.close()
    
	
def BB_ethernet(temps, delay, outfile, lbl):
    print("Starting Blackbody in ethernet mode...")
    lbl.configure(text = "Starting Blackbody in ethernet mode...")

    # host = '192.168.200.161'  # default static IP of BB
    host = '169.254.18.151'  # ip of bb should not change
    port = '7788'  # what the manual said to use

    print("Creating Telnet instance")
    tn = telnetlib.Telnet()
    print("Opening Telnet connection")
    tn.open(host, port)
    print("Telnet connection established")

    command = ("\n").encode('ascii')
    print(tn.read_until(command))  # needs to say connected to acc controler

    start_time = time.ctime()
    print(start_time)
    bb_temp = []
    for t in range(1, temps.shape[0] + 1):
        # print(t)
        # print(temps[-t])
        print("Temp:" + format(temps[-t], '.1f') + "C")  # keep track of what temp its on

        # DAxx.x sets the absolute temperature
        # ex: DA25.0 sets the abs. temp. to 25 C
        command = ("DA" + format(temps[-t], '.1f') + "\n").encode('ascii')  # set temp
        tn.write(command)

        # hold this temperature for the given amount of minutes
        time.sleep(delay*60)  # delay for how ever long you want [s]

        # MDA gets the absolute temperature from the BB
        command = ("MDA\n").encode('ascii')  # get temp
        tn.write(command)

        command = ("\n").encode('ascii')  # print temp
        bb_t = tn.read_until(command)

        print(bb_t)  # check that its reading temps
        bb_temp.append(bb_t)

    file = open(outfile, "w")  # change file name each time
    file.write(start_time + "\n")

    for i in range(len(bb_temp)):
        split = bb_temp[i].split()
        file.write(str(np.float64(split[-1])) + "\n")

    file.close()
    tn.close()

#class for EC steps
class ECCustomStep:
	def __init__(self, begin_val=23, end_val=25, rate_val = 1, time_val = 1):
		self.begin = np.float32(begin_val) #temp to start at
		self.end = np.float32(end_val) #temp to end at 
		self.rate = np.float32(rate_val) #degrees in celsius to change by
		self.time = int(time_val) #time in minutes to stay at each temp

		self.temps = np.arange(self.begin, self.end + 1, self.rate, dtype=np.float32)
		self.running = 0
		self.current_time = 0
		self.step = 0

	def read_file(self, file):
		with open(file) as f:
			read = f.readlines()
			read[0] = read[0].rstrip(read[0][-1])
			self.temps = read[0].split() #read first line for list of temps
			#convert string to float, then convert list to numpy array
			self.temps = np.array(list(map(np.float32, self.temps)))
			self.time = int(read[1])

	#ensures the step is valid
	def validate_EC_inputs(self):
		fail = False
		error_msg = ""
		if(self.begin < MIN_TEMP or self.begin > MAX_TEMP):
			fail = True
			error_msg += "Beginning value must be between " + str(MIN_TEMP) + " and " +  str(MAX_TEMP) + ".\n"
		if(self.end < MIN_TEMP or self.end > MAX_TEMP):
			fail = True
			error_msg += "Ending value must be between " + str(MIN_TEMP) + " and " +  str(MAX_TEMP) + ".\n"
		if(self.rate == 0):
			fail = True
			error_msg += "Rate cannot be equal to 0.\n"
		if(abs(self.begin - self.end) < abs(self.rate)):
			fail = True
			error_msg += "Rate cannot be greater than the difference between cstart and end.\n"
		if(self.end < self.begin and self.rate > 0):
			fail = True
			error_msg += "Rate must be negative if beginning is less than end.\n"
		if(self.end > self.begin and self.rate < 0):
			fail = True
			error_msg += "Rate must be positive if beginning is less than end.\n"
		if(self.time <= 0):
			fail = True
			error_msg += "Time at each step must be greater than 0 minutes.\n"
		#display error message if invalid inputs
		if(not fail):
			#print temperatures for confirmation
			error_msg += "Temperatures:\n"
			for i in np.arange(self.temps.size):
				error_msg += str(self.temps[i]) + " "
				if(i % 5 == 0 and i > 0):
					error_msg += "\n"
			error_msg +="\nNumber of Steps: " + str(self.temps.size)
			error_msg +="\nTime Between Each Step: " + str(self.time) + " minute(s)"
			error_msg +="\nTotal Program Length: " + str(self.time * (self.temps.size)) + " minute(s)"
			lbl_entry_error.configure(text = error_msg)
		lbl_entry_error.configure(text = error_msg)
		lbl_entry_error.grid()
		return fail
	
	def validate_file_inputs(self):
		fail = False
		error_msg = ""
		#check if each temperature is within a valid range
		for temp in self.temps:
			if(temp < MIN_TEMP or temp > MAX_TEMP):
				fail = True
				error_msg +="All input temperatures must be between " + str(MIN_TEMP) + " and " +  str(MAX_TEMP) + ".\n"
		if(self.time <= 0):
			fail = True
			error_msg += "Time at each step must be greater than 0 minutes.\n"
		error_msg += "Temperatures:\n"
		for i in np.arange(self.temps.size):
			error_msg += str(self.temps[i]) + " "
			if(i % 5 == 0 and i > 0):
				error_msg += "\n"
		error_msg +="\nNumber of Steps: " + str(self.temps.size)
		error_msg +="\nTime Between Each Step: " + str(self.time) + " minute(s)"
		error_msg +="\nTotal Program Length: " + str(self.time * (self.temps.size - 1))
		lbl_entry_error.configure(text = error_msg)
		lbl_entry_error.grid()
		return fail

	#sets the temperature to the first step
	def start(self):
		self.step = 0
		set_temp(self.temps[self.step])
		self.step += 1
		self.running = True
		
		#store time of day
		read = client.read_holding_registers(address = 14660 ,count = 1)
		self.current_time = read.registers[0]
		
		
	def next_step(self):
		if(self.step == (len(self.temps))):
			self.running = False
			return True
		#go to next temperature. If final step, return true
		set_temp(self.temps[self.step])
		self.step += 1
		
		#store time of day
		read = client.read_holding_registers(address = 14660 ,count = 1)
		self.current_time = read.registers[0]
		
		
		
		return False

custom = ECCustomStep()

def pause_button():
	global paused
	if(paused):
		print("Resuming")
		paused = False
		btn_start_pause.configure(text = "Pause Profile")
		lbl_entry_error.configure(text = "Running Profile: " + cb_profile_select.get())
		client.write_registers(16564, 147)
	else:
		print("Pausing")
		paused = True
		btn_start_pause.configure(text = "Resume Profile")
		lbl_entry_error.configure(text = "Profile Paused")
		client.write_registers(16566, 146)
    
	
#start program with selected profile
def start_button():
	print("Start")
	btn_start_pause.configure(text = "Pause Profile", command = pause_button)
	btn_term.grid()
	
	#hide other options to prevent accidental operation
	for ent in ents_custom:
		ent.grid_remove()
	btn_custom.grid_remove()
	btn_read_file.grid_remove()
	ent_file.grid_remove()
	lbl_profile_select.grid_remove()
	cb_profile_select.grid_remove()
	
	print(str(cb_profile_select.get()))
	cb_profile_select.configure(state = "disabled")
	client.write_registers(16558, int(cb_profile_select.get())) #Load profile number
	client.write_registers(16562, 1782) #Start process controller
	
	#label for telling user the program is running
	lbl_entry_error.configure(text = "Running Profile: " + cb_profile_select.get())
	
def term_button():
	print("Terminating")
	btn_start_pause.configure(text = "Start Profile", command = start_button)
	btn_term.grid_remove()
	#show custom program components
	for ent in ents_custom:
		ent.grid()
		ent.configure(state = "normal")
	btn_read_file.grid() #redisplay buttons for reading file and custom 
	btn_custom.grid()
	ent_file.grid()
	lbl_profile_select.grid()
	cb_profile_select.grid()
	
	cb_profile_select.configure(state = "normal")
	client.write_registers(16566, 148)
	
	time.sleep(1) #delay to allow termination to finish
	
	lbl_entry_error.configure(text = "Profile Terminated")
	set_temp(23)
	
def custom_button():
	global custom
	#get user input, create custom step and validate
	begin_input = ent_begin.get()
	end_input = ent_end.get()
	ramp_input = ent_ramp.get()
	time_input = ent_time.get()
	custom = ECCustomStep(begin_input, end_input, ramp_input, time_input)
	if(not custom.validate_EC_inputs()):
		#disable user input into entry
		for ent in ents_custom:
			ent.configure(state = "disabled")

		#change button to confirm and show edit button
		btn_custom.configure(text = "Confirm Program", command = confirm_button)
		btn_edit_custom.configure(text = "Edit Custom Program", command = edit_button)
		btn_edit_custom.grid()
		
		


def edit_button():
	#renable entry elements and hide custom button
	for ent in ents_custom:
		ent.configure(state = "normal")
	btn_custom.configure(text = "Create Custom Program", command = custom_button)
	btn_edit_custom.grid_remove()

#TODO: implement real time control
def confirm_button():
	global remaining_time, paused, remaining_time_total
	print("Program confirmed")
	custom.start()
	paused = False
	#begin program, calculate remaining time of first step and total program
	remaining_time = custom.time * 60
	remaining_time_total = remaining_time * (custom.temps.size)
	
	btn_custom.configure(text = "Pause Custom Program", command = pause_custom_button)
	
	#prevent editing, starting a profile, or loading a file
	btn_edit_custom.grid_remove()
	btn_start_pause.grid_remove()
	btn_read_file.grid_remove()

	
def pause_custom_button():
	global paused, remaining_time, remaining_time_total ,custom
	if(paused):
		#resume using new start time for step
		print("Resuming")
		paused = False
		btn_custom.configure(text = "Pause Custom Program")
		
		read = client.read_holding_registers(address = 14660 ,count = 1)
		custom.current_time = int(read.registers[0])
	else:
		print("Pausing")
		paused = True
		btn_custom.configure(text = "Resume Custom Program")
		btn_edit_custom.configure(text = "Terminate Custom Program", command = terminate_custom_button)
		btn_edit_custom.grid()
		
		#calculate new remaining time
		read = client.read_holding_registers(address = 14660 ,count = 1)
		current_time = int(read.registers[0])
		
		if(current_time < custom.current_time):
			#prevents overflow
			elapsed_time = (86400 - custom.current_time) + current_time
		else:
			elapsed_time = current_time - custom.current_time
		
		
		
		
		remaining_time -= (current_time - custom.current_time)
		remaining_time_total -= (current_time - custom.current_time)

def terminate_custom_button():
	#end the custom program
	custom.step = 0
	custom.running = False
	btn_custom.configure(text = "Create Custom Program", command = custom_button)
	for ent in ents_custom:
		ent.configure(state = "normal")
	btn_edit_custom.grid_remove()
	
	lbl_entry_error.configure(text = "Program Terminated")

	#show buttons for using profiles and reading a file
	btn_start_pause.grid()
	btn_read_file.grid()
	
	#set chamber set point to 23 C
	set_temp(23)


def file_button():
	file_name = ent_file.get()
	#read file, print error message if fail
	try:
		custom.read_file(file_name)
		if(not custom.validate_file_inputs()):
			btn_custom.configure(text = "Confirm Program", command = confirm_button)
			#change button to confirm and show edit button
			btn_edit_custom.configure(text = "Edit Custom Program", command = edit_button)
			btn_edit_custom.grid()
	except OSError as e:
		error_msg = "Unable to open file."
		lbl_entry_error.configure(text = error_msg)
		lbl_entry_error.grid()


def update():
	global disconnected
	try:
		#attempt to reconnect if chamber disconnected
		if(disconnected):
			lbl_entry_error.configure(text = "No Chamber Connection")
			client.connect()
			if client.is_socket_open():
				disconnected = False
				print("Chamber Reconnected!")		
				lbl_entry_error.configure(text = "Chamber Ready")

		
		#repeat after a half-second
		lbl_temp.after(500, update)
		
		#update temp label
		read = client.read_holding_registers(address = 16664 ,count = 4)
		decoder = BinaryPayloadDecoder.fromRegisters(read.registers, Endian.Big, wordorder=Endian.Little)
		current_temp = decoder.decode_32bit_float()
		
		decoder.reset()
		read = client.read_holding_registers(address = 2782, count = 4)
		decoder = BinaryPayloadDecoder.fromRegisters(read.registers, Endian.Big, wordorder=Endian.Little)

		set_point_temp = decoder.decode_32bit_float()
		lbl_temp.configure(text = "Current Temperature: " + "{:.1f}".format(current_temp) + " C\nSet Point: " + "{:.1f}".format(set_point_temp) + " C")
		
		#update humidity label
		decoder.reset()
		read = client.read_holding_registers(address = 16666 ,count = 4)
		decoder = BinaryPayloadDecoder.fromRegisters(read.registers, Endian.Big, wordorder=Endian.Little)
		current_humidity = decoder.decode_32bit_float()
		lbl_hum.configure(text = "Current Humidity: " + "{:.1f}".format(current_humidity) + "%")

		#update time
		update_time()
	except pymodbus.exceptions.ModbusException as e:
		lbl_entry_error.configure(text = "No Chamber Connection")
		print("No Chamber Connection")
		disconnected = True
	except  AttributeError:
		lbl_entry_error.configure(text = "No Chamber Connection")
		print("No Chamber Connection")
		disconnected = True
	
	#heartbeat print

def set_temp(temp):
	#create builder, add float to buffer, build, and then write to register
	builder = BinaryPayloadBuilder(wordorder=Endian.Little, byteorder=Endian.Big)
	builder.add_32bit_float(np.float32(temp))
	val_float= builder.build()
	client.write_registers(2782, val_float, skip_encode = True)
	
def update_time():
	global remaining_time_total, remaining_time
	#get hour, minute and second
	read = client.read_holding_registers(address = 14664 ,count = 1)
	hour = read.registers[0]
	if(hour < 10):
		time_str = "0" + str(hour)
	else:
		time_str = str(hour)
		
	read = client.read_holding_registers(address = 14666 ,count = 1)
	minute = read.registers[0]
	if(minute < 10):
		time_str += ":0" + str(minute)
	else:
		time_str += ":" + str(minute)

	read = client.read_holding_registers(address = 14668 ,count = 1)
	second = read.registers[0]
	if(second < 10):
		time_str += ":0" + str(second)
	else:
		time_str += ":" + str(second)
	#print(time_str)
	lbl_time.configure(text = time_str)
	
	#check if it is time to go to next step
	read = client.read_holding_registers(address = 14660 ,count = 1)
	current_time = int(read.registers[0])
	if(custom.running and not paused):
		#print remaining time of step and step number to entry label
		if(current_time < custom.current_time):
			#prevents overflow
			elapsed_time = (86400 - custom.current_time) + current_time
		else:
			elapsed_time = current_time - custom.current_time
		
		
		remaining_time_total_min = int((remaining_time_total - elapsed_time) / 60)
		remaining_time_total_sec = (remaining_time_total - elapsed_time) % 60
		time_str = "Remaining Time For Program: " + str(remaining_time_total_min)
		if(remaining_time_total_sec < 10):
			time_str += ":0" + str(remaining_time_total_sec)
		else:
			time_str += ":" + str(remaining_time_total_sec)
		
		remaining_time_min = int((remaining_time - elapsed_time) / 60)
		remaining_time_sec = (remaining_time - elapsed_time) % 60
		time_str += "\nRemaining Time For Current Step: " + str(remaining_time_min)
		if(remaining_time_sec < 10):
			time_str += ":0" + str(remaining_time_sec)
		else:
			time_str += ":" + str(remaining_time_sec)
		time_str += "\nStep " + str(custom.step) + " of " + str(custom.temps.size)
		lbl_entry_error.configure(text = time_str)
		#check if elapsed time exceeds remaining time
		if(elapsed_time > remaining_time):
			#decrement time by an interval
			remaining_time_total -= custom.time * 60
			#next_step returns true if final step was completed
			if(custom.next_step()):
					btn_custom.configure(text = "Create Custom Program", command = custom_button)
					lbl_entry_error.configure(text = "Program Finished!")
					for ent in ents_custom:
						ent.configure(state = "normal")
					btn_start_pause.grid()
					btn_read_file.grid()
					btn_edit_custom.grid_remove()
					
					ent_file.grid()
					set_temp(23)
	
	
#GUI objects for EC chamber
app = ctk.CTk() 
lbl_temp = ctk.CTkLabel(master=app, text="No Temp Recorded", width=120, height = 25)
lbl_hum= ctk.CTkLabel(master=app, text="No Humidity Recorded", width=120, height = 25)
lbl_profile_select= ctk.CTkLabel(master=app, text="Program Number", width=120, height = 25)
lbl_entry_error= ctk.CTkLabel(master=app, text="Chamber Ready", width=120, height = 25)
lbl_time= ctk.CTkLabel(master=app, text="No Chamber Connection", width=120, height = 25, font=("Arial", 30))

btn_term = ctk.CTkButton(master = app, width = 120, height = 32, border_width = 1, text = "Terminate Profile", command = term_button)
btn_start_pause = ctk.CTkButton(master = app, width = 120, height = 32, border_width = 1, text = "Start Profile", command = start_button)
btn_custom = ctk.CTkButton(master = app, width = 120, height = 64, border_width = 1, text = "Create Custom Program", command = custom_button)
btn_edit_custom = ctk.CTkButton(master = app, width = 120, height = 64, border_width = 1, text = "Edit Custom Program", command = edit_button)
btn_read_file = ctk.CTkButton(master = app, width = 120, height = 32, border_width = 1, text = "Load File", command = file_button)
cb_profile_select = ctk.CTkComboBox(master = app, values =["1", "2", "3", "4", "5"])

ent_begin = ctk.CTkEntry(master=app, placeholder_text="Begin")
ent_end = ctk.CTkEntry(master=app, placeholder_text="End")
ent_ramp = ctk.CTkEntry(master=app, placeholder_text="Ramp")
ent_time = ctk.CTkEntry(master=app, placeholder_text="Time (minutes)")
ent_file = ctk.CTkEntry(master = app, placeholder_text="File Name")

ents_custom = [ent_begin, ent_end, ent_ramp, ent_time]

#start point of program
if __name__ == "__main__":
	print("Running main")
	print("Connecting to chamber...")
	""" try:
		client.connect()		
		print("Connected!")
	except pymodbus.exceptions.ModbusException as e:
		print("Connection Failed")
		lbl_entry_error.configure(text = "No Connection to Chamber")
		disconnected = True """
	
	ctk.set_appearance_mode("dark")
	ctk.set_default_color_theme("blue")

	#set window size and title
	app.geometry("1200x720")	
	app.title("Chamber Controller")
	app.resizable(width=False, height=False)
	
	#place labels
	lbl_time.grid(row = 1, column=3, padx = 40, pady = 5)
	lbl_temp.grid(row = 2, column=3, padx = 40, pady = 5)
	lbl_hum.grid(row = 3, column=3, padx = 40, pady = 5)
	lbl_profile_select.grid(row = 1, column = 2, padx = 40, pady = 5)
	lbl_entry_error.grid(row = 4, column = 3, padx = 40, pady = 5)

	#place buttons and hide terminate and custom button
	btn_start_pause.grid(row = 1, column=1, padx = 40, pady = 5)
	btn_term.grid(row = 2, column=1, padx = 40, pady = 5)
	btn_term.grid_remove()
	btn_custom.grid(row = 3, column = 1, padx = 40, pady = 5)
	btn_edit_custom.grid(row = 4, column = 1, padx = 40, pady = 5)
	btn_edit_custom.grid_remove()
	btn_read_file.grid(row = 7, column = 1, padx = 40, pady = 5)
	#place combo box on grid
	cb_profile_select.grid(row = 2, column = 2, padx = 40, pady = 5)
	
	#place entry fields on grid
	ent_begin.grid(row=3, column = 2, padx = 40, pady = 5)
	ent_end.grid(row=4, column = 2, padx = 40, pady = 5)
	ent_ramp.grid(row=5, column = 2, padx = 40, pady = 5)
	ent_time.grid(row=6, column = 2, padx = 40, pady = 5)
	ent_file.grid(row=7, column = 2, padx = 40, pady = 5)
	
	#########     BB GUI                   ####################
	lbl_topMsg = ctk.CTkLabel(master=app, text="Please click Enter button on screen after typing each input value.")

	# entry labels
	frm_labels = ctk.CTkFrame(master=app)

	lbl_startTemp = ctk.CTkLabel(master=frm_labels, text="Start Temperature: ")
	lbl_endTemp = ctk.CTkLabel(master=frm_labels, text="End Temperature: ")
	lbl_step = ctk.CTkLabel(master=frm_labels, text="Temperature Step: ")
	lbl_delay = ctk.CTkLabel(master=frm_labels, text="Hold Time: ")
	lbl_outfile = ctk.CTkLabel(master=frm_labels, text="Output Filename: ")

	lbl_startTemp.grid(row=8, column=0, pady=6)
	lbl_endTemp.grid(row=9, column=0, pady=6)
	lbl_step.grid(row=10, column=0, pady=6)
	lbl_delay.grid(row=11, column=0, pady=6)
	lbl_outfile.grid(row=12, column=0, pady=6)

	# entry widgets
	frm_entries = ctk.CTkFrame(master=app)

	ent_startTemp = ctk.CTkEntry(master=frm_entries, width=36)
	ent_endTemp = ctk.CTkEntry(master=frm_entries, width=36)
	ent_step = ctk.CTkEntry(master=frm_entries, width=36)
	ent_delay = ctk.CTkEntry(master=frm_entries, width=36)
	ent_outfile = ctk.CTkEntry(master=frm_entries, width=36)

	ent_startTemp.grid(row=8, column=0, pady=6)
	ent_endTemp.grid(row=9, column=0, pady=6)
	ent_step.grid(row=10, column=0, pady=6)
	ent_delay.grid(row=11, column=0, pady=6)
	ent_outfile.grid(row=12, column=0, pady=6)

	# entry units
	frm_units = ctk.CTkFrame(master=app)

	lbl_startTempC = ctk.CTkLabel(master=frm_units, text="\N{DEGREE CELSIUS}")
	lbl_endTempC = ctk.CTkLabel(master=frm_units, text="\N{DEGREE CELSIUS}")
	lbl_stepC = ctk.CTkLabel(master=frm_units, text="\N{DEGREE CELSIUS}")
	lbl_delayM = ctk.CTkLabel(master=frm_units, text="minutes")
	lbl_outfileTxt = ctk.CTkLabel(master=frm_units, text=".txt")

	lbl_startTempC.grid(row=8, column=0, sticky="w", pady=6)
	lbl_endTempC.grid(row=9, column=0, sticky="w", pady=6)
	lbl_stepC.grid(row=10, column=0, sticky="w", pady=6)
	lbl_delayM.grid(row=11, column=0, sticky="w", pady=6)
	lbl_outfileTxt.grid(row=12, column=0, sticky="w", pady=6)

	# display labels
	frm_displays = ctk.CTkFrame(master=app)

	lbl_dispStartTemp = ctk.CTkLabel(master=frm_displays, text = "")
	lbl_dispEndTemp = ctk.CTkLabel(master=frm_displays, text = "")
	lbl_dispStep = ctk.CTkLabel(master=frm_displays,text = "")
	lbl_dispDelay = ctk.CTkLabel(master=frm_displays, text = "")
	lbl_dispOutfile = ctk.CTkLabel(master=frm_displays, text = "")

	lbl_dispStartTemp.grid(row=8, column=0, pady=6, sticky="w")
	lbl_dispEndTemp.grid(row=9, column=0, pady=6, sticky="w")
	lbl_dispStep.grid(row=10, column=0, pady=6, sticky="w")
	lbl_dispDelay.grid(row=11, column=0, pady=6, sticky="w")
	lbl_dispOutfile.grid(row=12, column=0, pady=6, sticky="w")


	# enter buttons
	frm_entBtns = ctk.CTkFrame(master=app)

	btn_startEnter = ctk.CTkButton(
		master=frm_entBtns,
		text="ENTER",
		command=lambda: read_startTemp(lbl_dispStartTemp=lbl_dispStartTemp, ent_startTemp=ent_startTemp)
		# run this subroutine when button is pressed
	)
	btn_endEnter = ctk.CTkButton(
		master=frm_entBtns,
		text="ENTER",
		command=lambda: read_endTemp(lbl_dispEndTemp=lbl_dispEndTemp, ent_endTemp=ent_endTemp, startTemp=startTemp)
		# run this subroutine when button is pressed
	)
	btn_stepEnter = ctk.CTkButton(
		master=frm_entBtns,
		text="ENTER",
		command=lambda: read_step(lbl_dispStep=lbl_dispStep, ent_step=ent_step) # run this subroutine when button is pressed
	)
	btn_delayEnter = ctk.CTkButton(
		master=frm_entBtns,
		text="ENTER",
		command=lambda: read_delay(lbl_dispDelay=lbl_dispDelay, ent_delay=ent_delay) # run this subroutine when button is pressed
	)
	btn_outfileEnter = ctk.CTkButton(
		master=frm_entBtns,
		text="ENTER",
		command=lambda: read_outfile(lbl_dispOutfile=lbl_dispOutfile, ent_outfile=ent_outfile)  # run this subroutine when button is pressed
	)

	btn_startEnter.grid(row=8, column=0, pady=3)
	btn_endEnter.grid(row=9, column=0, pady=3)
	btn_stepEnter.grid(row=10, column=0, pady=3)
	btn_delayEnter.grid(row=11, column=0, pady=3)
	btn_outfileEnter.grid(row=12, column=0, pady=3)

	# compute sweep
	lbl_dispSweep = ctk.CTkLabel(master=app, text = "")
	btn_compute = ctk.CTkButton(
		master=app,
		text="Compute Sweep",
		command=lambda: compute(lbl_dispSweep=lbl_dispSweep)  # run this subroutine when button is pressed
	)

	# start buttons
	lbl_dispStartSerial = ctk.CTkLabel(master=app, text = "")
	lbl_dispStartEthernet = ctk.CTkLabel(master=app, text = "")
	btn_startSerial = ctk.CTkButton(
		master=app,
		text="Start Serial",
		command=lambda: BB_serial(temps=temps, delay=delay, outfile=outfile, lbl=lbl_dispStartSerial) # run this subroutine when button is pressed
	)
	btn_startEthernet = ctk.CTkButton(
		master=app,
		text="Start Ethernet",
		command=lambda: BB_ethernet(temps=temps, delay=delay, outfile=outfile, lbl=lbl_dispStartEthernet) # run this subroutine when button is pressed
	)

	# pack it all
	lbl_topMsg.grid(row=8, columnspan=3)
	frm_labels.grid(row=9, column=0, padx=10, pady=10)
	frm_entries.grid(row=9, column=1, padx=10, pady=10)
	frm_units.grid(row=9, column=2, padx=10, pady=10)
	frm_entBtns.grid(row=9, column=3, padx=10, pady=10)
	frm_displays.grid(row=9, column=4, padx=10, pady=10)
	btn_compute.grid(row=10, column=0, columnspan=2, padx=10, pady=10)
	lbl_dispSweep.grid(row=10, column=2, columnspan=3, padx=10, pady=10)
	btn_startSerial.grid(row=11, column=0, columnspan=2, padx=10, pady=10)
	btn_startEthernet.grid(row=11, column=3, columnspan=2, padx=10, pady=10)
	lbl_dispStartSerial.grid(row=12, columnspan=5, padx=10, pady=10)
	lbl_dispStartEthernet.grid(row=12, columnspan=5, padx=10, pady=10)
	
	#begin running update
	#update()
	
	#open window
	app.mainloop()
