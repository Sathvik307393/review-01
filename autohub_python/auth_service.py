import json
import hashlib
import os
import time
import uuid
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from db_client import get_db_collection

PORT = 5001

users_col = get_db_collection("users")
sessions_col = get_db_collection("sessions")

def hash_password(password, salt=None):
    if not salt:
        salt = os.urandom(16).hex()
    hashed = hashlib.sha256((password + salt).encode("utf-8")).hexdigest()
    return hashed, salt

class AuthHandler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        # Log to stderr/console for orchestrator
        ts = time.strftime("%H:%M:%S")
        print(f"  [{ts}] [Auth] {self.command} {self.path}  →  {args[1] if len(args)>1 else ''}")

    def _read_json(self):
        length = int(self.headers.get("Content-Length", 0))
        if length:
            try:
                return json.loads(self.rfile.read(length).decode("utf-8"))
            except Exception as e:
                print(f"Auth parse error: {e}")
                return {}
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

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/")

        if path == "/api/auth/register":
            body = self._read_json()
            username = body.get("username", "").strip()
            password = body.get("password", "").strip()
            email = body.get("email", "").strip()

            if not username or not password or not email:
                self._send_json(400, {"error": "Username, password, and email are required."})
                return

            # Check if user exists
            existing = users_col.find_one({"username": username})
            if existing:
                self._send_json(409, {"error": "Username is already taken."})
                return

            hashed, salt = hash_password(password)
            user_doc = {
                "username": username,
                "password_hash": hashed,
                "salt": salt,
                "email": email,
                "created_at": time.time()
            }
            users_col.insert_one(user_doc)
            self._send_json(201, {"message": "User registered successfully.", "username": username})
            return

        elif path == "/api/auth/login":
            body = self._read_json()
            username = body.get("username", "").strip()
            password = body.get("password", "").strip()

            if not username or not password:
                self._send_json(400, {"error": "Username and password are required."})
                return

            user = users_col.find_one({"username": username})
            if not user:
                self._send_json(401, {"error": "Invalid username or password."})
                return

            hashed, _ = hash_password(password, user["salt"])
            if hashed != user["password_hash"]:
                self._send_json(401, {"error": "Invalid username or password."})
                return

            # Generate session token
            token = uuid.uuid4().hex
            session_doc = {
                "token": token,
                "username": username,
                "created_at": time.time(),
                "expires_at": time.time() + 86400  # 24 hours
            }
            sessions_col.insert_one(session_doc)
            self._send_json(200, {
                "message": "Login successful.",
                "token": token,
                "username": username,
                "email": user["email"]
            })
            return

        self._send_json(404, {"error": "Not found"})

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/")

        if path == "/api/auth/verify":
            # Extract token from headers
            auth_header = self.headers.get("Authorization", "")
            token = ""
            if auth_header.startswith("Bearer "):
                token = auth_header[7:].strip()

            if not token:
                self._send_json(401, {"error": "Token is missing."})
                return

            session = sessions_col.find_one({"token": token})
            if not session:
                self._send_json(401, {"error": "Session is invalid or expired."})
                return

            if session.get("expires_at", 0) < time.time():
                sessions_col.delete_one({"token": token})
                self._send_json(401, {"error": "Session has expired."})
                return

            user = users_col.find_one({"username": session["username"]})
            if not user:
                self._send_json(401, {"error": "User not found."})
                return

            self._send_json(200, {
                "valid": True,
                "username": user["username"],
                "email": user["email"]
            })
            return

        self._send_json(404, {"error": "Not found"})

if __name__ == "__main__":
    server = HTTPServer(("", PORT), AuthHandler)
    print(f"Auth Service listening on port {PORT}...")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("Shutting down Auth Service.")
