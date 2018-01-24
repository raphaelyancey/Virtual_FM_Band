from RPi import GPIO
from time import sleep
import logging

logger = logging.getLogger('virtual_fm_band.rotaryencoder')

class Encoder:

    clk = None
    dt = None
    sw = None

    counter = 0
    step = 1
    max_counter = 100
    min_counter = 0
    clkLastState = None

    inc_callback = None # Clockwise rotation (increment)
    dec_callback = None # Anti-clockwise rotation (decrement)
    chg_callback = None # Rotation (either way)
    sw_callback = None # Switch pressed

    def __init__(self, clkPin, dtPin):
        self.clk = clkPin
        self.dt = dtPin
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.clk, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
        GPIO.setup(self.dt, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
        self.clkLastState = GPIO.input(self.clk)

    def setup(self, min_c, max_c, **params):

        # Note: boundaries are inclusive : [min_c, max_c]

        self.min_counter = min_c
        self.counter = self.min_counter + 0
        self.max_counter = max_c

        if 'step' in params:
            self.step = params['step']
        if 'inc_callback' in params:
            self.inc_callback = params['inc_callback']
        if 'dec_callback' in params:
            self.dec_callback = params['dec_callback']
        if 'chg_callback' in params:
            self.chg_callback = params['chg_callback']
        if 'sw_callback' in params:
            self.sw_callback = params['sw_callback']

    # def def_inc_callback(self, callback):
    #     self.inc_callback = callback

    # def def_dec_callback(self, callback):
    #     self.dec_callback = callback

    # def def_chg_callback(self, callback):
    #     self.chg_callback = callback

    def watch(self):
        while True:
            try:
                # Switch part
                if self.sw_callback:
                    if GPIO.input(self.sw) == GPIO.HIGH:
                        # LOW or HIGH? Test irl
                        self.sw_callback()
                # Encoder part
                clkState = GPIO.input(self.clk)
                dtState = GPIO.input(self.dt)
                if clkState != self.clkLastState:
                    if dtState != clkState:
                        if self.counter + self.step <= self.max_counter:
                            self.counter += self.step
                        if self.inc_callback is not None:
                            self.inc_callback(self.counter)
                        if self.chg_callback is not None:
                            self.chg_callback(self.counter)
                    else:
                        if self.counter - self.step >= self.min_counter:
                            self.counter -= self.step
                        if self.dec_callback is not None:
                            self.dec_callback(self.counter)
                        if self.chg_callback is not None:
                            self.chg_callback(self.counter)
                self.clkLastState = clkState
                sleep(0.001)
            except:
                logger.info("Exiting...")
                GPIO.cleanup()
                break
        return
