import os
import pydevd_pycharm

host = os.environ.get("PYCHARM_DEBUG_HOST", "host.docker.internal")
port = int(os.environ.get("PYCHARM_DEBUG_PORT", "8888"))
suspend = os.environ.get("PYCHARM_DEBUG_WAIT", "0") == "1"

try:
    pydevd_pycharm.settrace(
        host,
        port=port,
        suspend=suspend,
        patch_multiprocessing=True,
    )
    print(f"Connected to PyCharm debugger at {host}:{port}")
except Exception as e:
    print(f"Could not connect to PyCharm debugger at {host}:{port} — {e}")
    print("Continuing without debugger.")