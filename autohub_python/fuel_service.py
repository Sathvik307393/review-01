import json
import time
from datetime import date
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from db_client import get_db_collection

PORT = 5007
fuel_col = get_db_collection("fuel")
vehicles_col = get_db_collection("vehicles")

# Seed data
SEED_FUEL = [
    {"id": "f1", "car_id": "c1", "date": "2024-04-20", "litres": 45.2, "cost_per_litre": 102.50, "odometer": 14800, "full_tank": True},
    {"id": "f2", "car_id": "c3", "date": "2024-04-18", "litres": 38.0, "cost_per_litre": 104.20, "odometer": 24900, "full_tank": True},
    {"id": "f3", "car_id": "c1", "date": "2024-03-30", "litres": 42.0, "cost_per_litre": 101.80, "odometer": 14200, "full_tank": True}
]

if fuel_col.count_documents() == 0:
    print("Seeding fuel database logs...")
    for f in SEED_FUEL:
        f["_id"] = f["id"]
        fuel_col.insert_one(f)

class FuelHandler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        ts = time.strftime("%H:%M:%S")
        print(f"  [{ts}] [Fuel] {self.command} {self.path}  →  {args[1] if len(args)>1 else ''}")

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
        self.send_header("Access-Control-Allow-Methods", "GET,POST,DELETE,OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/")
        query = parse_qs(parsed.query)
        parts = [p for p in path.split("/") if p]

        # GET /api/fuel
        if len(parts) == 2 and parts[0] == "api" and parts[1] == "fuel":
            car_id_filter = query.get("car_id", [None])[0]
            
            if car_id_filter:
                fuel_logs = fuel_col.find({"car_id": car_id_filter})
            else:
                fuel_logs = fuel_col.find()

            logs = []
            for l in fuel_logs:
                l["total_cost"] = round(l.get("litres", 0) * l.get("cost_per_litre", 0), 2)
                logs.append(l)

            stats = {}
            for l in logs:
                cid = l.get("car_id")
                if cid not in stats:
                    stats[cid] = {"total_litres": 0, "total_cost": 0, "fill_count": 0}
                stats[cid]["total_litres"] += l.get("litres", 0)
                stats[cid]["total_cost"] += l.get("total_cost", 0)
                stats[cid]["fill_count"] += 1

            for cid, s in stats.items():
                s["avg_cost_per_litre"] = round(s["total_cost"] / s["total_litres"], 3) if s["total_litres"] else 0
                s["car"] = vehicles_col.find_one({"_id": cid}) or {}

            self._send_json(200, {
                "logs": logs,
                "stats_by_car": stats,
                "total_entries": len(logs)
            })
            return

        self._send_json(404, {"error": "Not found"})

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/")
        parts = [p for p in path.split("/") if p]

        # POST /api/fuel
        if len(parts) == 2 and parts[0] == "api" and parts[1] == "fuel":
            body = self._read_json()
            car_id = body.get("car_id", "").strip()
            litres = body.get("litres", 0.0)
            cost_per_litre = body.get("cost_per_litre", 0.0)

            if not car_id or litres <= 0 or cost_per_litre <= 0:
                self._send_json(400, {"error": "car_id, valid litres, and cost_per_litre are required."})
                return

            fid = "f" + str(fuel_col.count_documents() + 1)
            while fuel_col.find_one({"_id": fid}):
                fid = "f" + str(int(fid[1:]) + 1)

            log_entry = {
                "_id": fid,
                "id": fid,
                "car_id": car_id,
                "litres": litres,
                "cost_per_litre": cost_per_litre,
                "odometer": body.get("odometer", 0),
                "full_tank": body.get("full_tank", True),
                "date": body.get("date", str(date.today()))
            }
            fuel_col.insert_one(log_entry)
            self._send_json(201, log_entry)
            return

        self._send_json(404, {"error": "Not found"})

    def do_DELETE(self):
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/")
        parts = [p for p in path.split("/") if p]

        # DELETE /api/fuel/<log_id>
        if len(parts) == 3 and parts[0] == "api" and parts[1] == "fuel":
            log_id = parts[2]
            existing = fuel_col.find_one({"_id": log_id})
            if not existing:
                self._send_json(404, {"error": "Log not found"})
                return

            fuel_col.delete_one({"_id": log_id})
            self._send_json(200, {"message": "Deleted", "deleted": existing})
            return

        self._send_json(404, {"error": "Not found"})

if __name__ == "__main__":
    server = HTTPServer(("", PORT), FuelHandler)
    print(f"Fuel Service listening on port {PORT}...")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("Shutting down Fuel Service.")
