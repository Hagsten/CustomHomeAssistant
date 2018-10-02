
import appdaemon.plugins.hass.hassapi as hass

class Utils(hass.Hass):
    def initialize(self):
        pass

    def anyone_home(self):
        return self.get_state("group.trusted_people") == "home"

    def send_notification(self, title, message):
        self.call_service("notify/pushbullet_notifier", title=title, message=message)