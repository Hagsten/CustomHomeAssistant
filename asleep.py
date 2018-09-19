import datetime


class Asleep():
    def is_asleep(self):
        return datetime.datetime.now().hour >= 0 and datetime.datetime.now().hour <= 6

