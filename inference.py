#!/usr/bin/env python3
"""
Inference Script — Email Classification Environment
====================================================
MANDATORY
- Environment variables:
    API_BASE_URL   The API endpoint for the LLM.
    MODEL_NAME     The model identifier to use for inference.
    HF_TOKEN       Your Hugging Face / API key.
    LOCAL_IMAGE_NAME  (optional) Docker image name for local env.

- The inference script must be named `inference.py` and placed in the root directory.
- Uses OpenAI Client for all LLM calls.
- Emits structured stdout logs: [START], [STEP], [END].

STDOUT FORMAT
    [START] task=<task_name> env=<benchmark> model=<model_name>
    [STEP]  step=<n> action=<action_str> reward=<0.00> done=<true|false> error=<msg|null>
    [END]   success=<true|false> steps=<n> score=<score> rewards=<r1,r2,...,rn>
"""

import os
import sys
import textwrap
from typing import List, Optional

import requests
from openai import OpenAI

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from models import MyAction, MyObservation
from grader import grade_episode

# ─── Configuration ───────────────────────────────────────────────────────────
API_BASE_URL = os.getenv("API_BASE_URL", "https://router.huggingface.co/v1")
MODEL_NAME = os.getenv("MODEL_NAME", "Qwen/Qwen2.5-72B-Instruct")
HF_TOKEN = os.getenv("HF_TOKEN") or os.getenv("API_KEY")
LOCAL_IMAGE_NAME = os.getenv("LOCAL_IMAGE_NAME")

# Environment server URL (HF Space or local Docker container)
ENV_BASE_URL = os.getenv(
    "ENV_BASE_URL",
    "https://pritoo-my-openenv-email-env.hf.space"
)

BENCHMARK = "email-agent-env"
TASKS = ["easy", "medium", "hard"]
MAX_STEPS_PER_TASK = {"easy": 3, "medium": 5, "hard": 7}
TEMPERATURE = 0.0
MAX_TOKENS = 10
SUCCESS_SCORE_THRESHOLD = 0.1

SYSTEM_PROMPT = textwrap.dedent("""
    You are an email classifier. Given an email, classify it as either "spam" or "important".

    Spam indicators: lottery/prize offers, phishing attempts, fake account warnings,
    too-good-to-be-true deals, suspicious links, "click here" language.

    Important indicators: meeting invitations, project updates, invoices,
    deadlines, client feedback, professional communications.

    Respond with EXACTLY one word: spam or important
    No quotes, no punctuation, no explanation — just the classification word.
""").strip()


# ─── Structured Logging ─────────────────────────────────────────────────────
def log_start(task: str, env: str, model: str) -> None:
    print(f"[START] task={task} env={env} model={model}", flush=True)


def log_step(
    step: int, action: str, reward: float, done: bool, error: Optional[str]
) -> None:
    error_val = error if error else "null"
    done_val = str(done).lower()
    print(
        f"[STEP] step={step} action={action} reward={reward:.2f} "
        f"done={done_val} error={error_val}",
        flush=True,
    )


def log_end(
    success: bool, steps: int, score: float, rewards: List[float]
) -> None:
    rewards_str = ",".join(f"{r:.2f}" for r in rewards)
    print(
        f"[END] success={str(success).lower()} steps={steps} "
        f"score={score:.2f} rewards={rewards_str}",
        flush=True,
    )


# ─── LLM-powered Classification ─────────────────────────────────────────────
def classify_email(client: OpenAI, email_text: str) -> str:
    """Use the LLM to classify an email as spam or important."""
    try:
        completion = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"Classify this email:\n\n{email_text}"},
            ],
            temperature=TEMPERATURE,
            max_tokens=MAX_TOKENS,
            stream=False,
        )
        text = (completion.choices[0].message.content or "").strip().lower()

        # Parse response — look for the classification word
        if "spam" in text:
            return "spam"
        elif "important" in text:
            return "important"
        else:
            # Default to spam for unrecognized responses
            return "spam"
    except Exception as exc:
        print(f"[DEBUG] LLM request failed: {exc}", flush=True)
        return "spam"


