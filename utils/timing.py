from datetime import datetime
timings = {}


def start(name):
    """
    Start a timer, by its name.
    @param {string} name to identify timer
    @returns {datetime} timestamp of timer creation
    """
    now = datetime.now()
    timings[name] = now
    return now


def tick(name):
    """
    Tick a timer, returning the time elapsed from its start.
    @param {string} name to identify timer
    @returns {timedelta} time elapsed since start of timer
    """
    return datetime.now() - timings[name]


def stop(name):
    """
    Tick a timer, returning the time elapsed from its start and delete it.
    @param {string} name to identify timer
    @returns {timedelta} time elapsed since start of timer
    """
    result = datetime.now() - timings[name]
    del timings[name]
    return result
