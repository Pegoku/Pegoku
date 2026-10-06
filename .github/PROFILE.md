# Maintaining the profile

Edit `README.template.md` in this directory to change the ASCII logo, introduction,
tools, or interests. `README.md` at the repository root is generated; direct edits
will be replaced by the next update. Manage featured projects through GitHub's
profile pin controls.

The generator reads the account's public `name`, `location`, and `company` fields
from the GitHub API. An empty name falls back to the account login. Empty location
and company fields leave those logo rows without labels. Failed requests or invalid
data leave the existing README intact.

Run locally with Python 3.10 or newer (no additional packages):

```sh
python3 -m unittest discover -s scripts -p 'test_*.py'
python3 scripts/update_profile.py
```

After publishing the workflow to the default branch, GitHub Actions checks daily
at 06:23 UTC, when its template/script/tests/workflow change, or through
**Actions > Update profile README > Run workflow**. Scheduled runs may be delayed
by GitHub, and scheduled workflows in inactive public repositories may be disabled
after 60 days.

The workflow uses the built-in `GITHUB_TOKEN` with `contents: write`. It commits
and pushes only a changed `README.md` as `github-actions[bot]`. No personal token
is needed. Repository rules that prohibit direct bot pushes would need a PR-based
workflow instead.