# ─── Environment Interaction (HTTP) ──────────────────────────────────────────
def set_task(base_url: str, task: str) -> None:
    """Tell the server which task to use on the next reset()."""
    try:
        resp = requests.post(f"{base_url}/set_task/{task}", timeout=10)
        resp.raise_for_status()
    except Exception as exc:
        print(f"[DEBUG] set_task({task}) failed: {exc}", flush=True)


def env_reset(base_url: str) -> dict:
    """POST /api/reset and return the response JSON."""
    resp = requests.post(f"{base_url}/api/reset", timeout=30)
    resp.raise_for_status()
    return resp.json()


def env_step(base_url: str, action_type: str) -> dict:
    """POST /api/step with the action and return the response JSON."""
    resp = requests.post(
        f"{base_url}/api/step",
        json={"action": {"action_type": action_type}},
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()


# ─── Run One Task Episode ────────────────────────────────────────────────────
def run_task(
    llm_client: OpenAI, base_url: str, task: str
) -> float:
    """Run a single task episode and return the grader score."""
    max_steps = MAX_STEPS_PER_TASK.get(task, 5)

    # Select the task on the server, then reset
    set_task(base_url, task)
    reset_data = env_reset(base_url)

    obs_data = reset_data.get("observation", {})
    email = obs_data.get("email", "")

    log_start(task=task, env=BENCHMARK, model=MODEL_NAME)

    rewards: List[float] = []
    history = []
    steps_taken = 0
    done = False

    for step_num in range(1, max_steps + 1):
        if done:
            break

        # LLM classifies the email
        action_type = classify_email(llm_client, email)
        action = MyAction(action_type=action_type)

        # Step the environment
        step_data = env_step(base_url, action_type)
        obs = step_data.get("observation", {})

        reward = obs.get("reward", 0.0)
        done = obs.get("done", False)
        info = obs.get("info", {})
        email = obs.get("email", "")
        error = info.get("error", None)

        observation = MyObservation(
            email=email,
            reward=reward,
            done=done,
            info=info,
        )

        rewards.append(reward)
        history.append((action, observation))
        steps_taken = step_num

        log_step(
            step=step_num,
            action=action_type,
            reward=reward,
            done=done,
            error=error,
        )

        if done:
            break

    # Grade the episode
    grade_result = grade_episode(history)
    score = grade_result["score"]
    success = score >= SUCCESS_SCORE_THRESHOLD

    log_end(success=success, steps=steps_taken, score=score, rewards=rewards)

    return score


# ─── Main ────────────────────────────────────────────────────────────────────
def main() -> None:
    # Validate API key
    if not HF_TOKEN:
        print(
            "[ERROR] HF_TOKEN (or API_KEY) environment variable is required.",
            flush=True,
        )
        sys.exit(1)

    llm_client = OpenAI(base_url=API_BASE_URL, api_key=HF_TOKEN)
    base_url = ENV_BASE_URL.rstrip("/")

    print(f"[INFO] LLM endpoint: {API_BASE_URL}", flush=True)
    print(f"[INFO] Model: {MODEL_NAME}", flush=True)
    print(f"[INFO] Environment: {base_url}", flush=True)
    print(flush=True)

    all_scores = {}

    for task in TASKS:
        try:
            score = run_task(llm_client, base_url, task)
            all_scores[task] = score
        except Exception as exc:
            print(f"[ERROR] Task '{task}' failed: {exc}", flush=True)
            all_scores[task] = 0.0
        print(flush=True)

    # ─── Summary ───
    print("=== BASELINE SCORES ===", flush=True)
    for task_name, score in all_scores.items():
        status = "✅" if score >= SUCCESS_SCORE_THRESHOLD else "❌"
        print(f"  {status} {task_name}: {score:.2f}", flush=True)

    avg_score = sum(all_scores.values()) / len(all_scores) if all_scores else 0.0
    print(f"  average: {avg_score:.2f}", flush=True)

    # Exit with non-zero if all tasks failed
    if all(s == 0.0 for s in all_scores.values()):
        sys.exit(1)


if __name__ == "__main__":
    main()
