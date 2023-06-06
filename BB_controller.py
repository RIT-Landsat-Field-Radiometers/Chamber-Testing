#!/usr/bin/env python

# Script for interfacing with the SBIR
# Blackbody Controller

# Utilizes ethernet or serial to
# control BB with Telnet or UART, respectively

# Authors: Austin Martinez, Lucy Falcon

import getopt, sys, os, re  # for command line and file IO
import telnetlib            # for ethernet connection
import serial               # for serial connection
import numpy as np          # for array manipulation
import tkinter as tk        # for the gui
import time                 # for the delay

global startTemp
global endTemp
global step
global delay
global outfile
global temps


def main():
    global startTemp
    global endTemp
    global step
    global delay
    global outfile
    global temps
    startTemp = -1000
    endTemp = -1000
    step = -1000
    delay = -1000
    outfile = ""
    temps = []

   # get user input from input arguments
    try:
        opts, args = getopt.getopt(sys.argv[1:], "hgb:e:s:d:o:m:",
                                   ["help",  "gui", "begin=", "end=", "step=", "delay=", "outfile=", "mode="])
    except getopt.GetoptError as err:
        # print help information and exit:
        print(err)  # will print something like "option -a not recognized"
        helpexit()
    for o, a in opts:
        if o in ("-h", "--help"):
            helpexit()
        elif o in ("-g", "--gui"):
            run_gui()
        elif o in ("-b", "--begin"):
            begin = int(a)
        elif o in ("-e", "--end"):
            end = int(a)
        elif o in ("-s", "--step"):
            step = int(a)
        elif o in ("-d", "--delay"):
            delay = int(a)        
        elif o in ("-o", "--outfile"):
            outfile = a
        elif o in ("-m", "--mode"):
            mode = a            
        else:
            assert False, "unhandled option"
            
    # check to see if all inputs were given
    if not((begin > -1000) and (end > -1000) and (step > -1000) and (delay > -1000) and outfile and mode):
        print("Invalid input. Please try again.")
        helpexit()
    # if they were, make sure they are all valid
    elif (begin > -1000) and (end > -1000) and (step > -1000) and (delay > -1000) and outfile and mode:
        validate_inputs(begin=begin, end=end, step=step, delay=delay, outfile=outfile, mode=mode)

    # initialize temperature array
    temps = np.arange(begin, end, step)  # temps in [C]
    temps = np.append(25, temps)  # make sure the script leaves the BB at 25C
    
    # confirm temperatures, steps, and delay with user
    print("Temperature values based on your input are:")
    print(temps)
    print("Holding each temperature for " + str(delay) + " minutes.")
    print("Sweep will be done in reverse order, ending on 25 C.")

    user_input = input('Do you accept these values? (y/n): ')
    while user_input.lower() != 'y':
        if user_input.lower() == 'n':
            print('Exiting. Please try again.')
            sys.exit(1)
        else:
            print('Please only type y or n')
            user_input = input('Do you accept these values? (y/n): ')
            continue
    
    # if the user confirms, go into BB operation
    print('Values accepted')
    
    # check mode and initiate respective subroutine
    if mode.lower() == 'serial':
        BB_serial(temps=temps, delay=delay, outfile=outfile)
    if mode.lower() == 'ethernet':
        BB_ethernet(temps=temps, delay=delay, outfile=outfile)
    

# TODO: maybe format outfile to be CSV

# subroutine to validate the inputs given by the user
def validate_inputs( begin, end, step, delay, outfile, mode ) :

    print("Validating inputs...")
    
    if (begin < 0 or begin > 100) :    # check begin temp
        print("ERROR: Begin temperature must be between 0 and 100")
        sys.exit(1)
    if (end < begin+1 or end > 100) :    # check end temp
        print("ERROR: End temperature must be larger than begin temperature and between 0 and 100")
        sys.exit(1)
    if (step < 1) :         # check step
        print("ERROR: Temperature step must be at least 1C")
        sys.exit(1)
    if (delay < 5) :         # check step
        print("ERROR: Delay must be at least 5 minutes")
        sys.exit(1)
    if (len(outfile) < 1) : # check outfile
        print("ERROR: Invalid outfile name")
        sys.exit(1)
    if (mode.lower() != 'serial') and (mode.lower() != 'ethernet'):
        print("ERROR: Invalid mode. Mode must be 'serial' or 'ethernet'")
        sys.exit(1)
    
    print("Validated!")

# subroutine to read in starting temperature and validate it
def read_startTemp(lbl_dispStartTemp, ent_startTemp):
    global startTemp
    startTemp = int(ent_startTemp.get())
    if startTemp < 0:
        lbl_dispStartTemp["text"] = "Minimum start temperature is 0"
    elif startTemp > 100:
        lbl_dispStartTemp["text"] = "Maximum start temperature is 100"
    else:
        lbl_dispStartTemp["text"] = f"{startTemp}\N{DEGREE CELSIUS}"
        
