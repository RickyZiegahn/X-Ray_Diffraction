'''
Version 1.1 last updated 29-July-2018
https://github.com/RickyZiegahn/X-Ray_Diffraction
Made for McGill University under D.H. Ryan
'''

import time
import serial
from pyqtgraph.Qt import QtGui
import pyqtgraph as pg

ser = serial.Serial(port='COM3',baudrate=9600,timeout=10)
factor = 400 # 400 steps per degree
constant = 0 # 0 is a placeholder, to simplify things
sample = '1'
detector = '2'
degree_max = 180
degree_min = 0
anglelist = []
countlist = []


def confirm_flag():
    '''Accepts the confirmation from the Arduino that the task is complete and
    future operations can proceed'''
    while True:
        flag = str(ser.readline().decode()).strip()
        if flag == '999999999':
            break
        
def response_time():
    '''Inputting too quickly will result in the Arduino missing the command
    so this function is added to ensure that the Arduino will recieve all
    commands sent by the computer (much faster than a human)'''
    time.sleep(1.2)

def done():
    '''Prints a confirmation for the user'''
    response_time()
    print("\nDone, returning to main menu\n")
    
def degrees_to_steps(degree):
    '''Multiplies the degrees inputted by the conversion factor, constant is
    zero by default, but there in case the zero point is not zero degrees
    Steps must be integer values'''
    return str(float(degree) * float(factor) + float(constant))

def steps_to_degrees(step):
    return str((float(step) - float(constant))/float(factor))

def current_degree():
    return str(float(starting_degree) + float(degree_increment) * len(countlist))
    
def file_chooser(motor):
    '''Chooses the location to update based of the motor, used to make tracking
    which motor is being moved where simple and cleans up the code'''
    if motor == '1':
        return 'sample_location.txt'
    if motor == '2':
        return 'detector_location.txt'
    
def read_location(motor):
    with open (file_chooser(motor)) as f_loc:
        locations = f_loc.readlines()
        return locations[-1]

def set_location(new_location, motor):
    '''Updates location in file, used for if the file is inaccurate
    Erases previous location to save space because the old locations are no
    longer important'''
    with open (file_chooser(motor), 'w') as f_loc:
        f_loc.write(new_location.strip())
    
def increment_location(steps, motor):
    '''Updates the location after a drive command'''
    with open (file_chooser(motor), 'r+') as f_loc:
        locations = f_loc.readlines()
        old_location = locations[-1]
        new_location = str(int(old_location) + int(steps))
    set_location(new_location, motor)

def give_drive(steps, motor):
    '''Passes the Arduino an amount of steps to drive, updates the file and then
    waits for the Arduino to confirm that the task is complete'''
    ser.write(motor.encode())
    response_time()
    ser.write(steps.encode())
    increment_location(steps, motor)
    confirm_flag()
    
def goto(location, motor):
    '''Reads the current location and where the user wants to go, then does the
    necessary caluclations to determine how many steps are required to go
    there from the current location'''
    with open (file_chooser(motor)) as f_loc:
        locations = f_loc.readlines()
    current_location = locations[-1]
    step = str(int(location) - int(current_location))
    give_drive(step, motor)
    
def check_limit(steps, motor):
    '''Reads the current location to determine if performing the steps will cause
    the motor to exceed its limit'''
    current_loc = read_location()
    step_max = degrees_to_steps(degree_max)
    step_min = degrees_to_steps(degree_min)
    if (int(current_loc) + int(steps)) <= step_max and (int(current_loc) + int(steps)) >= step_min:
        return True
    else:
        return False

def recieve_count():
    '''Reads the amount of pulses counted by the Arduino'''
    count = ser.readline().decode().strip()
    return count


