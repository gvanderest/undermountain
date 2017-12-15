from mud.manager import Manager

import gevent
import logging


class TimerManager(Manager):
    TIMER_DELAY = 1.0  # Seconds between ticks.

    def start(self):
        """Instantiate the timer loop."""
        gevent.spawn(self.start_timer_loop)

    def start_timer_loop(self):
        """Start a timer."""
        self.running = True
        while self.running:
            gevent.sleep(self.TIMER_DELAY)
            logging.debug("Ticking {}".format(self.__class__.__name__))
            self.tick()

    def tick(self):
        """Commands to run on the looped timer."""
        pass
