# Raspberry Pi Plant Watering System
import RPi.GPIO as GPIO
import spidev
import datetime
import time
import csv
import os
import numpy as np


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
    filename = "Documents/RPiPlantWatering/pin{}.csv".format(pin)

    with open(filename, 'w') as csvfile:
        csvwriter = csv.writer(csvfile)
        csvwriter.writerow(fields)
        csvwriter.writerows(rows) 

def rename_file(current_name, new_name):
    os.rename("Documents/RPiPlantWatering/{}.csv".format(current_name), "Documents/RPiPlantWatering/{}.csv".format(new_name))

if __name__ == "__main__":
    try:
        while True:

            #Check if a pin is active
            for i in range(7):
                if get_value(i) > 2:
                    create_table(i)

            #df = pd.DataFrame(pin0.csv)
            
            rename_file("pin0", "pins")

            time.sleep(500)

    except KeyboardInterrupt:
        print("Cancel.")
