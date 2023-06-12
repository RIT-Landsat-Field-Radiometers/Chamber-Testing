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

import customtkinter

import numpy as np
import time



MAX_TEMP = 180
MIN_TEMP = -45
# declare and open a Modbus connection to the EC
client = ModbusTcpClient("169.254.18.153", port=502, timeout=3)
paused = False
remaining_time = 0 #variable for monitoring how much time is left in step
remaining_time_total = 0 
#object for step
class CustomStep:
	def __init__(self, begin_val=23, end_val=25, rate_val = 1, time_val = 1):
		self.begin = np.float32(begin_val) #temp to start at
		self.end = np.float32(end_val) #temp to end at 
		self.rate = np.float32(rate_val) #degrees in celsius to change by
		self.time = int(time_val) #time in minutes to stay at each temp

		self.temps = np.arange(self.begin, self.end + 1, self.rate, dtype=np.float32)
		self.running = 0
		self.current_time = 0
		self.step = 0

	#ensures the step is valid
	def validate_inputs(self):
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
		if(fail):
			lbl_entry_error.configure(text = error_msg)
		else:
			#print temperatures for confirmation
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
		self.step += 1;
		self.running = True
		
		#store time of day
		read = client.read_holding_registers(address = 14660 ,count = 1)
		self.current_time = read.registers[0]
		
		
	def next_step(self):
		#go to next temperature. If final step, return true
		set_temp(self.temps[self.step])
		self.step += 1;
		
		#store time of day
		read = client.read_holding_registers(address = 14660 ,count = 1)
		self.current_time = read.registers[0]
		
		
		if(self.step == len(self.temps)):
			self.running = False
			return True;
		return False

custom = CustomStep()

def pause_button():
	global paused
	if(paused):
		print("Resuming")
		paused = False
		btn_start_pause.configure(text = "Pause Profile")
		client.write_registers(16564, 147)
	else:
		print("Pausing")
		paused = True
		btn_start_pause.configure(text = "Resume Profile")
		client.write_registers(16566, 146)
    
	
#start program with selected profile
def start_button():
	print("Start")
	btn_start_pause.configure(text = "Pause Profile", command = pause_button)
	btn_term.grid()
	
	#hide custom profile buttons
	for ent in ents_custom:
		ent.grid_remove()
	btn_custom.grid_remove()
	
	print(str(cb_profile_select.get()))
	cb_profile_select.configure(state = "disabled")
	client.write_registers(16558, int(cb_profile_select.get())) #Load profile number
	client.write_registers(16562, 1782) #Start process controller
	
def term_button():
	print("Terminating")
	btn_start_pause.configure(text = "Start Profile", command = start_button)
	btn_term.grid_remove()
	#show custom program components
	for ent in ents_custom:
		ent.grid()
		ent.configure(state = "normal")
	btn_custom.grid_remove()
	btn_custom.grid()
	cb_profile_select.configure(state = "normal")
	client.write_registers(16566, 148)
	
	time.sleep(1) #delay to allow termination to finish
	set_temp(23)
	
def custom_button():
	global custom
	#get user input, create custom step and validate
	begin_input = ent_begin.get()
	end_input = ent_end.get()
	ramp_input = ent_ramp.get()
	time_input = ent_time.get()
	custom = CustomStep(begin_input, end_input, ramp_input, time_input)
	if(not custom.validate_inputs()):
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
	remaining_time_total = remaining_time * (custom.temps.size - 1)
	
	btn_custom.configure(text = "Pause Custom Program", command = pause_custom_button)
	
	#prevent editing and starting a profile
	btn_edit_custom.grid_remove()
	btn_start_pause.grid_remove()
	
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
	btn_start_pause.grid()
	lbl_entry_error.configure(text = "Program Terminated")
		
def update():
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

	#repeat after a half-second
	lbl_temp.after(500, update)
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
			if(custom.next_step()):
					btn_custom.configure(text = "Create Custom Program", command = custom_button)
					lbl_entry_error.configure(text = "Program Finished!")
					for ent in ents_custom:
						ent.configure(state = "normal")
					btn_start_pause.grid()
					btn_edit_custom.grid_remove()
	
	
