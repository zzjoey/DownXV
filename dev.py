"""Dev server — watches src/ for changes and auto-restarts the app."""

import os
import subprocess
import sys
import time

SRC_DIR = os.path.join(os.path.dirname(__file__), "src")
POLL_INTERVAL = 1  # seconds


def _get_mtimes():
    mtimes = {}
    for root, _, files in os.walk(SRC_DIR):
        for f in files:
            if f.endswith(".py"):
                path = os.path.join(root, f)
                mtimes[path] = os.stat(path).st_mtime
    return mtimes


def main():
    prev = _get_mtimes()
    proc = subprocess.Popen([sys.executable, "run.py"])
    print("[dev] started — watching src/ for changes")

    try:
        while True:
            time.sleep(POLL_INTERVAL)
            current = _get_mtimes()
            changed = [
                p for p in current
                if current[p] != prev.get(p)
            ] + [p for p in prev if p not in current]

            if changed:
                names = [os.path.basename(p) for p in changed]
                print(f"[dev] changed: {', '.join(names)} — restarting")
                proc.terminate()
                proc.wait()
                proc = subprocess.Popen([sys.executable, "run.py"])
                prev = _get_mtimes()
            else:
                prev = current
    except KeyboardInterrupt:
        proc.terminate()
        proc.wait()


if __name__ == "__main__":
    main()
