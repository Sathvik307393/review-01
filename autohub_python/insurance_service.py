import json
import time
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from db_client import get_db_collection

PORT = 5008
insurance_col = get_db_collection("insurance")
vehicles_col = get_db_collection("vehicles")

# Seed data
SEED_POLICIES = [
    {"id": "i1", "car_id": "c1", "provider": "HDFC ERGO General Insurance", "policy_no": "HE-2024-441", "type": "Comprehensive", "premium": 45000, "start": "2024-01-01", "end": "2025-01-01", "status": "active"},
    {"id": "i2", "car_id": "c3", "provider": "ICICI Lombard Auto Co.", "policy_no": "IL-2024-882", "type": "Third Party", "premium": 8500, "start": "2024-02-15", "end": "2025-02-15", "status": "active"},
    {"id": "i3", "car_id": "c5", "provider": "Tata AIG Insurance Ltd.", "policy_no": "TA-2024-003", "type": "Comprehensive", "premium": 32000, "start": "2024-03-01", "end": "2025-03-01", "status": "active"}
]

if insurance_col.count_documents() == 0:
    print("Seeding insurance database policies...")
    for p in SEED_POLICIES:
        p["_id"] = p["id"]
        insurance_col.insert_one(p)

class InsuranceHandler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        ts = time.strftime("%H:%M:%S")
        print(f"  [{ts}] [Insurance] {self.command} {self.path}  →  {args[1] if len(args)>1 else ''}")

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
        self.send_header("Access-Control-Allow-Methods", "GET,POST,PUT,DELETE,OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/")
        parts = [p for p in path.split("/") if p]

        # GET /api/insurance
        # GET /api/insurance/<policy_id>
        if len(parts) >= 2 and parts[0] == "api" and parts[1] == "insurance":
            policy_id = parts[2] if len(parts) > 2 else None

            if policy_id:
                pol = insurance_col.find_one({"_id": policy_id})
                if not pol:
                    self._send_json(404, {"error": "Policy not found"})
                    return
                pol_copy = dict(pol)
                pol_copy["car"] = vehicles_col.find_one({"_id": pol_copy.get("car_id")}) or {}
                self._send_json(200, pol_copy)
                return

            policies = []
            all_pols = insurance_col.find()
            for p in all_pols:
                p_copy = dict(p)
                p_copy["car"] = vehicles_col.find_one({"_id": p_copy.get("car_id")}) or {}
                
                try:
                    expiry_date = datetime.strptime(p_copy.get("end", ""), "%Y-%m-%d")
                    days_left = (expiry_date - datetime.now()).days
                except:
                    days_left = 365
                
                p_copy["days_until_expiry"] = days_left
                p_copy["expiry_alert"] = days_left <= 30
                policies.append(p_copy)

            total_premium = sum(p.get("premium", 0) for p in policies)
            expiring_soon = [p for p in policies if p.get("expiry_alert")]
            
            self._send_json(200, {
                "policies": policies,
                "total": len(policies),
                "total_annual_premium": total_premium,
                "expiring_soon": len(expiring_soon)
            })
            return

        self._send_json(404, {"error": "Not found"})

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/")
        parts = [p for p in path.split("/") if p]

        # POST /api/insurance
        if len(parts) == 2 and parts[0] == "api" and parts[1] == "insurance":
            body = self._read_json()
            car_id = body.get("car_id", "").strip()
            provider = body.get("provider", "").strip()
            policy_no = body.get("policy_no", "").strip()

            if not car_id or not provider or not policy_no:
                self._send_json(400, {"error": "car_id, provider, and policy_no are required."})
                return

            pid = "i" + str(insurance_col.count_documents() + 1)
            while insurance_col.find_one({"_id": pid}):
                pid = "i" + str(int(pid[1:]) + 1)

            policy = {
                "_id": pid,
                "id": pid,
                "car_id": car_id,
                "provider": provider,
                "policy_no": policy_no,
                "type": body.get("type", "Comprehensive"),
                "premium": body.get("premium", 0),
                "start": body.get("start", ""),
                "end": body.get("end", ""),
                "status": "active"
            }
            insurance_col.insert_one(policy)
            self._send_json(201, policy)
            return

        self._send_json(404, {"error": "Not found"})

    def do_PUT(self):
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/")
        parts = [p for p in path.split("/") if p]

        # PUT /api/insurance/<policy_id>
        if len(parts) == 3 and parts[0] == "api" and parts[1] == "insurance":
            policy_id = parts[2]
            body = self._read_json()

            existing = insurance_col.find_one({"_id": policy_id})
            if not existing:
                self._send_json(404, {"error": "Policy not found"})
                return

            body.pop("_id", None)
            body.pop("id", None)

            insurance_col.update_one({"_id": policy_id}, {"$set": body})
            updated = insurance_col.find_one({"_id": policy_id})
            self._send_json(200, updated)
            return

        self._send_json(404, {"error": "Not found"})

    def do_DELETE(self):
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/")
        parts = [p for p in path.split("/") if p]

        # DELETE /api/insurance/<policy_id>
        if len(parts) == 3 and parts[0] == "api" and parts[1] == "insurance":
            policy_id = parts[2]
            existing = insurance_col.find_one({"_id": policy_id})
            if not existing:
                self._send_json(404, {"error": "Policy not found"})
                return

            insurance_col.delete_one({"_id": policy_id})
            self._send_json(200, {"message": "Policy deleted", "deleted": existing})
            return

        self._send_json(404, {"error": "Not found"})

if __name__ == "__main__":
    server = HTTPServer(("", PORT), InsuranceHandler)
    print(f"Insurance Service listening on port {PORT}...")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("Shutting down Insurance Service.")
