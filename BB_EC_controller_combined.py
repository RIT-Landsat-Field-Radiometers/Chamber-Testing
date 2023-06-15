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
import serial
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
global step
global delay
global outfile
global bb_temps
global bb_index
global bb_error_msg
global bb_start_time
global bb_actual_temp
global bb_finished
global bb_running

bb_running = False
bb_finished = False

# subroutine to read in starting temperature and validate it
def BB_read_startTemp():
	global startTemp, bb_error_msg
	startTemp = int(BB_ent_startTemp.get())
	if startTemp < 0:
		bb_error_msg += "Minimum start temperature is 0\n"
		return False
		
	elif startTemp > 100:
		bb_error_msg += "Maximum start temperature is 100\n"
		return False
	else:
		return True
        
# subroutine to read in end temperature and validate it
def BB_read_endTemp():
	global endTemp, bb_error_msg
	endTemp = int(BB_ent_endTemp.get())
	if endTemp < startTemp+1:
		bb_error_msg += "End temperature must be larger than start temp\n"
		return False
	elif endTemp > 100:
		bb_error_msg += "Exceeded maximum end temperature of 100\n"
		return False
	else:
		return True
        
# subroutine to read in temperature step and validate it
def BB_read_step():
	global step, bb_error_msg
	step = int(BB_ent_step.get())
	if step < 1:
		bb_error_msg += "Temperature step must be at least 1\n"
		return False
	else:
		return True
        
# subroutine to read in delay time and validate it
def BB_read_delay():
	global delay, bb_error_msg
	delay = int(BB_ent_delay.get())
	if delay < 5:
		bb_error_msg += "Time delay must be at least 5 minutes\n"
		return False
	else:
		return True
        
# subroutine to read in outfile and validate it
def BB_read_outfile():
	global outfile, bb_error_msg
	try:
		outfile = BB_ent_outfile.get()
	except ValueError:
		bb_error_msg += "Please type a filename\n"
		return False
	if len(outfile) < 1:
		bb_error_msg += "Please type a filename\n"
		return False
	else:
		outfile = outfile + ".txt"
		return True

#read in all inputs for BB control and validate them
def BB_validate_inputs():
	input_good = True
	if(not BB_read_startTemp()):
		input_good = False
	if(not BB_read_endTemp()):
		input_good = False
	if(not BB_read_delay()):
		input_good = False
	if(not BB_read_step()):
		input_good = False
	if(not BB_read_outfile()):
		input_good = False
	return input_good
def BB_compute():
	# initialize temperature array
	global bb_temps, startTemp, endTemp, step, delay, bb_error_msg
	bb_error_msg = ""
	if(BB_validate_inputs()):
		bb_temps = np.arange(startTemp, endTemp, step)  # temps in [C]
		bb_temps = np.append(25, bb_temps)  # make sure the script leaves the BB at 25C
		BB_lbl_entry_error.configure(text = f"Temperatures:\n{bb_temps}\nSweep will be done in reverse order, ending on 25C\nHold Time: {delay} minutes\nOutput File Name: {outfile}")
		BB_btn_startSerial.grid()
		BB_btn_startEthernet.grid()
	else:
		BB_lbl_entry_error.configure(text = bb_error_msg)
    

