from machine import ADC


class ReadJoyADC:
    """
    Centered ADC scaler with deadband + hysteresis.
    Scales ADC GPIO26 and GPIO27 to range 0–31.
    """

    def __init__(self):
        # ADC objects
        self._adc26 = ADC(26)
        self._adc27 = ADC(27)

        # Calibration (private)
        self._gpio26_min = 160
        self._gpio26_center = 31000
        self._gpio26_max = 65535

        self._gpio27_min = 1024
        self._gpio27_center = 33500
        self._gpio27_max = 65535

        # Noise control
        self._lock_band = 500
        self._release_band = 900

        # Hysteresis memory
        self._last26 = 15
        self._last27 = 15

    def _scale(self, x, center, xmin, xmax, last):
        # Lock at center
        if abs(x - center) <= self._lock_band:
            return 15

        # Hysteresis: do not leave 15 too easily
        if last == 15 and abs(x - center) < self._release_band:
            return 15

        # Clamp
        if x <= xmin:
            return 0
        if x >= xmax:
            return 31

        # Linear scale
        if x > center:
            return int(15 + (x - center) * 16 / (xmax - center))
        else:
            return int(15 - (center - x) * 15 / (center - xmin))

    def read(self):
        """
        Read ADCs and return scaled values (gpio26, gpio27)
        in range 0–31.
        """
        raw26 = self._adc26.read_u16()
        raw27 = self._adc27.read_u16()

        self._last26 = self._scale(
            raw26,
            self._gpio26_center,
            self._gpio26_min,
            self._gpio26_max,
            self._last26,
        )

        self._last27 = self._scale(
            raw27,
            self._gpio27_center,
            self._gpio27_min,
            self._gpio27_max,
            self._last27,
        )

        return self._last26, self._last27

#############################################
##         Test functions
#############################################

if __name__ == "__main__":
    import time
    adc = ReadJoyADC()

    while True:
        v26, v27 = adc.read()
        print("GPIO26:", v26, "| GPIO27:", v27)
        time.sleep(0.2)
    
