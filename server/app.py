# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.

from fastapi.responses import HTMLResponse

try:
    from openenv.core.env_server.http_server import create_app
except Exception as e:
    raise ImportError(
        "openenv is required for the web interface. Install dependencies."
    ) from e

try:
    from models import MyAction, MyObservation
    from .my_env_environment import MyEnvironment
except ModuleNotFoundError:
    from models import MyAction, MyObservation
    from server.my_env_environment import MyEnvironment


# ✅ Create OpenEnv FastAPI app
app = create_app(
    MyEnvironment,
    MyAction,
    MyObservation,
    env_name="my_env",
    max_concurrent_envs=1,
)

# =========================
# ✅ CUSTOM UI (MAIN PAGE)
# =========================
@app.get("/", response_class=HTMLResponse)
def root():
    return """
    <html>
    <head>
        <title>Email App</title>
        <style>
            body { font-family: Arial; background: #f5f5f5; padding: 20px; }
            .container { max-width: 800px; margin: auto; }
            button { padding: 10px 15px; margin: 5px; cursor: pointer; }
            .box { background: white; padding: 15px; border-radius: 8px; margin-top: 10px; }
            pre { background: #222; color: #0f0; padding: 10px; overflow-x: auto; }
        </style>
    </head>
    <body>
        <div class="container">
            <h2>📧 My Email Environment</h2>

            <button onclick="resetEnv()">Reset</button>
            <button onclick="getState()">Get State</button>
            <button onclick="goDocs()">API Docs</button>

            <div class="box">
                <h3>Output:</h3>
                <pre id="output">Click a button...</pre>
            </div>
        </div>

        <script>
            async function resetEnv() {
                const res = await fetch('/reset', { method: 'POST' });
                const data = await res.json();
                document.getElementById('output').innerText =
                    JSON.stringify(data, null, 2);
            }

            async function getState() {
                const res = await fetch('/state');
                const data = await res.json();
                document.getElementById('output').innerText =
                    JSON.stringify(data, null, 2);
            }

            function goDocs() {
                window.location.href = "/docs";
            }
        </script>
    </body>
    </html>
    """


# =========================
# ✅ OPTIONAL: /app route (same UI)
# =========================
@app.get("/app", response_class=HTMLResponse)
def app_ui():
    return root()


# =========================
# ✅ RUN SERVER (LOCAL)
# =========================
def main(host: str = "0.0.0.0", port: int = 8000):
    import uvicorn
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()
    main(port=args.port)