import time

class RetryManager:
    def __init__(self, max_retries=5, cooldown_seconds=30):
        self.max_retries = max_retries
        self.cooldown_seconds = cooldown_seconds
        self.current_retry = 0

    def increment(self):
        self.current_retry += 1
        return self.current_retry

    def reset(self):
        self.current_retry = 0

    def is_limit_reached(self):
        return self.current_retry >= self.max_retries

    def get_cooldown_time(self):
        return self.cooldown_seconds
