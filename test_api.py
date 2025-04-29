#!/usr/bin/env python3
import os
import sys
import json
import time
import requests
import pyotp
import urllib.parse
import uuid

# ── Configuration ──────────────────────────────────────────
BASE_URL          = "http://localhost:8000"
LOGIN_URL         = f"{BASE_URL}/auth/login"
PATIENTS_URL      = f"{BASE_URL}/patients"
PROJECTS_URL      = f"{BASE_URL}/projects"
PROJECT_USERS_URL = f"{PROJECTS_URL}/users"
REGISTER_URL      = f"{BASE_URL}/auth/register"
ME_URL            = f"{BASE_URL}/auth/me"
PENDING_LIST_URL  = f"{BASE_URL}/admin/pending-registrations"
APPROVE_URL       = lambda pid: f"{BASE_URL}/admin/pending-registrations/{pid}/approve"
DELETE_URL        = lambda pid: f"{BASE_URL}/admin/pending-registrations/{pid}"
TOKEN_FILE        = "token.json"
ADMIN_EMAIL       = "admin@example.com"
ADMIN_PASSWORD    = "secureAdminPassword"

# ── Auth Helpers ──────────────────────────────────────────
def load_token_data():
    if not os.path.exists(TOKEN_FILE):
        return {}
    return json.load(open(TOKEN_FILE))

def save_token_data(data):
    with open(TOKEN_FILE, "w") as f:
        json.dump(data, f)

def parse_secret_from_uri(uri):
    q = urllib.parse.urlparse(uri).query
    return urllib.parse.parse_qs(q).get("secret", [None])[0]

def login_and_get_token():
    td = load_token_data()
    r = requests.post(LOGIN_URL, json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD})
    if r.status_code == 200 and r.json().get("totp_setup"):
        uri = r.json()["qr_code_url"]
        secret = parse_secret_from_uri(uri)
        print("Scan this QR URL in your authenticator:\n", uri)
        code = input("Enter the current TOTP code: ").strip()
        td["totp_secret"] = secret
        r2 = requests.post(LOGIN_URL, json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD,
            "totp_code": code
        })
        r2.raise_for_status()
        token = r2.json()["access_token"]
        td.update(access_token=token, saved_at=time.time())
        save_token_data(td)
        return token
    if r.status_code == 400 and "TOTP code required" in r.json().get("detail", ""):
        secret = td.get("totp_secret") or input("Enter your Base32 TOTP secret: ").strip()
        tok = pyotp.TOTP(secret).now()
        r2 = requests.post(LOGIN_URL, json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD,
            "totp_code": tok
        })
        r2.raise_for_status()
        token = r2.json()["access_token"]
        td.update(access_token=token, saved_at=time.time(), totp_secret=secret)
        save_token_data(td)
        return token
    if r.status_code == 200 and "access_token" in r.json():
        token = r.json()["access_token"]
        td.update(access_token=token, saved_at=time.time())
        save_token_data(td)
        return token
    r.raise_for_status()
    raise RuntimeError("Unexpected login response")

def get_token():
    td = load_token_data()
    token = td.get("access_token")
    if token:
        r = requests.get(ME_URL, headers={"Authorization": f"Bearer {token}"})
        if r.status_code == 200:
            return token
        print("▶ Saved token expired; re-logging in…")
    return login_and_get_token()

# ── Patients Tests ─────────────────────────────────────────
def test_list_no_auth():
    r = requests.get(PATIENTS_URL)
    assert r.status_code == 401, f"Expected 401, got {r.status_code}"
    print("✔ Unauthorized /patients list passed")

