"""
Example Service - Demonstrates how to register with the service registry

This simulates a microservice that:
1. Registers itself on startup
2. Sends periodic heartbeats
3. Deregisters on shutdown
"""

import requests
import time
import signal
import sys
from threading import Thread, Event
from flask import Flask, jsonify

# Flask app for the microservice API
app = Flask(__name__)

class ServiceClient:
    def __init__(self, service_name, service_address, registry_url="http://localhost:5001"):
        self.service_name = service_name
        self.service_address = service_address
        self.registry_url = registry_url
        self.stop_event = Event()
        self.heartbeat_interval = 10  # seconds
        
    def register(self):
        """Register this service with the registry"""
        try:
            headers = {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            }
            
            response = requests.post(
                f"{self.registry_url}/register",
                json={
                    "service": self.service_name,
                    "address": self.service_address
                },
                headers=headers,
                timeout=5
            )
            
            if response.status_code in [200, 201]:
                print(f"✓ Registered {self.service_name} at {self.service_address}")
                return True
            else:
                print(f"✗ Registration failed (status {response.status_code})")
                print(f"   Response: {response.text if response.text else 'Empty response'}")
                return False

        except requests.exceptions.ConnectionError:
            print(f"✗ Cannot connect to registry at {self.registry_url}")
            print("Make sure registry is running: python service_registry_improved.py")
            return False

        except Exception as e:
            print(f"✗ Registration error: {e}")
            return False
    

    def deregister(self):
        """Deregister this service from the registry"""
        try:
            response = requests.post(
                f"{self.registry_url}/deregister",
                json={
                    "service": self.service_name,
                    "address": self.service_address
                }
            )
            
            if response.status_code == 200:
                print(f"✓ Deregistered {self.service_name}")
                return True
            else:
                print(f"✗ Deregistration failed")
                return False

        except Exception as e:
            print(f"✗ Deregistration error: {e}")
            return False
    

    def send_heartbeat(self):
        """Send heartbeat to registry"""
        try:
            response = requests.post(
                f"{self.registry_url}/heartbeat",
                json={
                    "service": self.service_name,
                    "address": self.service_address
                }
            )
            
            if response.status_code == 200:
                print(f"♥ Heartbeat sent for {self.service_name}")
                return True
            else:
                print("✗ Heartbeat failed")
                return False

        except Exception as e:
            print(f"✗ Heartbeat error: {e}")
            return False
    

    def heartbeat_loop(self):
        """Background thread that sends periodic heartbeats"""
        while not self.stop_event.is_set():
            self.send_heartbeat()
            self.stop_event.wait(self.heartbeat_interval)
    

    def start(self):
        """Start the service and register with registry"""

        if not self.register():
            print("Failed to register. Exiting.")
            return

        heartbeat_thread = Thread(target=self.heartbeat_loop, daemon=True)
        heartbeat_thread.start()

        print(f"\n{self.service_name} registered and sending heartbeats...")
        

    def stop(self):
        """Stop the service and deregister"""
        self.stop_event.set()
        self.deregister()



# ------------------------------------------------
# Microservice API endpoints
# ------------------------------------------------

@app.route("/")
def home():
    return jsonify({
        "message": "Example microservice running"
    })


@app.route("/info")
def info():
    return jsonify({
        "service": client.service_name,
        "address": client.service_address,
        "message": "Hello from this service instance"
    })


@app.route("/health")
def health():
    return jsonify({
        "status": "healthy"
    })


# ------------------------------------------------
# Main Program
# ------------------------------------------------

if __name__ == "__main__":

    if len(sys.argv) < 3:
        print("Usage: python example_service.py <service_name> <port>")
        print("Example:")
        print("  python example_service.py user-service 8001")
        print("  python example_service.py user-service 8002")
        sys.exit(1)

    service_name = sys.argv[1]
    port = sys.argv[2]
    service_address = f"http://localhost:{port}"

    client = ServiceClient(service_name, service_address)

    # start registration + heartbeat
    client.start()

    # graceful shutdown
    def signal_handler(sig, frame):
        print("\nShutting down service...")
        client.stop()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)

    print(f"{service_name} running on port {port}")
    app.run(host="0.0.0.0", port=int(port))