import os
import random
random.seed(42)

from uuid import uuid4

from email_loader import get_emails
from openenv.core.env_server.interfaces import Environment

try:
    from ..models import MyAction, MyObservation, State
except ImportError:
    from models import MyAction, MyObservation, State


# ─── Task override (set via /set_task endpoint or OPENENV_TASK env var) ───
_FORCED_TASK = os.getenv("OPENENV_TASK", None)

# ─── Task difficulty configurations ───
TASK_CONFIG = {
    "easy": {
        "max_steps": 3,
        "base_correct": 1.0,
        "base_incorrect": -0.25,
        "bonus_multiplier": 1.0,
        "streak_enabled": True,
        "filter_obvious": True,       # only high-signal emails
    },
    "medium": {
        "max_steps": 5,
        "base_correct": 1.0,
        "base_incorrect": -0.5,
        "bonus_multiplier": 1.0,
        "streak_enabled": True,
        "filter_obvious": False,      # all emails
    },
    "hard": {
        "max_steps": 7,
        "base_correct": 0.5,
        "base_incorrect": -1.0,
        "bonus_multiplier": 0.5,      # halved bonuses
        "streak_enabled": False,      # no streak bonus
        "filter_obvious": False,      # all emails
    },
}


class MyEnvironment(Environment):

    SUPPORTS_CONCURRENT_SESSIONS: bool = False

    def __init__(self):
        self._state = State(
            episode_id=str(uuid4()),
            email="",
            step_count=0,
            streak=0
        )
        self.task = "easy"  # default task

    # ─── helpers ───

    def _get_config(self) -> dict:
        return TASK_CONFIG.get(self.task, TASK_CONFIG["medium"])

    def _get_task_emails(self) -> list:
        """Return emails filtered by task difficulty."""
        emails = get_emails()
        cfg = self._get_config()

        if cfg["filter_obvious"]:
            # Easy: only emails with strong classification signals
            obvious = [
                e for e in emails
                if (e["label"] == "spam" and e.get("has_link"))
                or (e["label"] == "important" and e.get("urgency", 0) >= 0.8)
            ]
            return obvious if obvious else emails  # fallback safety

        return emails

    # ─── OpenEnv interface ───

    def reset(self) -> MyObservation:
        global _FORCED_TASK
        if _FORCED_TASK and _FORCED_TASK in TASK_CONFIG:
            self.task = _FORCED_TASK
        else:
            self.task = random.choice(["easy", "medium", "hard"])

        emails = self._get_task_emails()
        email = random.choice(emails)

        self._state = State(
            episode_id=str(uuid4()),
            email=email["text"],
            step_count=0,
            streak=0
        )

        return MyObservation(
            email=email["text"],
            reward=0.0,
            done=False,
            info={"task": self.task}
        )

    def step(self, action: MyAction) -> MyObservation:
        self._state.step_count += 1
        cfg = self._get_config()

        emails = get_emails()

        correct_label = next(
            (e["label"] for e in emails
             if e["text"].lower().strip() == self._state.email.lower().strip()),
            "unknown"
        )

        email_data = next(
            (e for e in emails if e["text"] == self._state.email),
            {}
        )

        # ── correctness ──
        is_correct = action.action_type == correct_label

        # ── base reward (varies by task) ──
        reward = cfg["base_correct"] if is_correct else cfg["base_incorrect"]

        # ── bonus: spam with link (scaled by task) ──
        if correct_label == "spam" and email_data.get("has_link"):
            if action.action_type == "spam":
                reward += 0.5 * cfg["bonus_multiplier"]

        # ── bonus: urgent important (scaled by task) ──
        if correct_label == "important" and email_data.get("urgency", 0) > 0.8:
            if action.action_type == "important":
                reward += 0.5 * cfg["bonus_multiplier"]

        # ── penalty: missed urgent ──
        if correct_label == "important" and action.action_type != "important":
            if email_data.get("urgency", 0) > 0.8:
                reward -= 1.0

        # ── streak system (disabled in hard mode) ──
        if is_correct:
            self._state.streak += 1
            if cfg["streak_enabled"]:
                reward += 0.1 * self._state.streak
        else:
            self._state.streak = 0

        # DEBUG
        print(f"[{self.task}] Action: {action.action_type}, Correct: {correct_label}, Reward: {reward}")

        # ── next email ──
        task_emails = self._get_task_emails()
        next_email = random.choice(task_emails)["text"]
        self._state.email = next_email

        done = self._state.step_count >= cfg["max_steps"]

        return MyObservation(
            email=next_email,
            reward=reward,
            done=done,
            info={
                "correct": correct_label,
                "task": self.task,
                "is_correct": is_correct,
                "streak": self._state.streak
            }
        )

    @property
    def state(self) -> State:
        return self._state