def test_list_with_auth(token):
    r = requests.get(PATIENTS_URL, headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200, f"Expected 200, got {r.status_code}"
    print(f"✔ Authorized /patients list returned {len(r.json())} record(s)")

def test_create_patient(token):
    for fn in ("consent.pdf", "related.pdf"):
        if not os.path.exists(fn):
            open(fn, "wb").write(b"%PDF-1.4\n%Dummy\n")
    data = {"first_name": "Alice", "last_name": "Smith", "dob": "1985-07-12", "ethnicity": "white", "gender": "female", "past_diagnoses": "none"}
    files = {"informed_consent_doc": open("consent.pdf", "rb"), "related_reports_doc": open("related.pdf", "rb")}
    r = requests.post(PATIENTS_URL, headers={"Authorization": f"Bearer {token}"}, data=data, files=files)
    for f in files.values(): f.close()
    assert r.status_code == 201, f"Create failed: {r.status_code}"
    pid = r.json()["id"]
    print(f"✔ Created patient id={pid}")
    return pid

def test_get_by_id(token, pid):
    r = requests.get(f"{PATIENTS_URL}/{pid}", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200, f"Expected 200, got {r.status_code}"
    print(f"✔ GET /patients/{pid} passed")

def test_update_patient(token, pid):
    r = requests.put(f"{PATIENTS_URL}/{pid}", headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"}, json={"first_name": "Alicia"})
    assert r.status_code == 200, f"Update failed: {r.status_code}"
    print(f"✔ Updated /patients/{pid} first_name → Alicia")

def test_verify_in_list(token, pid):
    r = requests.get(PATIENTS_URL, headers={"Authorization": f"Bearer {token}"})
    for p in r.json():
        if p["id"] == pid:
            print(f"✔ Patient {pid} in list as {p['first_name']} {p['last_name']}")
            return
    assert False, f"Patient {pid} not found"

# ── Projects Tests ────────────────────────────────────────
def test_projects_list_no_auth():
    r = requests.get(PROJECTS_URL)
    assert r.status_code == 401, f"Expected 401, got {r.status_code}"
    print("✔ Unauthorized /projects list passed")

def test_projects_list_with_auth(token):
    r = requests.get(PROJECTS_URL, headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200, f"Expected 200, got {r.status_code}"
    print(f"✔ Authorized /projects list returned {len(r.json())} record(s)")

def test_projects_create_valid(token):
    name = f"Test Project {int(time.time())}"
    payload = {"name": name, "description": "Auto-generated test", "lead_user_id": 1, "member_ids": [1]}
    r = requests.post(PROJECTS_URL, headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"}, json=payload)
    assert r.status_code == 201, f"Create project failed: {r.status_code}" 
    proj = r.json()
    print(f"✔ Created project id={proj['id']}")
    return proj["id"], name

def test_projects_update(token, pid):
    new_name = f"Updated Project {pid}_{int(time.time())}"
    r = requests.put(f"{PROJECTS_URL}/{pid}", headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"}, json={"name": new_name})
    assert r.status_code == 200, f"Update project failed: {r.status_code}"
    print(f"✔ Updated project {pid} name → {new_name}")
    return new_name

def test_projects_update_nonexistent(token):
    r = requests.put(f"{PROJECTS_URL}/999999", headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"}, json={"name": "Nope"})
    assert r.status_code == 404, f"Expected 404, got {r.status_code}"
    print("✔ Non-existent /projects update returned 404")

# ── Auth/Register & Me Tests ─────────────────────────────────
def test_register_and_pending_flow(token):
    # Create a pending registration
    unique_email = f"pending+{uuid.uuid4().hex[:6]}@example.com"
    data = {
        "email": unique_email,
        "password": "TestPass123!",
        "first_name": "Foo",
        "last_name": "Bar"
    }
    r = requests.post(REGISTER_URL, headers={"Authorization": f"Bearer {token}"}, data=data)
    assert r.status_code == 201, f"Register failed: {r.status_code} {r.text}"
    pending = r.json()
    pid = pending["id"]
    print(f"✔ Registered pending user id={pid}")
    
    # List pending registrations
    r2 = requests.get(PENDING_LIST_URL, headers={"Authorization": f"Bearer {token}"})
    assert r2.status_code == 200 and any(p["id"] == pid for p in r2.json()), "Pending list missing registration"
    print("✔ /admin/pending-registrations list contains new pending")

    # Approve pending
    r3 = requests.post(APPROVE_URL(pid), headers={"Authorization": f"Bearer {token}"}, json={"role_ids": [3]})
    assert r3.status_code == 200, f"Approve failed: {r3.status_code} {r3.text}"
    user = r3.json()
    assert user.get("email") == unique_email
    print(f"✔ Approved pending user -> new user id={user['id']}")

# ── Current User Info Test ─────────────────────────────────
def test_me_endpoint(token):
    r = requests.get(ME_URL, headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200, f"GET /auth/me failed: {r.status_code}"
    data = r.json()
    assert data.get("email") == ADMIN_EMAIL
    print("✔ /auth/me returned current admin user info")

# ── Main Runner ────────────────────────────────────────────
def main():
    token = get_token()

    test_list_no_auth()
    test_list_with_auth(token)
    pid = test_create_patient(token)
    test_get_by_id(token, pid)
    test_update_patient(token, pid)
    test_verify_in_list(token, pid)

    test_projects_list_no_auth()
    test_projects_list_with_auth(token)
    proj_id, _ = test_projects_create_valid(token)
    new_name = test_projects_update(token, proj_id)
    test_projects_update_nonexistent(token)

    test_register_and_pending_flow(token)
    test_me_endpoint(token)

    print("\n🎉 All tests passed!")

if __name__ == "__main__":
    try:
        main()
    except AssertionError as e:
        print("❌ Test failed:", e)
        sys.exit(1)
    except Exception as e:
        print("❌ Error:", e)
        sys.exit(2)

