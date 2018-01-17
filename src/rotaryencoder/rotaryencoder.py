from RPi import GPIO
from time import sleep


class Encoder:

    clk = None
    dt = None

    counter = 0
    step = 1
    max_counter = 100
    min_counter = 0
    clkLastState = GPIO.input(clk)

    inc_callback = None
    dec_callback = None
    chg_callback = None

    def __init__(self, clkPin=None, dtPin=None):
        self.clk = clkPin
        self.dt = dtPin
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.clk, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
        GPIO.setup(self.dt, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

    def setup(self, min_c, max_c, **params):

        # Note: boundaries are inclusive : [min_c, max_c]

        self.min_counter = min_c
        self.counter = self.min_counter + 0
        self.max_counter = max_c

        if params['step']:
            self.step = params['step']
        if params['inc_callback']:
            self.inc_callback = params['inc_callback']
        if params['dec_callback']:
            self.dec_callback = params['dec_callback']
        if params['chg_callback']:
            self.chg_callback = params['chg_callback']

    # def def_inc_callback(self, callback):
    #     self.inc_callback = callback

    # def def_dec_callback(self, callback):
    #     self.dec_callback = callback

    # def def_chg_callback(self, callback):
    #     self.chg_callback = callback

    def watch(self):
        try:
            while True:
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
        finally:
                GPIO.cleanup()
