from enum import Enum

class WorkerStatus(Enum):
    LOADING = "Loading"
    LAUNCHING = "Launching"
    ONLINE = "Online"
    RESTARTING = "Restarting"
    OFFLINE = "Offline"
    ERROR = "Error"
