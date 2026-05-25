import subprocess
import sys
import threading
import time
import os

SERVICES = [
    ("Metrics", "metrics_service.py"),
    ("Auth", "auth_service.py"),
    ("Inventory", "inventory_service.py"),
    ("Booking", "booking_service.py"),
    ("Maintenance", "maintenance_service.py"),
    ("Payment", "payment_service.py"),
    ("Valuation", "valuation_service.py"),
    ("Fuel", "fuel_service.py"),
    ("Insurance", "insurance_service.py"),
    ("FrontendServer", "frontend_server.py")
]

processes = []

def stream_logs(name, proc):
    try:
        while True:
            line = proc.stdout.readline()
            if not line:
                break
            print(f"[{name}] {line.decode('utf-8', errors='ignore').strip()}")
            sys.stdout.flush()
    except Exception as e:
        print(f"[{name}] Log stream error: {e}")

def main():
    print("====================================================")
    print("      AutoHub Microservices Platform Launcher       ")
    print("====================================================")
    
    mongo_uri = os.environ.get("MONGO_URI")
    if mongo_uri:
        print("Production Mode: Connecting to AWS / Remote Database")
    else:
        print("Offline Mode: Persistent File-Based DB Client Active")
        
    print("\nStarting services...")

    # Start each service in sequence
    for name, script in SERVICES:
        print(f"  -> Starting {name} ({script})...")
        try:
            proc = subprocess.Popen(
                [sys.executable, "-u", script],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                bufsize=1
            )
            processes.append((name, proc))
            
            t = threading.Thread(target=stream_logs, args=(name, proc), daemon=True)
            t.start()
            
            time.sleep(0.5)
        except Exception as e:
            print(f"Failed to start {name}: {e}")
            shutdown()
            sys.exit(1)

    print("\nAll microservices and local frontend server initialized successfully.")
    print("Central Access Endpoint: http://localhost:5000")
    print("Press Ctrl+C to terminate all services.\n")

    # Keep main thread alive
    try:
        while True:
            time.sleep(1)
            for name, proc in processes:
                poll = proc.poll()
                if poll is not None:
                    print(f"\n[Warning] {name} service terminated with exit code {poll}!")
                    shutdown()
                    sys.exit(1)
    except KeyboardInterrupt:
        print("\nCtrl+C detected. Initiating graceful shutdown...")
        shutdown()

def shutdown():
    print("\nStopping all microservices...")
    for name, proc in processes:
        if proc.poll() is None:
            print(f"  Killing {name} (PID: {proc.pid})...")
            try:
                proc.terminate()
                proc.wait(timeout=2)
            except subprocess.TimeoutExpired:
                proc.kill()
            except Exception as e:
                print(f"Error stopping {name}: {e}")
    print("All services stopped. AutoHub offline.\n")

if __name__ == "__main__":
    main()
