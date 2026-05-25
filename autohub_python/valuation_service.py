import json
import time
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from db_client import get_db_collection

PORT = 5006
vehicles_col = get_db_collection("vehicles")

class ValuationHandler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        ts = time.strftime("%H:%M:%S")
        print(f"  [{ts}] [Valuation] {self.command} {self.path}  →  {args[1] if len(args)>1 else ''}")

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
        self.send_header("Access-Control-Allow-Methods", "GET,OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/")
        parts = [p for p in path.split("/") if p]

        # GET /api/valuation
        # GET /api/valuation/<car_id>
        if len(parts) >= 2 and parts[0] == "api" and parts[1] == "valuation":
            car_id = parts[2] if len(parts) > 2 else None

            if car_id:
                car = vehicles_col.find_one({"_id": car_id})
                if not car:
                    self._send_json(404, {"error": "Car not found"})
                    return
                cars_to_value = [car]
            else:
                cars_to_value = vehicles_col.find()

            results = []
            current_year = datetime.now().year
            for car in cars_to_value:
                age = current_year - car.get("year", 2024)
                base = car.get("price", 0)
                dep_rate = 0.15 + (0.12 * max(0, age - 1))
                dep_rate = min(dep_rate, 0.75)
                mileage_penalty = (car.get("mileage", 0) / 100000.0) * 0.05 * base
                market_value = round(base * (1 - dep_rate) - mileage_penalty, 2)
                market_value = max(market_value, base * 0.10)
                results.append({
                    "car_id": car.get("_id"),
                    "make": car.get("make"),
                    "model": car.get("model"),
                    "year": car.get("year"),
                    "original_price": base,
                    "market_value": market_value,
                    "depreciation_pct": round(dep_rate * 100, 1),
                    "age_years": age,
                    "mileage": car.get("mileage"),
                    "image_url": car.get("image_url", "")
                })

            if car_id:
                self._send_json(200, results[0])
            else:
                self._send_json(200, {"valuations": results, "total": len(results)})
            return

        self._send_json(404, {"error": "Not found"})

if __name__ == "__main__":
    server = HTTPServer(("", PORT), ValuationHandler)
    print(f"Valuation Service listening on port {PORT}...")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("Shutting down Valuation Service.")
