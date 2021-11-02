# Raspberry Pi Plant Watering System
# NOTE: To run the program on VSCode you must do so via the terminal (not sure if the issue is replicable)
# "python3 RaspberryPiPlantWateringSystem.py"

from tkinter.constants import DISABLED, NORMAL
from twilio.rest import Client
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
GUI.geometry("700x650")
frame = tk.Frame(GUI)
frame.grid()

threshold = 30

# Global Booleans for first loop and auto watering loop
setup = True
auto_water_bool = False
sms_bool = False
moisture_below = False
first_water = True
phone_number = ''


def auto_water_boolean():
    # auto_water_boolean changes the global boolean auto_water_bool to True or False
    # Determines wether manual_water() is run in moisturewatch()

    global auto_water_bool
    auto_water_bool = not auto_water_bool
    if auto_water_bool:
        auto_water_button = tk.Button(
            GUI, fg='green', text='Turn Automatic Watering OFF', command=auto_water_boolean).grid(row=3, column=0, sticky='ew', pady=1, padx=10)
    else:
        auto_water_button = tk.Button(
            GUI, fg='red', text='Turn Automatic Watering ON ', command=auto_water_boolean).grid(row=3, column=0, sticky='ew', pady=1, padx=10)


def sms_boolean():
    # sms_boolean changes the global boolean sms_bool to True or False
    # Determines wether smd_sms() is run in moisture_watch()

    global sms_bool
    sms_bool = not sms_bool
    if sms_bool:
        message_button = tk.Button(
            GUI, fg='green', text='Turn SMS texting OFF', command=lambda: sms_boolean()).grid(row=3, column=1, sticky='ew', pady=1, padx=10)
    else:
        message_button = tk.Button(
            GUI, fg='red', text='Turn SMS texting ON ', command=lambda: sms_boolean()).grid(row=3, column=1, sticky='ew', pady=1, padx=10)


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
        counter = 0
        for i in range(7):
            if get_moisture(i) > 2:
                # Checks if a channel is active
                create_table(i, counter)
                active_channels.append(i)

        setup = False

        # GUI.after(2000, background)
    else:
        # Runs after first time
        # Undefined can be ignored as this is inaccessible before declaration of variables

        for i in active_channels:
            add_moisture(i, counter)
    load_moisture_graph()

    GUI.after(5000, moisture_watch)

    counter += 1
    print('Background has run {} times'.format(counter))

    GUI.after(5000, background)


def load_moisture_graph():
    # load_moisture_graph opens a new window containing the soil moisture level over time

    # moisture_graph_window = tk.Toplevel(GUI)

    df = pd.read_csv("csvfiles/moisturechannel0.csv")

    if len(df['Time']) > 2:
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

        canvas = FigureCanvasTkAgg(fig, master=GUI)

        canvas.get_tk_widget().grid(row=1, column=0, columnspan=2)
        last_record_label = tk.Label(GUI, text='Last Recorded: {}'.format(load_csv(
            "moisturechannel0")[-1][2]), font='Helvetica 12').grid(row=0, column=1, padx=10)


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
    # Accepts an array of length 3, integer, file opening operation and integer

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
        if int(threshold) > 100 or int(threshold) < 0:
            threshold_error_window = tk.Toplevel(GUI)
            threshold_error_label = tk.Label(
                threshold_error_window, text='The entered value is not in the range 0 to 100!').grid(row=0, column=0)
        else:
            threshold_current = tk.Text(
                threshold_entry_window, height=1, width=5)
            threshold_current.insert(tk.END, threshold)
            threshold_current.config(state=DISABLED)
            threshold_current.grid(row=0, column=1)

    threshold_entry_window = tk.Toplevel(GUI)
    current_threshold_label = tk.Label(
        threshold_entry_window, text='The current threshold is ').grid(row=0, column=0)
    threshold_current = tk.Text(threshold_entry_window, height=1, width=5)
    threshold_current.insert(tk.END, threshold)
    threshold_current.config(state=DISABLED)
    threshold_current.grid(row=0, column=1)
    threshold_label = tk.Label(
        threshold_entry_window, text='Enter a value').grid(row=1, column=0, columnspan=2)
    threshold_text_box = tk.Text(threshold_entry_window, height=1, width=10)
    threshold_text_box.grid(row=2, column=0, columnspan=2)

    submit_button = tk.Button(
        threshold_entry_window, text='Submit', command=lambda: get_threshold()).grid(row=3, column=0, sticky='ew', pady=1, padx=10)
    exit_button = tk.Button(threshold_entry_window, text='Exit',
                            command=threshold_entry_window.destroy).grid(row=3, column=1, sticky='ew', pady=1, padx=10)


def manual_water():
    # Manual water turns the water pump on for 1 second
    # Requires the water pump to be connected to GPIO pin 7 on the Raspberry Pi

    global first_water

    pump_pin = 7
    GPIO.setup(pump_pin, GPIO.OUT)
    GPIO.output(pump_pin, GPIO.LOW)
    GPIO.output(pump_pin, GPIO.HIGH)
    GPIO.output(pump_pin, GPIO.LOW)
    time.sleep(1)
    GPIO.output(pump_pin, GPIO.HIGH)

    fields = ['Time', 'Pin']

    if first_water:
        with open("csvfiles/waterpump.csv", 'w', newline='') as csvfile:
            csvwriter = csv.writer(csvfile)
            csvwriter.writerow(fields)
            csvwriter.writerow(
                {datetime.datetime.now().replace(microsecond=0), pump_pin})
            first_water = False
    else:
        with open("csvfiles/waterpump.csv", 'a') as csvfile:
            csvwriter = csv.writer(csvfile)
            csvwriter.writerow(
                {pump_pin, datetime.datetime.now().replace(microsecond=0)})


