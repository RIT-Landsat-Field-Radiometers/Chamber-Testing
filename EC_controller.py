#!/usr/bin/env python

# Script for sending individual commands to the TPS
# Encironmental Cahmber's Watlow F4T panel

# Utilizes ethernet to
# control F4T with Telnet

# Author: Austin Martinez, Christian Secular

NUM_PROG = 3
from pymodbus.client import ModbusTcpClient
from pymodbus.payload import BinaryPayloadDecoder
from pymodbus.constants import Endian
import pymodbus
import sys

#input values
args = sys.argv[1:]
rw = str(args[0]) #r = read, w = write


# declare and open a Modbus connection to the EC
client = ModbusTcpClient("169.254.18.153", port=502, timeout=3)
print("Connecting to chamber...")
client.connect()
print("Connected!")

if(rw == "-w"):
	#Write 148 to 16566 to terminate current program
	reg = int(args[1]) #reg to write to
	val = int(args[2]) #value to write
	print("Writing " + str(val) + " to register " + str(reg))
	client.write_registers(reg, val)
elif (rw == "-r"): #read register
	reg = int(args[1]) #reg to read
	val = int(args[2]) #Num of values to read
	read = client.read_holding_registers(address = reg ,count = val)
	print("Register " + str(reg) + ": " + str(read.registers))

elif (rw == "-pf"): #run program number
	read = client.read_holding_registers(address = 48000 ,count = 1)
	val = int(args[1]) # Program number to begin
	if(val >= 1 and val <= NUM_PROG):
		client.write_registers(16558, val) #Load program number
		client.write_registers(16562, 1782) #Start process controller
		print("Running profile " + str(val))
	else:
		print("Input exceeds total number of profile: " + str(read))
elif (rw == "-p"): #pause profile
	print("Pausing profile")
	client.write_registers(16566, 146)
elif (rw == "-up"): #unpause profile
	print("Resuming profile")
	client.write_registers(16564, 147)
elif (rw == "-t"): #terminate profile
	print("Terminating profile")
	client.write_registers(16566, 148)
elif (rw == "-s"):
	print("Chamber Status")
	print("----------------------")

	#get chamber temp
	read = client.read_holding_registers(address = 16664 ,count = 4)
	decoder = BinaryPayloadDecoder.fromRegisters(read.registers, Endian.Big, wordorder=Endian.Little)
	print("Current Temperature: " + "{:.1f}".format(decoder.decode_32bit_float()) + " C")
	
	#get chamber humidity
	read = client.read_holding_registers(address = 16666 ,count = 4)
	print("Current Humidity: " + "{:.1f}".format(decoder.decode_32bit_float()) + "%")
	
	#read profile status
	read = client.read_holding_registers(address = 16568 ,count = 1)
	if(int(read.registers[0]) == 149):
		#read number of profile currently running
		read = client.read_holding_registers(address = 16588, count = 1)
		print("Profile Running: " + str(read.registers))
		
		read = client.read_holding_registers(address = 16590, count = 1)
		print("Current Step: " + str(read.registers))
	else:
		print("Profile running: None")
	
elif (rw == "-h"): #print list of commands
	print("-w (reg) (val)		: Write (val) to register (reg)")
	print("-r (reg) (count)		: Read (count) values from register (reg)" )
	print("-pf (pf_num)		: Begin pf (pf_num)")
	print("-s		: Chamber status")
	print("-p		: Pause program")
	print("-up		: Resume program")
	print("-t		: Terminate program")
	print("-h		: Print list of all commands")
else:
	print("ERROR: Invalid command, use command h to see all available commands")


