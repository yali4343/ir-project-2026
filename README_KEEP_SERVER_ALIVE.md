# Keeping the Search Server Running (GCP VM)

This guide explains how to run the Flask search server in the background so it stays alive even after closing the SSH session or browser.

## Prerequisites
- You are connected to the GCP VM via SSH.
- The project code is located under `~/search_engine`.
- A Python virtual environment exists at `~/venv` (recommended).

---

## 1) Activate the virtual environment
```bash
source ~/venv/bin/activate
```
You should see `(venv)` in your prompt.

---

## 2) Navigate to the project directory
```bash
cd ~/search_engine
```

Verify the main server file exists (usually `search_frontend.py`):
```bash
ls
```

---

## 3) Run the server in the background using nohup
```bash
nohup python3 search_frontend.py > server.log 2>&1 &
```

This command:
- Keeps the server running after disconnecting from SSH.
- Redirects logs and errors to `server.log`.
- Runs the process in the background.

---

## 4) Verify the server is running
Check the process:
```bash
ps aux | grep search_frontend.py
```

Check that port 8080 is listening:
```bash
ss -tulpn | grep 8080
```

---

## 5) Test from your browser
Open the root URL (IMPORTANT: use `http` and include `/`):
```
http://<VM_EXTERNAL_IP>:8080/
```

Example search endpoint:
```
http://<VM_EXTERNAL_IP>:8080/search?query=test
```

---

## 6) View logs (if needed)
```bash
cd ~/search_engine
tail -f server.log
```

---

## 7) Stop the server
Find the PID:
```bash
ps aux | grep search_frontend.py
```

Stop the process:
```bash
kill <PID>
```

Force stop if necessary:
```bash
kill -9 <PID>
```

---

## Notes
- Ensure the Flask app runs on `0.0.0.0` and port `8080`.
- Ensure the GCP firewall allows incoming TCP traffic on port `8080`.
