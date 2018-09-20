import appdaemon.plugins.hass.hassapi as hass
import datetime
from threading import Timer

class TvRoomMotion(hass.Hass):
  thresholdReachedAt = None
  noMotionTimer = None

  def initialize(self):
    self.interpretIllumination(self.get_state("sensor.illumination_158d00023db75a"))

    self.listen_state(self.motion, "binary_sensor.motion_sensor_158d00023db75a", new = "on")
    self.listen_state(self.no_motion, "binary_sensor.motion_sensor_158d00023db75a", new = "off")
    self.listen_state(self.illuminationListener, "sensor.illumination_158d00023db75a")
    self.log("TvMotion app is running...")

  def illuminationListener(self, entity, attribute, old, new, kwargs):
        self.interpretIllumination(new)

  def motion(self, entity, attribute, old, new, kwargs):
      if self.noMotionTimer is not None:
          self.noMotionTimer.cancel()

      if self.thresholdReachedAt is None:
        return
      
      if self.get_state("group.tv_room_rgb_lights") == "on":
        self.log("Ligths already on, doing nothing...")
        return
      
      if self.get_state("media_player.vardagsrum") == "playing":
          self.log("Chromecast is playing, doing nothing...")
          return

      shouldTrigger = (datetime.datetime.now() - self.thresholdReachedAt).total_seconds() / 60.0 >= 5

      if shouldTrigger:
        self.log("Run script to turn on lights")
        self.turn_on("script.1536574687151")

  def interpretIllumination(self, illumination):
        self.log("Illumination: ")
        self.log(illumination)
        
        if float(illumination) >= 9.0:
              self.log("Value above theshold, reset timer")
              self.thresholdReachedAt = None
        elif self.thresholdReachedAt is None:
              self.log("Value below theshold, set timer to now")
              self.thresholdReachedAt = datetime.datetime.now()

  def no_motion(self, entity, attribute, old, new, kwargs):
    if self.noMotionTimer is not None:
          self.noMotionTimer.cancel()

    timerDuration = 300.0 if datetime.datetime.now().hour >= 0 and datetime.datetime.now().hour <= 5 else 1800.0

    self.log("Motion cleared, setting timer to ")
    self.log(timerDuration)

    self.noMotionTimer = Timer(timerDuration, self.no_motion_cb)
    self.noMotionTimer.start()

  def no_motion_cb(self):
    self.log("Timer complete, trying to turn off lights...")

    if self.get_state("media_player.vardagsrum") == "off":
      return

    self.turn_off("group.tv_room_rgb_lights")