def BB_serial():
	global bb_index, bb_temps, bb_start_time, bb_actual_temp, bb_finished, bb_running
	# initialize a serial instance
	ser = serial.Serial(
			port='/dev/ttyS0', # Connect to port
			baudrate = 115200,   # baud rate per the manual
			parity=serial.PARITY_NONE,    # parity per the manual
			stopbits=serial.STOPBITS_ONE, # stop bits per the manual
			bytesize=serial.EIGHTBITS,    # byte size per the manual
			timeout=1	
	)
	
	if(bb_finished): #once cooldown period finished, turn off blackbody control
		command = ("DOFF\n").encode('ascii')  # turn off blackbody control
		ser.write(command)
		ser.close()
		BB_lbl_dispStartSerial.configure(text = "Blackbody finished")
		bb_finished = False #set flag false to confirm cooldown period is over
		BB_btn_compute.grid()
		BB_btn_startSerial.grid_remove()
		BB_btn_startEthernet.grid_remove()
		bb_running = False
		return #finish running serial control of blackbody
		
	#initialize BB serial
	if(bb_index == 1):
		print("Starting Blackbody in serial mode...")
		BB_lbl_dispStartSerial.configure(text = "Starting Blackbody in serial mode...")
		bb_start_time = time.ctime()
		bb_running = True
		BB_btn_compute.grid_remove() #hide buttons to prevent accidentally starting
		BB_btn_startSerial.grid_remove() #hide buttons to prevent accidentally starting
		BB_btn_startEthernet.grid_remove() #hide buttons to prevent accidentally starting
		print(bb_start_time)
		bb_actual_temp = [] #initialize array for actual BB temps
	if(bb_running):	
		#check connection to controller
		command = ("\n").encode('ascii')
		print(ser.read_until(command))  # needs to say connected to acc controler

		#for t in range(1, temps.shape[0] + 1):
		# print(t)
		# print(temps[-t])
		print("Temp:" + format(bb_temps[-bb_index], '.1f') + "C")  # keep track of what temp its on

		# DAxx.x sets the absolute temperature
		# ex: DA25.0 sets the abs. temp. to 25 C
		command = ("DA" + format(bb_temps[-bb_index], '.1f') + "\n").encode('ascii')  # set temp
		ser.write(command)

		# hold this temperature for the given amount of minutes
		#time.sleep(delay*60)  # delay for how ever long you want [s]

		# M2 gets the absolute temperature from the BB
		command = ("M2\n").encode('ascii')  # get temp
		ser.write(command)

		command = ("\n").encode('ascii')  # print temp
		bb_t = ser.read_until(command)

		print(bb_t)  # check that its reading temps
		bb_actual_temp.append(bb_t)
		
		#once finished running the other temperatures, set BB to 25C
		if(bb_index == bb_temps.shape[0]):
			#write actual temps to file
			file = open(outfile, "w")  # change file name each time
			file.write(bb_start_time + "\n")
		
			for i in range(len(bb_actual_temp)):
				split = bb_actual_temp[i].split()
				file.write(str(np.float64(split[-1])) + "\n")

			file.close()
			print("finished")
			bb_finished = True
			BB_lbl_dispStartSerial.configure(text = "Blackbody in Cooldown Period")
			bb_index = 1
			app.after(delay * 1000, BB_serial) #wait 10 seconds, then turn off BB control
		else:
			bb_index += 1
			app.after(delay * 1000, BB_serial)

def BB_ethernet():
	global bb_index, bb_temps
	if(bb_index == 1):
		print("Starting Blackbody in ethernet mode...")
		BB_lbl_dispStartEthernet.configure(text = "Starting Blackbody in ethernet mode...")

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
	bb_actual_temp = []
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
		bb_actual_temp.append(bb_t)

	file = open(outfile, "w")  # change file name each time
	file.write(start_time + "\n")

	for i in range(len(bb_actual_temp)):
		split = bb_actual_temp[i].split()
		file.write(str(np.float64(split[-1])) + "\n")

	file.close()
	tn.close()

def BB_stop():
	global bb_running, bb_index
	bb_running = False
	bb_index = 1
	ser = serial.Serial(
			port='/dev/ttyS0', # Connect to port
			baudrate = 115200,   # baud rate per the manual
			parity=serial.PARITY_NONE,    # parity per the manual
			stopbits=serial.STOPBITS_ONE, # stop bits per the manual
			bytesize=serial.EIGHTBITS,    # byte size per the manual
			timeout=1	
	)
	
	# DAxx.x sets the absolute temperature
	# ex: DA25.0 sets the abs. temp. to 25 C
	command = ("DA" + format(25, '.1f') + "\n").encode('ascii')  # set temp
	ser.write(command)
	BB_btn_compute.grid()
	BB_btn_startSerial.grid_remove()
	BB_btn_startEthernet.grid_remove()
	
	ser.close()
	
	
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
			EC_lbl_entry_error.configure(text = error_msg)
		EC_lbl_entry_error.configure(text = error_msg)
		EC_lbl_entry_error.grid()
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
		EC_lbl_entry_error.configure(text = error_msg)
		EC_lbl_entry_error.grid()
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
		EC_btn_start_pause.configure(text = "Pause Profile")
		EC_lbl_entry_error.configure(text = "Running Profile: " + cb_profile_select.get())
		client.write_registers(16564, 147)
	else:
		print("Pausing")
		paused = True
		EC_btn_start_pause.configure(text = "Resume Profile")
		EC_lbl_entry_error.configure(text = "Profile Paused")
		client.write_registers(16566, 146)
    
