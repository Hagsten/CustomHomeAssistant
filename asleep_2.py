import appdaemon.plugins.hass.hassapi as hass
import datetime

class asleep_2(hass.Hass):
    wentToSleepSubscribers = []
    wokeUpSubscribers = []

    def initialize(self):
        self.utils = self.get_app('utils')
        
        self.listen_state(self.handleMotionCleared, "binary_sensor.motion_sensor_upper_floor", new = "off")
        self.listen_state(self.handleMotionDetected, "group.motion_sensors", new = "on")
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

        for subsc in self.wentToSleepSubscribers:
            subsc()

    def handleMotionDetected(self, event_name, data, old, new, handle):
        if not self.utils.anyone_home():
            return

        if not self.asleep:
            return

        sortedSensors = self.getMotionSensors()

        if sortedSensors[0]['entity_id'] == "binary_sensor.motion_sensor_upper_floor" and sortedSensors[0]['state'] == 'on':
            self.asleep = False
            self.log("Calling waking up subscribers...")

            for subsc in self.wokeUpSubscribers:
                subsc()

    def registerWentToSleep(self, cb):
        self.log(self.wentToSleepSubscribers)
        self.wentToSleepSubscribers.append(cb)

    def registerWokeUp(self, cb):
        self.wokeUpSubscribers.append(cb)

    def getMotionSensors(self):
        motionSensors = [self.get_state(x, attribute="all") for x in self.get_state("group.motion_sensors", attribute="entity_id")]
        
        return sorted(motionSensors, key=lambda x: x['last_changed'], reverse=True)
