"""
Desktop launcher for the Medical Laboratory Management System.

This is the module PyInstaller builds into MedicalLaboratory.exe.
It is what makes the app feel like a normal Windows desktop program
instead of "a Flask website opened in a browser":

  - Starts the Flask backend on a free local port, in a background thread
  - Waits until the server actually responds before opening the window
  - Opens a native PyWebView window (no Chrome/Edge/Firefox, no address
    bar, no visible localhost) titled "Medical Laboratory Management
    System"
  - Prevents a second instance from starting (single-instance lock);
    if the user double-clicks the icon again, it just focuses the
    existing window
  - Shuts the Flask server down cleanly when the window is closed and
    exits the process completely (no orphaned background process)
  - Never shows a console/terminal window (see the PyInstaller .spec,
    which builds this with --noconsole / --windowed)
"""

import os
import sys
import socket
import threading
import time
import logging

# Make sure "app" package is importable both in dev mode and when frozen.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app  # noqa: E402
from app.config import Config  # noqa: E402


APP_TITLE = Config.APP_NAME
WINDOW_WIDTH = 1280
WINDOW_HEIGHT = 800
MIN_WIDTH = 1024
MIN_HEIGHT = 700

logger = logging.getLogger("desktop_launcher")


# --------------------------------------------------------------------------
# Single-instance lock (Part 84)
# --------------------------------------------------------------------------
def acquire_single_instance_lock():
    """
    Returns True if this is the only running instance (lock acquired).
    Returns False if another instance is already running.

    Implementation: bind a TCP socket on a fixed local port used purely
    as a mutex. This works cross-platform without extra dependencies.
    The socket is kept open for the process lifetime (its garbage
    collection / process exit releases the port automatically).
    """
    global _lock_socket
    LOCK_PORT = 47821  # arbitrary fixed port, just for instance locking

    _lock_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    _lock_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 0)
    try:
        _lock_socket.bind(("127.0.0.1", LOCK_PORT))
        _lock_socket.listen(1)
        return True
    except OSError:
        return False


_lock_socket = None


def notify_existing_instance():
    """
    Best-effort: tell the already-running instance to come to the front.
    Falls back to just informing the user if that fails.
    """
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(1)
        s.connect(("127.0.0.1", 47821))
        s.sendall(b"FOCUS")
        s.close()
    except OSError:
        pass


# --------------------------------------------------------------------------
# Free port discovery
# --------------------------------------------------------------------------
def find_free_port(start, end):
    for port in range(start, end):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("127.0.0.1", port))
                return port
            except OSError:
                continue
    raise RuntimeError("No free port available for the local server.")


# --------------------------------------------------------------------------
# Flask server thread
# --------------------------------------------------------------------------
class FlaskServerThread(threading.Thread):
    def __init__(self, app, host, port):
        super().__init__(daemon=True)
        self.app = app
        self.host = host
        self.port = port
        self._server = None

    def run(self):
        from werkzeug.serving import make_server
        self._server = make_server(self.host, self.port, self.app, threaded=True)
        self._server.serve_forever()

    def shutdown(self):
        if self._server:
            self._server.shutdown()


def wait_until_ready(host, port, timeout=15):
    """Poll the health endpoint until Flask responds, or timeout."""
    import urllib.request
    import urllib.error

    url = f"http://{host}:{port}/api/health"
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=1) as resp:
                if resp.status == 200:
                    return True
        except (urllib.error.URLError, ConnectionError, OSError):
            pass
        time.sleep(0.15)
    return False


# --------------------------------------------------------------------------
# Main entry point
# --------------------------------------------------------------------------
def main():
    # 1. Single instance check (Part 84)
    if not acquire_single_instance_lock():
        notify_existing_instance()
        try:
            import webview
            webview.create_window(
                APP_TITLE, html="<h3 style='font-family:sans-serif;padding:40px;'>"
                                 "Medical Laboratory Management System is already running.<br>"
                                 "Please check your taskbar.</h3>",
                width=480, height=200,
            )
            webview.start()
        except Exception:
            pass
        sys.exit(0)

    # 2. Start Flask backend on an internal free port (Part 82, step 1-2)
    host = Config.SERVER_HOST
    port = find_free_port(*Config.SERVER_PORT_RANGE)

    flask_app = create_app()
    server_thread = FlaskServerThread(flask_app, host, port)
    server_thread.start()

    if not wait_until_ready(host, port, timeout=20):
        logger.error("Flask backend did not become ready in time.")
        sys.exit(1)

    # 3. Open the PyWebView desktop window (Part 78, 80, 81, 82 step 3-5)
    import webview

    window = webview.create_window(
        APP_TITLE,
        url=f"http://{host}:{port}/",
        width=WINDOW_WIDTH,
        height=WINDOW_HEIGHT,
        min_size=(MIN_WIDTH, MIN_HEIGHT),
        resizable=True,
        text_select=True,
        confirm_close=False,
    )

    def on_closed():
        # 4. Clean shutdown (Part 83): stop Flask, release the port, exit.
        try:
            server_thread.shutdown()
        except Exception:
            pass
        # Give the server a brief moment to release the socket, then force-exit
        # so no hidden process is left running.
        os._exit(0)

    window.events.closed += on_closed

    # gui='edgechromium' explicitly selects the WebView2 (Chromium) engine
    # on Windows — this is what avoids the old, limited MSHTML/IE engine
    # and requires the WebView2 Runtime (see Part 89 / installer notes).
    if sys.platform == "win32":
        webview.start(gui="edgechromium")
    else:
        # Dev/testing on Linux/macOS: let pywebview pick an available engine.
        webview.start()


if __name__ == "__main__":
    main()
