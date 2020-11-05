from os import system
import requests
import json
from time import sleep
import RPi.GPIO as GPIO

GPIO.setmode(GPIO.BCM)

key = {
    1: GPIO.HIGH,
    0: GPIO.LOW}


def initialize():
    while True:
        try:
            with open("config.json", "r") as config:
                # print(config.read())
                return json.loads(config.read())
        except Exception as e:
            print("error  - {}".format(e))
        sleep(2)


def export_gpio(gpio, direction):
    # system("echo {} > /sys/class/gpio/export".format(gpio))
    # system("gpio mode {} {}".format(gpio, direction))
    GPIO.setup(int(gpio), GPIO.OUT, initial=GPIO.LOW)


def initialize_gpio(config):
    for gpio_pin in config["gpio"]:
        export_gpio(gpio_pin["pin"], gpio_pin["direction"])


def set_gpio(pin, value, inverted):
    # system("gpio write {} {}".format(pin, abs(value - inverted)))
    GPIO.output(int(pin), key[abs(value - inverted)])


def send_in_trigger(pin, config):
    print("trigger to pin {}".format(pin))
    GPIO.output(int(pin), key[1])
    sleep(config['trigger_up_time_s'])
    GPIO.output(int(pin), key[0])
    sleep(config['trigger_down_time_s'])


def handle_gpio(config, occupancy):
    if occupancy["occupancy"] >= occupancy["maximum_occupancy"]:
        for gpio_pin in config["gpio"]:
            set_gpio(gpio_pin["pin"], 1, gpio_pin["inverted"])
    else:
        for gpio_pin in config["gpio"]:
            set_gpio(gpio_pin["pin"], 0, gpio_pin["inverted"])


def get_occupancy_data(config):
    url = "http://{}:{}{}".format(config["device_ip"], config["device_port"], config["api"])
    # print(url)
    try:
        response = requests.get(url)
        return json.loads(response.text)
    except Exception as e:
        print("error while retrieving occupancy data - {}".format(e))
        return 0


def main():
    config = initialize()
    prev_in = None
    prev_out = None
    sleep(30)
    while True:
        try:
            initialize_gpio(config)
            break
        except Exception as e:
            print("error while gpio initializing {}".format(e))
        sleep(5)
    while True:
        occupancy_data = get_occupancy_data(config)
        # print(occupancy_data)
        if occupancy_data == 0:
            sleep(2)
            continue
        if int(occupancy_data['relay-function']) == 0:
            # print("relay function is off")
            if prev_in is None and prev_out is None:
                
                print("Starting for the first time")
                prev_in = occupancy_data['in']
                prev_out = occupancy_data['out']
                continue
            
            in_diff = abs(prev_in - occupancy_data['in'])
            out_diff = abs(prev_out - occupancy_data['out'])
            
            if in_diff > 50 or out_diff > 50:
                prev_in = occupancy_data['in']
                prev_out = occupancy_data['out']
                continue
            print(in_diff, out_diff)
            
            for _in in range(0, in_diff):
                send_in_trigger(config['gpio'][0]['pin'], config)
            for _out in range(0, out_diff):
                send_in_trigger(config['gpio'][1]['pin'], config)
            prev_in = occupancy_data['in']
            prev_out = occupancy_data['out']
            
        else:
            handle_gpio(config, occupancy_data)
        sleep(2)


if __name__ == '__main__':
    main()

# initialize_gpio(initialize())