#start program with selected profile
def start_button():
	print("Start")
	EC_btn_start_pause.configure(text = "Pause Profile", command = pause_button)
	EC_btn_term.grid()
	
	#hide other options to prevent accidental operation
	for ent in EC_ents_custom:
		ent.grid_remove()
	EC_btn_custom.grid_remove()
	EC_btn_read_file.grid_remove()
	EC_ent_file.grid_remove()
	EC_lbl_profile_select.grid_remove()
	EC_cb_profile_select.grid_remove()
	
	print(str(EC_cb_profile_select.get()))
	EC_cb_profile_select.configure(state = "disabled")
	client.write_registers(16558, int(EC_cb_profile_select.get())) #Load profile number
	client.write_registers(16562, 1782) #Start process controller
	
	#label for telling user the program is running
	EC_lbl_entry_error.configure(text = "Running Profile: " + cb_profile_select.get())
	
def term_button():
	print("Terminating")
	EC_btn_start_pause.configure(text = "Start Profile", command = start_button)
	EC_btn_term.grid_remove()
	#show custom program components
	for ent in EC_ents_custom:
		ent.grid()
		ent.configure(state = "normal")
	EC_btn_read_file.grid() #redisplay buttons for reading file and custom 
	EC_btn_custom.grid()
	EC_ent_file.grid()
	EC_lbl_profile_select.grid()
	EC_cb_profile_select.grid()
	
	EC_cb_profile_select.configure(state = "normal")
	client.write_registers(16566, 148)
	
	time.sleep(1) #delay to allow termination to finish
	
	EC_lbl_entry_error.configure(text = "Profile Terminated")
	set_temp(23)
	
def custom_button():
	global custom
	#get user input, create custom step and validate
	begin_input = EC_ent_begin.get()
	end_input = EC_ent_end.get()
	ramp_input = EC_ent_ramp.get()
	time_input = EC_ent_time.get()
	custom = ECCustomStep(begin_input, end_input, ramp_input, time_input)
	if(not custom.validate_EC_inputs()):
		#disable user input into entry
		for ent in EC_ents_custom:
			ent.configure(state = "disabled")

		#change button to confirm and show edit button
		EC_btn_custom.configure(text = "Confirm Program", command = confirm_button)
		EC_btn_edit_custom.configure(text = "Edit Custom Program", command = edit_button)
		EC_btn_edit_custom.grid()
		
def edit_button():
	#renable entry elements and hide custom button
	for ent in EC_ents_custom:
		ent.configure(state = "normal")
	EC_btn_custom.configure(text = "Create Custom Program", command = custom_button)
	EC_btn_edit_custom.grid_remove()

def confirm_button():
	global remaining_time, paused, remaining_time_total
	print("Program confirmed")
	custom.start()
	paused = False
	#begin program, calculate remaining time of first step and total program
	remaining_time = custom.time * 60
	remaining_time_total = remaining_time * (custom.temps.size)
	
	EC_btn_custom.configure(text = "Pause Custom Program", command = pause_custom_button)
	
	#prevent editing, starting a profile, or loading a file
	EC_btn_edit_custom.grid_remove()
	EC_btn_start_pause.grid_remove()
	EC_btn_read_file.grid_remove()
	
def pause_custom_button():
	global paused, remaining_time, remaining_time_total ,custom
	if(paused):
		#resume using new start time for step
		print("Resuming")
		paused = False
		EC_btn_custom.configure(text = "Pause Custom Program")
		
		read = client.read_holding_registers(address = 14660 ,count = 1)
		custom.current_time = int(read.registers[0])
	else:
		print("Pausing")
		paused = True
		EC_btn_custom.configure(text = "Resume Custom Program")
		EC_btn_edit_custom.configure(text = "Terminate Custom Program", command = terminate_custom_button)
		EC_btn_edit_custom.grid()
		
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
	EC_btn_custom.configure(text = "Create Custom Program", command = custom_button)
	for ent in EC_ents_custom:
		ent.configure(state = "normal")
	EC_btn_edit_custom.grid_remove()
	
	EC_lbl_entry_error.configure(text = "Program Terminated")

	#show buttons for using profiles and reading a file
	EC_btn_start_pause.grid()
	EC_btn_read_file.grid()
	
	#set chamber set point to 23 C
	set_temp(23)

