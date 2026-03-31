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
    <body style="font-family: Arial; padding:20px;">
        <h2>📧 My Email App</h2>

        <button onclick="resetEnv()">Reset</button>
        <button onclick="getState()">Get State</button>

        <pre id="output">Click buttons...</pre>

        <script>
            async function resetEnv() {
                const res = await fetch('/api/reset', { method: 'POST' });
                const data = await res.json();
                document.getElementById('output').innerText =
                    JSON.stringify(data, null, 2);
            }

            async function getState() {
                const res = await fetch('/api/state');
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