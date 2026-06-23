"""
Seed the database with synthetic marketing performance data.

Run:  python data/seed.py
"""

import os
import random
import sqlite3
from datetime import date, timedelta

random.seed(42)  # stable numbers between runs

DB_PATH = os.path.join(os.path.dirname(__file__), "marketing.db")

# rough economics per channel — drives how the numbers shake out
CHANNELS = {
    "Paid Search":   {"cpc": 1.80, "cvr": 0.045, "aov": 95,  "base_clicks": 900},
    "Paid Social":   {"cpc": 0.95, "cvr": 0.022, "aov": 78,  "base_clicks": 1400},
    "Display":       {"cpc": 0.40, "cvr": 0.008, "aov": 70,  "base_clicks": 2200},
    "Email":         {"cpc": 0.05, "cvr": 0.060, "aov": 88,  "base_clicks": 600},
    "Affiliate":     {"cpc": 0.70, "cvr": 0.030, "aov": 110, "base_clicks": 500},
}

CAMPAIGNS = [
    ("Spring Sale",        "Paid Search"),
    ("Brand Always-On",    "Paid Search"),
    ("Prospecting Q2",     "Paid Social"),
    ("Retargeting Q2",     "Paid Social"),
    ("Awareness Push",     "Display"),
    ("Newsletter",         "Email"),
    ("Win-back Flow",      "Email"),
    ("Partner Network",    "Affiliate"),
]

SCHEMA = """
DROP TABLE IF EXISTS daily_performance;
DROP TABLE IF EXISTS campaigns;
DROP TABLE IF EXISTS channels;

CREATE TABLE channels (
    channel_id   INTEGER PRIMARY KEY,
    name         TEXT NOT NULL UNIQUE
);

CREATE TABLE campaigns (
    campaign_id  INTEGER PRIMARY KEY,
    name         TEXT NOT NULL,
    channel_id   INTEGER NOT NULL REFERENCES channels(channel_id),
    start_date   TEXT NOT NULL
);

CREATE TABLE daily_performance (
    id           INTEGER PRIMARY KEY,
    date         TEXT NOT NULL,
    campaign_id  INTEGER NOT NULL REFERENCES campaigns(campaign_id),
    impressions  INTEGER NOT NULL,
    clicks       INTEGER NOT NULL,
    spend        REAL NOT NULL,
    conversions  INTEGER NOT NULL,
    revenue      REAL NOT NULL
);
"""


def build():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.executescript(SCHEMA)

    channel_ids = {}
    for i, name in enumerate(CHANNELS, start=1):
        cur.execute("INSERT INTO channels (channel_id, name) VALUES (?, ?)", (i, name))
        channel_ids[name] = i

    start = date.today() - timedelta(days=90)
    campaign_ids = {}
    for i, (cname, chan) in enumerate(CAMPAIGNS, start=1):
        cur.execute(
            "INSERT INTO campaigns (campaign_id, name, channel_id, start_date) VALUES (?, ?, ?, ?)",
            (i, cname, channel_ids[chan], start.isoformat()),
        )
        campaign_ids[cname] = (i, chan)

    rows = []
    for day_offset in range(90):
        d = start + timedelta(days=day_offset)
        is_weekend = d.weekday() >= 5
        weekend_factor = 0.7 if is_weekend else 1.0

        for cname, (cid, chan) in campaign_ids.items():
            econ = CHANNELS[chan]
            noise = random.uniform(0.85, 1.15)

            # Spring Sale gets a promo bump in the middle of the window
            promo = 1.0
            if cname == "Spring Sale" and 30 <= day_offset <= 55:
                promo = 1.9

            clicks = int(econ["base_clicks"] * weekend_factor * noise * promo)
            ctr = {"Display": 0.004, "Paid Social": 0.012}.get(chan, 0.05)
            impressions = int(clicks / ctr)

            spend = round(clicks * econ["cpc"] * random.uniform(0.95, 1.05), 2)
            cvr = econ["cvr"] * random.uniform(0.8, 1.2) * (1.15 if promo > 1 else 1.0)
            conversions = int(clicks * cvr)
            revenue = round(conversions * econ["aov"] * random.uniform(0.9, 1.1), 2)

            rows.append((d.isoformat(), cid, impressions, clicks, spend, conversions, revenue))

    cur.executemany(
        """INSERT INTO daily_performance
           (date, campaign_id, impressions, clicks, spend, conversions, revenue)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        rows,
    )

    conn.commit()
    n = cur.execute("SELECT COUNT(*) FROM daily_performance").fetchone()[0]
    conn.close()
    print(f"Seeded {DB_PATH} — {n} rows across {len(CAMPAIGNS)} campaigns, {len(CHANNELS)} channels.")


if __name__ == "__main__":
    build()
