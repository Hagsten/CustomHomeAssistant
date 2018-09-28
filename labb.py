
import appdaemon.plugins.hass.hassapi as hass
import datetime
from threading import Timer

class Labb(hass.Hass):
    def initialize(self):
        self.listen_state(self.leavingHome, "group.trusted_people", new = "not_home")
        self.listen_state(self.comingHome, "group.trusted_people", new = "home")

        self.app = self.get_app('asleep')
        self.utils = self.get_app('utils')
        self.app.registerWentToSleep(self.arm)
        self.app.registerWokeUp(self.disarm)

        self.armed = self.utils.anyone_home() == False or self.app.asleep
        self.log("Alarmsystem up and running. Is armed: {}".format(self.armed))
        #self.utils.alarm_flash()

        self.log(self.get_state("light.gateway_light_7811dcdf0cfa",attribute="all"))

    def leavingHome(self, entity, attribute, old, new, kwargs):
        self.arm()

    def comingHome(self, entity, attribute, old, new, kwargs):
        self.disarm()

    def arm(self):
        if self.armed:
            return

        self.armed = True
        self.log("Armed")
        self.utils.send_notification("Test: Larm aktiverat", "Test: Orsak - antas sova")
        self.utils.flash_lights_long("group.all_lights", "red")

    def disarm(self):
        if not self.armed:
            return

        self.armed = False
        self.log("Disarmed")
        self.utils.send_notification("Test: Larm deaktiverat", "Test: Orsak - antas ha vaknat")
        self.utils.flash_lights_long("group.all_lights", "green")
