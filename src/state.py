from threading import Lock
from collections import deque


class ASRAState:
    def __init__(self):
        self.mem_pct = 0.0
        self.stability = 0.0
        self.suspended_count = 0
        self.ai_calls = 0
        self.actions_taken = 0

        self.last_decision = "Initializing..."
        self.last_action_type = "NONE"

        self.mem_history = []

        # ✅ Action history (last 10 events)
        self.action_history = deque(maxlen=10)

        # ✅ Resume trigger flag
        self.resume_requested = False

        self._lock = Lock()

    def update(self, **kwargs):
        with self._lock:
            for key, value in kwargs.items():
                if hasattr(self, key):
                    setattr(self, key, value)

    def add_history(self, entry):
        with self._lock:
            self.action_history.appendleft(entry)

    def request_resume_all(self):
        with self._lock:
            self.resume_requested = True

    def consume_resume_flag(self):
        with self._lock:
            flag = self.resume_requested
            self.resume_requested = False
            return flag

    def snapshot(self):
        with self._lock:
            return {
                "mem_pct": self.mem_pct,
                "stability": self.stability,
                "suspended_count": self.suspended_count,
                "ai_calls": self.ai_calls,
                "actions_taken": self.actions_taken,
                "last_decision": self.last_decision,
                "last_action_type": self.last_action_type,
                "mem_history": list(self.mem_history),
                "action_history": list(self.action_history),
            }


shared_state = ASRAState()