from RPi import GPIO
from time import sleep

clk = 17
dt = 18

GPIO.setmode(GPIO.BCM)
GPIO.setup(clk, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(dt, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

counter = 0
clkLastState = GPIO.input(clk)

inc_callback = None
dec_callback = None
chg_callback = None

def init_counter(i)
    global counter
    counter = i

def def_inc_callback(callback):
    global inc_callback
    inc_callback = callback

def def_dec_callback(callback):
    global dec_callback
    dec_callback = callback

def def_chg_callback(callback):
    global chg_callback
    chg_callback = callback

try:
        while True:
                clkState = GPIO.input(clk)
                dtState = GPIO.input(dt)
                if clkState != clkLastState:
                        if dtState != clkState:
                                counter += 1
                                inc_callback(counter) if inc_callback is not None
                                chg_callback(counter) if chg_callback is not None
                        else:
                                counter -= 1
                                dec_callback(counter) if dec_callback is not None
                                chg_callback(counter) if chg_callback is not None
                        print(counter)
                clkLastState = clkState
                sleep(0.01)
finally:
        GPIO.cleanup()