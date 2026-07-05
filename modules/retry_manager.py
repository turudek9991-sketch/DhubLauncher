import time


class RetryManager:
    def __init__(self, max_retries: int = 5, cooldown: int = 30):
        self.max_retries = max_retries
        self.cooldown = cooldown
        self.failed_attempts = 0

    def reset(self):
        self.failed_attempts = 0

    def record_failure(self):
        self.failed_attempts += 1

    def wait_if_needed(self, running_event=None):
        if self.failed_attempts < self.max_retries:
            return

        waited = 0
        while waited < self.cooldown:
            if running_event is not None and not running_event.is_set():
                return
            time.sleep(1)
            waited += 1

        self.reset()
