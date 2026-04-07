---
title: My Env Environment Server
emoji: 📼
colorFrom: red
colorTo: gray
sdk: docker
pinned: false
app_port: 7860
base_path: /web
tags:
  - openenv
---

# Email Classification Environment

An OpenEnv environment that simulates **email triage** — classifying incoming emails as `spam` or `important`. The agent must learn to identify phishing/junk emails vs. legitimate work emails using contextual signals like urgency, links, and content keywords.

## Environment Overview

| Property | Value |
|---|---|
| **Task** | Email classification (spam vs. important) |
| **Difficulty Levels** | Easy, Medium, Hard |
| **Reward Range** | 0.0 – 1.0 (grader score, clamped) |
| **Framework** | OpenEnv + FastAPI |

## Action Space

**`MyAction`** — a Pydantic model with one field:

| Field | Type | Description |
|---|---|---|
| `action_type` | `str` | Either `"spam"` or `"important"` |

## Observation Space

**`MyObservation`** — returned after every `step()` and `reset()`:

| Field | Type | Description |
|---|---|---|
| `email` | `str` | The email text to classify |
| `reward` | `float` | Reward received for the previous action |
| `done` | `bool` | Whether the episode is finished |
| `info` | `dict` | Metadata: `task`, `correct` label, `is_correct`, `streak` |

## Task Difficulties

The environment supports three difficulty levels, randomly selected on `reset()`:

### Easy (3 steps)
- **Emails**: Only high-signal emails (spam with links, important with urgency ≥ 0.8)
- **Rewards**: +1.0 correct, −0.25 incorrect
- **Bonuses**: Full bonuses for catching spam-with-links (+0.5) and urgent emails (+0.5)
- **Streak**: Enabled (+0.1 × consecutive correct)

### Medium (5 steps)
- **Emails**: All emails in the dataset
- **Rewards**: +1.0 correct, −0.5 incorrect
- **Bonuses**: Full bonuses
- **Streak**: Enabled

### Hard (7 steps)
- **Emails**: All emails (including ambiguous ones)
- **Rewards**: +0.5 correct, −1.0 incorrect
- **Bonuses**: Halved (×0.5)
- **Streak**: Disabled
- **Penalty**: −1.0 for missing urgent important emails

## Reward Function

The reward is **multi-signal** and provides partial progress feedback:

1. **Base reward**: Correct/incorrect classification (varies by difficulty)
2. **Spam-with-link bonus**: Extra reward for correctly flagging spam that contains links
3. **Urgent important bonus**: Extra reward for correctly keeping urgent important emails
4. **Missed-urgent penalty**: Penalty for misclassifying urgent important emails as spam
5. **Streak bonus** (easy/medium only): Incremental reward for consecutive correct classifications

The final **episode score** (from the grader) is:
```
score = clamp(0.7 × accuracy + 0.3 × avg_reward, 0.0, 1.0)
```

## Quick Start

### Running Locally

```bash
# Install dependencies
pip install -r requirements.txt

# Start the server
uvicorn server.app:app --reload
```

The web UI is available at `http://localhost:8000/web`.

### Using the Client

```python
from client import MyEnv
from models import MyAction

with MyEnv(base_url="http://localhost:8000").sync() as client:
    state = client.reset()

    for _ in range(5):
        # Classify the email
        action = MyAction(action_type="spam")  # or "important"
        result = client.step(action)

        print(f"Email: {result.observation.email}")
        print(f"Reward: {result.observation.reward}")

        if result.observation.done:
            break
```

### Running the Baseline Agent

The included baseline agent (`client.py`) uses keyword matching to classify emails:

```bash
# Start the server first, then:
python client.py
```

The baseline agent checks for spam keywords (`win`, `free`, `offer`, `lottery`, `click`) and important keywords (`meeting`, `project`, `invoice`, `deadline`) to make classification decisions.

## Building & Deploying

### Docker

```bash
# Build
docker build -t email-agent-env:latest .

# Run
docker run -p 7860:7860 email-agent-env:latest
```

### Hugging Face Spaces

```bash
# Deploy using openenv CLI
openenv push

# Or with options
openenv push --repo-id your-username/email-agent-env --private
```

After deployment, the Space will be available at `https://huggingface.co/spaces/<repo-id>` with:
- **Web Interface** at `/web`
- **API Docs** at `/docs`
- **WebSocket** at `/ws`

## Project Structure

```
my-openenv-email-env/
├── openenv.yaml           # OpenEnv manifest (tasks, entry point)
├── models.py              # Pydantic models: MyAction, MyObservation, State
├── emails.csv             # Email dataset (text, label, has_link, urgency)
├── email_loader.py        # CSV/Gmail email data loader
├── client.py              # Baseline agent + EnvClient
├── grader.py              # Episode grader (score clamped to 0.0–1.0)
├── Dockerfile             # Container for HF Spaces (port 7860)
├── requirements.txt       # Python dependencies
├── __init__.py            # Module exports
└── server/
    ├── app.py             # FastAPI app with /web UI and /api endpoints
    └── my_env_environment.py  # Core environment logic (step/reset/state)
```

## Dataset

The environment uses `emails.csv` with 10 pre-labeled emails:

| Text | Label | Has Link | Urgency |
|---|---|---|---|
| Win a free iPhone!!! | spam | ✅ | 0.9 |
| Meeting at 5 PM | important | ❌ | 0.8 |
| URGENT: Verify your bank account | spam | ✅ | 1.0 |
| Client feedback attached | important | ❌ | 0.6 |
| Limited time offer!!! | spam | ✅ | 0.7 |
| ... | ... | ... | ... |

An optional Gmail loader (`load_from_gmail()`) is available for real email data but defaults to CSV for consistent grading.
