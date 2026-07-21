"""Fetch the real-world evaluation dataset (run once).

UCI SMS Spam Collection (5,574 real SMS, ham/spam) — a standard public
benchmark. Free for research use. Saved to tests/realworld/sms.tsv, which
is gitignored (we do not redistribute the dataset).

  python tests/realworld/fetch.py
"""
import ssl
import sys
import urllib.request
from pathlib import Path

OUT = Path(__file__).resolve().parent / "sms.tsv"
URLS = [
    "https://raw.githubusercontent.com/justmarkham/pycon-2016-tutorial/master/data/sms.tsv",
]


def main() -> None:
    ctx = ssl.create_default_context()
    for url in URLS:
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            data = urllib.request.urlopen(req, timeout=30, context=ctx).read()
            OUT.write_bytes(data)
            n = len(OUT.read_text(encoding="utf-8", errors="replace").splitlines())
            print(f"saved {OUT} ({n} messages)")
            return
        except Exception as e:
            print(f"failed {url}: {type(e).__name__} {e}")
    print("could not download dataset"); sys.exit(1)


if __name__ == "__main__":
    main()
