from enum import Enum


class Status(Enum):
    RUNNING = 1
    PARTIALLY_SYNCED = 2
    ERROR = 3
    UNDEFINED = 4


class JobDetails:
    def __init__(self, list_id, last_sync_date_time):
        self.list_id = list_id
        self.last_sync_date_time = last_sync_date_time

    def to_dict(self):
        return {
            "listId": self.list_id,
            "last_sync_date_time": self.last_sync_date_time
        }


class SyncJob:
    def __init__(self, job_details: JobDetails, status: Status):
        self.job_details = job_details
        self.status = status

    def to_dict(self):
        return {
            "job_details": self.job_details.to_dict(),
            "status": self.status,
        }
