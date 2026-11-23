import httpx
import pytest

from ia.links.fetcher import SafeFetcher, UnsafeURL

pytestmark = pytest.mark.anyio


@pytest.fixture
def anyio_backend():
    return "asyncio"


async def public(host):
    return ["93.184.216.34"]


def ip(addr):
    async def resolver(host):
        return [addr]
    return resolver


def fetcher(handler, resolver=public, **kw):
    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    return SafeFetcher(client=client, resolver=resolver, **kw)


def html(text, status=200, **headers):
    return httpx.Response(status, text=text, headers={"content-type": "text/html", **headers})


@pytest.mark.parametrize("addr", ["127.0.0.1", "10.0.0.5", "192.168.1.1", "172.16.0.1",
                                  "169.254.169.254", "0.0.0.0", "::1", "fd00::1"])
async def test_check_url_blocks_non_public_ips(addr):
    with pytest.raises(UnsafeURL):
        await fetcher(lambda r: html("x"), resolver=ip(addr)).check_url("https://evil.com/")


@pytest.mark.parametrize("url", ["file:///etc/passwd", "ftp://x.com/", "gopher://x.com/",
                                 "https://x.com:6379/", "https://x.com:22/", "https:///nohost"])
async def test_check_url_blocks_bad_scheme_port_host(url):
    with pytest.raises(UnsafeURL):
        await fetcher(lambda r: html("x")).check_url(url)


async def test_check_url_dns_failure():
    async def broken(host):
        raise OSError("nxdomain")
    with pytest.raises(UnsafeURL):
        await fetcher(lambda r: html("x"), resolver=broken).check_url("https://x.com/")


async def test_get_ok():
    page = await fetcher(lambda r: html("<p>hello</p>")).get("https://x.com/")
    assert page and page.status == 200 and "hello" in page.text


async def test_get_returns_none_when_unsafe():
    assert await fetcher(lambda r: html("x"), resolver=ip("127.0.0.1")).get("https://x.com/") is None


async def test_get_follows_redirect_and_returns_final_url():
    def handler(r):
        if r.url.path == "/old":
            return httpx.Response(301, headers={"location": "/new"})
        return html("final")
    page = await fetcher(handler).get("https://x.com/old")
    assert page and page.url == "https://x.com/new" and page.text == "final"


async def test_get_rechecks_ip_on_redirect():
    async def resolver(host):
        return ["127.0.0.1"] if host == "internal.x.com" else ["93.184.216.34"]

    def handler(r):
        if r.url.host == "x.com":
            return httpx.Response(302, headers={"location": "http://internal.x.com/admin"})
        return html("SECRET")
    assert await fetcher(handler, resolver=resolver).get("https://x.com/") is None


async def test_get_redirect_loop_gives_none():
    loop = lambda r: httpx.Response(302, headers={"location": "/loop"})
    assert await fetcher(loop, max_redirects=3).get("https://x.com/loop") is None


async def test_get_truncates_big_bodies():
    page = await fetcher(lambda r: html("a" * 5000), max_bytes=1000).get("https://x.com/")
    assert page and len(page.text) == 1000


async def test_get_ignores_binary_content():
    resp = lambda r: httpx.Response(200, content=b"\x89PNG", headers={"content-type": "image/png"})
    page = await fetcher(resp).get("https://x.com/logo.png")
    assert page and page.status == 200 and page.text == ""


async def test_get_keeps_404_status():
    page = await fetcher(lambda r: html("nope", 404)).get("https://x.com/missing")
    assert page and page.status == 404


async def test_get_network_error_gives_none():
    def boom(r):
        raise httpx.ConnectError("down")
    assert await fetcher(boom).get("https://x.com/") is None
