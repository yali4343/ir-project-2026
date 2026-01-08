import subprocess
import time
import requests
import sys
import os
import signal
from run_experiment import run_experiment

SERVER_CMD = [sys.executable, "-u", "search_frontend.py"]
SERVER_URL = "http://localhost:8080/search"

def wait_for_server(url, timeout=60):
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            requests.get(url.replace("/search", "/")) # Health check on root or just connection
            print("Server is up!")
            return True
        except requests.exceptions.ConnectionError:
            time.sleep(1)
            print("Waiting for server...")
    return False

def main():
    print("Starting server...")
    # Start server
    server_process = subprocess.Popen(SERVER_CMD, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    try:
        if wait_for_server(SERVER_URL):
            print("Server ready. Running experiment...")
            run_experiment()
        else:
            print("Server failed to start.")
            # Print stderr
            out, err = server_process.communicate(timeout=5)
            print("Server Output:", out.decode())
            print("Server Error:", err.decode())
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        print("Stopping server...")
        server_process.terminate()
        try:
            # Get output before it dies fully or after terminate
            out, err = server_process.communicate(timeout=10)
            print("--- Server STDOUT ---")
            print(out.decode(errors='ignore'))
            print("--- Server STDERR ---")
            print(err.decode(errors='ignore'))
        except subprocess.TimeoutExpired:
            server_process.kill()
            print("Server killed (timeout).")
        print("Server stopped.")

if __name__ == "__main__":
    main()
