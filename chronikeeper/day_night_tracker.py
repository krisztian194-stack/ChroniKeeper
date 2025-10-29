from datetime import datetime

class DayNightTracker:
    def __init__(self):
        self.current_day = 1
        self.is_night = False

    def advance_time(self, hours=1):
        """
        Advances the story time; toggle day/night for simplicity.
        """
        if hours >= 12:
            self.current_day += 1
        self.is_night = not self.is_night

    def get_time_status(self):
        return {"day": self.current_day, "is_night": self.is_night}
