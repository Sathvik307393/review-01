import json
import time
from datetime import date
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from db_client import get_db_collection

PORT = 5004
maintenance_col = get_db_collection("maintenance")
vehicles_col = get_db_collection("vehicles")

# Seed data
SEED_RECORDS = [
    {"id": "s1", "car_id": "c1", "type": "Oil Change", "date": "2024-03-15", "cost": 6500, "mileage": 15000, "notes": "Synthetic 5W-30", "next_due_miles": 20000},
    {"id": "s2", "car_id": "c3", "type": "Tyre Rotation", "date": "2024-02-10", "cost": 800, "mileage": 25000, "notes": "All 4 tyres rotated", "next_due_miles": 30000},
    {"id": "s3", "car_id": "c5", "type": "Brake Inspection", "date": "2024-04-01", "cost": 1500, "mileage": 18000, "notes": "Front pads 70% remaining", "next_due_miles": 28000}
]

if maintenance_col.count_documents() == 0:
    print("Seeding maintenance logs...")
    for r in SEED_RECORDS:
        r["_id"] = r["id"]
        maintenance_col.insert_one(r)

class MaintenanceHandler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        ts = time.strftime("%H:%M:%S")
        print(f"  [{ts}] [Maintenance] {self.command} {self.path}  →  {args[1] if len(args)>1 else ''}")

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

        # GET /api/service
        if len(parts) == 2 and parts[0] == "api" and parts[1] == "service":
            car_id_filter = query.get("car_id", [None])[0]
            if car_id_filter:
                records = maintenance_col.find({"car_id": car_id_filter})
            else:
                records = maintenance_col.find()

            # Attach vehicle details
            for r in records:
                r["car"] = vehicles_col.find_one({"_id": r["car_id"]}) or {}

            total_cost = sum(r.get("cost", 0) for r in records)
            self._send_json(200, {"records": records, "total": len(records), "total_cost": total_cost})
            return

        self._send_json(404, {"error": "Not found"})

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/")
        parts = [p for p in path.split("/") if p]

        # POST /api/service
        if len(parts) == 2 and parts[0] == "api" and parts[1] == "service":
            body = self._read_json()
            car_id = body.get("car_id", "").strip()
            svc_type = body.get("type", "").strip()
            cost = body.get("cost", 0)

            if not car_id or not svc_type:
                self._send_json(400, {"error": "car_id and type are required."})
                return

            sid = "s" + str(maintenance_col.count_documents() + 1)
            while maintenance_col.find_one({"_id": sid}):
                sid = "s" + str(int(sid[1:]) + 1)

            record = {
                "_id": sid,
                "id": sid,
                "car_id": car_id,
                "type": svc_type,
                "cost": cost,
                "mileage": body.get("mileage", 0),
                "next_due_miles": body.get("next_due_miles", 0),
                "notes": body.get("notes", ""),
                "date": body.get("date", str(date.today())),
                "payment_status": "pending"
            }
            maintenance_col.insert_one(record)
            self._send_json(201, record)
            return

        self._send_json(404, {"error": "Not found"})

    def do_DELETE(self):
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/")
        parts = [p for p in path.split("/") if p]

        # DELETE /api/service/<record_id>
        if len(parts) == 3 and parts[0] == "api" and parts[1] == "service":
            record_id = parts[2]
            existing = maintenance_col.find_one({"_id": record_id})
            if not existing:
                self._send_json(404, {"error": "Record not found"})
                return

            maintenance_col.delete_one({"_id": record_id})
            self._send_json(200, {"deleted": existing})
            return

        self._send_json(404, {"error": "Not found"})


if __name__ == "__main__":
    server = HTTPServer(("", PORT), MaintenanceHandler)
    print(f"Maintenance Service listening on port {PORT}...")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("Shutting down Maintenance Service.")
