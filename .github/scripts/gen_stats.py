#!/usr/bin/env python3
"""Generate GitHub stats + contribution graph SVGs (no external service)."""
import os
import json
import datetime
import urllib.request

USER = os.environ.get("GH_USER", "qutexora62")
TOKEN = os.environ.get("GH_TOKEN", "")
OUT = "dist"
os.makedirs(OUT, exist_ok=True)

HEADERS = {"Authorization": f"bearer {TOKEN}", "User-Agent": "stats-bot"}


def gql(query):
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": query}).encode(),
        headers={**HEADERS, "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req) as r:
        return json.load(r)


def esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


# ---------- fetch data ----------
q = """
query {
  user(login: "%s") {
    name
    followers { totalCount }
    repositories(privacy: PUBLIC) { totalCount }
    contributionsCollection {
      totalCommitContributions
      totalPullRequestContributions
      totalIssueContributions
      contributionCalendar {
        totalContributions
        weeks { contributionDays { date contributionCount } }
      }
    }
  }
}
""" % USER

data = gql(q)["data"]["user"]
cc = data["contributionsCollection"]
cal = cc["contributionCalendar"]
followers = data["followers"]["totalCount"]
repos = data["repositories"]["totalCount"]
commits = cc["totalCommitContributions"]
prs = cc["totalPullRequestContributions"]
issues = cc["totalIssueContributions"]
total = cal["totalContributions"]

# ---------- stats card ----------
stats_svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="495" height="195" viewBox="0 0 495 195">
  <style>
    .bg {{ fill: #0D1117; }}
    .title {{ fill: #00E5FF; font: 600 18px 'Segoe UI',sans-serif; }}
    .label {{ fill: #c9d1d9; font: 400 14px 'Segoe UI',sans-serif; }}
    .value {{ fill: #00E5FF; font: 700 14px 'Segoe UI',sans-serif; }}
  </style>
  <rect class="bg" width="495" height="195" rx="12" stroke="#30363d"/>
  <text x="25" y="35" class="title">{esc(data.get("name") or USER)}'s GitHub Stats</text>
  <text x="25" y="70" class="label">Total Stars:</text><text x="180" y="70" class="value">-</text>
  <text x="25" y="100" class="label">Total Commits:</text><text x="180" y="100" class="value">{commits}</text>
  <text x="25" y="130" class="label">Pull Requests:</text><text x="180" y="130" class="value">{prs}</text>
  <text x="25" y="160" class="label">Total Issues:</text><text x="180" y="160" class="value">{issues}</text>
  <text x="300" y="70" class="label">Contributions:</text><text x="430" y="70" class="value">{total}</text>
  <text x="300" y="100" class="label">Public Repos:</text><text x="430" y="100" class="value">{repos}</text>
  <text x="300" y="130" class="label">Followers:</text><text x="430" y="130" class="value">{followers}</text>
</svg>'''

with open(f"{OUT}/stats.svg", "w") as f:
    f.write(stats_svg)

# ---------- contribution graph ----------
weeks = cal["weeks"]
cell = 12
gap = 3
n = len(weeks)
width = n * (cell + gap) + 60
height = 7 * (cell + gap) + 60


def color(c):
    if c == 0:
        return "#161b22"
    if c <= 2:
        return "#0e4429"
    if c <= 5:
        return "#006d32"
    if c <= 9:
        return "#26a641"
    return "#39d353"


rects = []
for wi, w in enumerate(weeks):
    for di, d in enumerate(w["contributionDays"]):
        x = 40 + wi * (cell + gap)
        y = 40 + di * (cell + gap)
        rects.append(
            f'<rect x="{x}" y="{y}" width="{cell}" height="{cell}" rx="2" fill="{color(d["contributionCount"])}"/>'
        )

graph_svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
  <rect width="{width}" height="{height}" fill="#0D1117" rx="12"/>
  <text x="40" y="25" fill="#00E5FF" font-family="Segoe UI,sans-serif" font-size="16" font-weight="600">{esc(data.get("name") or USER)}'s Contribution Graph — {total} contributions</text>
  {"".join(rects)}
</svg>'''

with open(f"{OUT}/graph.svg", "w") as f:
    f.write(graph_svg)

print("Generated stats.svg and graph.svg")