#GUI objects
app = customtkinter.CTk() 
lbl_temp = customtkinter.CTkLabel(master=app, text="No Temp Recorded", width=120, height = 25)
lbl_hum= customtkinter.CTkLabel(master=app, text="No Humidity Recorded", width=120, height = 25)
lbl_profile_select= customtkinter.CTkLabel(master=app, text="Program Number", width=120, height = 25)
lbl_entry_error= customtkinter.CTkLabel(master=app, text="test", width=120, height = 25)
lbl_time= customtkinter.CTkLabel(master=app, text="time", width=120, height = 25, font=("Arial", 30))

btn_term = customtkinter.CTkButton(master = app, width = 120, height = 32, border_width = 1, text = "Terminate Profile", command = term_button)
btn_start_pause = customtkinter.CTkButton(master = app, width = 120, height = 32, border_width = 1, text = "Start Profile", command = start_button)
btn_custom = customtkinter.CTkButton(master = app, width = 120, height = 64, border_width = 1, text = "Create Custom Program", command = custom_button)
btn_edit_custom = customtkinter.CTkButton(master = app, width = 120, height = 64, border_width = 1, text = "Edit Custom Program", command = edit_button)

cb_profile_select = customtkinter.CTkComboBox(master = app, values =["1", "2", "3", "4", "5"])

ent_begin = customtkinter.CTkEntry(master=app, placeholder_text="Begin")
ent_end = customtkinter.CTkEntry(master=app, placeholder_text="End")
ent_ramp = customtkinter.CTkEntry(master=app, placeholder_text="Ramp")
ent_time = customtkinter.CTkEntry(master=app, placeholder_text="Time (minutes)")

ents_custom = [ent_begin, ent_end, ent_ramp, ent_time]

#start point of program
if __name__ == "__main__":
	print("Running main")
	print("Connecting to chamber...")
	client.connect()
	print("Connected!") #TODO: implement check for chamber connection
	read = client.read_holding_registers(address = 16664 ,count = 4)
	decoder = BinaryPayloadDecoder.fromRegisters(read.registers, Endian.Big, wordorder=Endian.Little)

	customtkinter.set_appearance_mode("dark")
	customtkinter.set_default_color_theme("blue")

	#set window size and title
	app.geometry("800x480")	
	app.title("Chamber Controller")
	app.resizable(width=False, height=False)
	
	#place labels
	lbl_time.grid(row = 1, column=3, padx = 40, pady = 5)
	lbl_temp.grid(row = 2, column=3, padx = 40, pady = 5)
	lbl_hum.grid(row = 3, column=3, padx = 40, pady = 5)
	lbl_profile_select.grid(row = 1, column = 2, padx = 40, pady = 5)
	lbl_entry_error.grid(row = 4, column = 3, padx = 40, pady = 5)
	lbl_entry_error.grid_remove()

	#place buttons and hide terminate and custom button
	btn_start_pause.grid(row = 1, column=1, padx = 40, pady = 5)
	btn_term.grid(row = 2, column=1, padx = 40, pady = 5)
	btn_term.grid_remove()
	btn_custom.grid(row = 3, column = 1, padx = 40, pady = 5)
	btn_edit_custom.grid(row = 4, column = 1, padx = 40, pady = 5)
	btn_edit_custom.grid_remove()

	#place combo box on grid
	cb_profile_select.grid(row = 2, column = 2, padx = 40, pady = 5)
	
	#place entry fields on grid
	ent_begin.grid(row=3, column = 2, padx = 40, pady = 5)
	ent_end.grid(row=4, column = 2, padx = 40, pady = 5)
	ent_ramp.grid(row=5, column = 2, padx = 40, pady = 5)
	ent_time.grid(row=6, column = 2, padx = 40, pady = 5)
	
	#begin running update
	update()

	#open window
	app.mainloop()