def file_button():
	file_name = EC_ent_file.get()
	#read file, print error message if fail
	try:
		custom.read_file(file_name)
		if(not custom.validate_file_inputs()):
			EC_btn_custom.configure(text = "Confirm Program", command = confirm_button)
			#change button to confirm and show edit button
			EC_btn_edit_custom.configure(text = "Edit Custom Program", command = edit_button)
			EC_btn_edit_custom.grid()
	except OSError as e:
		error_msg = "Unable to open file."
		EC_lbl_entry_error.configure(text = error_msg)
		EC_lbl_entry_error.grid()

def update():
	global disconnected
	try:
		#attempt to reconnect if chamber disconnected
		if(disconnected):
			EC_lbl_entry_error.configure(text = "No Chamber Connection")
			client.connect()
			if client.is_socket_open():
				disconnected = False
				print("Chamber Reconnected!")		
				EC_lbl_entry_error.configure(text = "Chamber Ready")

		
		#repeat after a half-second
		EC_lbl_temp.after(500, update)
		
		#update temp label
		read = client.read_holding_registers(address = 16664 ,count = 4)
		decoder = BinaryPayloadDecoder.fromRegisters(read.registers, Endian.Big, wordorder=Endian.Little)
		current_temp = decoder.decode_32bit_float()
		
		decoder.reset()
		read = client.read_holding_registers(address = 2782, count = 4)
		decoder = BinaryPayloadDecoder.fromRegisters(read.registers, Endian.Big, wordorder=Endian.Little)

		set_point_temp = decoder.decode_32bit_float()
		EC_lbl_temp.configure(text = "Current Temperature: " + "{:.1f}".format(current_temp) + " C\nSet Point: " + "{:.1f}".format(set_point_temp) + " C")
		
		#update humidity label
		decoder.reset()
		read = client.read_holding_registers(address = 16666 ,count = 4)
		decoder = BinaryPayloadDecoder.fromRegisters(read.registers, Endian.Big, wordorder=Endian.Little)
		current_humidity = decoder.decode_32bit_float()
		EC_lbl_hum.configure(text = "Current Humidity: " + "{:.1f}".format(current_humidity) + "%")

		#update time
		update_time()
	except pymodbus.exceptions.ModbusException as e:
		EC_lbl_entry_error.configure(text = "No Chamber Connection")
		print("No Chamber Connection")
		disconnected = True
	except  AttributeError:
		EC_lbl_entry_error.configure(text = "No Chamber Connection")
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
	EC_lbl_time.configure(text = time_str)
	
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
		EC_lbl_entry_error.configure(text = time_str)
		#check if elapsed time exceeds remaining time
		if(elapsed_time > remaining_time):
			#decrement time by an interval
			remaining_time_total -= custom.time * 60
			#next_step returns true if final step was completed
			if(custom.next_step()):
					EC_btn_custom.configure(text = "Create Custom Program", command = custom_button)
					EC_lbl_entry_error.configure(text = "Program Finished!")
					for ent in EC_ents_custom:
						ent.configure(state = "normal")
					EC_btn_start_pause.grid()
					EC_btn_read_file.grid()
					EC_btn_edit_custom.grid_remove()
					
					EC_ent_file.grid()
					set_temp(23)
		
#GUI objects for EC chamber
app = ctk.CTk() 
EC_lbl_temp = ctk.CTkLabel(master=app, text="No Temp Recorded", width=120, height = 25)
EC_lbl_hum= ctk.CTkLabel(master=app, text="No Humidity Recorded", width=120, height = 25)
EC_lbl_profile_select= ctk.CTkLabel(master=app, text="Program Number", width=120, height = 25)
EC_lbl_entry_error= ctk.CTkLabel(master=app, text="Chamber Ready", width=120, height = 25)
EC_lbl_time= ctk.CTkLabel(master=app, text="No Chamber Connection", width=120, height = 25, font=("Arial", 30))

