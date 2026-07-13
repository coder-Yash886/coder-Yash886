# GitHub PAT Setup (Token)

Profile stats **private contributions** ke liye GitHub Personal Access Token chahiye.

## Step 1 — Token banayein

1. Open: https://github.com/settings/tokens
2. **Generate new token** → **Generate new token (classic)**
3. Note: `profile-readme-stats`
4. Scopes select karein:
   - `read:user`
   - `repo` (private contributions count ke liye)
5. **Generate token** → token copy karein (sirf ek baar dikhega)

## Step 2 — Repo secret add karein

1. Open: https://github.com/coder-Yash886/coder-Yash886/settings/secrets/actions
2. **New repository secret**
3. Name: `PAT`
4. Value: apna token paste karein
5. **Add secret**

## Step 3 — Workflow run karein

1. **Actions** tab → **Update Profile Stats**
2. **Run workflow** → **Run workflow**

## Kya hota hai token se?

| File | Kaam |
|------|------|
| `github_stats.py` | GraphQL API se stats (private contributions included) |
| `generate_stats_cards.py` | `assets/github-stats.svg` + `assets/top-langs.svg` banata hai |
| `generate_neofetch.py` | Neofetch card mein live contributions |
| `update_readme_stats.py` | README update |
| `.github/workflows/update-neofetch.yml` | Har 6 ghante auto-run |

## Local test (optional)

```bash
export GITHUB_TOKEN=ghp_your_token_here
python3 generate_stats_cards.py
python3 generate_neofetch.py
python3 update_readme_stats.py
```

## README images

Ab stats **local SVG files** use karte hain — external API par depend nahi:

```markdown
![GitHub Stats](./assets/github-stats.svg)
![Top Languages](./assets/top-langs.svg)
```

Isliye GitHub par hamesha show honge.
