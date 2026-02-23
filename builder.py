"""
Layout Builder launcher.

Starts both the builder API server (Python) and the React dev UI (npm) with a
single command, then opens the browser automatically.

Usage:
    python builder.py [--api-port 8081] [--ui-port 3000]

Press Ctrl+C to stop both processes.
"""
import argparse
import os
import signal
import subprocess
import sys
import time
import webbrowser
from pathlib import Path

ROOT = Path(__file__).parent
BUILDER_DIR = ROOT / 'builder'

API_STARTUP_WAIT = 2   # seconds to wait for the API server before opening browser
UI_STARTUP_WAIT = 4    # seconds to wait for React dev server before opening browser


def main() -> None:
    parser = argparse.ArgumentParser(description='LED Panel Layout Builder')
    parser.add_argument('--api-port', type=int, default=8081, help='Builder API port (default: 8081)')
    parser.add_argument('--ui-port', type=int, default=3000, help='React UI port (default: 3000)')
    parser.add_argument('--no-browser', action='store_true', help='Do not open browser automatically')
    args = parser.parse_args()

    processes = []

    def _stop_all(signum=None, frame=None) -> None:
        print('\nStopping builder...', flush=True)
        for p in processes:
            if p.poll() is None:
                p.terminate()
        for p in processes:
            try:
                p.wait(timeout=5)
            except subprocess.TimeoutExpired:
                p.kill()
        sys.exit(0)

    signal.signal(signal.SIGINT, _stop_all)
    signal.signal(signal.SIGTERM, _stop_all)

    # --- 1. Start the Python API server ---
    print(f'Starting builder API server on port {args.api_port}...', flush=True)
    api_proc = subprocess.Popen(
        [sys.executable, 'builder_server.py', '--port', str(args.api_port)],
        cwd=ROOT,
    )
    processes.append(api_proc)

    # --- 2. Check npm is available ---
    npm_cmd = 'npm.cmd' if sys.platform == 'win32' else 'npm'
    try:
        subprocess.run([npm_cmd, '--version'], capture_output=True, check=True)
    except (FileNotFoundError, subprocess.CalledProcessError):
        print('ERROR: npm not found. Install Node.js to run the builder UI.', file=sys.stderr)
        _stop_all()

    # --- 3. Install node_modules if missing ---
    if not (BUILDER_DIR / 'node_modules').exists():
        print('Installing builder dependencies (first run)...', flush=True)
        result = subprocess.run([npm_cmd, 'install'], cwd=BUILDER_DIR)
        if result.returncode != 0:
            print('ERROR: npm install failed.', file=sys.stderr)
            _stop_all()

    # --- 4. Start the React dev server ---
    print(f'Starting builder UI on port {args.ui_port}...', flush=True)
    ui_env = {**os.environ, 'PORT': str(args.ui_port), 'BROWSER': 'none'}
    ui_proc = subprocess.Popen(
        [npm_cmd, 'start'],
        cwd=BUILDER_DIR,
        env=ui_env,
    )
    processes.append(ui_proc)

    # --- 5. Open browser after a short delay ---
    if not args.no_browser:
        time.sleep(UI_STARTUP_WAIT)
        url = f'http://localhost:{args.ui_port}'
        print(f'Opening {url}', flush=True)
        webbrowser.open(url)

    print('Builder running. Press Ctrl+C to stop.', flush=True)

    # --- 6. Wait; exit if either process dies unexpectedly ---
    while True:
        time.sleep(2)
        for p in processes:
            if p.poll() is not None:
                print(f'A builder process exited unexpectedly (code {p.returncode}). Stopping.', flush=True)
                _stop_all()


if __name__ == '__main__':
    main()
