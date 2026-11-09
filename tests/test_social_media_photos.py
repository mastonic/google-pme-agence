from unittest.mock import Mock, patch

from backend.services.social_media_photos import (
    discover_official_accounts, discover_apify_photo_candidates,
)


def test_official_accounts_only_from_website():
    response = Mock(status_code=200, content=b"<html></html>", text=(
        '<a href="https://www.instagram.com/frootybowl/">Instagram</a>'
        '<a href="https://www.facebook.com/frootybowl/">Facebook</a>'
        '<a href="https://www.instagram.com/explore/">Explore</a>'
    ))
    response.headers = {"Content-Type": "text/html"}
    with patch("socket.getaddrinfo", return_value=[(2, 1, 6, "", ("8.8.8.8", 443))]), \
         patch("requests.get", return_value=response):
        accounts = discover_official_accounts("https://frootybowl.example/")
    assert {a["platform"] for a in accounts} == {"instagram", "facebook"}
    assert all(a["verified"] == "linked_from_official_website" for a in accounts)


def test_private_website_is_not_fetched():
    with patch("requests.get") as get:
        assert discover_official_accounts("https://127.0.0.1/") == []
        get.assert_not_called()


def test_apify_candidates_not_auto_approved():
    accounts = [{"platform": "instagram", "handle": "frootybowl",
                 "url": "https://www.instagram.com/frootybowl/"}]
    response = Mock()
    response.raise_for_status.return_value = None
    response.json.return_value = [
        {"url": "https://www.instagram.com/p/abc/", "ownerUsername": "frootybowl",
         "displayUrl": "https://cdn.example/image.jpg"},
        {"url": "https://www.instagram.com/p/xyz/", "ownerUsername": "other",
         "displayUrl": "https://cdn.example/wrong.jpg"},
    ]
    with patch.dict("os.environ", {"APIFY_TOKEN": "test", "SOCIAL_PHOTOS_APIFY_ACTOR_ID": "user~actor"}), \
         patch("requests.post", return_value=response):
        photos = discover_apify_photo_candidates(accounts)
    assert len(photos) == 1
    assert photos[0]["approved_for_site"] is False
    assert photos[0]["rights_status"] == "unverified"