time.sleep(1.4) # prevents input until the serial connection is established
while True:
    print("1. Perform a regular run\n2. Run commands")
    a = input("Type your choice (number): ")
    ser.write(a.encode())
    response_time()
    if a == '1':
        countlist = []
        anglelist = []
        response_time()
        print("Please wait for the machine to go to zero")
        goto('0', sample)
        response_time()
        goto('0', detector)
        b = input("Is the machine zero'd (Y \ N): ")
        if b.upper() == 'Y':
            ser.write(b'1')
            print("\nProceeding to setup...\n")
            name = input("Please enter your name: ")
            while True: # forcing the user to enter a detailed title
                title = input("Enter a detailed title: ")
                if len(title) >= 10:
                    break
            current_datetime = time.strftime("%Y%m%d-%H%M%S")
            datafile = current_datetime + '-' + title + '.txt'
            with open (datafile, 'w') as f_data:
                f_data.write("Name: " + name + "\nTitle: " + title + 
                             "\nDate (YYYYmmdd-HHMMSS): " + current_datetime)
                while True:
                    param = input("\nEnter the parameters in the following format (excluding the guillemets):" +
                                  "\n<<starting degree>> <<ending degree>> " + 
                                  "<<degree increment>> <<milliseconds per reading>>\n")
                    
                    # all the degrees are for the detector motor
                    parameters = param.split()
                    starting_degree = parameters[0]
                    ending_degree = parameters[1]
                    degree_increment = parameters[2]
                    ms_per_reading = parameters[3]
                    try: #ensuring that only numbers are entered
                        int(degree_increment)
                        int(ms_per_reading)
                        if float(starting_degree) >= degree_min and float(ending_degree) <= degree_max:
                            break
                        if float(starting_degree) < degree_min or float(ending_degree) > degree_max: 
                            print("This is not within the motors range (between " 
                                + str(degree_min) + " and " + str(degree_max) + " degrees.)")
                    except ValueError:
                        print("Please enter only numbers\n")
                        
                f_data.write('Starting Degree: ' + starting_degree +
                             '\nEnding Degree: ' + ending_degree +
                             '\nDegree Increment: ' + degree_increment +
                             '\nMilliseconds per Reading: ' + ms_per_reading +
                             '\n')
                
                app = QtGui.QApplication([])
                p = pg.plot()
                p.setLabel('top', title)
                p.setLabel('bottom', 'Angle (degrees)')
                p.setLabel('left', str('Detections per ' + ms_per_reading + ' milliseconds'))
                p.setXRange(0, (float(ending_degree) + float(ending_degree) * 0.1), padding=0)
                curve = p.plot()
                
                print('\nPassing parameters to Arduino\n')
                ser.write(starting_degree.strip().encode())
                response_time()
                ser.write(ending_degree.strip().encode())
                response_time()
                ser.write(degree_increment.strip().encode())
                response_time()
                ser.write(ms_per_reading.strip().encode())
                print('\nDone passing parameters to Arduino\n' +
                      '\nMeasuring\n')
                f_data.write('\n\ndegrees, detections')
                
                for i in range(9999999): #arbitrarily large number, will break function before then
                    next_location_sample = round(float(degrees_to_steps(float(current_degree())/2)))
                    next_location_detector = round(float(degrees_to_steps(float(current_degree()))))
                    needed_steps_sample = next_location_sample - int(read_location(sample))
                    needed_steps_detector = next_location_detector - int(read_location(detector))
                    increment_location(str(needed_steps_sample), sample)
                    increment_location(str(needed_steps_detector), detector)
                    real_degree = steps_to_degrees(next_location_detector)
                    count = recieve_count()
                    anglelist.append(float(real_degree))
                    countlist.append(int(count))
                    f_data.write('\n' + str(real_degree) + ' , ' + count)
                    p.setYRange(0,(max(countlist) + (max(countlist) * 0.1)), padding=0)
                    curve.setData(x=anglelist,y=countlist)
                    app.processEvents()
                    if float(real_degree) >= float(ending_degree):
                        break
            print('Data saved to program directory as ' + datafile)                    
            done()

        if b == 'N':
            print("Select 2. to run commands, from the main" +
                  "menu and zero the machine (drive both motors to zero" +
                  "then update the location of both motors to zero")
        else:
            print("Please'Y' or 'N', returning to main menu")
        
    if a == '2':
        while True:
            print("\n\nMANUAL COMMANDS:" +
                  "\n1. Drive; used to move the motors" +
                  "\n2. Set location; set location to a step count" +
                  "\n3. Goto; move to a location" +
                  "\n4. Count; read detected pulses per unit time" +
                  "\nTo Return to the main menu, input any other value")
            
            while True:
                b = input("Input your choice (number): ")
                ser.write(b.encode())
            
                if b == '1':
                    response_time()
                    print("\n\nMOTOR OPTIONS:" +
                          "\n1. Sample Motor" +
                          "\n2. Detector Motor" +
                          "\nTo return to the main menu, input any other value")
                    c = input("Input the motor you would like to drive: ")
                    response_time()
                    if c == '1' or '2':
                        while True:
                            steps = input("400 steps per degree." +
                                          "\nInput the amount of steps to move " +
                                            "(negative value results in clockwise movement): ")
                            try:
                                if int(steps) != float(steps):
                                    print('Enter only integer numbers')
                                else:
                                    if check_limit(steps,c):
                                        break
                                    else:
                                        print("This is not within the motors range (between " 
                                            + str(degree_min) + " and " + str(degree_max) + " degrees.)")
                            except ValueError:
                                print('Enter only integer numbers')
                        give_drive(steps, c)
                    else:
                        print('\nReturning to main menu\n')
                        break
                    done()
                    break
                if b == '2':
                    response_time()
                    print("\n\nMOTOR OPTIONS:" +
                          "\n1. Sample Motor" +
                          "\n2. Detector Motor" +
                          "\nTo return to the main menu, input any other value")
                    c = input("Input the motor you would like to update: ")
                    if c == '1' or '2':
                        new_location = input("400 steps per degree" + 
                                            "\nInput the step to update to: ")
                        set_location(new_location, c)
                    else:
                        print('\nReturning to main menu\n')
                        break
                    done()
                    break
                if b == '3':
                    response_time()
                    print("\n\nMOTOR OPTIONS:" +
                          "\n1. Sample Motor" +
                          "\n2. Detector Motor" +
                          "\nTo return to the main menu, input any other value")
                    c = input("Input the motor you would like to move to a location: ")
                    if c == '1' or '2':
                        while True:
                            goto_location = input("400 steps per degree" + 
                                                  "\nInput the location (steps) to go to: ")
                            try:
                                int(goto_location)
                                if float(goto_location) != int(goto_location):
                                    print('Enter an integer number.')
                                elif (int(goto_location)) >= float(degrees_to_steps(degree_max)) and (int(goto_location)) <= float(degrees_to_steps(degree_min)):
                                    print("This is not within the motors range (between " 
                                            + str(degree_min) + " and " + str(degree_max) + " degrees.)")
                                else:
                                    break
                            except ValueError:
                                print('Enter only integer numbers.')
                        goto(goto_location, c)
                        done()
                    break
                if b == '4':
                    response_time()
                    while True:
                        length = input("Input the time (milliseconds) to record pulses: ")
                        if float(length) == int(length):
                            ser.write(length.strip().encode())
                            break
                        else:
                            print('Enter an integer number.')
                    count = recieve_count()
                    print('\nIn ' + str(length) + ' second(s), ' + count + ' counts were recorded')
                    done()
                    break
                else:
                    print('\nReturning to main menu\n')
                    break
            break