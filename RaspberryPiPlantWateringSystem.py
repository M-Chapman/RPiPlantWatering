# Raspberry Pi Plant Watering System
from tkinter.constants import DISABLED
import RPi.GPIO as GPIO
import spidev
import datetime
import time
import csv
import os
import tkinter as tk
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import matplotlib.animation as animation
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
GUI.geometry("500x200")
frame = tk.Frame(GUI)
frame.pack()

threshold = 30

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
    # Background runs from the launch of the GUI
    # it records the soil moisture levels and controls automatic watering

    global setup
    global active_channels
    global counter
    global auto_water_bool
    global threshold
    # Global variables to be changed or compared based on run environment

    if setup:
        # Runs for first time only
        active_channels = []
        threshold = 30
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
        # automatic watering is ON
        GUI.after(5000, auto_water)

    counter += 1
    print('Background has run {} times'.format(counter))

    GUI.after(5000, background)


def open_moisture_graph():
    # open_moisture_graph opens a new window containing the soil moisture level over time

    moisture_graph_window = tk.Toplevel(GUI)

    df = pd.read_csv("csvfiles/moisturechannel0.csv")

    if len(df['Time']) < 2:
        no_data_msg = tk.Text(moisture_graph_window)
        no_data_msg.insert(tk.END, chars='There is no data to display')
        no_data_msg.pack()
    else:
        moistures = df['Moisture']

        fig = Figure(figsize=(6, 4), dpi=100)

        # Formatting of x-axis
        xAxis = []
        last = ''
        xTicks = []
        for i in range(len(df['Time'])):

            if i == 0:
                xAxis.append(df['Time'][i][5:-3])
                last = df['Time'][i]
                xTicks.append(i)

            if i % 10 == 0 and i > 0:
                if last[5:10] == df['Time'][i][5:10]:
                    xAxis.append(df['Time'][i][11:-3])
                else:
                    xAxis.append(df['Time'][i][5:-3])
                last = df['Time'][i]
                xTicks.append(i)

            if i == len(df['Time'])-1:
                xAxis.append(df['Time'][i][5:-3])
                xTicks.append(i)

        # Formatting of plot
        a = fig.add_subplot(111)
        a.set_xticks(xTicks)
        a.plot(df['Time'], moistures)
        a.set_xticklabels(xAxis, rotation=30, horizontalalignment='right')
        a.set_xlabel('Time of Reading')
        a.set_ylabel('Soil Moisture %')
        a.set_title('Soil Moisture Level over Time')
        fig.subplots_adjust(bottom=0.23)

        canvas = FigureCanvasTkAgg(fig, master=moisture_graph_window)

        canvas.get_tk_widget().pack()
        toolbar = NavigationToolbar2Tk(canvas, moisture_graph_window)
        toolbar.update()

    exit_button = tk.Button(moisture_graph_window, text='Exit',
                            command=moisture_graph_window.destroy).pack()


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
        # Runs upon file creation only
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


def water_threshold(threshold):
    # water_threshold changes the % soil moisture before the water pump turns on
    # Accepts an integer

    def get_threshold():
        global threshold
        threshold = threshold_text_box.get('1.0', tk.END)
        threshold_current.insert(tk.END, threshold)

    threshold_entry_window = tk.Toplevel(GUI)
    current_threshold_label = tk.Label(
        threshold_entry_window, text='The current threshold is ').pack()
    threshold_current = tk.Text(threshold_entry_window, height=1, width=5)
    threshold_current.insert(tk.END, threshold)
    threshold_current.config(state=DISABLED)
    threshold_current.pack()
    threshold_label = tk.Label(
        threshold_entry_window, text='Enter a value').pack()
    threshold_text_box = tk.Text(threshold_entry_window, height=1, width=10)
    threshold_text_box.pack()

    submit_Button = tk.Button(
        threshold_entry_window, text='Submit', command=lambda: get_threshold()).pack()
    exit_button = tk.Button(threshold_entry_window, text='Exit',
                            command=threshold_entry_window.destroy).pack()


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
    global threshold

    if float(last_line_csv) <= threshold:
        # **CURRENTLY ONLY WATERS AT <=30 PERCENT MAX MOISTURE VALUE**
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
    GUI, fg='blue', text='Set Soil Moisture Threshold', command=lambda: water_threshold(threshold)).pack()
manual_water_button = tk.Button(
    GUI, fg='blue', text='Manual Water', command=manual_water).pack()
moisture_visualisation_button = tk.Button(
    GUI, fg='blue', text='Show Soil Moisture Level Over Time', command=open_moisture_graph).pack()


GUI.after(2000, background)
GUI.mainloop()
GPIO.cleanup()