# subroutine to read in end temperature and validate it
def read_endTemp(lbl_dispEndTemp, ent_endTemp, startTemp):
    global endTemp
    endTemp = int(ent_endTemp.get())
    if endTemp < startTemp+1:
        lbl_dispEndTemp["text"] = "End temperature must be larger than start temp"
    elif endTemp > 100:
        lbl_dispEndTemp["text"] = "Exceeded maximum end temperature of 100"
    else:
        lbl_dispEndTemp["text"] = f"{endTemp}\N{DEGREE CELSIUS}"
        
# subroutine to read in temperature step and validate it
def read_step(lbl_dispStep, ent_step):
    global step
    step = int(ent_step.get())
    if step < 1:
        lbl_dispStep["text"] = "Temperature step must be at least 1"
    else:
        lbl_dispStep["text"] = f"{step}\N{DEGREE CELSIUS}"
        
# subroutine to read in delay time and validate it
def read_delay(lbl_dispDelay, ent_delay):
    global delay
    delay = int(ent_delay.get())
    if delay < 5:
        lbl_dispDelay["text"] = "Time delay must be at least 5 minutes"
    else:
        lbl_dispDelay["text"] = f"{delay} minutes"
        
# subroutine to read in outfile and validate it
def read_outfile(lbl_dispOutfile, ent_outfile):
    global outfile
    try:
        outfile = ent_outfile.get()
    except ValueError:
        lbl_dispOutfile["text"] = "Please type a filename"
    if len(outfile) < 1:
        lbl_dispOutfile["text"] = "Please type a filename"
    else:
        lbl_dispOutfile["text"] = f"{outfile}.txt"
        outfile = outfile + ".txt"
        
def compute(lbl_dispSweep):
    # initialize temperature array
    global temps
    temps = np.arange(startTemp, endTemp, step)  # temps in [C]
    temps = np.append(25, temps)  # make sure the script leaves the BB at 25C
    lbl_dispSweep["text"] = f"{temps}\nSweep will be done in reverse order, ending on 25C"
    
def BB_serial(temps, delay, outfile):
    print("Starting Blackbody in serial mode...")
    print(outfile)
    
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
    
	
def BB_ethernet():
    print("Starting Blackbody in ethernet mode...")

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

