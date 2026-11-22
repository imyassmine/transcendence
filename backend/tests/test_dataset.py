from pathlib import Path

from ia.links.dataset import DeletionDataset

DS = DeletionDataset.from_file(Path("ia/links/data/jdm_sites.json"))


def test_subdomain_hit():
    hit = DS.lookup("mail.netflix.com")
    assert hit and "netflix.com" in hit["url"]
    assert hit["instructions"]


def test_name_fallback():
    assert DS.lookup("domaine-inconnu.xyz", name="Spotify")


def test_miss():
    assert DS.lookup("domaine-inconnu.xyz") is None


def test_entries_without_url_ignored():
    ds = DeletionDataset([{"name": "NoUrl", "domains": ["nourl.com"]}])
    assert ds.lookup("nourl.com") is None
