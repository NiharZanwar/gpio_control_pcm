from os import system
import requests
import json
from time import sleep


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
    system("gpio mode {} {}".format(gpio, direction))


def initialize_gpio(config):
    for gpio_pin in config["gpio"]:
        export_gpio(gpio_pin["pin"], gpio_pin["direction"])


def set_gpio(pin, value, inverted):
    system("gpio write {} {}".format(pin, abs(value - inverted)))


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
    while True:
        try:
            initialize_gpio(config)
            break
        except Exception as e:
            print("error while gpio initializing {}".format(e))
        sleep(5)
    while True:
        occupancy_data = get_occupancy_data(config)
        if occupancy_data == 0:
            sleep(2)
            continue
        else:
            handle_gpio(config, occupancy_data)
        sleep(2)


if __name__ == '__main__':
    main()
# initialize_gpio(initialize())
