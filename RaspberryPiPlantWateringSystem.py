# Raspberry Pi Plant Watering System
import RPi.GPIO as GPIO
import spidev
import datetime
import time
import csv
import os
import tkinter as tk
from tkinter import messagebox as tkMessageBox
import numpy as np
import pandas as pd
import matplotlib

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

# Global Booleans for first loop and auto watering loop
setup = True
auto_water_bool = False


def auto_water_boolean():
    # auto_water_boolean changes the global boolean auto_water_bool to True or False
    # Determines wether auto_water() is run in background()

    global auto_water_bool
    auto_water_bool = not auto_water_bool
    return None


def background():
    # Background runs the soil moisture monitoring
    # Changes the global variable setup to only run once and then begins monitoring soil moisture

    # Global variables to be changed or compared based on run environment
    global setup
    global active_channels
    global counter
    global auto_water_bool

    if setup:
        # Runs for first time only
        active_channels = []
        counter = 0
        for i in range(7):
            if get_moisture(i) > 2:
                # Checks if a channel is active
                create_table(i, counter)
                active_channels.append(i)

        setup = False
        GUI.after(2000, background)
    else:
        # Runs after first time
        # Undefined can be ignored as this is inaccessible before declaration of variables
        for i in active_channels:
            add_moisture(i, counter)

    if auto_water_bool:
        GUI.after(5000, auto_water)

    counter += 1
    print('Background has run {} times'.format(counter))

    GUI.after(5000, background)


def get_status(pin):
    # **NOT CURRENTLY USED**
    # get_status queries the current status of a RPi pin
    # Accepts an integer

    GPIO.setup(pin, GPIO.IN)
    return GPIO.input(pin)


def get_moisture(channel):
    # get_moisture obtains the value of a specified channel of the ADC
    # Returns the percentage soil moisture level as a float (0 to 100)
    # Accepts an integer in the range 0 to 7

    if 0 <= channel <= 7:
        val = spi.xfer2([1, (8+channel) << 4, 0])
        data = ((val[1] & 3) << 8) + val[2]
        return round(data/10.23, 2)  # Outputs value as % of max value
    else:
        print("The channel specified ({}) is outside the valid range (0 to 7)"
              .format(channel))


def create_table(channel, loop_counter):
    # CSV file creation for soil moisture level
    # Uses the ADC channel to determine the generated file name
    # Accepts an integer in the range 0 to 7

    if 0 <= channel <= 7:
        fields = ['channel', 'Time', 'Moisture']
        with open("csvfiles/moisturechannel{}.csv".format(channel), 'w', newline='') as csvfile:
            csv_file_write(fields, channel, csvfile, loop_counter)
    else:
        print("The channel specified ({}) is outside the valid range (0 to 7)"
              .format(channel))


def add_moisture(channel, loop_counter):
    # Adds the soil moisture level to the csv file of the specified channel
    # Accepts an integer in the range 0 to 7 and float

    if 0 <= channel <= 7:
        fields = ['channel', 'Time', 'Moisture']
        with open("csvfiles/moisturechannel{}.csv".format(channel), 'a') as csvfile:
            csv_file_write(fields, channel, csvfile, loop_counter)
    else:
        print("The channel specified ({}) is outside the valid range (0 to 7)"
              .format(channel))


def csv_file_write(fields, channel, csvfile, loop_counter):
    # csv_file_write adds the moisture values to the .csv file
    # It adds a header if the program is running for the first time
    # Accepts an array, integer, file opening operation and integer

    csvwriter = csv.DictWriter(csvfile, fieldnames=fields)
    if loop_counter == 0:
        # -1 is outside the range of values returned by get_moisture()
        # Runs upon file creation
        csvwriter.writeheader()
    csvwriter.writerow({'channel': channel, 'Time': datetime.datetime.now(
    ).replace(microsecond=0), 'Moisture': get_moisture(channel)})


def load_csv(filename):
    # load_csv retrieves the content of a specified .csv file
    # Accepts a String
    csv_data = []
    row_index = 0
    with open("csvfiles/"+filename+".csv", "r", encoding="utf-8", errors="ignore") as scraped:
        reader = csv.reader(scraped, delimiter=',')
        for row in reader:
            if row:  # avoid blank lines
                row_index += 1
                columns = [str(row_index), row[0], row[1], row[2]]
                csv_data.append(columns)
    return csv_data


def water_threshold(new_threshold):
    # water_threshold changes the % soil moisture before the water pump turns on
    # Accepts an integer
    global threshold
    threshold = new_threshold
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


def auto_water():
    # auto_water turns the watering pump on when the last read moisture level falls below specified %
    last_line_csv = load_csv("pin0")[-1][-1]
    print(last_line_csv)
    if float(last_line_csv) <= 30:
        manual_water()

    return None


def sel():
    # **WIP**
    # sel identifies the selection from the rename file radiofield
    # it will then run a function that opens a textbox popup to enter the new file name

    selection = "you selected option: "


def rename_popup():
    # **WIP**
    # rename_popup generates a popup window containing all file names in /csvfiles in a radiofield
    # goal: user selects a file from the radiofield to rename

    #pop_up = tkMessageBox.showinfo('Rename a file', 'Choose file to rename')
    popup_main = tk.Toplevel(GUI)
    files = [f for f in os.listdir('csvfiles') if os.path.isfile(
        os.path.join('csvfiles', f))]
    files.sort()
    file_list = []
    for i in range(len(files)-1):
        file_list.append(tk.Radiobutton(
            popup_main, text=files[i], value=i, command=sel))
    for i in range(len(files)-1):
        file_list[i].pack()
    submit_Button = tk.Button(popup_main, text='Submit').pack()


def rename_file(current_name, new_name):
    # Renames the specified .csv file to a new name
    # Accepts 2 strings
    files = [f for f in os.listdir('csvfiles') if os.path.isfile(
        os.path.join('csvfiles', f))]

    os.rename("csvfiles/{}.csv".format(current_name),
              "csvfiles/{}.csv".format(new_name))


auto_water_button = tk.Button(
    GUI, fg='blue', text='Turn Automatic Watering ON', command=auto_water_boolean).pack()
rename_button = tk.Button(
    GUI, fg='blue', text='Rename a File', command=rename_popup).pack()
water_threshold_button = tk.Button(
    GUI, fg='blue', text='Set Soil Moisture Level', command=water_threshold).pack()
manual_water_button = tk.Button(
    GUI, fg='blue', text='Manual Water', command=manual_water).pack()

GUI.after(2000, background)
GUI.mainloop()
GPIO.cleanup()
