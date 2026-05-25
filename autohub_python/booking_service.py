import json
import time
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import urllib.request
import urllib.error
from db_client import get_db_collection

PORT = 5003
bookings_col = get_db_collection("bookings")
vehicles_col = get_db_collection("vehicles")

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
        print(f"[Booking Auth Check] Validation failed: {e}")
    return None

class BookingHandler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        ts = time.strftime("%H:%M:%S")
        print(f"  [{ts}] [Booking] {self.command} {self.path}  →  {args[1] if len(args)>1 else ''}")

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

        # GET /api/booking
        if len(parts) == 2 and parts[0] == "api" and parts[1] == "booking":
            username = self.get_auth_user()
            if not username:
                self._send_json(401, {"error": "Authentication token missing or invalid."})
                return

            # Retrieve only bookings belonging to the verified user
            bookings = bookings_col.find({"username": username})

            # Attach car details
            for b in bookings:
                b["car"] = vehicles_col.find_one({"_id": b["car_id"]}) or {}

            self._send_json(200, {"bookings": bookings, "total": len(bookings)})
            return

        self._send_json(404, {"error": "Not found"})

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/")
        parts = [p for p in path.split("/") if p]

        # POST /api/booking
        if len(parts) == 2 and parts[0] == "api" and parts[1] == "booking":
            username = self.get_auth_user()
            if not username:
                self._send_json(401, {"error": "Authentication token missing or invalid."})
                return

            body = self._read_json()
            car_id = body.get("car_id", "").strip()
            start_date_str = body.get("start_date", "").strip()
            end_date_str = body.get("end_date", "").strip()

            if not car_id or not start_date_str or not end_date_str:
                self._send_json(400, {"error": "Missing required details (car_id, start_date, end_date)."})
                return

            car = vehicles_col.find_one({"_id": car_id})
            if not car:
                self._send_json(404, {"error": "Selected vehicle not found."})
                return

            if car.get("status") == "sold":
                self._send_json(400, {"error": "Vehicle is sold and unavailable for renting."})
                return

            try:
                start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
                end_date = datetime.strptime(end_date_str, "%Y-%m-%d")
                delta = end_date - start_date
                days = max(1, delta.days)
            except Exception as e:
                self._send_json(400, {"error": f"Invalid date format. Use YYYY-MM-DD. Error: {e}"})
                return

            daily_rate = max(1000, car.get("price", 0) * 0.002)
            total_cost = round(days * daily_rate)

            bid = "b" + str(bookings_col.count_documents() + 1)
            while bookings_col.find_one({"_id": bid}):
                bid = "b" + str(int(bid[1:]) + 1)

            booking_doc = {
                "_id": bid,
                "id": bid,
                "car_id": car_id,
                "username": username,
                "start_date": start_date_str,
                "end_date": end_date_str,
                "total_cost": total_cost,
                "status": "confirmed",
                "created_at": time.time()
            }
            bookings_col.insert_one(booking_doc)
            
            # Update vehicle status
            vehicles_col.update_one({"_id": car_id}, {"$set": {"status": "reserved"}})

            self._send_json(201, booking_doc)
            return

        self._send_json(404, {"error": "Not found"})

    def do_PUT(self):
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/")
        parts = [p for p in path.split("/") if p]

        # PUT /api/booking/<booking_id>/status
        if len(parts) == 4 and parts[0] == "api" and parts[1] == "booking" and parts[3] == "status":
            username = self.get_auth_user()
            if not username:
                self._send_json(401, {"error": "Authentication token missing or invalid."})
                return

            booking_id = parts[2]
            body = self._read_json()
            new_status = body.get("status", "").strip()

            if not new_status:
                self._send_json(400, {"error": "Status is required."})
                return

            booking = bookings_col.find_one({"_id": booking_id})
            if not booking:
                self._send_json(404, {"error": "Booking not found."})
                return

            # Ensure the user owns this booking
            if booking["username"] != username:
                self._send_json(403, {"error": "Access denied. You do not own this reservation."})
                return

            bookings_col.update_one({"_id": booking_id}, {"$set": {"status": new_status}})
            
            if new_status == "cancelled":
                vehicles_col.update_one({"_id": booking["car_id"]}, {"$set": {"status": "available"}})

            updated = bookings_col.find_one({"_id": booking_id})
            self._send_json(200, updated)
            return

        self._send_json(404, {"error": "Not found"})


if __name__ == "__main__":
    server = HTTPServer(("", PORT), BookingHandler)
    print(f"Booking Service listening on port {PORT}...")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("Shutting down Booking Service.")
