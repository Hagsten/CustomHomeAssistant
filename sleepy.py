import appdaemon.plugins.hass.hassapi as hass
import datetime

class Sleepy(hass.Hass):
    wentToSleepSubscribers = {}
    wokeUpSubscribers = {}

    def initialize(self):
        self.utils = self.get_app('utils')
        
        self.listen_state(self.handleMotionCleared, "binary_sensor.motion_sensor_upper_floor", new = "off")
        self.listen_state(self.handleMotionDetected, "group.motion_sensors", new = "on")

        #Listen to a IFTTT battery charging event. If the below conditions are met + battery is charging then apply a more offensive strategy (the current)
        #else wait at least double the time to activate the alarm

        #If it is in the middle of the night we can ignore this and apply the offensive strategy since one would not unplug the phone when going to the bathroom.

        self.asleep = False

        self.log("Asleep up and running")

    def handleMotionCleared(self, event_name, data, foo, bar, baz):
        if not self.utils.anyone_home():
            return

        if self.asleep:
            return

        if datetime.datetime.now().hour >= 7 and datetime.datetime.now().hour <= 19:
            return

        sortedSensors = self.getMotionSensors()
        
        if not all(sensor['state'] == 'off' for sensor in sortedSensors):
            return

        if not (sortedSensors[0]['entity_id'] == "binary_sensor.motion_sensor_upper_floor" and int(sortedSensors[0]['attributes']['No motion since']) >= 900):
            return

        self.log("Calling went to sleep subscribers...")

        self.asleep = True

        for key in self.wentToSleepSubscribers:
            self.wentToSleepSubscribers[key]()

    def handleMotionDetected(self, event_name, data, old, new, handle):
        if not self.utils.anyone_home():
            return

        if not self.asleep:
            return

        sortedSensors = self.getMotionSensors()

        if sortedSensors[0]['entity_id'] == "binary_sensor.motion_sensor_upper_floor" and sortedSensors[0]['state'] == 'on':
            self.asleep = False
            self.log("Calling waking up subscribers...")

            for key in self.wokeUpSubscribers:
                self.wokeUpSubscribers[key]()

    def registerWentToSleep(self, key, cb):
        self.log(self.wentToSleepSubscribers)
        self.wentToSleepSubscribers[key] = cb

    def registerWokeUp(self, key, cb):
        self.wokeUpSubscribers[key] = cb

    def getMotionSensors(self):
        motionSensors = [self.get_state(x, attribute="all") for x in self.get_state("group.motion_sensors", attribute="entity_id")]
        
        return sorted(motionSensors, key=lambda x: x['last_changed'], reverse=True)