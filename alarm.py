
import appdaemon.plugins.hass.hassapi as hass
import datetime
from threading import Timer

class Alarm(hass.Hass):
    def initialize(self):
        self.listen_state(self.leavingHome, "group.trusted_people", new = "not_home")
        self.listen_state(self.comingHome, "group.trusted_people", new = "home")

        #TODO: If the state triggers to "on" even if it is already "on" then I do not need the 2nd listener. Investigate...
        self.listen_state(self.shell_breached, "group.house_shell", new="on") #Sensors that should be "off" when armed
        self.listen_state(self.shell_breached, "binary_sensor.door_window_sensor_158d00022f151e", new="on") #bedroom window which can be open while alarm is armed

        self.last_triggered = None

        self.app = self.get_app('sleepy')
        self.utils = self.get_app('utils')
        self.lights = self.get_app('lights')

        self.app.registerWentToSleep("alarm_app" ,self.arm)
        self.app.registerWokeUp("alarm_app", self.disarm)

        self.armed = self.utils.anyone_home() == False or self.app.asleep

        self.log("Alarmsystem up and running. Is armed: {}".format(self.armed))

    def shell_breached(self, entity, attribute, old, new, kwargs):
        self.log("Skalskyddet brutet. Info: {} \n {}".format(entity, attribute))

        if not self.armed:
            return

        if self.last_triggered is not None and (datetime.datetime.now() - self.last_triggered).total_seconds < 900:
            return

        self.last_triggered = datetime.datetime.now()

        #Wait for 1 minute in case of "home"-delay
        Timer(60.0, timer_complete).start()

        def timer_complete(self):
            if not self.utils.anyone_home():
                self.utils.send_notification("Larm utlöst", "Sensor: {}".format(entity))
                self.lights.alarm_flash()
            else:
                self.log("Någon hann komma hem innan larmet utlöstes...")

    def leavingHome(self, entity, attribute, old, new, kwargs):
        self.arm()

    def comingHome(self, entity, attribute, old, new, kwargs):
        self.disarm()

    def arm(self):
        if self.armed:
            return

        self.armed = True
        self.utils.send_notification("Larm aktiverat", "Larmet är aktivt")
        self.lights.flash_lights_long("group.all_lights", "red")

    def disarm(self):
        if not self.armed:
            return

        self.armed = False
        self.utils.send_notification("Larm deaktiverat", "Larmet är ej aktivt")
        self.lights.flash_lights_long("group.all_lights", "green")
