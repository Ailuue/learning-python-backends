def test_create_tag(client, auth_headers):
    response = client.post(
        "/tags/", headers=auth_headers, json={"name": "python"}
    )
    assert response.status_code == 201
    assert response.json()["name"] == "python"


def test_create_tag_idempotent(client, auth_headers):
    first = client.post("/tags/", headers=auth_headers, json={"name": "python"}).json()
    second = client.post("/tags/", headers=auth_headers, json={"name": "python"}).json()
    assert first["id"] == second["id"]


def test_tags_isolated_per_user(client, auth_headers, other_auth_headers):
    client.post("/tags/", headers=auth_headers, json={"name": "mine"})
    client.post("/tags/", headers=other_auth_headers, json={"name": "yours"})

    response = client.get("/tags/", headers=auth_headers)
    names = {t["name"] for t in response.json()}
    assert names == {"mine"}


def test_list_tags_includes_bookmark_tags(client, auth_headers):
    client.post(
        "/bookmarks/",
        headers=auth_headers,
        json={"url": "https://example.com", "tags": ["from-bookmark"]},
    )
    response = client.get("/tags/", headers=auth_headers)
    names = {t["name"] for t in response.json()}
    assert "from-bookmark" in names


def test_delete_tag(client, auth_headers):
    created = client.post(
        "/tags/", headers=auth_headers, json={"name": "todelete"}
    ).json()
    response = client.delete(f"/tags/{created['id']}", headers=auth_headers)
    assert response.status_code == 204


def test_delete_other_users_tag_returns_404(client, auth_headers, other_auth_headers):
    created = client.post(
        "/tags/", headers=other_auth_headers, json={"name": "private"}
    ).json()
    response = client.delete(f"/tags/{created['id']}", headers=auth_headers)
    assert response.status_code == 404
