import appdaemon.plugins.hass.hassapi as hass
import datetime

class TvRoomSwitch(hass.Hass):
    counter = 0  
    lastAcceptedClick = datetime.datetime.now()
    colors = ["blue", "green", "red", "cyan", "pink", "darkorange"]
    colorCounter = 0

    def initialize(self):
        self.lights = self.get_app('lights')
        self.listen_event(self.buttonListener, event="click", entity_id="binary_sensor.switch_158d000215c957", click_Type="single")
        self.log("Tv room switch app is running...")

    def buttonListener(self, event_name, data, foo):
        if data['click_type'] == "double":
            self.handleDoubleClick()
            return
        
        timeSinceLastAcceptedClick = (datetime.datetime.now() - self.lastAcceptedClick).total_seconds()

        if timeSinceLastAcceptedClick < 0.4:
            self.log("Too fast!")
            return

        self.handleSingleClick() 
        self.lastAcceptedClick = datetime.datetime.now()

    def handleSingleClick(self):
        matches = [key for key in self.brighnessStrategies if self.brighnessStrategies[key]['fn'](self)]
        sortedMatches = sorted(matches, key=lambda x: self.brighnessStrategies[x]['order'])
        
        self.brighnessStrategyHandlers[sortedMatches[0]](self) if len(sortedMatches) > 0 else self.handleDefault()

    def handleDoubleClick(self):
        self.lights.on("group.tv_room_rgb_lights", color_name=self.colors[self.colorCounter])

        self.colorCounter = self.colorCounter + 1 if self.colorCounter < len(self.colors) - 1 else 0

    def onOffStrategy(self):
        if (datetime.datetime.now() - self.lastAcceptedClick).total_seconds() > (30 * 60):
            return True

        if float(self.get_state("sensor.illumination_158d00023db75a")) >= 15.0:
            return True

        currentTime = datetime.datetime.now()

        if currentTime.hour > 0 and currentTime.hour <= 5:
            return True

        return False

    def cozyStrategy(self):
        return self.sun_down()

    def handleDimmableStrategies(self, brightnesses):
        brightnesses = ["0", "50", "100"] if brightnesses is None else brightnesses

        if self.get_state("group.tv_room_rgb_lights") == "off":
            self.counter = 1
        else:
            self.counter = self.counter + 1 if self.counter < len(brightnesses) - 1 else 0

        if(self.counter == 0):
            self.lights.off("group.tv_room_rgb_lights")
        else:
            self.lights.on("group.tv_room_rgb_lights", brightness_pct=brightnesses[self.counter], kelvin=3000)

    def handleOnOff(self):
        if self.get_state("group.tv_room_rgb_lights") == "off":
            brightnesses = "100" if datetime.datetime.now().hour > 6 else "10"
            
            self.lights.on("group.tv_room_rgb_lights", brightness_pct=brightnesses, kelvin=3000)
        else:
            self.lights.off("group.tv_room_rgb_lights")

    def handleCozy(self):
        self.handleDimmableStrategies(["0", "10", "50", "100"])

    def handleDefault(self):
        self.handleDimmableStrategies(["0", "50", "100"])

    brighnessStrategies = {
        "on_off" : { "order": 1, "fn": onOffStrategy },
        "cozy": { "order": 2, "fn": cozyStrategy }
    }

    brighnessStrategyHandlers = {
        "cozy": handleCozy,
        "on_off" : handleOnOff
    }
