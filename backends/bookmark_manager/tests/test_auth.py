def test_register_user(client):
    response = client.post(
        "/auth/register",
        json={
            "email": "new@example.com",
            "username": "newuser",
            "password": "newpass123",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "new@example.com"
    assert data["username"] == "newuser"
    assert "password" not in data
    assert "hashed_password" not in data


def test_register_short_password_rejected(client):
    response = client.post(
        "/auth/register",
        json={"email": "x@example.com", "username": "shorty", "password": "short"},
    )
    assert response.status_code == 422


def test_register_invalid_email_rejected(client):
    response = client.post(
        "/auth/register",
        json={"email": "not-an-email", "username": "newuser", "password": "longenough"},
    )
    assert response.status_code == 422


def test_register_duplicate_email(client, user):
    response = client.post(
        "/auth/register",
        json={
            "email": "test@example.com",
            "username": "different",
            "password": "newpass123",
        },
    )
    assert response.status_code == 400


def test_register_duplicate_username(client, user):
    response = client.post(
        "/auth/register",
        json={
            "email": "different@example.com",
            "username": "testuser",
            "password": "newpass123",
        },
    )
    assert response.status_code == 400


def test_login_success(client, user):
    response = client.post(
        "/auth/token",
        data={"username": "testuser", "password": "testpass123"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_wrong_password(client, user):
    response = client.post(
        "/auth/token",
        data={"username": "testuser", "password": "wrongpassword"},
    )
    assert response.status_code == 401


def test_login_unknown_user(client):
    response = client.post(
        "/auth/token",
        data={"username": "ghost", "password": "irrelevant"},
    )
    assert response.status_code == 401


def test_me_with_valid_token(client, auth_headers):
    response = client.get("/auth/me", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["username"] == "testuser"


def test_me_without_token(client):
    response = client.get("/auth/me")
    assert response.status_code == 401


def test_me_invalid_token(client):
    response = client.get("/auth/me", headers={"Authorization": "Bearer not-a-real-token"})
    assert response.status_code == 401


def test_logout_blocklists_token(client, auth_headers):
    # Token works before logout
    assert client.get("/auth/me", headers=auth_headers).status_code == 200

    # Logout — server should add jti to blocklist
    response = client.post("/auth/logout", headers=auth_headers)
    assert response.status_code == 204

    # Same token should no longer work
    assert client.get("/auth/me", headers=auth_headers).status_code == 401


def test_logout_requires_auth(client):
    response = client.post("/auth/logout")
    assert response.status_code == 401


def test_new_login_after_logout_works(client, user, auth_headers):
    # Revoke the existing token
    client.post("/auth/logout", headers=auth_headers)

    # A fresh login should produce a new token that works
    login_res = client.post(
        "/auth/token",
        data={"username": "testuser", "password": "testpass123"},
    )
    assert login_res.status_code == 200
    new_token = login_res.json()["access_token"]
    me_res = client.get("/auth/me", headers={"Authorization": f"Bearer {new_token}"})
    assert me_res.status_code == 200
