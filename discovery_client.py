import requests
import random
import sys

REGISTRY_URL = "http://localhost:5001"

def discover_service(service_name):
    response = requests.get(f"{REGISTRY_URL}/discover/{service_name}", timeout=5)
    if response.status_code != 200:
        print(f"Discovery failed: {response.text}")
        return []

    data = response.json()
    return data.get("instances", [])

def call_random_instance(service_name):
    instances = discover_service(service_name)

    if not instances:
        print("No active instances found.")
        return

    chosen = random.choice(instances)
    address = chosen["address"]

    print(f"Discovered {len(instances)} instance(s)")
    print(f"Randomly selected: {address}")

    response = requests.get(f"{address}/info", timeout=5)
    print("Response:")
    print(response.json())

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python discovery_client.py <service_name>")
        print("Example: python discovery_client.py user-service")
        sys.exit(1)

    call_random_instance(sys.argv[1])