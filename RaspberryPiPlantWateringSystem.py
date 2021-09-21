# Raspberry Pi Plant Watering System
import RPi.GPIO as GPIO
import spidev
import datetime
import time
import csv
import os
import numpy as np
import pandas as pd


GPIO.setmode(GPIO.BOARD)  # Broadcom pin-numbering scheme
spi = spidev.SpiDev()
spi.open(0, 0)
spi.max_speed_hz = 1000000

# def setup():

def get_status(pin):
    GPIO.setup(pin, GPIO.IN)
    return GPIO.input(pin)


def get_moisture(channel):
    #Returns the percentage soil moisture level as a float (0 to 100)
    #Accepts an integer
    val = spi.xfer2([1, (8+channel) << 4, 0])
    data = ((val[1] & 3) << 8) + val[2]
    return round(data/10.23, 2)  # Outputs value as % of max value

def create_table(channel):
    #CSV file creation for soil moisture level
    #Accepts an integer in the range 0 to 7
    if 0 <= channel <= 7:
        fields = ['channel', 'Time', 'Moisture']
        filename = "csvfiles/moisturechannel{}.csv".format(channel)

        with open(filename, 'w', newline='') as csvfile:
            csvwriter = csv.DictWriter(csvfile, fieldnames=fields)
            csvwriter.writeheader()
            #csvwriter.writerow(fields)

            csvwriter.writerow({'channel': channel,'Time':  datetime.datetime.now().replace(microsecond = 0), 'Moisture': get_moisture(channel)})
    else:
        print("The channel specified ({}) is outside the valid range (0 to 7)".format(channel))

def add_moisture(channel, value):
    #Adds the soil moisture level to the csv file of the specified channel
    #Accepts an integer and float
    fields = ['channel', 'Time', 'Moisture']
    with open("csvfiles/moisturechannel.csv".format(channel), 'a') as csvfile:
        csvwriter = csv.DictWriter(csvfile, fields)
        csvwriter.writerow({'channel': channel, 'Time' : datetime.datetime.now().replace(microsecond = 0), 'Moisture': value})

def rename_file(current_name, new_name):
    #Renames the specified .csv file to a new name
    #Accepts 2 strings
    os.rename("csvfiles/{}.csv".format(current_name), "csvfiles/{}.csv".format(new_name))

if __name__ == "__main__":
    try:
        active_channels = []
        setup = True
        while True:

            if setup:
                #Runs for first time only
                for i in range(7):
                    if get_moisture(i) > 2:
                        #Checks if a channel is active
                        create_table(i)
                        active_channels.append(i)
                    time.sleep(1)
                setup = False
            else:
                #Runs after first time
                for i in active_channels:
                    add_moisture(i,get_moisture(i))
                    time.sleep(1)

            # df = pd.read_csv("csvfiles/channel0.csv")

            # print(df)

            time.sleep(5)

    except KeyboardInterrupt:
        print("Cancel.")