# subroutine to run the graphical interface for inputting values
def run_gui() :
    # create new window
    window = tk.Tk()
    window.title("Blackbody Controller")
    window.resizable(width=False, height=False)
    window.geometry("1000x600")
    
    lbl_topMsg = tk.Label(master=window, text="Please click Enter button on screen after typing each input value.")
    
    # start temperature
    frm_startTemp = tk.Frame(master=window)
    lbl_startTemp = tk.Label(master=frm_startTemp, text="Start Temperature:")
    ent_startTemp = tk.Entry(master=frm_startTemp, width=5)
    lbl_startTempC = tk.Label(master=frm_startTemp, text="\N{DEGREE CELSIUS}")

    lbl_startTemp.grid(row=0, column=0, sticky="w")
    ent_startTemp.grid(row=0, column=1, sticky="nsew")
    lbl_startTempC.grid(row=0, column=2, sticky="e")

    lbl_dispStartTemp = tk.Label(master=window)
    btn_startEnter = tk.Button(
        master=window,
        text="ENTER",
        command=lambda: read_startTemp(lbl_dispStartTemp=lbl_dispStartTemp, ent_startTemp=ent_startTemp) # run this subroutine when button is pressed
    )

    # end temperature
    frm_endTemp = tk.Frame(master=window)
    lbl_endTemp = tk.Label(master=frm_endTemp, text="End Temperature:")
    ent_endTemp = tk.Entry(master=frm_endTemp, width=5)
    lbl_endTempC = tk.Label(master=frm_endTemp, text="\N{DEGREE CELSIUS}")

    lbl_endTemp.grid(row=1, column=0, sticky="w")
    ent_endTemp.grid(row=1, column=1, sticky="nsew")
    lbl_endTempC.grid(row=1, column=2, sticky="e")

    lbl_dispEndTemp = tk.Label(master=window)
    btn_endEnter = tk.Button(
        master=window,
        text="ENTER",
        command=lambda: read_endTemp(lbl_dispEndTemp=lbl_dispEndTemp, ent_endTemp=ent_endTemp, startTemp=startTemp) # run this subroutine when button is pressed
    )
    
    # temperature step
    frm_step = tk.Frame(master=window)
    lbl_step = tk.Label(master=frm_step, text="Temperature Step:")
    ent_step = tk.Entry(master=frm_step, width=5)
    lbl_stepC = tk.Label(master=frm_step, text="\N{DEGREE CELSIUS}")

    lbl_step.grid(row=2, column=0, sticky="w")
    ent_step.grid(row=2, column=1, sticky="nsew")
    lbl_stepC.grid(row=2, column=2, sticky="e")

    lbl_dispStep = tk.Label(master=window)
    btn_stepEnter = tk.Button(
        master=window,
        text="ENTER",
        command=lambda: read_step(lbl_dispStep=lbl_dispStep, ent_step=ent_step) # run this subroutine when button is pressed
    )
    
    # delay
    frm_delay = tk.Frame(master=window)
    lbl_delay = tk.Label(master=frm_delay, text="Holding Time:")
    ent_delay = tk.Entry(master=frm_delay, width=5)
    lbl_delayM = tk.Label(master=frm_delay, text="minutes")

    lbl_delay.grid(row=3, column=0, sticky="w")
    ent_delay.grid(row=3, column=1, sticky="nsew")
    lbl_delayM.grid(row=3, column=2, sticky="e")

    lbl_dispDelay = tk.Label(master=window)
    btn_delayEnter = tk.Button(
        master=window,
        text="ENTER",
        command=lambda: read_delay(lbl_dispDelay=lbl_dispDelay, ent_delay=ent_delay) # run this subroutine when button is pressed
    )

    # outfile
    frm_outfile = tk.Frame(master=window)
    lbl_outfile = tk.Label(master=frm_outfile, text="Output Filename:")
    ent_outfile = tk.Entry(master=frm_outfile, width=36)
    lbl_outfileTxt = tk.Label(master=frm_outfile, text=".txt")

    lbl_outfile.grid(row=3, column=0, sticky="w")
    ent_outfile.grid(row=3, column=1, sticky="nsew")
    lbl_outfileTxt.grid(row=3, column=2, sticky="e")

    lbl_dispOutfile = tk.Label(master=window)
    btn_outfileEnter = tk.Button(
        master=window,
        text="ENTER",
        command=lambda: read_outfile(lbl_dispOutfile=lbl_dispOutfile, ent_outfile=ent_outfile)  # run this subroutine when button is pressed
    )
    
    # compute sweep
    frm_sweep = tk.Frame(master=window)
    lbl_sweep = tk.Label(master=frm_sweep, text="Temperature Sweep:")
    
    lbl_sweep.grid(row=3, column=0, sticky="w")
    
    lbl_dispSweep = tk.Label(master=window, wraplength=360)
    btn_compute = tk.Button(
        master=window,
        text="Compute",
        command=lambda: compute(lbl_dispSweep=lbl_dispSweep) # run this subroutine when button is pressed
    )
    
    # start buttons
    btn_startSerial = tk.Button(
        master=window,
        text="Start Serial",
        command=lambda: BB_serial(temps=temps, delay=delay, outfile=outfile) # run this subroutine when button is pressed
    )

    btn_startEthernet = tk.Button(
        master=window,
        text="Start Ethernet",
        command=lambda: BB_ethernet(temps=temps, delay=delay, outfile=outfile) # run this subroutine when button is pressed
    )

    # pack everything and position in properly
    lbl_topMsg.grid(row=0, column=0, pady=10)
    
    frm_startTemp.grid(row=1, column=0, padx=10)
    btn_startEnter.grid(row=1, column=1, pady=10)
    lbl_dispStartTemp.grid(row=1, column=2, padx=50, pady=10)
    
    frm_endTemp.grid(row=2, column=0, padx=10)
    btn_endEnter.grid(row=2, column=1, pady=10)
    lbl_dispEndTemp.grid(row=2, column=2, padx=50, pady=10)

    frm_step.grid(row=3, column=0, padx=10)
    btn_stepEnter.grid(row=3, column=1, pady=10)
    lbl_dispStep.grid(row=3, column=2, padx=50, pady=10)
    
    frm_delay.grid(row=4, column=0, padx=10)
    btn_delayEnter.grid(row=4, column=1, pady=10)
    lbl_dispDelay.grid(row=4, column=2, padx=50, pady=10)
    
    frm_outfile.grid(row=5, column=0, padx=10)
    btn_outfileEnter.grid(row=5, column=1, pady=10)
    lbl_dispOutfile.grid(row=5, column=2, padx=50, pady=10)
    
    frm_sweep.grid(row=6, column=0, padx=10)
    btn_compute.grid(row=6, column=1, pady=10)
    lbl_dispSweep.grid(row=6, column=2)
    
    btn_startSerial.grid(row=7, column = 0, padx=10, pady=30)
    btn_startEthernet.grid(row=7, column = 1, padx=10, pady=30)
    
    # run the gui
    window.mainloop()



# subroutine to print a help message and exit the script
def helpexit() :
    print("-h --help                        : display help message")
    print("-g --gui                         : start the graphical interface")
    print("-b --begin      [int value]      : input start temperature (0C to 100C)")
    print("-e --end        [int value]      : input end temperature (0C to 100C)")
    print("-s --step       [int value]      : input temperature step")
    print("-d --delay      [int value]      : input delay time in minutes")
    print("-o --outfile    [filename.txt]   : input filename of output file")
    print("-m --mode       [string]         : input BB mode, 'serial' or 'ethernet'")
    print("\n")
    print("Must input begin, end, step, delay, outfile, and mode if not using gui")
    sys.exit(1)


if __name__ == "__main__":
    main()
