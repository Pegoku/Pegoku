"""Generate the profile README using public GitHub account fields."""

import argparse
import json
import os
from pathlib import Path
import re
import tempfile
from urllib.parse import quote
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[1]


def clean(value):
    if value is None:
        return ""
    if not isinstance(value, str):
        raise ValueError("Profile fields must be strings or null")
    # Keep account text on one line and prevent it closing the code fence.
    return " ".join(value.replace("`", "'").split())


def fetch_profile(username):
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "Pegoku-profile-readme",
    }
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = Request(
        f"https://api.github.com/users/{quote(username, safe='')}", headers=headers
    )
    with urlopen(request, timeout=30) as response:
        profile = json.load(response)
    if not isinstance(profile, dict) or clean(profile.get("login")).lower() != username.lower():
        raise ValueError("GitHub returned an unexpected profile")
    return profile


def render(template, profile):
    name = clean(profile.get("name")) or clean(profile.get("login"))
    if not name:
        raise ValueError("Profile has no name or login")
    location = clean(profile.get("location"))
    company = clean(profile.get("company"))
    fields = {
        "name": re.sub(r"([\\`*_{}\[\]<>()!#|])", r"\\\1", name),
        "name_line": f"Name       {name}",
        "location_line": f"Based in   {location}" if location else "",
        "company_line": f"Company    {company}" if company else "",
    }
    result = re.sub(r"\{\{(\w+)\}\}", lambda match: fields[match[1]], template)
    return "\n".join(line.rstrip() for line in result.splitlines()) + "\n"


def update(username, template_path, output_path):
    # Fetch and render fully before touching the existing README.
    profile = fetch_profile(username)
    content = render(template_path.read_text(encoding="utf-8"), profile)
    if output_path.exists() and output_path.read_text(encoding="utf-8") == content:
        return False
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=output_path.parent, delete=False
        ) as handle:
            temporary = Path(handle.name)
            handle.write(content)
        temporary.chmod(0o644)
        temporary.replace(output_path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
    return True


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--username", default="Pegoku")
    args = parser.parse_args()
    changed = update(args.username, ROOT / ".github/README.template.md", ROOT / "README.md")
    print("Updated README.md" if changed else "README.md is already up to date")


if __name__ == "__main__":
    main()