EC_btn_term = ctk.CTkButton(master = app, width = 120, height = 32, border_width = 1, text = "Terminate Profile", command = term_button)
EC_btn_start_pause = ctk.CTkButton(master = app, width = 120, height = 32, border_width = 1, text = "Start Profile", command = start_button)
EC_btn_custom = ctk.CTkButton(master = app, width = 120, height = 64, border_width = 1, text = "Create Custom Program", command = custom_button)
EC_btn_edit_custom = ctk.CTkButton(master = app, width = 120, height = 64, border_width = 1, text = "Edit Custom Program", command = edit_button)
EC_btn_read_file = ctk.CTkButton(master = app, width = 120, height = 32, border_width = 1, text = "Load File", command = file_button)
EC_cb_profile_select = ctk.CTkComboBox(master = app, values =["1", "2", "3", "4", "5"])

EC_ent_begin = ctk.CTkEntry(master=app, width = 140, placeholder_text="Beginning Temp (\N{DEGREE CELSIUS})")
EC_ent_end = ctk.CTkEntry(master=app, width = 140, placeholder_text="Ending Temp (\N{DEGREE CELSIUS})")
EC_ent_ramp = ctk.CTkEntry(master=app, width = 140, placeholder_text="Temp Step (\N{DEGREE CELSIUS})")
EC_ent_time = ctk.CTkEntry(master=app, width = 140, placeholder_text="Hold Time (minutes)")
EC_ent_file = ctk.CTkEntry(master = app, width = 140, placeholder_text=" Input File Name")

EC_ents_custom = [EC_ent_begin, EC_ent_end, EC_ent_ramp, EC_ent_time]

#GUI objects for BB program
# entry labels
BB_frm_labels = ctk.CTkFrame(master=app)

BB_lbl_topMsg = ctk.CTkLabel(master=app, text="Blackbody Controller", font=("Arial", 30))

BB_lbl_startTemp = ctk.CTkLabel(master=BB_frm_labels, text="Start Temperature: ", width=120, height = 25)
BB_lbl_endTemp = ctk.CTkLabel(master=BB_frm_labels, text="End Temperature: ")
BB_lbl_step = ctk.CTkLabel(master=BB_frm_labels, text="Temperature Step: ")
BB_lbl_delay = ctk.CTkLabel(master=BB_frm_labels, text="Hold Time: ")
BB_lbl_outfile = ctk.CTkLabel(master=BB_frm_labels, text="Output Filename: ")

BB_frm_entries = ctk.CTkFrame(master=app)

BB_ent_startTemp = ctk.CTkEntry(master=BB_frm_entries, width = 140, placeholder_text="Beginning Temp (\N{DEGREE CELSIUS})")
BB_ent_endTemp = ctk.CTkEntry(master=BB_frm_entries, width = 140, placeholder_text="Ending Temp (\N{DEGREE CELSIUS})")
BB_ent_step = ctk.CTkEntry(master=BB_frm_entries, width = 140, placeholder_text="Temp Step (\N{DEGREE CELSIUS})")
BB_ent_delay = ctk.CTkEntry(master=BB_frm_entries, width = 140, placeholder_text="Hold Time (minutes)")
BB_ent_outfile = ctk.CTkEntry(master=BB_frm_entries, width = 140, placeholder_text="Outfile Name")

BB_frm_units = ctk.CTkFrame(master=app)

""" lbl_startTempC = ctk.CTkLabel(master=frm_units, text="\N{DEGREE CELSIUS}")
lbl_endTempC = ctk.CTkLabel(master=frm_units, text="\N{DEGREE CELSIUS}")
lbl_stepC = ctk.CTkLabel(master=frm_units, text="\N{DEGREE CELSIUS}")
lbl_delayM = ctk.CTkLabel(master=frm_units, text="minutes")
lbl_outfileTxt = ctk.CTkLabel(master=frm_units, text=".txt") """

BB_frm_displays = ctk.CTkFrame(master=app)