def moisture_watch():
    global threshold
    global auto_water_bool
    global sms_bool
    global moisture_below

    moisture = float(load_csv("moisturechannel0")[-1][-1])
    threshold = int(threshold)

    if moisture > threshold:
        moisture_below = False

    else:

        if not moisture_below:
            moisture_below = True

            if sms_bool:
                send_sms(load_csv("moisturechannel0")[-1][-1])

        if auto_water_bool:
            manual_water()


def send_sms(last_moisture):
    # send_sms sends a text message to the specified number when the soil moisture level falls below the threshold
    global phone_number

    account_sid = 'AC4a8c4824464ddea06e3c5df97d9a76aa'

    with open('authtkn.txt', 'r') as f:
        auth_token = f.readlines()

    client = Client(account_sid, auth_token[0])

    message = client.messages.create(
        messaging_service_sid='MG3a937b8d59947201ea4ccbe9daad8b43', body='Your plant needs watering, the soil moisture level is {}'.format(last_moisture), to=phone_number)

    print(message.sid)


def change_sms():
    # change_sms changes the phone number text SMS are sent to

    def get_number():
        # get_number obtains the entered phone number in the text box
        global phone_number
        phone_number = phoneno_text_box.get('1.0', tk.END)
        if len(phone_number) != 12:
            phoneno_error_window = tk.Toplevel(GUI)
            phoneno_error_label = tk.Label(
                phoneno_error_window, text='The entered phone number is not the right length!').grid(row=0, column=0)
        else:
            phoneno_current = tk.Text(phoneno_entry_window, height=1, width=15)
            phoneno_current.insert(tk.END, phone_number)
            phoneno_current.config(state=DISABLED)
            phoneno_current.grid(row=0, column=1)

    phoneno_entry_window = tk.Toplevel(GUI)
    phoneno_entry_window.grab_set()
    current_phoneno_label = tk.Label(
        phoneno_entry_window, text='The current phone number is ').grid(row=0, column=0)
    phoneno_current = tk.Text(phoneno_entry_window, height=1, width=15)
    phoneno_current.insert(tk.END, phone_number)
    phoneno_current.config(state=DISABLED)
    phoneno_current.grid(row=0, column=1)
    phoneno_label = tk.Label(
        phoneno_entry_window, text='Enter a Phone Number (e.g.+447123456789)').grid(row=1, column=0, columnspan=2)
    phoneno_text_box = tk.Text(phoneno_entry_window, height=1, width=15)
    phoneno_text_box.grid(row=2, column=0, columnspan=2)

    submit_button = tk.Button(
        phoneno_entry_window, text='Submit', command=lambda: get_number()).grid(row=3, column=0, sticky='ew', pady=1, padx=10)
    exit_button = tk.Button(phoneno_entry_window, text='Exit',
                            command=phoneno_entry_window.destroy).grid(row=3, column=1, sticky='ew', pady=1, padx=10)


graph_label = tk.Label(GUI, text='Channel 0 Soil Moisture Level Over Time',
                       font='Helvetica 14 bold').grid(row=0, column=0, padx=10)

watering_label = tk.Label(GUI, text='Plant Watering Controls', font='Helvetica 14 bold').grid(
    row=2, column=0, sticky='ew', pady=7)
auto_water_button = tk.Button(
    GUI, fg='red', text='Turn Automatic Watering ON ', command=auto_water_boolean).grid(row=3, column=0, sticky='ew', pady=1, padx=10)
manual_water_button = tk.Button(
    GUI, fg='black', text='Manual Water', command=manual_water).grid(row=4, column=0, sticky='ew', pady=1, padx=10)

notification_label = tk.Label(GUI, text='Notification Controls', font='Helvetica 14 bold').grid(
    row=2, column=1, sticky='ew', pady=7)
message_button = tk.Button(
    GUI, fg='red', text='Turn SMS texting ON', command=lambda: sms_boolean()).grid(row=3, column=1, sticky='ew', pady=1, padx=10)
phoneno_button = tk.Button(
    GUI, fg='black', text='Change SMS number', command=change_sms).grid(row=4, column=1, sticky='ew', pady=1, padx=10)

threshold_label = tk.Label(GUI, text='Water Threshold For Notifications Or Automatic Watering Control', font='Helvetica 14 bold').grid(
    row=5, column=0, columnspan=2, sticky='ew', pady=7)
water_threshold_button = tk.Button(
    GUI, fg='black', text='Change Soil Moisture Threshold', command=lambda: water_threshold(threshold)).grid(row=6, column=0, columnspan=2, sticky='ew', pady=1, padx=10)

background()
GUI.after(2000, background)
GUI.mainloop()
GPIO.cleanup()
