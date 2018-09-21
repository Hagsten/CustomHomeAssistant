
import appdaemon.plugins.hass.hassapi as hass
import datetime
from threading import Timer

class Labb(hass.Hass):
    motionSensors = None

    def initialize(self):
        app = self.get_app('asleep')
        self.log(app.is_asleep())
        #app.is_asleep()



