#!/usr/bin/env python

# Script for GUI for chamber control using the TPS
# Environmental Chamber's Watlow F4T panel

# Utilizes ethernet to
# control F4T with Telnet

# Author: Austin Martinez, Christian Secular


from pymodbus.client import ModbusTcpClient
from pymodbus.payload import BinaryPayloadDecoder
from pymodbus.constants import Endian
import pymodbus

import tkinter
import customtkinter

# declare and open a Modbus connection to the EC
client = ModbusTcpClient("169.254.18.153", port=502, timeout=3)
paused = False


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
	print(str(cb_profile_select.get()))
	cb_profile_select.configure(state = "disabled")
	client.write_registers(16558, int(cb_profile_select.get())) #Load profile number
	client.write_registers(16562, 1782) #Start process controller
	
def term_button():
	print("Terminating")
	btn_start_pause.configure(text = "Start Profile", command = start_button)
	btn_term.grid_remove()
	cb_profile_select.configure(state = "normal")
	client.write_registers(16566, 148)

def update():
	#update temp label
	read = client.read_holding_registers(address = 16664 ,count = 4)
	decoder = BinaryPayloadDecoder.fromRegisters(read.registers, Endian.Big, wordorder=Endian.Little)
	#print("Current Temperature: " + "{:.1f}".format(decoder.decode_32bit_float()) + " C")
	lbl_temp.configure(text = "Current Temperature: " + "{:.1f}".format(decoder.decode_32bit_float()) + " C")
	
	#update humidity label
	read = client.read_holding_registers(address = 16666 ,count = 4)
	lbl_hum.configure(text = "Current Humidity: " + "{:.1f}".format(decoder.decode_32bit_float()) + "%")
	
	#repeat after 10s
	lbl_temp.after(1000, update)
	


#GUI objects
app = customtkinter.CTk() 
lbl_temp = customtkinter.CTkLabel(master=app, text="No Temp Recorded", width=120, height = 25)
lbl_hum= customtkinter.CTkLabel(master=app, text="No Humidity Recorded", width=120, height = 25)
lbl_profile_select= customtkinter.CTkLabel(master=app, text="Program Number", width=120, height = 25)
btn_term = customtkinter.CTkButton(master = app, width = 120, height = 32, border_width = 1, text = "Terminate Profile", command = term_button)
btn_start_pause = customtkinter.CTkButton(master = app, width = 120, height = 32, border_width = 1, text = "Start Profile", command = start_button)
cb_profile_select = customtkinter.CTkComboBox(master = app, values =["1", "2", "3", "4", "5"])

if __name__ == "__main__":
	print("Running main")
	print("Connecting to chamber...")
	client.connect()
	print("Connected!")
	read = client.read_holding_registers(address = 16664 ,count = 4)
	decoder = BinaryPayloadDecoder.fromRegisters(read.registers, Endian.Big, wordorder=Endian.Little)
	print("Current Temperature: " + "{:.1f}".format(decoder.decode_32bit_float()) + " C")
	customtkinter.set_appearance_mode("dark")
	customtkinter.set_default_color_theme("blue")

	
	#set window size and title
	app.geometry("720x240")	
	app.title("Chamber Controller")
	app.resizable(width=False, height=False)

	#place labels
	lbl_temp.grid(row = 1, column=3, padx = 40, pady = 5)
	lbl_hum.grid(row = 2, column=3, padx = 40, pady = 5)
	lbl_profile_select.grid(row = 1, column = 2, padx = 40, pady = 5)
	
	#place buttons and hide terminate button
	btn_start_pause.grid(row = 1, column=1, padx = 40, pady = 5)
	btn_term.grid(row = 2, column=1, padx = 40, pady = 5)
	btn_term.grid_remove()
	
	#place combo box on grid
	cb_profile_select.grid(row = 2, column = 2, padx = 40, pady = 5)
	
	update()
	app.mainloop()



