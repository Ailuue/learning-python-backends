def test_create_category(client, auth_headers):
    response = client.post(
        "/categories/",
        headers=auth_headers,
        json={"name": "Work", "description": "Work-related links"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Work"
    assert data["description"] == "Work-related links"


def test_create_duplicate_category_rejected(client, auth_headers):
    client.post("/categories/", headers=auth_headers, json={"name": "Work"})
    response = client.post(
        "/categories/", headers=auth_headers, json={"name": "Work"}
    )
    assert response.status_code == 400


def test_categories_isolated_per_user(client, auth_headers, other_auth_headers):
    client.post("/categories/", headers=auth_headers, json={"name": "Work"})
    client.post("/categories/", headers=other_auth_headers, json={"name": "Personal"})

    response = client.get("/categories/", headers=auth_headers)
    names = {c["name"] for c in response.json()}
    assert names == {"Work"}


def test_update_category(client, auth_headers):
    created = client.post(
        "/categories/", headers=auth_headers, json={"name": "Work"}
    ).json()
    response = client.patch(
        f"/categories/{created['id']}",
        headers=auth_headers,
        json={"description": "Office stuff"},
    )
    assert response.status_code == 200
    assert response.json()["description"] == "Office stuff"


def test_delete_category(client, auth_headers):
    created = client.post(
        "/categories/", headers=auth_headers, json={"name": "Temp"}
    ).json()
    response = client.delete(f"/categories/{created['id']}", headers=auth_headers)
    assert response.status_code == 204
    response = client.get(f"/categories/{created['id']}", headers=auth_headers)
    assert response.status_code == 404


def test_get_other_users_category_returns_404(
    client, auth_headers, other_auth_headers
):
    created = client.post(
        "/categories/", headers=other_auth_headers, json={"name": "Private"}
    ).json()
    response = client.get(f"/categories/{created['id']}", headers=auth_headers)
    assert response.status_code == 404


def test_bookmark_can_reference_category(client, auth_headers):
    category = client.post(
        "/categories/", headers=auth_headers, json={"name": "Reading"}
    ).json()
    response = client.post(
        "/bookmarks/",
        headers=auth_headers,
        json={"url": "https://example.com", "category_id": category["id"]},
    )
    assert response.status_code == 201
    assert response.json()["category_id"] == category["id"]
