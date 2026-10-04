"""Hiding secrets in URLs before they reach a log: three attempts, each one smarter, one safe.

Every URL below carries a secret (a password, token, stream key or stream alias). A redactor
passes a URL only if the secret no longer appears in its output.

  block-list        hide the parts you know are secret: "user:pass@" and "?query"
  path-keeping      an allow-list: keep scheme, host, port and a plain-looking path for rtsp
  allow-list        URLs; everything else becomes ***
  shortest          keep only scheme and a host that really looks like a host
  allow-list        (IP, localhost or a dotted name). Everything after the host is /***.

The middle one looks right and passes the first twelve URLs. The last five are why it isn't:
real devices put secrets in places that look perfectly safe.

Run:  uv run python 06-url-redaction/redaction.py
"""

import re

# (url, the secret hidden in it, what makes it tricky)
URLS = [
    ("rtsp://admin:SECRET@10.0.0.21:554/Streaming/Channels/101", "SECRET", "user info"),
    ("rtsp://admin:P@SECRET@10.0.0.21/live", "SECRET", "'@' inside the password"),
    ("rtsp://admin:pa/SECRET@10.0.0.21/live", "SECRET", "'/' inside the password"),
    ("rtsp://10.0.0.21/live?user=admin&password=SECRET", "SECRET", "credentials in the query"),
    ("rtsp://10.0.0.21/live?user=ops@example.com&password=SECRET", "SECRET", "'@' inside the query"),
    ("rtsp://10.0.0.21/live;password=SECRET", "SECRET", "path parameter"),
    ("rtsp://10.0.0.21:554/user=admin&password=SECRET&channel=1", "SECRET", "credentials in the path"),
    ("http://10.0.0.21/videostream.cgi/user=admin/pwd=SECRET", "SECRET", "path segments"),
    ("http://cam.local/video.mjpg#token=SECRET", "SECRET", "fragment"),
    ("rtmp://live.example.com/app/SECRET", "SECRET", "stream key as a plain path"),
    ("rtsp:/10.0.0.21/live?password=SECRET", "SECRET", "typo: one slash"),
    ("10.0.0.21/live?password=SECRET", "SECRET", "no scheme at all"),
    # The paths below look harmless. They aren't.
    ("rtsp://192.168.1.1:7447/5nPr7RCmueGTKMP7", "5nPr7RCmueGTKMP7", "the stream alias IS the secret"),
    ("rtsps://192.168.1.1:7441/5nPr7RCmueGTKMP7", "5nPr7RCmueGTKMP7", "same, over TLS"),
    ("rtsp://10.0.0.21:554/admin/Pw9SECRET/ch0.h264", "Pw9SECRET", "password as a plain path segment"),
    ("rtsp://admin:12345/Streaming/Channels/101", "12345", "forgot '@host': looks like host:port"),
    ("live.example.com/app/live_12_SECRETKEY", "SECRETKEY", "stream key, no scheme"),
]


def block_list(url: str) -> str:
    url = re.sub(r"//[^/@]+@", "//***@", url)  # user:pass@
    return re.sub(r"\?.*$", "?***", url)  # query string


SCHEME = re.compile(r"[A-Za-z][A-Za-z0-9+.\-]*")
AMBIGUOUS = set("?=&#;")  # an '@' after one of these may be inside a query or parameter


def path_keeping_allow_list(url: str) -> str:
    """My first allow-list. Keeps a plain-looking path for rtsp, because paths look useful."""
    host_re = re.compile(r"(\[[0-9A-Fa-f:.]+\]|[A-Za-z0-9.\-]+)(:\d{1,5})?")
    plain_path = re.compile(r"(/[A-Za-z0-9._\-]*)*")
    scheme, sep, rest = url.partition("://")
    if not sep or not SCHEME.fullmatch(scheme):
        return url if re.fullmatch(r"[A-Za-z0-9._\-/]+", url) else "***"
    userinfo = ""
    if "@" in rest:
        before, _, rest = rest.rpartition("@")
        if set(before) & AMBIGUOUS:
            return f"{scheme}://***"
        userinfo = "***@"
    host, slash, path = rest.partition("/")
    if not host_re.fullmatch(host):
        return f"{scheme}://***"
    tail = f"/{path}" if slash else ""
    if tail and (scheme.lower() not in {"rtsp", "rtsps"} or not plain_path.fullmatch(tail)):
        tail = "/***"
    return f"{scheme}://{userinfo}{host}{tail}"


def shortest_allow_list(url: str) -> str:
    """Keep only what a log line needs to say which device failed: scheme and host."""
    host_re = re.compile(
        r"(\d{1,3}(\.\d{1,3}){3}|\[[0-9A-Fa-f:.]+\]|localhost|[A-Za-z0-9\-]+(\.[A-Za-z0-9\-]+)+)"
        r"(:\d{1,5})?"
    )
    scheme, sep, rest = url.partition("://")
    if not sep or not SCHEME.fullmatch(scheme):
        return url if re.fullmatch(r"(/|\./|\.\./)[A-Za-z0-9._\-/]*", url) else "***"
    userinfo = ""
    if "@" in rest:
        before, _, rest = rest.rpartition("@")
        if set(before) & AMBIGUOUS:
            return f"{scheme}://***"
        userinfo = "***@"
    host, slash, path = rest.partition("/")
    if not host_re.fullmatch(host):
        return f"{scheme}://***"  # "admin:12345" is not a host, whatever it looks like
    return f"{scheme}://{userinfo}{host}{'/***' if slash and path else ''}"


REDACTORS = {
    "block-list": block_list,
    "path-keeping": path_keeping_allow_list,
    "shortest": shortest_allow_list,
}


def leaks(fn: object) -> list[str]:
    """URLs whose secret survives this redactor."""
    return [url for url, secret, _ in URLS if secret in fn(url)]  # type: ignore[operator]


if __name__ == "__main__":
    for url, secret, why in URLS:
        print(f"{url}\n   ({why})")
        for name, fn in REDACTORS.items():
            out = fn(url)
            print(f"   {name:<13} {'LEAK ' if secret in out else 'safe '} {out}")
        print()
    total = len(URLS)
    for name, fn in REDACTORS.items():
        print(f"{name:<13} leaked {len(leaks(fn)):2d}/{total}")
    print("\nThe path-keeping allow-list looked safe until devices hid secrets in plain-looking paths.")
    print("The most secure allow-list is the shortest one: keep only what you need.")
