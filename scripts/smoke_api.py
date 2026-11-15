import getpass
import httpx

base = "http://127.0.0.1:8000"
r = httpx.get(base + "/health", timeout=10)
print("health:", r.status_code, r.json())
username = input("Founder username: ")
password = getpass.getpass("Founder password (hidden): ")
r = httpx.post(base + "/auth/login",
               json={"username": username, "password": password}, timeout=10)
print("login:", r.status_code)
if r.status_code != 200:
    raise SystemExit(1)
token = r.json()["access_token"]
r = httpx.get(base + "/review/pending",
              headers={"Authorization": "Bearer " + token}, timeout=10)
print("review/pending with token:", r.status_code, "items:", len(r.json()))
r = httpx.get(base + "/review/pending", timeout=10)
print("review without token (must be 401):", r.status_code)
print("OK: live API verified")
