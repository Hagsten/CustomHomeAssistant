
import appdaemon.plugins.hass.hassapi as hass
import datetime
from threading import Timer

class Alarm(hass.Hass):
    def initialize(self):
        self.listen_state(self.leavingHome, "group.trusted_people", new = "not_home")
        self.listen_state(self.comingHome, "group.trusted_people", new = "home")

        self.listen_state(self.trigger_alarm, "group.house_shell", new="on") #Sensors that should be "off" when armed
        self.listen_state(self.trigger_alarm, "binary_sensor.door_window_sensor_158d00022f151e", new="on") #bedroom window which can be open while alarm is armed
        self.listen_state(self.trigger_alarm, "group.motion_sensors", new="on")

        self.listen_state(self.manual_arming, "input_boolean.alarm_state", new="on")
        self.listen_state(self.manual_disarming, "input_boolean.alarm_state", new="off")

        self.last_triggered = None

        self.app = self.get_app('sleepy')
        self.utils = self.get_app('utils')
        self.lights = self.get_app('lights')

        self.app.registerWentToSleep("alarm_app" ,self.arm)
        self.app.registerWokeUp("alarm_app", self.disarm)

        self.armed = self.get_state("input_boolean.alarm_state") == "on" or (self.utils.anyone_home() == False or self.app.asleep)

        self.manualArmingTimer = None

        self.log("Alarmsystem up and running. Is armed: {}".format(self.armed))

    def trigger_alarm(self, entity, attribute, old, new, kwargs):
        triggered_entity = self.__get_entity_thet_caused_trigger__(entity)       
        
        if not self.armed:
            return

        if self.last_triggered is not None and (datetime.datetime.now() - self.last_triggered).total_seconds() < 900:
            return

        self.last_triggered = datetime.datetime.now()

        self.log("Alarm about to be triggered. Info: {}".format(triggered_entity))
        self.utils.send_notification("Larm på väg att lösas ut", "Orsak: {}".format(triggered_entity))

        #Wait for 1 minute in case of "home"-delay
        t = Timer(60.0, self.__alarm_timer_complete__)
        t.start()

    def manual_arming(self, entity, attribute, old, new, kwargs):
        self.log("Armed manually")

        self.arm()

    def manual_disarming(self, entity, attribute, old, new, kwargs):
        self.log("Disarmed manually")
        
        self.disarm()

    def leavingHome(self, entity, attribute, old, new, kwargs):
        self.arm()

    def comingHome(self, entity, attribute, old, new, kwargs):
        self.disarm()

    def arm(self):
        if self.armed:
            return

        self.armed = True
        self.set_state("input_boolean.alarm_state", state="on")
        self.utils.send_notification("Larm aktiverat", "Larmet är aktivt")
        self.lights.flash_lights_long("light.gateway_light_7811dcdf0cfa", "red")

    def disarm(self):
        if self.manualArmingTimer is not None:
            self.manualArmingTimer.cancel()
        
        if not self.armed:
            return

        self.armed = False
        self.set_state("input_boolean.alarm_state", state="off")
        self.set_state("input_boolean.alarm_triggered", state="off")

        self.utils.send_notification("Larm deaktiverat", "Larmet är ej aktivt")
        self.lights.flash_lights_long("light.gateway_light_7811dcdf0cfa", "green")

    def __get_entity_thet_caused_trigger__(self, entity_id):
        if entity_id.startswith("group."):
            entities_in_group = [self.get_state(x, attribute="all") for x in self.get_state(entity_id, attribute="entity_id")]
        
            candidate = sorted(entities_in_group, key=lambda x: x['last_changed'], reverse=True)[0]

            if candidate['entity_id'].startswith("group."):
                return self.__get_entity_thet_caused_trigger__(candidate['entity_id'])

            return candidate['attributes']['friendly_name']
        
        return entity_id

    def __alarm_timer_complete__(self):
        if self.armed:
            self.utils.send_notification("Larm utlöst", "Sensor: {}".format("placeholder")) #TODO: pass args in timer. Investigate how
            self.set_state("input_boolean.alarm_triggered", state="on")
            #self.lights.alarm_flash()
        else:
            self.log("Någon hann komma hem innan larmet utlöstes...")