
import appdaemon.plugins.hass.hassapi as hass
from threading import Timer
import datetime

class Utils(hass.Hass):
    standardGatewayColor = "255, 255, 35"
    standardLightKelvin = 3000

    def initialize(self):
        pass

    def anyone_home(self):
        return self.get_state("group.trusted_people") == "home"

    def send_notification(self, title, message):
        self.call_service("notify/pushbullet_notifier", title=title, message=message)

    def flash_lights_long(self, entity_id, color_name):
        self.turn_on(entity_id, color_name=color_name)

        t = Timer(5, lambda: self.__done_flashing__(entity_id))
        t.start()

    def alarm_flash(self):
        self.flash_lights("group.all_lights", 60, "red")

    def flash_lights(self, entity_id, duration, color_name):
        self.turn_on(entity_id, color_name=color_name)

        RepeatedTimer(2, duration, self.__flash_lights__, self.__done_flashing__, entity_id)

    def __flash_lights__(self, entity_id):
        self.toggle(entity_id)

    def __done_flashing__(self, entity_id):
        self.turn_off(entity_id)

class RepeatedTimer(object):
    def __init__(self, interval, total_duration, function, stop_cb, *args, **kwargs):
        self.stop_callback = stop_cb
        self._timer     = None
        self.interval   = interval
        self.function   = function
        self.args       = args
        self.kwargs     = kwargs
        self.is_running = False
        self.total_duration = total_duration
        self._total_duration_timer = Timer(self.total_duration, self.stop)
        self._total_duration_timer.start()
        self.start()

    def __exit__(self, exc_type, exc_value, traceback):
        if self._timer is not None:
            self._timer.cancel()
        
        if self._total_duration_timer is not None:
            self._total_duration_timer.cancel()

    def _run(self):
        self.is_running = False
        self.start()
        self.function(*self.args, **self.kwargs)

    def start(self):
        if not self.is_running:
            self._timer = Timer(self.interval, self._run)
            self._timer.start()
            self.is_running = True

    def stop(self):
        self._timer.cancel()
        self.is_running = False

        self.stop_callback(*self.args)
