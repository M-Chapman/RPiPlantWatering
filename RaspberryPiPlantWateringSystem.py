#Raspberry Pi Plant Watering System
import RPi.GPIO as GPIO
import spidev
import datetime
import time

GPIO.setmode(GPIO.BOARD) # Broadcom pin-numbering scheme
spi = spidev.SpiDev()
spi.open(0,0)
spi.max_speed_hz=1000000

#def setup():
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
    val = spi.xfer2([1,(8+channel)<<4,0])
    data = ((val[1]&3) << 8) + val[2]
    return data/10.23 # Outputs value as % of max value

if __name__ == "__main__":
  try:
    while True:
        val = get_value(0)
        f = open("last_checked_0.txt", "w")
        f.write("Last checked {}".format(datetime.datetime.now()))
        f.close()
        if (val != 0):
            print(val) 
        time.sleep(500)
      
  except KeyboardInterrupt:
    print ("Cancel.")