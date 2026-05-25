import json
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import urllib.request
import urllib.error
from db_client import get_db_collection

PORT = 5005
payments_col = get_db_collection("payments")
bookings_col = get_db_collection("bookings")
maintenance_col = get_db_collection("maintenance")

def verify_token(token):
    req = urllib.request.Request(
        "http://localhost:5001/api/auth/verify",
        headers={"Authorization": f"Bearer {token}"},
        method="GET"
    )
    try:
        with urllib.request.urlopen(req, timeout=3) as res:
            data = json.loads(res.read().decode("utf-8"))
            if data.get("valid"):
                return data.get("username")
    except Exception as e:
        print(f"[Payment Auth Check] Validation failed: {e}")
    return None

class PaymentHandler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        ts = time.strftime("%H:%M:%S")
        print(f"  [{ts}] [Payment] {self.command} {self.path}  →  {args[1] if len(args)>1 else ''}")

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

    def get_auth_user(self):
        auth_header = self.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:].strip()
            return verify_token(token)
        return None

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/")
        parts = [p for p in path.split("/") if p]

        username = self.get_auth_user()
        if not username:
            self._send_json(401, {"error": "Authentication token missing or invalid."})
            return

        # GET /api/payment
        if len(parts) == 2 and parts[0] == "api" and parts[1] == "payment":
            transactions = payments_col.find({"username": username})
            self._send_json(200, {"transactions": transactions, "total": len(transactions)})
            return

        # GET /api/payment/stats
        if len(parts) == 3 and parts[0] == "api" and parts[1] == "payment" and parts[2] == "stats":
            transactions = payments_col.find()
            total_revenue = sum(t.get("amount", 0) for t in transactions)
            by_method = {}
            for t in transactions:
                method = t.get("payment_method", "Other")
                by_method[method] = by_method.get(method, 0) + t.get("amount", 0)
            
            self._send_json(200, {
                "total_transactions": len(transactions),
                "total_revenue": total_revenue,
                "revenue_by_method": by_method
            })
            return

        self._send_json(404, {"error": "Not found"})

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/")
        parts = [p for p in path.split("/") if p]

        # POST /api/payment
        if len(parts) == 2 and parts[0] == "api" and parts[1] == "payment":
            username = self.get_auth_user()
            if not username:
                self._send_json(401, {"error": "Authentication token missing or invalid."})
                return

            body = self._read_json()
            booking_id = body.get("booking_id", "").strip()
            service_id = body.get("service_id", "").strip()
            amount = body.get("amount", 0)
            payment_method = body.get("payment_method", "UPI").strip()

            if not booking_id and not service_id:
                self._send_json(400, {"error": "booking_id or service_id is required."})
                return

            if amount <= 0:
                self._send_json(400, {"error": "Payment amount must be greater than zero."})
                return

            # Verify ownership before payment
            if booking_id:
                booking = bookings_col.find_one({"_id": booking_id})
                if not booking:
                    self._send_json(404, {"error": "Booking record not found."})
                    return
                if booking["username"] != username:
                    self._send_json(403, {"error": "Access denied. Cannot pay for another user's reservation."})
                    return

            pid = "p" + str(payments_col.count_documents() + 1)
            while payments_col.find_one({"_id": pid}):
                pid = "p" + str(int(pid[1:]) + 1)

            payment_doc = {
                "_id": pid,
                "id": pid,
                "booking_id": booking_id,
                "service_id": service_id,
                "username": username,
                "amount": amount,
                "payment_method": payment_method,
                "status": "completed",
                "timestamp": time.time()
            }
            payments_col.insert_one(payment_doc)

            # Update status in bookings or maintenance records
            if booking_id:
                bookings_col.update_one({"_id": booking_id}, {"$set": {"status": "paid"}})
            elif service_id:
                maintenance_col.update_one({"_id": service_id}, {"$set": {"payment_status": "paid"}})

            self._send_json(201, payment_doc)
            return

        self._send_json(404, {"error": "Not found"})


if __name__ == "__main__":
    server = HTTPServer(("", PORT), PaymentHandler)
    print(f"Payment Service listening on port {PORT}...")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("Shutting down Payment Service.")
