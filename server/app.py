import sys

from fastapi import FastAPI
from fastapi.responses import HTMLResponse

try:
    from openenv.core.env_server.http_server import create_app
except Exception as e:
    raise ImportError("openenv required") from e

try:
    from models import MyAction, MyObservation
    from .my_env_environment import MyEnvironment
except ModuleNotFoundError:
    from models import MyAction, MyObservation
    from server.my_env_environment import MyEnvironment


# ✅ OpenEnv backend
openenv_app = create_app(
    MyEnvironment,
    MyAction,
    MyObservation,
    env_name="my_env",
    max_concurrent_envs=1,
)

# ✅ Main app
app = FastAPI()

# mount backend under /api
app.mount("/api", openenv_app)


# =========================
# ✅ THIS IS THE IMPORTANT PART
# =========================
@app.get("/web", response_class=HTMLResponse)
def web_ui():
    return """
    <html>
    <head>
        <title>Email App</title>
        <style>
            body { font-family: Arial; background:#f5f7fa; padding:20px; }
            .container { max-width: 800px; margin:auto; }
            .card {
                background:white;
                padding:15px;
                border-radius:10px;
                box-shadow:0 2px 10px rgba(0,0,0,0.1);
                margin-top:15px;
            }
            button {
                padding:10px 15px;
                margin:5px;
                border:none;
                border-radius:6px;
                cursor:pointer;
                background:#007bff;
                color:white;
            }
            button:hover { background:#0056b3; }
            .spam { background:#dc3545; }
            .safe { background:#28a745; }
            pre { background:#111; color:#0f0; padding:10px; }
        </style>
    </head>

    <body>
        <div class="container">
            <h2>📧 My Email App</h2>

            <div class="card">
                <button onclick="resetEnv()">🔄 Reset</button>
                <button onclick="getState()">📥 Load Email</button>
            </div>

            <div class="card">
                <h3>Email:</h3>
                <p id="email">No email loaded</p>

                <button class="spam" onclick="takeAction('spam')">🚫 Mark as Spam</button>
                <button class="safe" onclick="takeAction('important')">✅ Keep</button>
            </div>

            <div class="card">
                <h3>Reward: <span id="reward_score">0.0</span></h3>
            </div>

            <div class="card">
                <h3>Status:</h3>
                <pre id="output">Waiting...</pre>
            </div>
        </div>

        <script>
            async function resetEnv() {
                const res = await fetch('/api/reset', { method: 'POST', credentials: 'same-origin' });
                const data = await res.json();

                if (data.observation && data.observation.email) {
                    document.getElementById('email').innerText = data.observation.email;
                    document.getElementById('reward_score').innerText = data.observation.reward !== undefined ? data.observation.reward : 0.0;
                }

                document.getElementById('output').innerText =
                    JSON.stringify(data, null, 2);
            }

            async function getState() {
                const res = await fetch('/api/state', { credentials: 'same-origin' });
                const data = await res.json();

                if (data.observation && data.observation.email) {
                    document.getElementById('email').innerText =
                        data.observation.email;
                    document.getElementById('reward_score').innerText = data.observation.reward !== undefined ? data.observation.reward : 0.0;
                } else {
                    document.getElementById('email').innerText =
                        "⚠️ No email in state (click Reset)";
                    document.getElementById('reward_score').innerText = "0.0";
                }
 
                document.getElementById('output').innerText =
                    JSON.stringify(data, null, 2);
            }

            async function takeAction(action) {
                const res = await fetch('/api/step', {
                    method: 'POST',
                    credentials: 'same-origin',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ action: { action_type: action } })
                });

                const data = await res.json();

                if (data.observation) {
                    if (data.observation.email) {
                        document.getElementById('email').innerText = data.observation.email;
                    }
                    if (data.observation.reward !== undefined) {
                        document.getElementById('reward_score').innerText = data.observation.reward;
                    }
                } else if (data.reward !== undefined) {
                    document.getElementById('reward_score').innerText = data.reward;
                }

                document.getElementById('output').innerText =
                    JSON.stringify(data, null, 2);
            }
        </script>
    </body>
    </html>
    """

# ─── task selection endpoint (for inference.py) ───
@app.post("/set_task/{task}")
def set_task(task: str):
    env_mod = sys.modules.get(MyEnvironment.__module__)
    if env_mod and task in ("easy", "medium", "hard"):
        env_mod._FORCED_TASK = task
        return {"task": task, "status": "ok"}
    return {"error": f"invalid task: {task}", "valid": ["easy", "medium", "hard"]}


# optional root redirect
@app.get("/")
def root():
    return {"message": "Go to /web"}