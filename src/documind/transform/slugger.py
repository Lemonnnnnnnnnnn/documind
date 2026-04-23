"""Slug generation for chunk file names and anchors."""

from __future__ import annotations

import re
import unicodedata


SLUG_RE = re.compile(r"[^\w\u4e00-\u9fff]+", re.UNICODE)


class Slugger:
    def slugify(self, text: str) -> str:
        normalized = unicodedata.normalize("NFKC", text).lower().strip()
        slug = SLUG_RE.sub("-", normalized).strip("-")
        return slug or "section"

    def unique_slug(self, title: str, counts: dict[str, int]) -> str:
        slug = self.slugify(title)
        count = counts.get(slug, 0) + 1
        counts[slug] = count
        if count == 1:
            return slug
        return f"{slug}-{count}"

    def filename_for_title(self, title: str, counts: dict[str, int]) -> str:
        return f"{self.unique_slug(title, counts)}.md"
