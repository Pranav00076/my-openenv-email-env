import random
random.seed(42)

from uuid import uuid4

from email_loader import get_emails
from openenv.core.env_server.interfaces import Environment
from openenv.core.env_server.types import State

try:
    from ..models import MyAction, MyObservation
except ImportError:
    from models import MyAction, MyObservation



class MyEnvironment(Environment):

    SUPPORTS_CONCURRENT_SESSIONS: bool = True

    def __init__(self):
        self._state = State(episode_id=str(uuid4()), step_count=0)
        self.task = "easy"  # default task
        self._state.email = ""
        # track consecutive correct answers
        self.streak = 0

    def reset(self) -> MyObservation:
        # pick a task first, then sample an email from that task
        self.task = random.choice(["easy", "medium", "hard"])

        emails = get_emails()
        email = random.choice(emails)

        self._state = State(
            episode_id=str(uuid4()),
            step_count=0,
        )
        self._state.email = email["text"]

        # reset streak on new episode
        self._state.streak = 0

        return MyObservation(
            email=email["text"],
            reward=0.0,
            done=False,
            info={"task": self.task}
        )

    def step(self, action: MyAction) -> MyObservation:
        self._state.step_count += 1

        emails = get_emails()
        email_data = next(
            (e for e in emails if e["text"] == self._state.email),
            {}
        )

        # find correct label
        correct_label = next(
            (e["label"] for e in emails
             if e["text"].lower().strip() == self._state.email.lower().strip()),
            "unknown"
        )
        # determine correctness and compute reward consistently
        # Base correctness
        is_correct = action.action_type == correct_label

        reward = 0.0

        # ✅ base reward
        reward += 1.0 if is_correct else -0.5

        # ✅ bonus: spam detection with link
        if correct_label == "spam" and email_data.get("has_link"):
            if action.action_type == "spam":
                reward += 0.5

        # ✅ bonus: urgent important emails
        if correct_label == "important" and email_data.get("urgency", 0) > 0.8:
            if action.action_type == "important":
                reward += 0.5

        # ❌ penalty: missing urgent email
        if correct_label == "important" and action.action_type != "important":
            if email_data.get("urgency", 0) > 0.8:
                reward -= 1.0

        # 🔥 streak bonus (VERY IMPORTANT)
        if is_correct:
            self._state.streak += 1
            reward += 0.1 * self._state.streak
        else:
            self._state.streak = 0
        # update streak
        if correct:
            self.streak += 1
        else:
            self.streak = 0

        reward += 0.1 * self.streak

        # next email
        next_email = random.choice(emails)["text"]
        self._state.email = next_email

        done = self._state.step_count >= 5

        # print("DEBUG TASK:", self.task)
        # print("DEBUG ACTION:", action.action_type)
        # print("DEBUG CORRECT:", correct_label)

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