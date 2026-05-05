# libraries needed
import time
import network
import machine
import ubinascii
import ujson
from machine import Pin, I2C
from umqtt.simple import MQTTClient
from i2c_lcd import I2cLcd

# wifi setup
WIFI_SSID = "ClassroomNet"
WIFI_PASSWORD = "**********"

# mqtt setup
MQTT_BROKER = "192.168.0.***"
MQTT_PORT = 1883
MQTT_TOPIC = b"classroom/feedback"
MQTT_CLIENT_ID = b"pico-" + ubinascii.hexlify(machine.unique_id())

# student deive setup
STUDENT_ID = "STUDENT_01"

# lcd screen setup
i2c = I2C(0, scl=Pin(17), sda=Pin(16), freq=100000)
lcd = I2cLcd(i2c, 0x27, 2, 16)
lcd.backlight_on()

# button setup
btn_understand = Pin(18, Pin.IN, Pin.PULL_UP)
btn_slow = Pin(19, Pin.IN, Pin.PULL_UP)
btn_help = Pin(20, Pin.IN, Pin.PULL_UP)

# checks every 0.25 seconds
DEBOUNCE_MS = 250
last_press = {
    "understand": 0,
    "slow_down": 0,
    "help": 0
}

mqtt_client = None

# custom lcd face setup
happy_face = [
    0b00000,
    0b01010,
    0b01010,
    0b00000,
    0b00000,
    0b10001,
    0b01110,
    0b00000
]

neutral_face = [
    0b00000,
    0b01010,
    0b01010,
    0b00000,
    0b00000,
    0b01110,
    0b00000,
    0b00000
]

sad_face = [
    0b00000,
    0b01010,
    0b01010,
    0b00000,
    0b00000,
    0b01110,
    0b10001,
    0b00000
]

lcd.custom_char(0, happy_face)
lcd.custom_char(1, neutral_face)
lcd.custom_char(2, sad_face)

# lcd screen helper functions
def show_message(line1="", line2=""):
    lcd.clear()
    lcd.move_to(0, 0)
    lcd.putstr(line1[:16])
    lcd.move_to(0, 1)
    lcd.putstr(line2[:16])

def show_idle():
    lcd.clear()
    lcd.move_to(0, 0)
    lcd.putstr("Choose a button")
    lcd.move_to(0, 1)
    lcd.putstr(chr(0))
    lcd.putstr(" ")
    lcd.putstr(chr(1))
    lcd.putstr(" ")
    lcd.putstr(chr(2))

def show_sending(text):
    lcd.clear()
    lcd.move_to(0, 0)
    lcd.putstr("Sending...")
    lcd.move_to(0, 1)
    lcd.putstr(text[:16])

def show_success(status):
    lcd.clear()

    if status == "understand":
        lcd.move_to(0, 0)
        lcd.putstr("I got it! ")
        lcd.putstr(chr(0))
        lcd.move_to(0, 1)
        lcd.putstr("Great job!")

    elif status == "slow_down":
        lcd.move_to(0, 0)
        lcd.putstr("Too fast ")
        lcd.putstr(chr(1))
        lcd.move_to(0, 1)
        lcd.putstr("Slow down pls")

    elif status == "help":
        lcd.move_to(0, 0)
        lcd.putstr("Need help ")
        lcd.putstr(chr(2))
        lcd.move_to(0, 1)
        lcd.putstr("Please help")

def show_publish_failed():
    show_message("Send failed", "Try again")

def show_wifi_connecting():
    show_message("Connecting WiFi", "Please wait...")

def show_wifi_ok():
    show_message("WiFi connected", "Ready soon...")
    time.sleep(1)

def show_mqtt_connecting():
    show_message("Connecting MQTT", "Please wait...")

def show_mqtt_ok():
    show_message("System ready", "Press button")
    time.sleep(1)

# wifi functions
def wifi_connect():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)

    if wlan.isconnected():
        return wlan

    print("Connecting to Wi-Fi:", WIFI_SSID)
    show_wifi_connecting()
    wlan.connect(WIFI_SSID, WIFI_PASSWORD)

    timeout = 15
    start = time.time()

    while not wlan.isconnected():
        if time.time() - start > timeout:
            show_message("WiFi failed", "Timeout")
            raise RuntimeError("Wi-Fi connection timeout")
        time.sleep(1)
        print(".", end="")

    print("\nWi-Fi connected")
    print("Pico IP:", wlan.ifconfig()[0])
    show_wifi_ok()
    return wlan

def wifi_ensure():
    wlan = network.WLAN(network.STA_IF)
    if not wlan.active():
        wlan.active(True)

    if not wlan.isconnected():
        print("Wi-Fi lost, reconnecting...")
        show_message("WiFi lost", "Reconnecting...")
        wlan = wifi_connect()

    return wlan

# mqtt functions
def mqtt_connect():
    global mqtt_client

    print("Connecting to MQTT broker:", MQTT_BROKER)
    show_mqtt_connecting()

    mqtt_client = MQTTClient(
        client_id=MQTT_CLIENT_ID,
        server=MQTT_BROKER,
        port=MQTT_PORT,
        keepalive=30
    )
    mqtt_client.connect()
    print("MQTT connected")
    show_mqtt_ok()

def mqtt_ensure():
    global mqtt_client
    wifi_ensure()

    if mqtt_client is None:
        mqtt_connect()

# publish on mqtt function
def publish_status(status):
    global mqtt_client

    payload = {
        "id": STUDENT_ID,
        "msg": status
    }

    message = ujson.dumps(payload)

    if status == "understand":
        show_sending("I got it")
    elif status == "slow_down":
        show_sending("Too fast")
    elif status == "help":
        show_sending("Need help")

    try:
        mqtt_ensure()
        mqtt_client.publish(MQTT_TOPIC, message)
        print("Published:", message)

        show_success(status)
        time.sleep(2.5)
        show_idle()

    except Exception as e:
        print("Publish failed:", e)

        try:
            mqtt_connect()
            mqtt_client.publish(MQTT_TOPIC, message)
            print("Published after reconnect:", message)

            show_success(status)
            time.sleep(2.5)
            show_idle()

        except Exception as e2:
            print("MQTT reconnect failed:", e2)
            show_publish_failed()
            time.sleep(2.5)
            show_idle()

# checks if button is pressed
def pressed(pin, label):
    now = time.ticks_ms()
    if pin.value() == 0 and time.ticks_diff(now, last_press[label]) > DEBOUNCE_MS:
        last_press[label] = now
        return True
    return False

# main function
def main():
    print("Starting pod", STUDENT_ID)
    show_message("Starting pod...", STUDENT_ID)

    try:
        wifi_connect()
        mqtt_connect()
        print("Ready")
        show_idle()

    except Exception as e:
        print("Startup connection problem:", e)
        show_message("Startup failed", "Check network")
        return

    while True:
        if pressed(btn_understand, "understand"):
            publish_status("understand")

        elif pressed(btn_slow, "slow_down"):
            publish_status("slow_down")

        elif pressed(btn_help, "help"):
            publish_status("help")

        time.sleep(0.05)

main()