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

                <button class="spam" onclick="takeAction('mark_spam')">🚫 Mark as Spam</button>
                <button class="safe" onclick="takeAction('keep')">✅ Keep</button>
            </div>

            <div class="card">
                <h3>Status:</h3>
                <pre id="output">Waiting...</pre>
            </div>
        </div>

        <script>
            async function resetEnv() {
                await fetch('/api/reset', { method: 'POST' });
                getState();
            }

            async function getState() {
                const res = await fetch('/api/state');
                const data = await res.json();

                document.getElementById('email').innerText =
                    data.observation.email;

                document.getElementById('output').innerText =
                    JSON.stringify(data, null, 2);
            }

            async function takeAction(action) {
                const res = await fetch('/api/step', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ action: action })
                });

                const data = await res.json();

                document.getElementById('output').innerText =
                    JSON.stringify(data, null, 2);
            }
        </script>
    </body>
    </html>
    """

# optional root redirect
@app.get("/")
def root():
    return {"message": "Go to /web"}