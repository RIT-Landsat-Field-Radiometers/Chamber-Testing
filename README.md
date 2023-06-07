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
			        
**EXAMPLES**\
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
			
