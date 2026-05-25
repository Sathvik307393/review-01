import json
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from db_client import get_db_collection

PORT = 5002
vehicles_col = get_db_collection("vehicles")

# Seed data
SEED_VEHICLES = [
    {
        "id": "c1", "make": "Mahindra", "model": "XUV700", "year": 2023, "color": "Midnight Black", 
        "mileage": 15000, "status": "available", "price": 2200000,
        "image_url": "https://images.unsplash.com/photo-1533473359331-0135ef1b58bf?auto=format&fit=crop&w=600&q=80"
    },
    {
        "id": "c2", "make": "Tata", "model": "Nexon EV", "year": 2023, "color": "Empowered Oxide", 
        "mileage": 8000, "status": "sold", "price": 1750000,
        "image_url": "https://images.unsplash.com/photo-1563720223185-11003d516935?auto=format&fit=crop&w=600&q=80"
    },
    {
        "id": "c3", "make": "Maruti Suzuki", "model": "Swift", "year": 2022, "color": "Solid Fire Red", 
        "mileage": 25000, "status": "available", "price": 750000,
        "image_url": "https://images.unsplash.com/photo-1583121274602-3e2820c69888?auto=format&fit=crop&w=600&q=80"
    },
    {
        "id": "c4", "make": "Mahindra", "model": "Thar 4x4", "year": 2023, "color": "Rocky Beige", 
        "mileage": 12000, "status": "reserved", "price": 1600000,
        "image_url": "https://images.unsplash.com/photo-1605559424843-9e4c228bf1c2?auto=format&fit=crop&w=600&q=80"
    },
    {
        "id": "c5", "make": "Hyundai", "model": "Creta", "year": 2023, "color": "Ranger Khaki", 
        "mileage": 18000, "status": "available", "price": 1850000,
        "image_url": "https://images.unsplash.com/photo-1549399542-7e3f8b79c341?auto=format&fit=crop&w=600&q=80"
    }
]

# Ensure database is seeded
if vehicles_col.count_documents() == 0:
    print("Seeding vehicle database...")
    for v in SEED_VEHICLES:
        # Map seed 'id' to '_id' for compatibility
        v["_id"] = v["id"]
        vehicles_col.insert_one(v)

class InventoryHandler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        ts = time.strftime("%H:%M:%S")
        print(f"  [{ts}] [Inventory] {self.command} {self.path}  →  {args[1] if len(args)>1 else ''}")

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
        query = parse_qs(parsed.query)
        parts = [p for p in path.split("/") if p]

        # GET /api/inventory
        if len(parts) == 2 and parts[0] == "api" and parts[1] == "inventory":
            status_filter = query.get("status", [None])[0]
            if status_filter:
                cars = vehicles_col.find({"status": status_filter})
            else:
                cars = vehicles_col.find()
            self._send_json(200, {"cars": cars, "total": len(cars)})
            return

        # GET /api/inventory/<car_id>
        if len(parts) == 3 and parts[0] == "api" and parts[1] == "inventory":
            car_id = parts[2]
            car = vehicles_col.find_one({"_id": car_id})
            if car:
                self._send_json(200, car)
            else:
                self._send_json(404, {"error": "Car not found"})
            return

        self._send_json(404, {"error": "Not found"})

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/")
        parts = [p for p in path.split("/") if p]

        # POST /api/inventory
        if len(parts) == 2 and parts[0] == "api" and parts[1] == "inventory":
            body = self._read_json()
            make = body.get("make", "").strip()
            model = body.get("model", "").strip()
            if not make or not model:
                self._send_json(400, {"error": "Make and Model are required."})
                return

            cid = "c" + str(vehicles_col.count_documents() + 1)
            while vehicles_col.find_one({"_id": cid}):
                cid = "c" + str(int(cid[1:]) + 1)

            img_url = body.get("image_url") or "https://images.unsplash.com/photo-1533473359331-0135ef1b58bf?auto=format&fit=crop&w=600&q=80"
            car = {
                "_id": cid,
                "id": cid,
                "make": make,
                "model": model,
                "year": body.get("year", 2024),
                "color": body.get("color", "Unknown"),
                "mileage": body.get("mileage", 0),
                "price": body.get("price", 0),
                "status": body.get("status", "available"),
                "image_url": img_url
            }
            vehicles_col.insert_one(car)
            self._send_json(201, car)
            return

        self._send_json(404, {"error": "Not found"})

    def do_PUT(self):
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/")
        parts = [p for p in path.split("/") if p]

        # PUT /api/inventory/<car_id>
        if len(parts) == 3 and parts[0] == "api" and parts[1] == "inventory":
            car_id = parts[2]
            body = self._read_json()
            
            existing = vehicles_col.find_one({"_id": car_id})
            if not existing:
                self._send_json(404, {"error": "Car not found"})
                return

            # Avoid overwriting internal _id or id
            body.pop("_id", None)
            body.pop("id", None)

            vehicles_col.update_one({"_id": car_id}, {"$set": body})
            updated_car = vehicles_col.find_one({"_id": car_id})
            self._send_json(200, updated_car)
            return

        self._send_json(404, {"error": "Not found"})

    def do_DELETE(self):
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/")
        parts = [p for p in path.split("/") if p]

        # DELETE /api/inventory/<car_id>
        if len(parts) == 3 and parts[0] == "api" and parts[1] == "inventory":
            car_id = parts[2]
            existing = vehicles_col.find_one({"_id": car_id})
            if not existing:
                self._send_json(404, {"error": "Car not found"})
                return

            vehicles_col.delete_one({"_id": car_id})
            self._send_json(200, {"deleted": existing})
            return

        self._send_json(404, {"error": "Not found"})


if __name__ == "__main__":
    server = HTTPServer(("", PORT), InventoryHandler)
    print(f"Inventory Service listening on port {PORT}...")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("Shutting down Inventory Service.")
