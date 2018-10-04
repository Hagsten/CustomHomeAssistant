import appdaemon.plugins.hass.hassapi as hass
from threading import Timer

class Lights(hass.Hass):
    def initialize(self):
        self.lights = {
            "group.tv_room_rgb_lights" : Lights.Light(self, "group.tv_room_rgb_lights", self.__tv_room_rgb_default__),
            "group.hallway_lights" : Lights.Light(self, "group.hallway_lights", self.__hallway_default__),
            "light.gateway_light_7811dcdf0cfa" : Lights.Light(self, "light.gateway_light_7811dcdf0cfa", self.__gateway_default__)
        }

        self.listen_event(self.__ga_onoff_listener__, "lights_onoff")
        self.listen_event(self.__ga_mode_listener__, "lights_mode")

    def __ga_onoff_listener__(self, event_name, data, foo):
        self.log("Onoff: {} \n {} \n {} \n".format(event_name, data, foo))

        light = self.lights["group.tv_room_rgb_lights"]

        if data['state'] == 'on':
            self.__tv_room_rgb_default__(light)
        else:
            light.turn_off()
    
    def __ga_mode_listener__(self, event_name, data, foo):
        #'foo': 'cozy'
        self.log("Mode: {} \n {} \n {} \n".format(event_name, data, foo))

    def on(self, entity_id, brightness_pct=None, color_name=None, kelvin=None):
        light = self.lights[entity_id]

        light.turn_on(brightness_pct, color_name, kelvin)

    def off(self, entity_id):
        light = self.lights[entity_id]

        light.turn_off()

    def restore_previous(self, entity_id):
        light = self.lights[entity_id]

        light.restore_previous()

    def toggle_light(self, entity_id):
        light = self.lights[entity_id]

        light.toggle()

    def flash_lights_long(self, entity_id, color_name):
        self.turn_on(entity_id, color_name=color_name)

        t = Timer(5, lambda: self.__done_flashing__(entity_id))
        t.start()

    def alarm_flash(self):
        self.flash_lights("group.tv_room_rgb_lights", 60, "red")
        self.flash_lights("group.hallway_lights", 60, "red")
        self.flash_lights("light.gateway_light_7811dcdf0cfa", 60, "red")

    def flash_lights(self, entity_id, duration, color_name):
        self.turn_on(entity_id, color_name=color_name)

        RepeatedTimer(2, duration, self.__flash_lights__, self.__done_flashing__, entity_id)

    def __flash_lights__(self, entity_id):
        self.toggle(entity_id)

    def __done_flashing__(self, entity_id):
        self.restore_previous(entity_id)

    def __tv_room_rgb_default__(self, light):
        light.turn_on(brightness="50", kelvin=3000)

    def __gateway_default__(self, light):
        light.turn_on(brightness="10", rgb_color=[255,255,35])

    def __hallway_default__(self, light):
        light.turn_on()

    class Light():
        def __init__(self, parent, entity_id, default_on_fn):
            self.default_on_fn = default_on_fn
            self.parent = parent
            self.entity_id = entity_id
            
            current_state = self.parent.get_state(entity_id)

            self.previous = { "on": current_state != "on" }
            self.current = { "on": current_state == "on" }

            parent.listen_state(self.light_changed, entity_id)

        def light_changed(self, entity, attribute, old, new, kwargs):
            self.previous["on"] = old == "on"
            self.current["on"] = new == "on"

        def turn_on(self, brightness=None, color_name=None, kelvin=None, rgb_color=None):
            self.previous = self.current
            
            self.current = {
                "brightness_pct": brightness,
                "color_name": color_name,
                "kelvin": kelvin,
                "rgb_color": rgb_color,
                "on": True
            }

            self.__turn_on__(brightness_pct=brightness, color_name=color_name, kelvin=kelvin, rgb_color=rgb_color)

        def turn_off(self):
            self.previous = self.current

            self.current = { "on" : False }

            self.parent.turn_off(self.entity_id)

        def toggle(self):
            self.previous = self.current

            self.parent.toggle(self.entity_id)

            self.current["on"] = self.parent.get_state(self.entity_id) == "on"

        def restore_previous(self):
            prev_temp = self.previous

            self.parent.log("Restoring previous...{}".format(self.previous))
            
            if self.previous["on"]:
                if all(map(lambda x: self.previous[x] is None, self.__get_all_previous_color_keys__())):
                    self.parent.log("Restoring previous with a default ON strategy")
                    self.default_on_fn(self)
                else:
                    self.__turn_on__(
                        brightness_pct=self.previous["brightness_pct"], 
                        color_name=self.previous["color_name"], 
                        kelvin=self.previous["kelvin"], 
                        rgb_color=self.previous["rgb_color"])
            else:
                self.parent.turn_off(self.entity_id) 

            self.previous = self.current
            self.current = prev_temp

        def __get_all_previous_color_keys__(self):
            return [key for key in self.previous.keys() if key != "on"]

        def __turn_on__(self, brightness_pct=None, color_name=None, rgb_color=None, kelvin=None):
            brightness = brightness_pct if brightness_pct is not None else self.previous.get("brightness_pct", "50")

            if color_name is not None:
                self.parent.turn_on(self.entity_id, brightness_pct=brightness, color_name=color_name)
            elif rgb_color is not None:
                self.parent.turn_on(self.entity_id, brightness_pct=brightness, rgb_color=rgb_color)
            elif kelvin is not None:
                self.parent.turn_on(self.entity_id, brightness_pct=brightness, kelvin=kelvin)

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

