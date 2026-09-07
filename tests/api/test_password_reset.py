"""
Requirement:
    "The application should allow users to reset their password using their registered
     email address. The reset link expires after 30 minutes."

Acceptance Criterion [Confirmed - Requirement]:
    "A registered user can submit a password-reset request."

Test Case:
    "Verify that a registered user can request a password reset through the
     password-reset API."

Automation Type: API (Python / requests / pytest)

Traceability:
    Requirement -> Acceptance Criterion ("A registered user can submit a password-reset
    request.") -> Test Case (above) -> Automation Type: API -> this script
    (tests/api/test_password_reset.py).

Provenance note:
    The endpoint, header, request body, expected status code, and expected response body
    used below are supplied directly as [Confirmed - Supplied] test input (not discovered
    by api-agent, and not verified against a live/deployed application). No endpoints,
    fields, headers, status codes, or response fields beyond what was supplied have been
    added. The endpoint requires no authentication per the supplied findings, so none is
    implemented here.
"""

import requests

# [Confirmed - Supplied] Endpoint under test.
PASSWORD_RESET_URL = "https://example.test/api/password-reset"

# [Confirmed - Supplied] Request header.
REQUEST_HEADERS = {"Content-Type": "application/json"}

# [Confirmed - Supplied] Request body.
REQUEST_BODY = {"email": "registered-user@example.com"}

# [Confirmed - Supplied] Expected response.
EXPECTED_STATUS_CODE = 200
EXPECTED_RESPONSE_BODY = {"message": "If an account exists, instructions have been sent."}


def test_registered_user_can_request_password_reset():
    """
    Verify that a registered user can request a password reset through the
    password-reset API.

    AC: "A registered user can submit a password-reset request."
    """
    response = requests.post(
        PASSWORD_RESET_URL,
        json=REQUEST_BODY,
        headers=REQUEST_HEADERS,
    )

    assert response.status_code == EXPECTED_STATUS_CODE, (
        f"Expected status {EXPECTED_STATUS_CODE}, got {response.status_code}: "
        f"{response.text}"
    )

    assert response.json() == EXPECTED_RESPONSE_BODY, (
        f"Expected response body {EXPECTED_RESPONSE_BODY}, got {response.json()}"
    )
