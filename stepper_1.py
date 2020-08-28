#!/usr/bin/python3

"""Simple test for using adafruit_motorkit with a stepper motor"""
import time
import board
import atexit
from adafruit_motorkit import MotorKit
from adafruit_motor import stepper as stepper
import threading


# create empty threads (these will hold the stepper 1 and 2 threads)
st1 = threading.Thread()  # pylint: disable=bad-thread-instantiation
st2 = threading.Thread()  # pylint: disable=bad-thread-instantiation


steps_revolution = 200
revolution = 100
direction = 1	#foreward	2 reverse

# recommended for auto-disabling motors on shutdown!
def turnOffMotors():
    kit.stepper1.release()
    kit.stepper2.release()

atexit.register(turnOffMotors) 
kit = MotorKit(i2c=board.I2C())
 


def wind_one_row():

    loops = 0
    steps = steps_revolution * revolution
    for i in range(steps):
        #loops = kit.stepper1.onestep(style=stepper.DOUBLE)
        kit.stepper1.onestep(style=stepper.DOUBLE)
        loops = loops + 1
        #print("loops = ",loops)
        if ((loops % 10) == 0):
            if ((loops % 200)== 0):
                print("rotations = ",loops / 200)
            if loops > (steps/2):
                kit.stepper2.onestep(style=stepper.DOUBLE,direction=stepper.BACKWARD)
            else:
                kit.stepper2.onestep(style=stepper.DOUBLE,direction=stepper.FORWARD)


wind_one_row()
