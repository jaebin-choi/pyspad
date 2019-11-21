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
    PLOT_REFRESHING_INTERVAL = 100  # in milliseconds
    MAIN_UPDATING_INTERVAL = 100  # in milliseconds
