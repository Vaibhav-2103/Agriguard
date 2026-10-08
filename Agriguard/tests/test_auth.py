import pytest

def test_user_registration(client):
    res = client.post("/auth/register", json={
        "name": "Anil Sharma",
        "email": "anil@kisan.com",
        "password": "strongpassword123",
        "role": "farmer",
        "preferred_language": "hi"
    })
    assert res.status_code == 201
    data = res.json()
    assert "access_token" in data
    assert data["user"]["name"] == "Anil Sharma"
    assert data["user"]["email"] == "anil@kisan.com"
    assert data["user"]["role"] == "farmer"

def test_duplicate_registration_rejected(client):
    client.post("/auth/register", json={
        "name": "Dup User",
        "email": "dup@kisan.com",
        "password": "strongpassword123",
        "role": "farmer"
    })
    res = client.post("/auth/register", json={
        "name": "Dup User",
        "email": "dup@kisan.com",
        "password": "strongpassword123",
        "role": "farmer"
    })
    assert res.status_code == 400
    assert "already exists" in res.json()["detail"]

def test_login_success(client):
    client.post("/auth/register", json={
        "name": "Login User",
        "email": "loginuser@kisan.com",
        "password": "strongpassword123",
        "role": "farmer"
    })
    res = client.post("/auth/login", json={
        "email": "loginuser@kisan.com",
        "password": "strongpassword123"
    })
    assert res.status_code == 200
    assert "access_token" in res.json()

def test_login_invalid_password(client):
    client.post("/auth/register", json={
        "name": "Invalid Pass User",
        "email": "invalidpass@kisan.com",
        "password": "correctpassword",
        "role": "farmer"
    })
    res = client.post("/auth/login", json={
        "email": "invalidpass@kisan.com",
        "password": "wrongpassword"
    })
    assert res.status_code == 401
    assert "Incorrect email or password" in res.json()["detail"]

def test_get_current_user_me(client, test_farmer, farmer_token):
    res = client.get("/auth/me", headers={"Authorization": f"Bearer {farmer_token}"})
    assert res.status_code == 200
    assert res.json()["email"] == test_farmer.email
