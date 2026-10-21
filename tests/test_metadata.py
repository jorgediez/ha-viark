"""Checks on the files that describe the integration rather than run it."""

from __future__ import annotations

import json
from pathlib import Path
import tomllib

REPO = Path(__file__).resolve().parents[1]


def test_the_version_is_declared_once():
    """The release workflow refuses a tag that disagrees with any of the files.

    Catching a mismatch here keeps it from surfacing only after a release is
    published.
    """
    manifest = json.loads(
        (REPO / "custom_components" / "viark" / "manifest.json").read_text("utf-8")
    )
    project = tomllib.loads((REPO / "pyproject.toml").read_text("utf-8"))
    card = json.loads((REPO / "frontend" / "package.json").read_text("utf-8"))

    assert manifest["version"] == project["project"]["version"]
    # The card ships with the integration, so it carries the same version.
    assert card["version"] == manifest["version"]
