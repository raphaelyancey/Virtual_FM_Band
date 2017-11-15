from RPi import GPIO
from time import sleep

clk = 17
dt = 18

GPIO.setmode(GPIO.BCM)
GPIO.setup(clk, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(dt, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

counter = 0
step = 1
max_counter = 100
min_counter = 0
clkLastState = GPIO.input(clk)

inc_callback = None
dec_callback = None
chg_callback = None

def init(min_c, max_c, **params):
    global max_counter
    global min_counter
    global counter
    min_counter = min_c
    counter = min_counter + 0
    max_counter = max_c
    if params['step']:
        global step
        step = params['step']

def def_inc_callback(callback):
    global inc_callback
    inc_callback = callback

def def_dec_callback(callback):
    global dec_callback
    dec_callback = callback

def def_chg_callback(callback):
    global chg_callback
    chg_callback = callback

def loop():
    global clkLastState
    global counter
    try:
        while True:
            clkState = GPIO.input(clk)
            dtState = GPIO.input(dt)
            if clkState != clkLastState:
                if dtState != clkState:
                    if counter + step <= max_counter:
                        counter += step
                    if inc_callback is not None:
                        inc_callback(counter)
                    if chg_callback is not None:
                        chg_callback(counter)
                else:
                    if counter - step >= min_counter:
                        counter -= step
                    if dec_callback is not None:
                        dec_callback(counter)
                    if chg_callback is not None:
                        chg_callback(counter)
            clkLastState = clkState
            sleep(0.001)
    finally:
            GPIO.cleanup()