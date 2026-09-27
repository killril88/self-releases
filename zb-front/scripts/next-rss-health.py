#!/usr/bin/python3
import json
import subprocess
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

HIGH_GIB = 4.0
RESTART_GIB = 4.2
RECOVERY_GIB = 3.5
CHECK_INTERVAL_SECONDS = 60
RESTART_COMMAND = [
    "/usr/bin/supervisorctl",
    "restart",
    "zb_node_front_release:*",
]
alerting = False
restart_in_progress = False
restart_armed = True
state_lock = threading.Lock()


def next_processes():
    output = subprocess.run(
        ["/usr/bin/pgrep", "-f", "next-server \\(v[0-9]"],
        check=False,
        capture_output=True,
        text=True,
        timeout=3,
    ).stdout
    pids = [int(value) for value in output.split() if value.isdigit()]
    if not pids:
        raise RuntimeError("Next.js process not found")
    return sorted(pids)


def process_rss():
    processes = []
    for pid in next_processes():
        with open(f"/proc/{pid}/status", encoding="utf-8") as status_file:
            values = {}
            for line in status_file:
                if ":" in line:
                    key, value = line.split(":", 1)
                    values[key] = value.strip()
        rss_kib = int(values["VmRSS"].split()[0])
        processes.append({"pid": pid, "rss_bytes": rss_kib * 1024})
    return processes


def health():
    global alerting
    processes = process_rss()
    gib = 1024 ** 3
    max_rss_bytes = max(process["rss_bytes"] for process in processes)
    total_rss_bytes = sum(process["rss_bytes"] for process in processes)
    max_rss_gib = max_rss_bytes / gib
    with state_lock:
        if alerting:
            alerting = max_rss_gib >= RECOVERY_GIB
        else:
            alerting = max_rss_gib >= HIGH_GIB
        unhealthy = alerting
    return {
        "status": "down" if unhealthy else "up",
        "service": "next-rss",
        "ok": not unhealthy,
        "pid": processes[0]["pid"],
        "pids": [process["pid"] for process in processes],
        "instance_count": len(processes),
        "rss_bytes": max_rss_bytes,
        "rss_gib": round(max_rss_gib, 2),
        "max_rss_gib": round(max_rss_gib, 2),
        "total_rss_gib": round(total_rss_bytes / gib, 2),
        "alert_threshold_gib": HIGH_GIB,
        "restart_threshold_gib": RESTART_GIB,
        "recovery_threshold_gib": RECOVERY_GIB,
        "auto_restart_enabled": True,
        "check_interval_seconds": CHECK_INTERVAL_SECONDS,
    }


def restart_frontend(rss_gib):
    global restart_in_progress
    with state_lock:
        if restart_in_progress:
            return
        restart_in_progress = True
    try:
        print(
            f"Next.js RSS is {rss_gib:.2f} GiB (restart limit {RESTART_GIB:.2f} GiB); "
            "restarting all zb_node_front_release instances",
            flush=True,
        )
        result = subprocess.run(
            RESTART_COMMAND,
            check=False,
            capture_output=True,
            text=True,
            timeout=90,
        )
        print(result.stdout, end="", flush=True)
        if result.stderr:
            print(result.stderr, end="", flush=True)
        print(f"supervisorctl exit code: {result.returncode}", flush=True)
        return result.returncode == 0
    except Exception as error:
        print(f"Automatic Next.js restart failed: {error}", flush=True)
        return False
    finally:
        with state_lock:
            restart_in_progress = False


def watchdog_loop():
    global restart_armed
    while True:
        try:
            processes = process_rss()
            rss_gib = max(process["rss_bytes"] for process in processes) / (1024 ** 3)
            should_restart = False
            with state_lock:
                if rss_gib < RECOVERY_GIB:
                    restart_armed = True
                elif rss_gib >= RESTART_GIB and restart_armed:
                    restart_armed = False
                    should_restart = True
            if should_restart:
                restart_succeeded = restart_frontend(rss_gib)
                if not restart_succeeded:
                    # Retry on the next check instead of remaining disarmed until
                    # the process happens to drop below the recovery threshold.
                    with state_lock:
                        restart_armed = True
        except Exception as error:
            print(f"RSS watchdog check failed: {error}", flush=True)
        time.sleep(CHECK_INTERVAL_SECONDS)


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path != "/health":
            return self.reply(404, {"error": "not found"})
        try:
            result = health()
            self.reply(200 if result["ok"] else 503, result)
        except Exception as error:
            self.reply(503, {"status": "down", "service": "next-rss", "ok": False, "error": str(error)})

    def reply(self, status, payload):
        body = json.dumps(payload, separators=(",", ":")).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *_):
        pass


if __name__ == "__main__":
    threading.Thread(target=watchdog_loop, name="rss-watchdog", daemon=True).start()
    ThreadingHTTPServer(("127.0.0.1", 9107), Handler).serve_forever()
