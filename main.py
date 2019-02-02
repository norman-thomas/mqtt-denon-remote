import os
import logging
import json
import denonavr
import paho.mqtt.client as mqtt

LOGGER = logging.getLogger('denon')

DENON_HOST = os.getenv('DENON_HOST')
MQTT_BROKER = os.getenv('MQTT_BROKER')

MQTT_REFRESH = 'wohnzimmer/devices/denon/refresh'
MQTT_STATUS = 'wohnzimmer/devices/denon/status'

MQTT_POWER = 'wohnzimmer/devices/denon/power'
MQTT_VOLUME = 'wohnzimmer/devices/denon/volume'
MQTT_INPUT = 'wohnzimmer/devices/denon/input'
MQTT_MUTE = 'wohnzimmer/devices/denon/mute'
MQTT_PLAY = 'wohnzimmer/devices/denon/play'

MQTT_LISTEN = (
    (MQTT_REFRESH, 2),
    (MQTT_POWER, 2),
    (MQTT_VOLUME, 2),
    (MQTT_MUTE, 2),
    (MQTT_INPUT, 2),
    (MQTT_PLAY, 2)
)


def on_connect(mqttClient, userdata, flags, rc):
    LOGGER.info('Connected with result code %s', str(rc))
    for topic in MQTT_LISTEN:
        mqttClient.subscribe(topic)

def on_message(denon, mqttClient, userdata, msg):
    payload = str(msg.payload, 'utf-8')
    LOGGER.info('Received MQTT with topic: %s and payload: %s', msg.topic, payload)
    if msg.topic == MQTT_REFRESH:
        refresh(denon, mqttClient)
    elif msg.topic == MQTT_POWER:
        power(denon, mqttClient, payload)
    elif msg.topic == MQTT_VOLUME:
        volume(denon, mqttClient, payload)
    elif msg.topic == MQTT_MUTE:
        mute(denon, mqttClient, payload)
    elif msg.topic == MQTT_INPUT:
        source(denon, mqttClient, payload)
    elif msg.topic == MQTT_PLAY:
        play(denon, mqttClient, payload)


def publishStatus(denon, mqttClient):
    result = {
        'name': denon.name,
        'power': denon.power.lower(),
        'volume': denon.volume,
        'mute': denon.muted,
        'input': denon.input_func
    }
    payload = json.dumps(result)
    mqttClient.publish(MQTT_STATUS, payload=payload, qos=1, retain=False)

def refresh(denon, mqttClient):
    denon.update()
    publishStatus(denon, mqttClient)

def power(denon, mqttClient, arg):
    LOGGER.info('POWER, arg = %s', arg)
    if arg.lower() == 'on':
        denon.power_on()
    elif arg.lower() == 'off':
        denon.power_off()
    else:
        LOGGER.info('POWER, invalid argument: %s', arg)
    refresh(denon, mqttClient)

def volume(denon, mqttClient, arg):
    LOGGER.info('VOLUME, arg = %s', arg)
    denon.update()
    if arg.lower() == 'up':
        denon.set_volume(denon.volume + 5)
    elif arg.lower() == 'down':
        denon.set_volume(denon.volume - 5)
    elif arg[0] == '-' and arg[1:].isdecimal():
        target_volume = -int(arg[1:])
        denon.set_volume(target_volume)
    else:
        LOGGER.info('MUTE, invalid argument: %s', arg)
    refresh(denon, mqttClient)

def mute(denon, mqttClient, arg):
    LOGGER.info('MUTE, arg = %s', arg)
    if arg.lower() == 'on':
        denon.mute(True)
    elif arg.lower() == 'off':
        denon.mute(False)
    else:
        LOGGER.info('MUTE, invalid argument: %s', arg)
    refresh(denon, mqttClient)

def updateInputList(denon):
    inputMapping = {
        'CD': 'CD',
        'iPod/USB': 'USB/IPOD',
        'Media Player': 'MPLAY',
        'Blu-ray': 'BD',
        'NETWORK': 'NET',
        'FM': 'TUNER',
        'GAME': 'GAME',
        'DVD': 'DVD',
        'CBL/SAT': 'SAT/CBL',
        'AUX': 'AUX1',
        'TV AUDIO': 'TV'
    }
    denon._input_func_list = inputMapping  # pylint: disable=protected-access
    return inputMapping

def source(denon, mqttClient, arg):
    inputMapping = updateInputList(denon)

    if arg in inputMapping:
        denon.input_func = arg
    else:
        LOGGER.info('INPUT, invalid argument: %s', arg)

def play(denon, mqttClient, arg):
    LOGGER.info('PLAY/PAUSE')
    denon.toggle_play_pause()
    refresh(denon, mqttClient)

if __name__ == '__main__':
    d = denonavr.DenonAVR(DENON_HOST, 'Denon')
    updateInputList(d)

    d.update()

    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = lambda client, userdata, msg: on_message(d, client, userdata, msg)
    client.connect(MQTT_BROKER, 1883, 60)
    client.loop_forever()
