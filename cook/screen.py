#!/usr/bin/env python3
"""Just enough of the served companion document to judge what a designer sees."""
from __future__ import annotations

from html.parser import HTMLParser

VOID_TAGS = {"area", "base", "br", "col", "embed", "hr", "img", "input",
             "link", "meta", "param", "source", "track", "wbr"}

PLACEHOLDER_HEADING = "brainstorm companion"


class Screen(HTMLParser):
    """Just enough of the served document to tell a screen from the shell."""

    def __init__(self) -> None:
        super().__init__()
        self.headings: list[str] = []
        self.tags: set[str] = set()
        self.rankable_elements: set[str] = set()
        # element id -> {"drawn": bool, "offsite": [src]}. A thumbnail is only
        # a thumbnail if something actually paints in it.
        self.shots: dict[str, dict] = {}
        self._in_heading = False
        self._depth = 0
        self._decision_rows: list[tuple[str, int]] = []
        self._shot = ""
        self._shot_depth = 0

    def handle_starttag(self, tag: str, attrs: list) -> None:
        self.tags.add(tag)
        values = dict(attrs)
        classes = str(values.get("class") or "").split()
        element = str(values.get("data-element") or "").strip()
        if "dh-fb" in classes and element:
            self._decision_rows.append((element, self._depth))
        if self._decision_rows and "data-rank" in values:
            self.rankable_elements.add(self._decision_rows[-1][0])
        if "dh-shot" in classes and values.get("data-el"):
            self._shot = str(values["data-el"])
            self._shot_depth = self._depth
            self.shots.setdefault(self._shot, {"drawn": False, "offsite": []})
        if self._shot:
            shot = self.shots[self._shot]
            source = str(values.get("src") or "")
            if tag == "img" and source.startswith("data:"):
                shot["drawn"] = True
            elif tag == "img" and source:
                # The companion serves from its own session directory, so a
                # relative src resolves to nothing and paints white.
                shot["offsite"].append(source)
            elif tag == "svg" or "dh-shot-inner" in classes:
                shot["drawn"] = True
        if tag in ("h1", "h2"):
            self._in_heading = True
        if tag not in VOID_TAGS:
            self._depth += 1

    def handle_endtag(self, tag: str) -> None:
        if tag not in VOID_TAGS:
            self._depth = max(0, self._depth - 1)
            while self._decision_rows and self._decision_rows[-1][1] >= self._depth:
                self._decision_rows.pop()
            if self._shot and self._shot_depth >= self._depth:
                self._shot = ""
        if tag in ("h1", "h2"):
            self._in_heading = False

    def handle_data(self, data: str) -> None:
        if self._in_heading and data.strip():
            self.headings.append(data.strip().lower())
