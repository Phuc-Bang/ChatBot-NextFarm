#!/usr/bin/env python3
"""
robots.py - Kiem tra robots.txt truoc khi tai bat ky trang nao.

Quy chuan v2.0 DEC-028a: du an hop tac that voi doanh nghiep, khong duoc
tao rui ro phap ly / uy tin. Moi domain chi tai robots.txt mot lan roi cache.

Quy tac xu ly theo RFC 9309:
  - robots.txt tra 2xx  -> ap dung dung noi dung
  - robots.txt tra 4xx  -> coi nhu KHONG co han che (cho phep)
  - robots.txt tra 5xx  -> coi nhu CAM TOAN BO (than trong)
  - loi mang            -> coi nhu CAM TOAN BO (than trong)

Lua chon "than trong khi khong chac" giong voi nguyen tac thien lech an toan
cua Intent Router o muc 11.4: tha bo sot con hon lam sai.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from urllib.parse import urlsplit, urlunsplit
from urllib.robotparser import RobotFileParser

import requests

DEFAULT_TIMEOUT = 15


@dataclass
class RobotsDecision:
    """Ket qua kiem tra mot URL."""

    allowed: bool
    reason: str
    crawl_delay: float | None = None


@dataclass
class RobotsCache:
    """Cache robots.txt theo tung domain (scheme + netloc)."""

    user_agent: str
    timeout: int = DEFAULT_TIMEOUT
    _parsers: dict[str, RobotFileParser | None] = field(default_factory=dict)
    _reasons: dict[str, str] = field(default_factory=dict)

    # ------------------------------------------------------------------
    def _origin(self, url: str) -> str:
        parts = urlsplit(url)
        return urlunsplit((parts.scheme, parts.netloc, "", "", ""))

    def _load(self, origin: str) -> None:
        """Tai robots.txt cua mot origin. Ghi vao cache ke ca khi that bai."""
        robots_url = f"{origin}/robots.txt"
        try:
            resp = requests.get(
                robots_url,
                headers={"User-Agent": self.user_agent},
                timeout=self.timeout,
            )
        except requests.RequestException as exc:
            # Khong doc duoc robots.txt -> than trong, cam toan bo
            self._parsers[origin] = None
            self._reasons[origin] = f"khong tai duoc robots.txt ({type(exc).__name__})"
            return

        if 400 <= resp.status_code < 500:
            # Khong co robots.txt -> khong co han che
            parser = RobotFileParser()
            parser.parse([])
            self._parsers[origin] = parser
            self._reasons[origin] = f"khong co robots.txt (HTTP {resp.status_code})"
            return

        if resp.status_code >= 500:
            self._parsers[origin] = None
            self._reasons[origin] = f"robots.txt loi may chu (HTTP {resp.status_code})"
            return

        parser = RobotFileParser()
        resp.encoding = resp.encoding or "utf-8"
        parser.parse(resp.text.splitlines())
        self._parsers[origin] = parser
        self._reasons[origin] = f"doc duoc robots.txt (HTTP {resp.status_code})"

    # ------------------------------------------------------------------
    def check(self, url: str) -> RobotsDecision:
        """Tra ve quyet dinh cho mot URL cu the."""
        origin = self._origin(url)
        if origin not in self._parsers:
            self._load(origin)

        parser = self._parsers[origin]
        reason = self._reasons.get(origin, "")

        if parser is None:
            return RobotsDecision(allowed=False, reason=reason)

        allowed = parser.can_fetch(self.user_agent, url)
        delay = parser.crawl_delay(self.user_agent)
        return RobotsDecision(
            allowed=allowed,
            reason=reason if allowed else f"{reason}; robots.txt cam duong dan nay",
            crawl_delay=float(delay) if delay is not None else None,
        )
