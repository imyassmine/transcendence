from ia.links.domains import normalize_domain, registrable_domain, parent_domains


def test_normalize():
    assert normalize_domain("https://WWW.Netflix.com/fr/") == "netflix.com"
    assert normalize_domain("noreply@mail.spotify.com") == "mail.spotify.com"
    assert normalize_domain("  leboncoin.fr  ") == "leboncoin.fr"
    assert normalize_domain("http://shop.example.com:8080/x") == "shop.example.com"


def test_registrable():
    assert registrable_domain("accounts.google.co.uk") == "google.co.uk"
    assert registrable_domain("netflix.com") == "netflix.com"


def test_parents():
    assert parent_domains("a.b.netflix.com") == ["a.b.netflix.com", "b.netflix.com", "netflix.com"]
    assert parent_domains("netflix.com") == ["netflix.com"]