BB_lbl_dispStartTemp = ctk.CTkLabel(master=BB_frm_displays, text = "")
BB_lbl_dispEndTemp = ctk.CTkLabel(master=BB_frm_displays, text = "")
BB_lbl_dispStep = ctk.CTkLabel(master=BB_frm_displays,text = "")
BB_lbl_dispDelay = ctk.CTkLabel(master=BB_frm_displays, text = "")
BB_lbl_dispOutfile = ctk.CTkLabel(master=BB_frm_displays, text = "")
BB_lbl_entry_error= ctk.CTkLabel(master=app, text="Blackbody Ready", width=120, height = 25)

BB_frm_entBtns = ctk.CTkFrame(master=app)

BB_btn_startEnter = ctk.CTkButton(
	master=BB_frm_entBtns,
	text="ENTER",
	command=BB_read_startTemp
	# run this subroutine when button is pressed
)
BB_btn_endEnter = ctk.CTkButton(
	master=BB_frm_entBtns,
	text="ENTER",
	command=BB_read_endTemp
	# run this subroutine when button is pressed
)
BB_btn_stepEnter = ctk.CTkButton(
	master=BB_frm_entBtns,
	text="ENTER",
	command=BB_read_step # run this subroutine when button is pressed
)
BB_btn_delayEnter = ctk.CTkButton(
	master=BB_frm_entBtns,
	text="ENTER",
	command=BB_read_delay # run this subroutine when button is pressed
)
BB_btn_outfileEnter = ctk.CTkButton(
	master=BB_frm_entBtns,
	text="ENTER",
	command= BB_read_outfile  # run this subroutine when button is pressed
)

# compute sweep
BB_lbl_dispSweep = ctk.CTkLabel(master=app, text = "")
BB_btn_compute = ctk.CTkButton(
	master=app,
	text="Compute Sweep",
	command = BB_compute  # run this subroutine when button is pressed
)

# start buttons
BB_lbl_dispStartSerial = ctk.CTkLabel(master=app, text = "")
BB_lbl_dispStartEthernet = ctk.CTkLabel(master=app, text = "")
BB_btn_startSerial = ctk.CTkButton(
	master=app,
	text="Start Serial",
	command=lambda: BB_serial() # run this subroutine when button is pressed
)
BB_btn_startEthernet = ctk.CTkButton(
	master=app,
	text="Start Ethernet",
	command=lambda: BB_ethernet(temps=temps, delay=delay, outfile=outfile, lbl=BB_lbl_dispStartEthernet) # run this subroutine when button is pressed
)

BB_btn_stop = ctk.CTkButton(
	master=app,
	text="Stop",
	command=BB_stop() # run this subroutine when button is pressed
)

