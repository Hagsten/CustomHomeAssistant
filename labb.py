
import appdaemon.plugins.hass.hassapi as hass
import datetime
from threading import Timer

class Labb(hass.Hass):
    motionSensors = None

    def initialize(self):
        self.log(datetime.datetime.now())
        sensorNames = self.get_state("group.motion_sensors", attribute="entity_id")
        self.log(sensorNames)
        self.motionSensors = [self.get_state(x, attribute="all") for x in sensorNames]
        #self.log(self.motionSensors)

        foos = [{"last_changed": o['last_changed'], "entity_id": o['entity_id'], "state": o['state']} for o in self.motionSensors]

        self.log(foos)






