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


def get_last_checked(channel):
    try:
        f = open("last_checked_{}.txt".format(channel), "r")
        return f.readline()
    except:
        return "NEVER!"


def get_status(pin):
    GPIO.setup(pin, GPIO.IN)
    return GPIO.input(pin)


def get_value(channel):
    val = spi.xfer2([1, (8+channel) << 4, 0])
    data = ((val[1] & 3) << 8) + val[2]
    return round(data/10.23, 2)  # Outputs value as % of max value

def create_table(pin):
    #CSV file creation
    fields = ['Pin', 'Time', 'Moisture']
    rows = [[pin, datetime.datetime.now().replace(microsecond = 0), get_value(pin)]]
    filename = "csvfiles/pin{}.csv".format(pin)

    with open(filename, 'w', newline='') as csvfile:
        csvwriter = csv.DictWriter(csvfile, fieldnames=fields)
        csvwriter.writeheader()
        #csvwriter.writerow(fields)

        csvwriter.writerow({'Pin': pin,'Time':  datetime.datetime.now().replace(microsecond = 0), 'Moisture': get_value(pin)}) 

def add_value(pin, value):
    print(pin, value)
    fields = ['Pin', 'Time', 'Moisture']
    with open("csvfiles/pin{}.csv".format(pin), 'a') as csvfile:
        csvwriter = csv.DictWriter(csvfile, fields)
        csvwriter.writerow({'Pin': pin, 'Time' : datetime.datetime.now().replace(microsecond = 0), 'Moisture': value})

def rename_file(current_name, new_name):
    os.rename("csvfiles/{}.csv".format(current_name), "csvfiles/{}.csv".format(new_name))

if __name__ == "__main__":
    try:
        setup = True
        while True:

            #Check if a pin is active
            if setup:
                for i in range(7):
                    if get_value(i) > 2:
                        create_table(i)
                    time.sleep(1)
            else:
                #for i in range(7):
                    #if get_value(i) > 2:
                add_value(0,get_value(0))
                time.sleep(1)

            df = pd.read_csv("csvfiles/pin0.csv")
            
            #rename_file("pin0", "pins")

            print(df)
            setup = False
            time.sleep(5)

    except KeyboardInterrupt:
        print("Cancel.")
