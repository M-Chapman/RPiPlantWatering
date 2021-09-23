# Raspberry Pi Plant Watering System
import RPi.GPIO as GPIO
import spidev
import datetime
import time
import csv
import os
import tkinter as tk
import numpy as np
import pandas as pd

# GPIO initialisation
GPIO.setmode(GPIO.BOARD)  # Broadcom pin-numbering scheme
spi = spidev.SpiDev()
spi.open(0, 0)
spi.max_speed_hz = 1000000

# GUI initialisation
GUI = tk.Tk()
GUI.title('Raspberry Pi Plant Watering System')
GUI.geometry("800x600")
frame = tk.Frame(GUI)
frame.pack()

setup = True


def background():
    # Background runs the soil moisture monitoring
    # Changes the global variable setup to only run once and then begins monitoring soil moisture
    global setup
    global active_channels
    global counter

    if setup:
        # Runs for first time only
        active_channels = []
        counter = 0
        for i in range(7):
            if get_moisture(i) > 2:
                # Checks if a channel is active
                create_table(i)
                active_channels.append(i)
                
        setup = False
        GUI.after(2000, background)
    else:
        # Runs after first time
        for i in active_channels:
            add_moisture(i, get_moisture(i))
            
    counter += 1
    print('Background has run {} times'.format(counter))

    GUI.after(5000, background)


def get_status(pin):
    GPIO.setup(pin, GPIO.IN)
    return GPIO.input(pin)


def get_moisture(channel):
    # Returns the percentage soil moisture level as a float (0 to 100)
    # Accepts an integer in the range 0 to 7
    if 0 <= channel <= 7:
        val = spi.xfer2([1, (8+channel) << 4, 0])
        data = ((val[1] & 3) << 8) + val[2]
        return round(data/10.23, 2)  # Outputs value as % of max value
    else:
        print("The channel specified ({}) is outside the valid range (0 to 7)"
              .format(channel))


def create_table(channel):
    # CSV file creation for soil moisture level
    # Accepts an integer in the range 0 to 7
    if 0 <= channel <= 7:
        fields = ['channel', 'Time', 'Moisture']
        filename = "csvfiles/moisturechannel{}.csv".format(channel)

        with open(filename, 'w', newline='') as csvfile:
            csvwriter = csv.DictWriter(csvfile, fieldnames=fields)
            csvwriter.writeheader()
            # csvwriter.writerow(fields)

            csvwriter.writerow({'channel': channel, 'Time':  datetime.datetime.now(
            ).replace(microsecond=0), 'Moisture': get_moisture(channel)})
    else:
        print("The channel specified ({}) is outside the valid range (0 to 7)"
              .format(channel))


def add_moisture(channel, value):
    # Adds the soil moisture level to the csv file of the specified channel
    # Accepts an integer in the range 0 to 7 and float
    if 0 <= channel <= 7:
        fields = ['channel', 'Time', 'Moisture']
        with open("csvfiles/moisturechannel{}.csv".format(channel), 'a') as csvfile:
            csvwriter = csv.DictWriter(csvfile, fields)
            csvwriter.writerow({'channel': channel, 'Time': datetime.datetime.now(
            ).replace(microsecond=0), 'Moisture': value})
    else:
        print("The channel specified ({}) is outside the valid range (0 to 7)"
              .format(channel))

def auto_water():
    # auto_water turns the watering pump on when moisture level falls below specified %
    return None

def water_threshold():
    # water_threshold changes the % soil moisture before the water pump turns on
    return None

def manual_water():
    # Manual water turns the water pump on for 1 second
    # Requires the water pump to be connected to GPIO pin 7 on the Raspberry Pi
    pump_pin = 7
    GPIO.setup(pump_pin, GPIO.OUT)
    GPIO.output(pump_pin, GPIO.LOW)
    GPIO.output(pump_pin, GPIO.HIGH)
    GPIO.output(pump_pin, GPIO.LOW)
    time.sleep(1)
    GPIO.output(pump_pin, GPIO.HIGH)


def rename_file(current_name, new_name):
    # Renames the specified .csv file to a new name
    # Accepts 2 strings
    os.rename("csvfiles/{}.csv".format(current_name),
              "csvfiles/{}.csv".format(new_name))

auto_water_button = tk.Button(GUI, fg = 'blue', text='Turn Automatic Watering ON', command=auto_water)
water_threshold_button = tk.Button(GUI, fg = 'blue', text='Set Soil Moisture Level', command=water_threshold)
manual_water_button = tk.Button(GUI, fg = 'blue', text='Manual Water', command=manual_water)

auto_water_button.pack()
water_threshold_button.pack()
manual_water_button.pack()

GUI.after(2000, background)
GUI.mainloop()
GPIO.cleanup()
