# tests/test_login.py

import pytest
import pyotp
import urllib.parse

from httpx import AsyncClient, ASGITransport
from app.main import app  # Adjust if your FastAPI app is located elsewhere


# ------------------------------------------------------------------------------
# Test Case 1: User Not Found
# ------------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_login_user_not_found():
    transport = ASGITransport(app=app)
    async with AsyncClient(base_url="http://testserver", transport=transport) as ac:
        # Use an email that doesn't exist
        payload = {"email": "nonexistent@example.com", "password": "any_password"}
        response = await ac.post("/auth/login", json=payload)

        # Expect 401 Unauthorized with an appropriate detail message.
        assert response.status_code == 401
        data = response.json()
        assert "Invalid credentials" in data.get("detail", "")


# ------------------------------------------------------------------------------
# Test Case 2: Wrong Password
# ------------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_login_wrong_password():
    transport = ASGITransport(app=app)
    async with AsyncClient(base_url="http://testserver", transport=transport) as ac:
        # Assume test@example.com exists but the password is wrong.
        payload = {"email": "test@example.com", "password": "wrongpassword"}
        response = await ac.post("/auth/login", json=payload)

        # Expect a 401 Unauthorized
        assert response.status_code == 401
        data = response.json()
        assert "Invalid credentials" in data.get("detail", "")


# ------------------------------------------------------------------------------
# Test Case 3: Wrong TOTP Code
# ------------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_login_wrong_totp_code():
    transport = ASGITransport(app=app)
    async with AsyncClient(base_url="http://testserver", transport=transport) as ac:
        # Step 1: Send the initial request without TOTP to trigger TOTP setup.
        initial_payload = {"email": "test@example.com", "password": "testpassword"}
        response1 = await ac.post("/auth/login", json=initial_payload)
        # Expect a TOTP setup prompt.
        assert response1.status_code == 200, f"Initial login failed: {response1.text}"
        data1 = response1.json()
        assert data1.get("totp_setup") is True, "Expected a TOTP setup prompt"
        assert "qr_code_url" in data1, (
            "Response should contain a qr_code_url for TOTP setup"
        )

        # Parse the TOTP secret from the provisioning URL.
        provisioning_url = data1["qr_code_url"]
        parsed_url = urllib.parse.urlparse(provisioning_url)
        query_params = urllib.parse.parse_qs(parsed_url.query)
        secret = query_params.get("secret", [None])[0]
        assert secret is not None, "TOTP secret not found in the provisioning URL"

        # Step 2: Instead of a correct TOTP code, use an incorrect one.
        wrong_totp_code = "000000"  # deliberately incorrect
        followup_payload = {
            "email": "test@example.com",
            "password": "testpassword",
            "totp_code": wrong_totp_code,
        }
        response2 = await ac.post("/auth/login", json=followup_payload)
        # Expect 401 Unauthorized, and an error message about the invalid TOTP code.
        assert response2.status_code == 401, (
            f"Expected 401 for wrong TOTP, got {response2.status_code}"
        )
        data2 = response2.json()
        assert "Invalid TOTP code" in data2.get("detail", "")


# ------------------------------------------------------------------------------
# Test Case 4: Missing TOTP Code When It's Required
# ------------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_login_missing_totp_when_required():
    transport = ASGITransport(app=app)
    async with AsyncClient(base_url="http://testserver", transport=transport) as ac:
        # Step 1: Send initial login to trigger TOTP setup.
        initial_payload = {"email": "test@example.com", "password": "testpassword"}
        response1 = await ac.post("/auth/login", json=initial_payload)
        assert response1.status_code == 200
        data1 = response1.json()
        assert data1.get("totp_setup") is True

        # Now simulate a subsequent login without providing the TOTP code.
        followup_payload = {"email": "test@example.com", "password": "testpassword"}
        response2 = await ac.post("/auth/login", json=followup_payload)
        # Depending on your endpoint logic, this may respond with a 400 or 401
        assert response2.status_code in (400, 401), (
            "Expected an error when TOTP is omitted after setup"
        )
        data2 = response2.json()
        assert "TOTP" in data2.get("detail", ""), (
            "Expected TOTP requirement message in error detail"
        )


# ------------------------------------------------------------------------------
# Test Case 5: Successful Login (for completeness)
# ------------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_successful_login():
    transport = ASGITransport(app=app)
    async with AsyncClient(base_url="http://testserver", transport=transport) as ac:
        # Step 1: Trigger initial TOTP setup.
        payload = {"email": "test@example.com", "password": "testpassword"}
        response1 = await ac.post("/auth/login", json=payload)
        assert response1.status_code == 200
        data1 = response1.json()
        assert data1.get("totp_setup") is True

        # Parse the TOTP secret from the provisioning URL.
        provisioning_url = data1["qr_code_url"]
        parsed_url = urllib.parse.urlparse(provisioning_url)
        query_params = urllib.parse.parse_qs(parsed_url.query)
        secret = query_params.get("secret", [None])[0]
        assert secret is not None

        # Generate correct TOTP code.
        totp = pyotp.TOTP(secret)
        totp_code = totp.now()

        # Step 2: Send follow-up request with the valid TOTP code.
        followup_payload = {
            "email": "test@example.com",
            "password": "testpassword",
            "totp_code": totp_code,
        }
        response2 = await ac.post("/auth/login", json=followup_payload)
        assert response2.status_code == 200, f"Follow-up login failed: {response2.text}"
        data2 = response2.json()
        assert "access_token" in data2, (
            "Access token not returned upon successful login"
        )
        assert data2.get("token_type") == "bearer"

