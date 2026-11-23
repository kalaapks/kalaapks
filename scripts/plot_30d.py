import datetime as dt
import os
from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np
import requests
from scipy.interpolate import make_interp_spline

username = os.environ["GH_USERNAME"]
token = os.environ["GH_TOKEN"]

end_dt = dt.datetime.now(dt.timezone.utc)
start_dt = end_dt - dt.timedelta(days=35)

query = """
query($login: String!, $from: DateTime!, $to: DateTime!) {
  user(login: $login) {
    contributionsCollection(from: $from, to: $to) {
      contributionCalendar {
        weeks {
          contributionDays {
            date
            contributionCount
          }
        }
      }
    }
  }
}
"""

resp = requests.post(
    "https://api.github.com/graphql",
    json={
        "query": query,
        "variables": {
            "login": username,
            "from": start_dt.isoformat(),
            "to": end_dt.isoformat(),
        },
    },
    headers={"Authorization": f"Bearer {token}"},
    timeout=30,
)
resp.raise_for_status()

days_map = {}
weeks = resp.json()["data"]["user"]["contributionsCollection"]["contributionCalendar"]["weeks"]
for week in weeks:
    for day in week["contributionDays"]:
        days_map[day["date"]] = day["contributionCount"]

today = dt.date.today()
dates = [today - dt.timedelta(days=i) for i in range(29, -1, -1)]
counts = [days_map.get(d.isoformat(), 0) for d in dates]
labels = [str(d.day) for d in dates]
x = np.arange(len(dates))
y = np.array(counts, dtype=float)

bg = "#071017"
line_col = "#38bdf8"
grid_col = "#162936"
text_col = "#cbd5e1"

plt.rcParams["font.sans-serif"] = "DejaVu Sans"
fig, ax = plt.subplots(figsize=(12, 4), dpi=200)
fig.patch.set_facecolor(bg)
ax.set_facecolor(bg)

# Smooth spline curve + subtle area fill
if len(x) >= 4:
    x_smooth = np.linspace(x.min(), x.max(), 400)
    spline = make_interp_spline(x, y, k=3)
    y_smooth = np.clip(spline(x_smooth), 0, None)
    ax.plot(x_smooth, y_smooth, color=line_col, linewidth=2.6, zorder=3)
    ax.fill_between(x_smooth, y_smooth, color=line_col, alpha=0.14, zorder=2)
else:
    ax.plot(x, y, color=line_col, linewidth=2.6, zorder=3)

ax.scatter(x, y, s=28, facecolor="#ffffff", edgecolor=line_col, linewidth=1.8, zorder=4)

ax.set_title("Contribution Activity (Last 30 Days)", color=line_col, fontsize=13, pad=14, fontweight="medium")
ax.set_ylabel("Contributions", color=line_col, fontsize=10, labelpad=8)
ax.set_xlabel("Day of Month", color=line_col, fontsize=10, labelpad=8)

ax.set_xticks(x)
ax.set_xticklabels(labels, color=text_col, fontsize=8.5)
ax.tick_params(axis="y", colors=text_col, labelsize=9)
ax.set_xlim(-0.5, len(dates) - 0.5)
ax.set_ylim(0, max(10, y.max() * 1.15))

ax.grid(True, which="major", linestyle=(0, (3, 3)), linewidth=0.7, color=grid_col, zorder=1)
for spine in ["top", "right"]:
    ax.spines[spine].set_visible(False)
for spine in ["left", "bottom"]:
    ax.spines[spine].set_color(grid_col)

out_path = Path("images/last_30_days.png")
out_path.parent.mkdir(parents=True, exist_ok=True)
plt.tight_layout()
plt.savefig(out_path, facecolor=bg, dpi=200)