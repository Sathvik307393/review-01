import json
import time
import threading
import platform
import subprocess
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse
from db_client import get_db_collection

PORT = 5009

# Shared metrics datastore
METRICS = {
    "uptime_start": time.time(),
    "requests_total": 0,
    "requests_by_status": {},
    "requests_by_service": {},
    "latency_by_service": {},
    "system_cpu": 0.0,
    "system_memory": 0.0,
}
METRICS_LOCK = threading.Lock()

def record_request(service, status_code, elapsed_ms):
    with METRICS_LOCK:
        METRICS["requests_total"] += 1
        
        status_str = str(status_code)
        METRICS["requests_by_status"][status_str] = METRICS["requests_by_status"].get(status_str, 0) + 1
        
        if service not in METRICS["requests_by_service"]:
            METRICS["requests_by_service"][service] = 0
            METRICS["latency_by_service"][service] = []
        
        METRICS["requests_by_service"][service] += 1
        METRICS["latency_by_service"][service].append(elapsed_ms)
        
        # Keep only the last 100 values to avoid infinite memory growth
        if len(METRICS["latency_by_service"][service]) > 100:
            METRICS["latency_by_service"][service].pop(0)

# System utility functions (same as in monolith)
def get_windows_cpu_percent():
    try:
        p = subprocess.Popen(["typeperf", "\\Processor(_Total)\\% Processor Time", "-sc", "1"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        stdout, _ = p.communicate(timeout=1.5)
        lines = [l.strip() for l in stdout.splitlines() if l.strip()]
        if len(lines) > 2:
            val_str = lines[2].split(",")[-1].replace('"', '')
            return round(float(val_str), 1)
    except:
        pass
    return 0.0

def get_windows_memory_percent():
    try:
        p = subprocess.Popen(["typeperf", "\\Memory\\% Committed Bytes In Use", "-sc", "1"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        stdout, _ = p.communicate(timeout=1.5)
        lines = [l.strip() for l in stdout.splitlines() if l.strip()]
        if len(lines) > 2:
            val_str = lines[2].split(",")[-1].replace('"', '')
            return round(float(val_str), 1)
    except:
        pass
    return 0.0

def get_linux_cpu_percent():
    try:
        with open('/proc/stat', 'r') as f:
            line = f.readline()
        parts = line.split()
        if len(parts) >= 5:
            vals = [float(x) for x in parts[1:5]]
            total = sum(vals)
            idle = vals[3]
            return total, idle
    except:
        pass
    return 0.0, 0.0

def get_linux_memory_percent():
    try:
        with open('/proc/meminfo', 'r') as f:
            lines = f.readlines()
        mem_total = 0
        mem_free = 0
        mem_cached = 0
        mem_buffers = 0
        for line in lines:
            if 'MemTotal:' in line:
                mem_total = int(line.split()[1])
            elif 'MemFree:' in line:
                mem_free = int(line.split()[1])
            elif 'Cached:' in line:
                mem_cached = int(line.split()[1])
            elif 'Buffers:' in line:
                mem_buffers = int(line.split()[1])
        if mem_total > 0:
            used = mem_total - (mem_free + mem_cached + mem_buffers)
            return round((used / mem_total) * 100, 1)
    except:
        pass
    return 0.0

def update_system_load():
    global METRICS
    has_psutil = False
    try:
        import psutil
        has_psutil = True
    except ImportError:
        pass
        
    while True:
        cpu = 0.0
        mem = 0.0
        
        if has_psutil:
            try:
                cpu = psutil.cpu_percent(interval=None)
                mem = psutil.virtual_memory().percent
            except:
                pass
        else:
            if platform.system() == "Windows":
                cpu = get_windows_cpu_percent()
                mem = get_windows_memory_percent()
            else:
                try:
                    total1, idle1 = get_linux_cpu_percent()
                    time.sleep(0.5)
                    total2, idle2 = get_linux_cpu_percent()
                    diff_total = total2 - total1
                    diff_idle = idle2 - idle1
                    if diff_total > 0:
                        cpu = round(100.0 * (1.0 - diff_idle / diff_total), 1)
                except:
                    cpu = 0.0
                mem = get_linux_memory_percent()
                    
        with METRICS_LOCK:
            METRICS["system_cpu"] = cpu
            METRICS["system_memory"] = mem
            
        time.sleep(3)


class MetricsHandler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        # Prevent output spamming, or print to stderr
        pass

    def _read_json(self):
        length = int(self.headers.get("Content-Length", 0))
        if length:
            try: return json.loads(self.rfile.read(length).decode("utf-8"))
            except: return {}
        return {}

    def _send_json(self, status, data):
        body = json.dumps(data).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET,POST,OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/")

        if path == "/api/metrics":
            uptime = round(time.time() - METRICS["uptime_start"], 1)
            
            by_svc = {}
            with METRICS_LOCK:
                for svc in METRICS["requests_by_service"]:
                    count = METRICS["requests_by_service"][svc]
                    latencies = METRICS["latency_by_service"][svc]
                    avg_lat = round(sum(latencies) / len(latencies), 2) if latencies else 0.0
                    by_svc[svc] = {
                        "count": count,
                        "avg_latency_ms": avg_lat
                    }
                
                status_counts = dict(METRICS["requests_by_status"])
                cpu = METRICS["system_cpu"]
                mem = METRICS["system_memory"]

            # Query database counts directly from collections
            db_counts = {
                "inventory": get_db_collection("vehicles").count_documents(),
                "service": get_db_collection("maintenance").count_documents(),
                "bookings": get_db_collection("bookings").count_documents(),
                "payments": get_db_collection("payments").count_documents()
            }

            self._send_json(200, {
                "uptime_seconds": uptime,
                "system": {
                    "cpu_usage": cpu,
                    "memory_usage": mem,
                    "platform": platform.system()
                },
                "db": db_counts,
                "requests": {
                    "total": METRICS["requests_total"],
                    "by_status": status_counts,
                    "by_service": by_svc
                }
            })
            return

        self._send_json(404, {"error": "Not found"})

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/")

        if path == "/api/metrics/report":
            body = self._read_json()
            service = body.get("service")
            status_code = body.get("status_code")
            elapsed_ms = body.get("elapsed_ms", 0.0)

            if service and status_code:
                record_request(service, status_code, elapsed_ms)
                self._send_json(200, {"status": "ok"})
            else:
                self._send_json(400, {"error": "Missing parameters."})
            return

        self._send_json(404, {"error": "Not found"})

if __name__ == "__main__":
    # Start the monitor thread
    monitor_thread = threading.Thread(target=update_system_load, daemon=True)
    monitor_thread.start()

    server = HTTPServer(("", PORT), MetricsHandler)
    print(f"Metrics Service listening on port {PORT}...")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("Shutting down Metrics Service.")
