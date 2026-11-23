from urllib.parse import urlsplit
import tldextract # type: ignore


_extract = tldextract.TLDExtract(suffix_list_urls=(), cache_dir=None)

def normalize_domain(raw: str) -> str:
    """'https://WWW.Netflix.com/fr/' -> 'netflix.com'
    'noreply@mail.spotify.com'   -> 'mail.spotify.com'"""
    raw = raw.strip().lower()
    if "@" in raw and "://" not in raw:          
        raw = raw.rsplit("@", 1)[1]
    if "://" not in raw:
        raw = "//" + raw
    host = urlsplit(raw).hostname or ""
    host = host.rstrip(".")
    return host.removeprefix("www.")


def registrable_domain(host: str) -> str:
    """'accounts.google.co.uk' -> 'google.co.uk'"""
    return _extract(host).top_domain_under_public_suffix or host


def parent_domains(host: str) -> list[str]:
    """'a.b.netflix.com' -> ['a.b.netflix.com', 'b.netflix.com', 'netflix.com']"""
    base = registrable_domain(host)
    out = []
    cur = host
    while cur != base and "." in cur:
        out.append(cur)
        cur = cur.split(".", 1)[1]
    out.append(base)
    return out

