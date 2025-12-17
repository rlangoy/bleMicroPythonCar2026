# This example demonstrates a UART periperhal.

# This example demonstrates the low-level bluetooth module. For most
# applications, we recommend using the higher-level aioble library which takes
# care of all IRQ handling and connection management. See
# https://github.com/micropython/micropython-lib/tree/master/micropython/bluetooth/aioble
import machine
import bluetooth
import random
import struct
import time
import rp2

from machine import Pin, ADC
from ble_advertising import advertising_payload
from micropython import const

DOUBLE_CLICK_TIME = 400   # ms max time between clicks
DEBOUNCE_TIME = 50        # ms debounce
last_btn_state = False

last_click_time = 0
click_count = 0
last_state = False

_IRQ_CENTRAL_CONNECT = const(1)
_IRQ_CENTRAL_DISCONNECT = const(2)
_IRQ_GATTS_WRITE = const(3)

_FLAG_READ = const(0x0002)
_FLAG_WRITE_NO_RESPONSE = const(0x0004)
_FLAG_WRITE = const(0x0008)
_FLAG_NOTIFY = const(0x0010)

_UART_UUID = bluetooth.UUID("6E400001-B5A3-F393-E0A9-E50E24DCCA9E")
_UART_TX = (
    bluetooth.UUID("6E400003-B5A3-F393-E0A9-E50E24DCCA9E"),
    _FLAG_READ | _FLAG_NOTIFY,
)
_UART_RX = (
    bluetooth.UUID("6E400002-B5A3-F393-E0A9-E50E24DCCA9E"),
    _FLAG_WRITE | _FLAG_WRITE_NO_RESPONSE,
)
_UART_SERVICE = (
    _UART_UUID,
    (_UART_TX, _UART_RX),
)

led = machine.Pin("LED", machine.Pin.OUT)

class BLESimplePeripheral:
    def __init__(self, ble, name="mpy-uart"):
        self._ble = ble
        self._ble.active(True)
        self._ble.irq(self._irq)
        ((self._handle_tx, self._handle_rx),) = self._ble.gatts_register_services((_UART_SERVICE,))
        self._connections = set()
        self._write_callback = None
        self._payload = advertising_payload(name=name, services=[_UART_UUID])
        self._advertise()

    def _irq(self, event, data):
        # Track connections so we can send notifications.
        if event == _IRQ_CENTRAL_CONNECT:
            conn_handle, _, _ = data
            led.value(1)
            print("New connection", conn_handle)
            self._connections.add(conn_handle)
        elif event == _IRQ_CENTRAL_DISCONNECT:
            conn_handle, _, _ = data
            led.value(0)
            print("Disconnected", conn_handle)
            self._connections.remove(conn_handle)
            # Start advertising again to allow a new connection.
            self._advertise()
        elif event == _IRQ_GATTS_WRITE:
            conn_handle, value_handle = data
            value = self._ble.gatts_read(value_handle)
            if value_handle == self._handle_rx and self._write_callback:
                self._write_callback(value)

    def send(self, data):
        for conn_handle in self._connections:
            self._ble.gatts_notify(conn_handle, self._handle_tx, data)

    def is_connected(self):        
        return len(self._connections) > 0

    def _advertise(self, interval_us=100000):
        print("Starting advertising")
        self._ble.gap_advertise(interval_us, adv_data=self._payload)

    def on_write(self, callback):
        self._write_callback = callback


def startRemoteBLE(name="remote"):
    ble = bluetooth.BLE()
    p = BLESimplePeripheral(ble,name=name)

    def on_rx(v):
        print("RX", v)

    p.on_write(on_rx)

    i = 0
    #sett 27 høy
    #xPosition = ADC(Pin(27))
    p27 = Pin(27, Pin.OUT)    # create output pin on GPIO27
    p27.on()                  # set pin to "on" (high) level
    
    yPosition = ADC(Pin(26))
    oldXpos=0
    oldYpos=0
    oldButBootSel=False


    last_click_time = 0
    click_count = 0
    last_state = False
    ForwardDir=1
    while True:
      if p.is_connected():
       # print("Hei")    
            state = rp2.bootsel_button()
    
            # Detect rising edge (button just pressed)
            if state and not last_state:
                oldButBootSel = rp2.bootsel_button()
                now = time.ticks_ms()
            
                # First click or within double-click window
                if time.ticks_diff(now, last_click_time) < DOUBLE_CLICK_TIME:
                    click_count += 1
                else:
                    click_count = 1

                last_click_time = now

                # Double-click detected
                if click_count == 2:
                    if(ForwardDir==1):
                        ForwardDir=0
                    else:
                        ForwardDir=1
                        
                    data='{"M":'+str(ForwardDir) +' }'
                    print("TX", data)
                    p.send(data)

                    click_count = 0
                    
    
                time.sleep_ms(DEBOUNCE_TIME)

            last_state = state            
            
            y=0
            #for _ in range(10):
            time.sleep_ms(10)
            
            
            y= int((32*yPosition.read_u16()/65535 ))
            
            if(y==32):
                y=31


            if ((oldYpos!=y ) | (oldButBootSel != rp2.bootsel_button())) :
                oldButBootSel = rp2.bootsel_button()
                oldYpos=y
                
                #data='{"X":'
                data='{'
                if(oldButBootSel==True):
                    data=data+'"Y":'
                else :
                    data=data+'"X":'
                
                #data='{"X":'
                #data=data+str(x)+',"Y":'
                
                data=data+str(y)+'}'
                print("TX", data)
                p.send(data)

            time.sleep_ms(1)

if __name__ == "__main__":
    startRemoteBLE(name="Rem#10")

