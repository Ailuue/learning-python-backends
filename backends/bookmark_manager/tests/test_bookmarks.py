def test_create_bookmark_minimal(client, auth_headers):
    response = client.post(
        "/bookmarks/",
        headers=auth_headers,
        json={"url": "https://example.com"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["url"].startswith("https://example.com")
    assert data["title"] == data["url"]
    assert data["favorite"] is False
    assert data["tags"] == []


def test_create_bookmark_with_tags(client, auth_headers):
    response = client.post(
        "/bookmarks/",
        headers=auth_headers,
        json={
            "url": "https://example.com/foo",
            "title": "Foo Page",
            "description": "A page about foo",
            "favorite": True,
            "tags": ["python", "tutorial"],
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Foo Page"
    assert data["favorite"] is True
    assert {t["name"] for t in data["tags"]} == {"python", "tutorial"}


def test_create_bookmark_invalid_url(client, auth_headers):
    response = client.post(
        "/bookmarks/",
        headers=auth_headers,
        json={"url": "not-a-url"},
    )
    assert response.status_code == 422


def test_create_bookmark_without_auth(client):
    response = client.post("/bookmarks/", json={"url": "https://example.com"})
    assert response.status_code == 401


def test_list_bookmarks_isolated_per_user(client, auth_headers, other_auth_headers):
    client.post("/bookmarks/", headers=auth_headers, json={"url": "https://a.test"})
    client.post("/bookmarks/", headers=other_auth_headers, json={"url": "https://b.test"})

    response = client.get("/bookmarks/", headers=auth_headers)
    assert response.status_code == 200
    bookmarks = response.json()
    assert len(bookmarks) == 1
    assert bookmarks[0]["url"].startswith("https://a.test")


def test_list_bookmarks_filter_favorite(client, auth_headers):
    client.post(
        "/bookmarks/",
        headers=auth_headers,
        json={"url": "https://a.test", "favorite": True},
    )
    client.post("/bookmarks/", headers=auth_headers, json={"url": "https://b.test"})

    response = client.get("/bookmarks/?favorite=true", headers=auth_headers)
    assert response.status_code == 200
    assert len(response.json()) == 1


def test_get_bookmark(client, auth_headers):
    created = client.post(
        "/bookmarks/", headers=auth_headers, json={"url": "https://example.com"}
    ).json()
    response = client.get(f"/bookmarks/{created['id']}", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["id"] == created["id"]


def test_get_other_users_bookmark_returns_404(client, auth_headers, other_auth_headers):
    created = client.post(
        "/bookmarks/", headers=other_auth_headers, json={"url": "https://secret.test"}
    ).json()
    response = client.get(f"/bookmarks/{created['id']}", headers=auth_headers)
    assert response.status_code == 404


def test_update_bookmark(client, auth_headers):
    created = client.post(
        "/bookmarks/", headers=auth_headers, json={"url": "https://example.com"}
    ).json()
    response = client.patch(
        f"/bookmarks/{created['id']}",
        headers=auth_headers,
        json={"title": "Updated", "favorite": True, "tags": ["new"]},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Updated"
    assert data["favorite"] is True
    assert {t["name"] for t in data["tags"]} == {"new"}


def test_delete_bookmark(client, auth_headers):
    created = client.post(
        "/bookmarks/", headers=auth_headers, json={"url": "https://example.com"}
    ).json()
    response = client.delete(f"/bookmarks/{created['id']}", headers=auth_headers)
    assert response.status_code == 204
    response = client.get(f"/bookmarks/{created['id']}", headers=auth_headers)
    assert response.status_code == 404


def test_bookmark_with_invalid_category_returns_404(client, auth_headers):
    response = client.post(
        "/bookmarks/",
        headers=auth_headers,
        json={"url": "https://example.com", "category_id": 9999},
    )
    assert response.status_code == 404


# ─── Click tracking (write-behind cache) ─────────────────────────────────────


def test_record_click_increments_redis(client, auth_headers):
    from app.redis_client import get_redis

    created = client.post(
        "/bookmarks/", headers=auth_headers, json={"url": "https://example.com"}
    ).json()
    bookmark_id = created["id"]

    response = client.post(f"/bookmarks/{bookmark_id}/click", headers=auth_headers)
    assert response.status_code == 204

    assert get_redis().get(f"bookmark_clicks:{bookmark_id}") == "1"

    # A second click should reach 2
    client.post(f"/bookmarks/{bookmark_id}/click", headers=auth_headers)
    assert get_redis().get(f"bookmark_clicks:{bookmark_id}") == "2"


def test_record_click_does_not_immediately_update_db(client, auth_headers):
    created = client.post(
        "/bookmarks/", headers=auth_headers, json={"url": "https://example.com"}
    ).json()
    bookmark_id = created["id"]

    client.post(f"/bookmarks/{bookmark_id}/click", headers=auth_headers)

    # DB still shows 0 until the flush task runs — that's the write-behind contract
    response = client.get(f"/bookmarks/{bookmark_id}", headers=auth_headers)
    assert response.json()["click_count"] == 0


def test_record_click_other_user_returns_404(client, auth_headers, other_auth_headers):
    other_bm = client.post(
        "/bookmarks/", headers=other_auth_headers, json={"url": "https://example.com"}
    ).json()
    response = client.post(
        f"/bookmarks/{other_bm['id']}/click", headers=auth_headers
    )
    assert response.status_code == 404


def test_record_click_requires_auth(client):
    response = client.post("/bookmarks/1/click")
    assert response.status_code == 401


def test_flush_bookmark_clicks_writes_to_db(client, auth_headers):
    from app.redis_client import get_redis
    from app.tasks import flush_bookmark_clicks

    created = client.post(
        "/bookmarks/", headers=auth_headers, json={"url": "https://example.com"}
    ).json()
    bookmark_id = created["id"]

    r = get_redis()
    for _ in range(3):
        r.incr(f"bookmark_clicks:{bookmark_id}")

    result = flush_bookmark_clicks()
    assert result == {"flushed": 3, "bookmarks": 1}

    # Redis counter cleared
    assert r.get(f"bookmark_clicks:{bookmark_id}") is None

    # DB now reflects the count
    response = client.get(f"/bookmarks/{bookmark_id}", headers=auth_headers)
    assert response.json()["click_count"] == 3


def test_flush_bookmark_clicks_accumulates(client, auth_headers):
    from app.redis_client import get_redis
    from app.tasks import flush_bookmark_clicks

    created = client.post(
        "/bookmarks/", headers=auth_headers, json={"url": "https://example.com"}
    ).json()
    bookmark_id = created["id"]
    r = get_redis()

    # First window: 2 clicks
    r.incr(f"bookmark_clicks:{bookmark_id}")
    r.incr(f"bookmark_clicks:{bookmark_id}")
    flush_bookmark_clicks()

    # Second window: 5 more clicks
    for _ in range(5):
        r.incr(f"bookmark_clicks:{bookmark_id}")
    flush_bookmark_clicks()

    response = client.get(f"/bookmarks/{bookmark_id}", headers=auth_headers)
    assert response.json()["click_count"] == 7


def test_flush_with_no_clicks_is_noop(session):
    from app.tasks import flush_bookmark_clicks

    assert flush_bookmark_clicks() == {"flushed": 0, "bookmarks": 0}


def test_flush_drops_clicks_for_deleted_bookmarks(client, auth_headers):
    from app.redis_client import get_redis
    from app.tasks import flush_bookmark_clicks

    created = client.post(
        "/bookmarks/", headers=auth_headers, json={"url": "https://example.com"}
    ).json()
    bookmark_id = created["id"]

    get_redis().incr(f"bookmark_clicks:{bookmark_id}")
    client.delete(f"/bookmarks/{bookmark_id}", headers=auth_headers)

    # Flush shouldn't blow up; should just log a warning and skip the missing row
    result = flush_bookmark_clicks()
    assert result == {"flushed": 0, "bookmarks": 1}
