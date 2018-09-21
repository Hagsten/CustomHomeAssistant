import appdaemon.plugins.hass.hassapi as hass

class asleep_2(hass.Hass):
    def initialize(self):
        pass

    def is_asleep(self):
        motionSensors = [self.get_state(x, attribute="all") for x in self.get_state("group.motion_sensors", attribute="entity_id")]
        
        if not all(sensor['state'] == 'off' for sensor in motionSensors):
            return False

        sortedSensors = sorted(motionSensors, key=lambda x: x['last_changed'], reverse=True)

        if sortedSensors[0]['entity_id'] == "binary_sensor.motion_sensor_upper_floor" and int(sortedSensors[0]['attributes']['No motion since']) >= 300:
            return True

        return False

