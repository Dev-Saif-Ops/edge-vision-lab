"""Hiding secrets in URLs before they reach a log: a block-list vs an allow-list.

Every URL below contains the marker SECRET where a password, token or stream key would be.
A redactor passes a URL only if SECRET no longer appears in its output.

  block-list   hide the parts you know are secret: "user:pass@" and "?query"
  allow-list   keep only what you know is safe: scheme, host, port, and a plain path for
               rtsp/file URLs. Everything else becomes ***.

Run:  uv run python 06-url-redaction/redaction.py
"""

import re

URLS = [
    "rtsp://admin:SECRET@10.0.0.21:554/Streaming/Channels/101",  # user info
    "rtsp://admin:P@SECRET@10.0.0.21/live",  # '@' inside the password
    "rtsp://admin:pa/SECRET@10.0.0.21/live",  # '/' inside the password
    "rtsp://10.0.0.21/live?user=admin&password=SECRET",  # credentials in the query
    "rtsp://10.0.0.21/live?user=ops@example.com&password=SECRET",  # '@' inside the query
    "rtsp://10.0.0.21/live;password=SECRET",  # path parameter
    "rtsp://10.0.0.21:554/user=admin&password=SECRET&channel=1",  # credentials in the path
    "http://10.0.0.21/videostream.cgi/user=admin/pwd=SECRET",  # path segments
    "http://cam.local/video.mjpg#token=SECRET",  # fragment
    "rtmp://live.example.com/app/SECRET",  # stream key as a plain path
    "rtsp:/10.0.0.21/live?password=SECRET",  # typo: one slash
    "10.0.0.21/live?password=SECRET",  # no scheme at all
]


def block_list(url: str) -> str:
    url = re.sub(r"//[^/@]+@", "//***@", url)  # user:pass@
    return re.sub(r"\?.*$", "?***", url)  # query string


SCHEME = re.compile(r"[A-Za-z][A-Za-z0-9+.\-]*")
HOST = re.compile(r"(\[[0-9A-Fa-f:.]+\]|[A-Za-z0-9.\-]+)(:\d{1,5})?")
PLAIN_PATH = re.compile(r"(/[A-Za-z0-9._\-]*)*")
PLAIN_FILE = re.compile(r"[A-Za-z0-9._\-/]+")
PATH_SAFE_SCHEMES = {"rtsp", "rtsps", "file"}


def allow_list(url: str) -> str:
    scheme, sep, rest = url.partition("://")
    if not sep or not SCHEME.fullmatch(scheme):
        return url if PLAIN_FILE.fullmatch(url) else "***"  # not a URL we understand
    userinfo = ""
    if "@" in rest:
        before, _, rest = rest.rpartition("@")
        if set(before) & set("?=&#;"):
            return f"{scheme}://***"  # the '@' may be inside a query: ambiguous, hide it all
        userinfo = "***@"
    host, slash, path = rest.partition("/")
    if not HOST.fullmatch(host):
        return f"{scheme}://***"
    tail = f"/{path}" if slash else ""
    if tail and (scheme.lower() not in PATH_SAFE_SCHEMES or not PLAIN_PATH.fullmatch(tail)):
        tail = "/***"
    return f"{scheme}://{userinfo}{host}{tail}"


if __name__ == "__main__":
    leaks = {"block-list": 0, "allow-list": 0}
    for url in URLS:
        print(url)
        for name, fn in (("block-list", block_list), ("allow-list", allow_list)):
            out = fn(url)
            leaked = "SECRET" in out
            leaks[name] += leaked
            print(f"   {name:<10} {'LEAK ' if leaked else 'safe '} {out}")
        print()
    total = len(URLS)
    print(f"block-list leaked {leaks['block-list']}/{total}; allow-list leaked {leaks['allow-list']}/{total}")
    print("A block-list has to imagine every place a secret can hide. An allow-list only has to")
    print("know what a safe URL looks like.")
