"""Tests de ia/links/parsing.py (exercice 3a)."""

from ia.links.parsing import extract_links, find_privacy_emails, fold, score_link

BASE = "https://shop.example.com/fr/"


# ------------------------------------------------------------------ extract_links

def test_extract_links_absolute_and_text():
    html = '<a href="/account/delete">  Supprimer\n   mon <b>compte</b> </a>'
    assert extract_links(html, BASE) == [
        ("https://shop.example.com/account/delete", "Supprimer mon compte")]


def test_extract_links_relative_to_base():
    html = '<a href="privacy">Confidentialité</a>'
    assert extract_links(html, BASE) == [("https://shop.example.com/fr/privacy", "Confidentialité")]


def test_extract_links_keeps_mailto_as_is():
    html = '<a href="mailto:dpo@shop.example.com">DPO</a>'
    assert extract_links(html, BASE) == [("mailto:dpo@shop.example.com", "DPO")]


def test_extract_links_skips_useless_hrefs():
    html = ('<a href="#top">haut</a><a href="javascript:void(0)">x</a>'
            '<a href="tel:+33123456789">appel</a><a>sans href</a><a href="">vide</a>')
    assert extract_links(html, BASE) == []


def test_extract_links_aria_label_when_no_text():
    html = '<a href="/settings" aria-label="Paramètres du compte"><svg></svg></a>'
    assert extract_links(html, BASE) == [("https://shop.example.com/settings", "Paramètres du compte")]


def test_extract_links_malformed_html_does_not_crash():
    html = '<div><a href="/a">A</a><a href="/b">B<p></div></span><<<'
    links = extract_links(html, BASE)
    assert ("https://shop.example.com/a", "A") in links


# ------------------------------------------------------------------ fold

def test_fold():
    assert fold("Clôturer Mon COMPTE") == "cloturer mon compte"
    assert fold("Données personnelles") == "donnees personnelles"


# ------------------------------------------------------------------ score_link

def test_score_delete_plus_account_is_best():
    both = score_link("https://x.com/account/delete", "")
    only_delete = score_link("https://x.com/delete", "")
    only_account = score_link("https://x.com/account", "")
    assert both > only_delete > only_account > 0


def test_score_thresholds():
    assert score_link("https://x.com/account/delete", "") >= 7      # très probable
    assert score_link("https://x.com/p/123", "Supprimer mon compte") >= 7
    assert score_link("https://x.com/delete", "") >= 5              # probable
    assert 0 < score_link("https://x.com/settings", "") < 5         # pas assez seul


def test_score_text_accents_and_languages():
    assert score_link("https://x.com/p/1", "Clôturer mon compte") >= 7
    assert score_link("https://x.com/p/2", "Close account") >= 5
    assert score_link("https://x.com/p/3", "Désactiver le profil") >= 7


def test_score_privacy_pages_are_positive_but_below_delete():
    privacy = score_link("https://x.com/legal/privacy", "Politique de confidentialité")
    assert 0 < privacy < score_link("https://x.com/account/delete", "")


def test_score_noise_is_not_positive():
    assert score_link("https://x.com/blog/news", "Blog") <= 0
    assert score_link("https://x.com/login", "Se connecter") <= 0
    assert score_link("https://x.com/careers", "Jobs") <= 0


def test_score_underscore_equals_dash():
    assert score_link("https://x.com/close_account", "") == score_link("https://x.com/close-account", "")


# ------------------------------------------------------------------ find_privacy_emails

def test_find_privacy_emails_mailto_and_text():
    html = "<p>Écrivez à notre DPO : dpo@shop.example.com ou privacy@shop.example.com</p>"
    links = [("mailto:DPO@shop.example.com?subject=RGPD", "DPO")]
    assert find_privacy_emails(html, links) == ["dpo@shop.example.com", "privacy@shop.example.com"]


def test_find_privacy_emails_ignores_non_privacy():
    html = "<p>contact@shop.example.com, sav@shop.example.com, rgpd@shop.example.com</p>"
    assert find_privacy_emails(html, []) == ["rgpd@shop.example.com"]


def test_find_privacy_emails_empty():
    assert find_privacy_emails("<p>rien</p>", []) == []
