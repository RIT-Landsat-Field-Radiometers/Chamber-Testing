# Blackbody and Environmental Control Scripts


This folder contains scripts to control the Blackbody controller
and the environmental chamber, as well as the output files generated
by both of these scripts.

Below are the manual pages for the scripts.

**NAME**\
BB_controller.py
A script that is used to initiate a temperature sweep on the Blackbody.

**SYNOPSIS**
```
python BB_controller.py [-hg] [-b temperature] [-e temperature] [-s temperature] [-d time] [-o filename] [-m mode]
```
	
**DESCRIPTION**\
BB_controller.py is used to configure a temperature sweep for the
SBIR Blackbody to perform. The script can be configured to run
using Ethernet or Serial communication, depending on how the
Raspberry Pi is connected to the Blackbody controller. The script
can either be run by giving the parameters as options in the
command line, or by opening a GUI and inputting them there.
	
The options are as follows:
      
    -h, --help            
    		Print help.
    
    -g, --gui             
    		Run the graphical interface.
    
    -b, --begin [value]   
    		Enter the beginning temperature value as an integer
    
    -e, --end [value]     
    		Enter the end temperature value as an integer
                          
    -s, --step [value]    
    		Enter the temperature step value as an integer
                                                               
    -d, --delay [value]   
    		Enter the holding time value as an integer
    
    -o, --outfile [file]  
    		Enter the output filename ending in .txt
                  
    -m, --mode [string]  
    		Enter the blackbody mode, either 'serial' or 'ethernet'
			        
**EXAMPLES**
```
python BB_controller.py -g
```
This will open the script in GUI mode, allowing the user
			to input values and click buttons to start the script.
			
```
python BB_controller.py -b 10 -e 55 -s 5 -d 5 -o 123.txt -m serial
```
This will start the script without a GUI. The script will
then output a calculated sweep in the form 
[25 10 15 20 25 30 35 40 45 50], showing the temperatures
from last to first, ending on 25C. The script will then ask
the user if this sweep looks as they wanted, to which the
user answers "y" for yes, and "n" for no. If yes, the script
will begin blackbody operation in serial mode. If no, the 
script exits and the user must try again.
			
**NAME**\
EC_controller.py:
This script is used to control the TC180 controller via the Watlow F4T controller. 

**SYNOPSIS**
```
python EC_controller.py [command] [input value 1] [input value 2]
```
	
**DESCRIPTION**\
EC_controller.py is used to run commands on the chamber using a Raspberry Pi. Modbus is used to communicate with the chamber and an ethernet connection between the chamber and the Pi is required. Below is a list of commands that can be run using the scripts.
 
    -h        
    		Display list of commands.
    
    -w [reg] [val]           
    		Write [val] to register [reg]
    
    -wf [reg] [val]  
    		Write a IEEE float [val] to register [reg]
    
    -r [reg] [count]   
    		Read [count] values from register [reg]
                          
    -rf [reg]  
    		Read a IEEE float from register [reg]
                                                            
    -st [temp]
    		Set the chamber's temperature set point to [temp]. [temp] must be between -45 C and 180 C
    
    -pf [pf-num]
			Begin the profile with the same number as the profile saved in the chamber controller. This profile must be created on the controller.
                  
    -s
    		Prints chamber's current temperature. If a profile is running, the profile number and current step will be printed.
	
	-p
			Pauses the profile currently running on the chamber.

	-up
			Resumes the profile currently running.

	-t
			Terminates the profile currently running and sets chamber set point to 23 C.

**EXAMPLES**
```
python EC_controller.py -pf 3
```
This will beginning running profile 3 on the chamber.

```
python EC_controller.py -st 30
```
This command will set the chamber's temperature set point to 30 C

```
python EC_controller.py -w 16566 146
```
Writes 146 to register 16566, which will pause the profile currently running on the chamber if there is one. Equivalent to running 
```
python EC_controller.py -p
```
**NAME**\
EC_controller_gui.py:
This script launches a GUI that allows the user to monitor the chamber, run profiles, and run custom-made programs (WIP)

**SYNOPSIS**
```
python EC_controller_gui.py
```
	
**DESCRIPTION**\
The GUI will provide the user with the chamber's current temperature and set point, the current humidity, and the ability to start a new profile by selecting its number from the drop-down menu. Once a profile is started, it can be paused or terminated. A custom program can also be created by choosing "Custom Program", entering a starting temperature, ending temp, rate, and time (in minutes) at each step. Custom temperatures can be added by reading in a text file. The first line should be the desired temperature steps separated by a space and the second line of the text file should be the number of minutes to wait in between each step.

```
0 25 40 57.5
110
```

This will set the chamber to 0 C, to 25 C, and then to 40 C, waiting at each temperature for 110 minutes until staying at 57.5 C until a new set point is loaded.