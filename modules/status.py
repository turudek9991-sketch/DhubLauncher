from enum import Enum

class WorkerStatus(Enum):
    ONLINE = "Online"
    OFFLINE = "Offline"
    LAUNCHING = "Launching"
    LOADING = "Loading"
    RESTARTING = "Restarting"
    ERROR = "Error"
