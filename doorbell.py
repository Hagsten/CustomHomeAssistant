
import appdaemon.plugins.hass.hassapi as hass
import datetime
from threading import Timer

class Doorbell(hass.Hass):
    timer = None

    def initialize(self):
        self.asleep = self.get_app('sleepy')
        self.lights = self.get_app('lights')
        self.listen_event(self.buttonListener, event="click", entity_id="binary_sensor.switch_doorbell")
        self.log("Doorbell app is running...")

    def buttonListener(self, event_name, data, foo):
        if self.asleep.asleep:
            self.call_service("script/1537340978223", ringtone=10, volume=10)
        else:
            self.call_service("script/1537340978223", ringtone=10, volume=50)

        self.lights.on("group.hallway_lights")

        if self.timer is not None:
            self.timer.cancel()
    
        self.timer = Timer(120.0, self.turnOffLights)
        self.timer.start()

        if self.get_state("group.trusted_people") == "not_home":
            self.call_service("notify/pushbullet_notifier", title="Somebody at the door", message="There were somebody at the door")

    def turnOffLights(self):
        self.log("turning lights off...")
        self.lights.off("group.hallway_lights")