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
    ADC_DATA_CHECK_INTERVAL = 1  # in seconds
    TRIGGER_OUT_CHECK_INTERVAL = 1  # in seconds
    PLOT_REFRESHING_INTERVAL = 10  # in seconds
    MAIN_UPDATING_INTERVAL = 10  # in seconds