#start point of program
if __name__ == "__main__":
	print("Running main")
	print("Connecting to chamber...")
	try:
		client.connect()		
		print("Connected!")
	except pymodbus.exceptions.ModbusException as e:
		print("Connection Failed")
		lbl_entry_error.configure(text = "No Connection to Chamber")
		disconnected = True
	
	ctk.set_appearance_mode("dark")
	ctk.set_default_color_theme("blue")

	#set window size and title
	app.geometry("1200x720")	
	app.title("Chamber Controller")
	app.resizable(width=False, height=False)
	
	#place labels
	EC_lbl_time.grid(row = 1, column=3, padx = 40, pady = 5)
	EC_lbl_temp.grid(row = 2, column=3, padx = 40, pady = 5)
	EC_lbl_hum.grid(row = 3, column=3, padx = 40, pady = 5)
	EC_lbl_profile_select.grid(row = 1, column = 2, padx = 40, pady = 5)
	EC_lbl_entry_error.grid(row = 4, column = 3, padx = 40, pady = 5)

	#place buttons and hide terminate and custom button
	EC_btn_start_pause.grid(row = 1, column=1, padx = 40, pady = 5)
	EC_btn_term.grid(row = 2, column=1, padx = 40, pady = 5)
	EC_btn_term.grid_remove()
	EC_btn_custom.grid(row = 3, column = 1, padx = 40, pady = 5)
	EC_btn_edit_custom.grid(row = 4, column = 1, padx = 40, pady = 5)
	EC_btn_edit_custom.grid_remove()
	EC_btn_read_file.grid(row = 7, column = 1, padx = 40, pady = 5)
	#place combo box on grid
	EC_cb_profile_select.grid(row = 2, column = 2, padx = 40, pady = 5)
	
	#place entry fields on grid
	EC_ent_begin.grid(row=3, column = 2, padx = 40, pady = 5)
	EC_ent_end.grid(row=4, column = 2, padx = 40, pady = 5)
	EC_ent_ramp.grid(row=5, column = 2, padx = 40, pady = 5)
	EC_ent_time.grid(row=6, column = 2, padx = 40, pady = 5)
	EC_ent_file.grid(row=7, column = 2, padx = 40, pady = 5)
	
	#########     BB GUI                   ####################

	""" lbl_startTemp.grid(row=8, column=0, pady=6)
	lbl_endTemp.grid(row=9, column=0, pady=6)
	lbl_step.grid(row=10, column=0, pady=6)
	lbl_delay.grid(row=11, column=0, pady=6)
	lbl_outfile.grid(row=12, column=0, pady=6) """

	# place entry widgets
	BB_ent_startTemp.grid(row=8, column = 2, padx = 40, pady = 5)
	BB_ent_endTemp.grid(row=9, column = 2, padx = 40, pady = 5)
	BB_ent_step.grid(row=10, column = 2, padx = 40, pady = 5)
	BB_ent_delay.grid(row=11, column = 2, padx = 40, pady = 5)
	BB_ent_outfile.grid(row=12, column = 2, padx = 40, pady = 5)

	# entry units
	""" 	lbl_startTempC.grid(row=8, column=0, sticky="w", pady=6)
	lbl_endTempC.grid(row=9, column=0, sticky="w", pady=6)
	lbl_stepC.grid(row=10, column=0, sticky="w", pady=6)
	lbl_delayM.grid(row=11, column=0, sticky="w", pady=6)
	lbl_outfileTxt.grid(row=12, column=0, sticky="w", pady=6) """

	# display labels
	BB_lbl_dispStartTemp.grid(row=8, column=0, pady=6, sticky="w")
	BB_lbl_dispEndTemp.grid(row=9, column=0, pady=6, sticky="w")
	BB_lbl_dispStep.grid(row=10, column=0, pady=6, sticky="w")
	BB_lbl_dispDelay.grid(row=11, column=0, pady=6, sticky="w")
	BB_lbl_dispOutfile.grid(row=12, column=0, pady=6, sticky="w")
	BB_lbl_entry_error.grid(row = 9, column = 3)
	# enter buttons
	""" btn_startEnter.grid(row=8, column=0, pady=3)
	btn_endEnter.grid(row=9, column=0, pady=3)
	btn_stepEnter.grid(row=10, column=0, pady=3)
	btn_delayEnter.grid(row=11, column=0, pady=3)
	btn_outfileEnter.grid(row=12, column=0, pady=3) """

	# pack it all
	BB_lbl_topMsg.grid(row=8, columnspan=3, column = 1)
	#frm_labels.grid(row=9, column=0, padx=10, pady=10)
	BB_frm_entries.grid(row=9, column=2, padx=10, pady=10)
	#frm_units.grid(row=9, column=2, padx=10, pady=10)
	#frm_entBtns.grid(row=9, column=3, padx=10, pady=10)
	BB_frm_displays.grid(row=9, column=4, padx=10, pady=10)
	BB_btn_compute.grid(row=9, column=1, padx=10, pady=10)
	BB_lbl_dispSweep.grid(row=10, column=2, columnspan=3, padx=10, pady=10)
	BB_btn_startSerial.grid(row=10, column=0, columnspan=2, padx=10, pady=10)
	BB_btn_startEthernet.grid(row=11, column=0, columnspan=2, padx=10, pady=10)
	BB_btn_stop.grid(row=12, column=0, columnspan=2, padx=10, pady=10)
	BB_lbl_dispStartSerial.grid(row=12, columnspan=5, padx=10, pady=10)
	BB_lbl_dispStartEthernet.grid(row=12, columnspan=5, padx=10, pady=10)
	
	BB_btn_startSerial.grid_remove()
	BB_btn_startEthernet.grid_remove()
	
	bb_index = 1
	#begin running update
	update()
	
	#open window
	app.mainloop()
