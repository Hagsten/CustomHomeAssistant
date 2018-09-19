import appdaemon.plugins.hass.hassapi as hass
import datetime
import asleep
from threading import Timer

class Doorbell(hass.Hass):
    sleepCheck = asleep.Asleep()
    timer = None
    motionSensors = None

    def initialize(self):
        self.listen_event(self.buttonListener, event="click", entity_id="binary_sensor.switch_doorbell")
        sensorNames = self.get_state("group.motion_sensors", attribute="entity_id")
        self.log(sensorNames)
        self.motionSensors = [self.get_state(x, attribute="all") for x in sensorNames]
        self.log(self.motionSensors)
        self.log("Doorbell app is running...")

    def buttonListener(self, event_name, data, foo):
        #self.log(self.get_state("binary_sensor.motion_sensor_upper_floor", attribute="all"))

        if self.sleepCheck.is_asleep():
            self.call_service("script/1537340978223", ringtone=10, volume=10)
        else:
            self.call_service("script/1537340978223", ringtone=10, volume=50)

        self.turn_on("group.hallway_lights")

        if self.timer is not None:
            self.timer.cancel()
    
        self.timer = Timer(120.0, self.turnOffLights)
        self.timer.start()

        if self.get_state("group.trusted_people") == "not_home":
            self.call_service("notify/pushbullet_notifier", title="Somebody at the door", message="There were somebody at the door")

    def turnOffLights(self):
        self.log("turning lights off...")
        self.turn_off("group.hallway_lights")
