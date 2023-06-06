#!/usr/bin/env python

# Script for interfacing with the TPS
# Encironmental Cahmber's Watlow F4T panel

# Utilizes ethernet to
# control F4T with Telnet

# Author: Austin Martinez

from pymodbus.client import ModbusTcpClient
import pymodbus

# declare and open a Modbus connection to the EC
client = ModbusTcpClient("169.254.18.153", port=502, timeout=3)
print("Connecting to chamber...")
client.connect()
print("Connected!")

# read the number of profiles
read = client.read_holding_registers(address = 48000 ,count = 1)
print("There are " + str(read.registers) + " profiles")

# list the profiles
read = client.read_holding_registers(address = 48002 ,count = 10)
print(read.registers)
read = client.read_holding_registers(address = 18566 ,count = 10)
print(read.registers)

# run a test profile
print("Starting profile")
pymodbus.register_write_message.WriteSingleRegisterRequest(16558, 4)
pymodbus.register_write_message.WriteSingleRegisterRequest(16562, 1782)

