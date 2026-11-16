#!/usr/bin/env python3
"""Fail-closed static check for the version-aware QR Scanner support-site draft.

Run before merging or publishing; this does not approve privacy/legal language.
No network, third-party packages, or Apple account modifications.
"""
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parent
PAGES = ("index.html", "support.html", "privacy.html", "review-qr.html")


class Links(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.urls = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "a":
            self.urls.append(attrs.get("href"))
        if tag == "link" and attrs.get("rel") == "stylesheet":
            self.urls.append(attrs.get("href"))


def require(condition, reason):
    if not condition:
        raise AssertionError(reason)


def main():
    for name in PAGES:
        source = ROOT / name
        require(source.is_file(), f"Missing page: {name}")
        content = source.read_text(encoding="utf-8")
        require('<meta name="viewport"' in content, f"Missing mobile viewport: {name}")
        require('<html lang="en">' in content, f"Missing language: {name}")
        parser = Links()
        parser.feed(content)
        for url in parser.urls:
            require(bool(url), f"Empty link in {name}")
            parsed = urlsplit(url)
            if parsed.scheme:
                require(parsed.scheme == "https", f"Insecure external URL {url} in {name}")
            else:
                require(not parsed.netloc, f"Unexpected URL {url} in {name}")
                require((ROOT / parsed.path).is_file(),
                        f"Broken local URL {url} in {name}")
        print("PASS_STATIC_LINKS", name, len(parser.urls))

    support = (ROOT / "support.html").read_text(encoding="utf-8")
    privacy = (ROOT / "privacy.html").read_text(encoding="utf-8")
    for phrase in ("Build 29", "Restore Purchases", "Manage subscriptions",
                   "https://apps.apple.com/account/subscriptions",
                   "https://reportaproblem.apple.com/", "No automatic renewal",
                   "complete locally saved History"):
        # The lifetime disclosure is phrased as 'does not auto-renew' in help.
        if phrase == "No automatic renewal":
            phrase = "does not auto-renew"
        require(phrase in support, f"Missing essential Pro support claim: {phrase}")
    require("no subscription, trial, in-app purchase or Restore screen" not in support,
            "Vague timeless no-IAP claim would contradict newer paid builds")

    for phrase in ("Build 29", "paid-capable", "Apple StoreKit",
                   "complete saved history", "Open Food Facts",
                   "Apple processes payment information",
                   "Earlier pre-release / TestFlight versions"):
        require(phrase in privacy, f"Missing version-aware privacy disclosure: {phrase}")
    require("The first public iPhone release is <strong>free, with no advertisements" not in privacy,
            "Old free-only policy incorrectly applied to paid-capable releases")
    require("TestFlight use Apple's Sandbox" in support,
            "TestFlight support must distinguish Sandbox from real charges")
    # The published support channel is a PUBLIC GitHub issue tracker. Never
    # imply that posting legacy cloud-account identifiers there is private.
    require("Privacy and earlier test-account data" in support,
            "Missing legacy account/cloud-data privacy support guidance")
    require("Request%20a%20private%20privacy-support%20channel" in support,
            "Missing safe non-identifying intake request")
    require("do not place your email address, account identifier" in support,
            "Public issue tracker must warn against sharing sensitive identifiers")
    require("A secure contact and verification process must be arranged" in support,
            "Do not imply a private data-deletion service is already configured")
    require("before account or cloud records can be reviewed or deleted" in privacy,
            "Privacy policy must not promise deletion without secure verification")
    require("public support issue" in privacy and "support.html" in privacy,
            "Privacy notice must route deletion questions safely")
    print("PASS_LEGACY_TEST_ACCOUNT_PRIVACY_REQUEST_SAFETY")
    print("PASS_VERSION_AWARE_PURCHASE_AND_PRIVACY_DISCLOSURES")
    print("LOCAL_ONLY_NO_PUBLICATION_NO_APPLE_WRITE")


if __name__ == "__main__":
    main()
