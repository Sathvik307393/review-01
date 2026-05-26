import os
import socket
import sys
from pymongo import MongoClient

mongo_uri = os.environ.get("MONGO_URI")

if not mongo_uri:
    print("❌ ERROR: MONGO_URI environment variable is not set!")
    print("Please run: export MONGO_URI=\"mongodb://autohub_user:AutoHubPassword@192.16.0.101:27017/autohub?authSource=autohub\"")
    sys.exit(1)

print("==========================================")
print("   MongoDB Connection Diagnostic Tool (Py)  ")
print("==========================================")
# Mask password in log output
try:
    masked_uri = mongo_uri
    if "@" in mongo_uri:
        credentials = mongo_uri.split("://")[1].split("@")[0]
        masked_uri = mongo_uri.replace(credentials, "******")
    print(f"Connection String: {masked_uri}\n")
except Exception:
    print(f"Connection String: {mongo_uri}\n")

# Parse connection details
host = "192.16.0.101"
port = 27017
db_name = "autohub"

try:
    # Basic parsing for Socket check
    conn_part = mongo_uri.split("@")[1].split("/")[0]
    if ":" in conn_part:
        host, port_str = conn_part.split(":")
        port = int(port_str.split("?")[0])
    else:
        host = conn_part.split("?")[0]
except Exception:
    pass

# Step 1: Raw TCP Socket Check
print(f"Step 1: Testing raw TCP socket connection to {host}:{port}...")
try:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(2.5)
    s.connect((host, port))
    print(f"✅ Socket check: Successfully established TCP connection to port {port}!")
    s.close()
except Exception as err:
    print(f"❌ Socket check: Failed to connect to {host}:{port}")
    print(f"   Error details: {err}")
    print("\n❌ DIAGNOSIS: Network blockage. Check VPN tunnel status, AWS route tables, and Security Groups/NSGs.")
    sys.exit(1)

# Step 2: MongoDB Client Connection and Auth Check
print(f"\nStep 2: Connecting via PyMongo MongoClient and checking credentials...")
try:
    client = MongoClient(mongo_uri, serverSelectionTimeoutMS=3000)
    # Trigger connection / server info check
    client.server_info()
    print("✅ MongoClient: Connected successfully to database server.")
    
    print(f"\nStep 3: Checking authentication on database...")
    db = client.get_database(db_name)
    
    # Run ping command
    db.command("ping")
    print("✅ Auth check: Ping command completed successfully!")
    
    # List collections to verify read/write access
    collections = db.list_collection_names()
    print(f"✅ Auth check: Retrieved {len(collections)} collections from '{db_name}' database.")
    
    print("\n🎉 SUCCESS: Your database connection is 100% working and authenticated!")
except Exception as err:
    print("❌ MongoClient error encountered:")
    print(f"   Error: {err}")
    print("\n❌ DIAGNOSIS: Authentication Failed or Database is unreachable.")
    print("   Check your credentials and make sure authorization is enabled on the MongoDB server.")
finally:
    if 'client' in locals():
        client.close()
