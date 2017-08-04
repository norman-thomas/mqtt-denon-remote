import json
import denonavr
import paho.mqtt.client as mqtt

MQTT_BROKER = 'pluto.fritz.box'

MQTT_REFRESH = 'wohnzimmer/devices/denon/refresh'
MQTT_STATUS = 'wohnzimmer/devices/denon/status'

MQTT_POWER = 'wohnzimmer/devices/denon/power'
MQTT_VOLUME = 'wohnzimmer/devices/denon/volume'
MQTT_INPUT = 'wohnzimmer/devices/denon/input'
MQTT_MUTE = 'wohnzimmer/devices/denon/mute'
MQTT_PLAY= 'wohnzimmer/devices/denon/play'

MQTT_LISTEN = (
    (MQTT_REFRESH, 2),
    (MQTT_POWER, 2),
    (MQTT_VOLUME, 2),
    (MQTT_MUTE, 2),
    (MQTT_INPUT, 2),
    (MQTT_PLAY, 2)
)


def on_connect(client, userdata, flags, rc):
    print('Connected with result code ' + str(rc))
    for topic in MQTT_LISTEN:
        client.subscribe(topic)

def on_message(denon, client, userdata, msg):
    payload = str(msg.payload, 'utf-8')
    print('Received MQTT with topic:', msg.topic, 'and payload:', payload)
    if msg.topic == MQTT_REFRESH:
        refresh(denon, client)
    elif msg.topic == MQTT_POWER:
        power(denon, client, payload)
    elif msg.topic == MQTT_VOLUME:
        volume(denon, client, payload)
    elif msg.topic == MQTT_MUTE:
        mute(denon, client, payload)
    elif msg.topic == MQTT_INPUT:
        source(denon, client, payload)
    elif msg.topic == MQTT_PLAY:
        play(denon, client, payload)


def publishStatus(denon, mqttClient):
    result = {
        'name': denon.name,
        'power': denon.power.lower(),
        'volume': denon.volume,
        'mute': denon.muted,
        'input': denon.input_func
    }
    payload = json.dumps(result)
    mqttClient.publish(MQTT_STATUS, payload=payload, qos=2, retain=True)

def refresh(denon, mqttClient):
    denon.update()
    publishStatus(denon, mqttClient)

def power(denon, mqttClient, arg):
    print('POWER, arg =', arg)
    if arg.lower() == 'on':
        denon.power_on()
    elif arg.lower() == 'off':
        denon.power_off()
    else:
        print('POWER, invalid argument:', arg)
    refresh(denon, mqttClient)

def volume(denon, mqttClient, arg):
    print('VOLUME, arg =', arg)
    if arg.lower() == 'up':
        denon.volume_up()
    elif arg.lower() == 'down':
        denon.volume_down()
    elif arg[0] == '-' and arg[1:].isdecimal():
        target_volume = -int(arg[1:])
        denon.set_volume(target_volume)
    else:
        print('MUTE, invalid argument:', arg)
    refresh(denon, mqttClient)

def mute(denon, mqttClient, arg):
    print('MUTE, arg =', arg)
    if arg.lower() == 'on':
        denon.mute(True)
    elif arg.lower() == 'off':
        denon.mute(False)
    else:
        print('MUTE, invalid argument:', arg)
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
    denon._input_func_list = inputMapping
    return inputMapping

def source(denon, mqttClient, arg):
    inputMapping = updateInputList(denon)

    if arg in inputMapping:
        denon.input_func = arg
    else:
        print('INPUT, invalid argument:', arg)

def play(denon, mqttClient, arg):
    print('PLAY/PAUSE')
    denon.toggle_play_pause()
    refresh(denon, mqttClient)

if __name__ == '__main__':
    d = denonavr.DenonAVR('denon.fritz.box', 'Denon')
    updateInputList(d)

    d.update()

    mqttClient = mqtt.Client()
    mqttClient.on_connect = on_connect
    mqttClient.on_message = lambda client, userdata, msg: on_message(d, client, userdata, msg)
    mqttClient.connect(MQTT_BROKER, 1883, 60)
    mqttClient.loop_forever()

