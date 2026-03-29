# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

"""My Env Environment Client."""

from typing import Dict

from openenv.core import EnvClient
from openenv.core.client_types import StepResult
from openenv.core.env_server.types import State

from models import MyAction, MyObservation

import random

from grader import grade_episode

from transformers import pipeline
classifier = pipeline("text-classification", model="distilbert-base-uncased")

class MyEnv(
    EnvClient[MyAction, MyObservation, State]
):
    """
    Client for the My Env Environment.

    This client maintains a persistent WebSocket connection to the environment server,
    enabling efficient multi-step interactions with lower latency.
    Each client instance has its own dedicated environment session on the server.

    Example:
        >>> # Connect to a running server
        >>> with MyEnv(base_url="http://localhost:8000") as client:
        ...     result = client.reset()
        ...     print(result.observation.echoed_message)
        ...
        ...     result = client.step(MyAction(message="Hello!"))
        ...     print(result.observation.echoed_message)

    Example with Docker:
        >>> # Automatically start container and connect
        >>> client = MyEnv.from_docker_image("my_env-env:latest")
        >>> try:
        ...     result = client.reset()
        ...     result = client.step(MyAction(message="Test"))
        ... finally:
        ...     client.close()
    """

    def _step_payload(self, action: MyAction) -> Dict:
        """
        Convert MyAction to JSON payload for step message.

        Args:
            action: MyAction instance

        Returns:
            Dictionary representation suitable for JSON encoding
        """
        return {
            "action_type": action.action_type
        }

    def _parse_result(self, payload: Dict) -> StepResult[MyObservation]:
        obs_data = payload.get("observation", {})

        # obs_data may already be a dict (from server.obs.dict()) or a MyObservation-like object
        if hasattr(obs_data, "get"):
            email = obs_data.get("email", "")
            reward = obs_data.get("reward", payload.get("reward", 0.0))
            done = obs_data.get("done", False)
            info = obs_data.get("info", {})
        else:
            # fallback: object-like
            email = getattr(obs_data, "email", "")
            reward = getattr(obs_data, "reward", payload.get("reward", 0.0))
            done = getattr(obs_data, "done", False)
            info = getattr(obs_data, "info", {})

        observation = MyObservation(
            email=email,
            reward=reward,
            done=done,
            info=info
        )

        return StepResult(
            observation=observation,
            reward=observation.reward,   # 🔥 FIX
            done=observation.done,
        )

    def _parse_state(self, payload: Dict) -> State:
        """
        Parse server response into State object.

        Args:
            payload: JSON response from state request

        Returns:
            State object with episode_id and step_count
        """
        return State(
            episode_id=payload.get("episode_id"),
            step_count=payload.get("step_count", 0),
        )

    def act(self, state: State) -> MyAction:
        email = state.observation.email.lower()

        spam_keywords = ["win", "free", "offer", "lottery", "click"]
        important_keywords = ["meeting", "project", "invoice", "deadline"]

        spam_score = sum(word in email for word in spam_keywords)
        important_score = sum(word in email for word in important_keywords)

        if spam_score > important_score:
            return MyAction(action_type="spam")

        if important_score > 0:
            return MyAction(action_type="important")

        return MyAction(action_type="flag")
        
if __name__ == "__main__":
    with MyEnv(base_url="http://localhost:8000").sync() as client:
        state = client.reset()
        print("Initial:", state)

        total_reward = 0
        history = []

        for _ in range(5):
            action = client.act(state)

            result = client.step(action)
            obs = result.observation
            history.append((action, obs))

            print("Action:", action)
            print("Observation:", obs)

            total_reward += obs.reward

            if obs.done:
                break

            state = result

        print("Total Reward:", total_reward)

        result = grade_episode(history)

        print("\n=== FINAL SCORE ===")
        print(result)