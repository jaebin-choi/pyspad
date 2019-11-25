import threading

instanceLock = threading.RLock()

_instance = None


def Instance():
    instanceLock.acquire()
    global _instance
    if _instance is None:
        _instance = Constants()
    instanceLock.release()
    return _instance


class Constants(object):
    PLOT_REFRESHING_INTERVAL = 0.2  # in seconds
    MAIN_UPDATING_INTERVAL = 200  # in milliseconds
