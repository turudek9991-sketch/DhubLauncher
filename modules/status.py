from enum import Enum


class PackageStatus(str, Enum):
    Offline = "Offline"
    Loading = "Loading"
    Launching = "Launching"
    Online = "Online"
    Restarting = "Restarting"
    Error = "Error"
