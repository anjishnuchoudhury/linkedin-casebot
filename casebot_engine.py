# casebot_engine.py
import os, sqlite3, feedparser, requests
from datetime import datetime
from openai import OpenAI

DB_PATH = os.getenv("DB_PATH", "casebot.db")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

RSS_FEEDS = [
    "https://www.scobserver.in/feed",
    "https://barandbench.com/feed",
    "https://www.livelaw.in/rss"
]

SENSITIVE_KEYWORDS = ["politics", "religion", "violence", "sexual", "terrorism"]

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS cases (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        link TEXT,
        summary TEXT,
        explainer TEXT,
        status TEXT DEFAULT 'pending',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""")
    conn.commit()
    conn.close()

def fetch_cases():
    items = []
    for feed_url in RSS_FEEDS:
        feed = feedparser.parse(feed_url)
        for entry in feed.entries:
            title = entry.title
            if any(word.lower() in title.lower() for word in SENSITIVE_KEYWORDS):
                continue
            link = entry.link
            summary = getattr(entry, 'summary', '')
            items.append((title, link, summary))
    return items

def generate_explainer(title, summary):
    if not OPENAI_API_KEY:
        return f"Explainer for: {title}\nSummary: {summary}"
    client = OpenAI(api_key=OPENAI_API_KEY)
    prompt = f"""Write a non-controversial, simple LinkedIn-style explainer about this Indian court case.

Title: {title}
Summary: {summary}"""
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=300
    )
    return response.choices[0].message.content.strip()

def store_cases(cases):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    for title, link, summary in cases:
        c.execute("SELECT id FROM cases WHERE title = ? AND link = ?", (title, link))
        if c.fetchone():
            continue
        explainer = generate_explainer(title, summary)
        c.execute("INSERT INTO cases (title, link, summary, explainer) VALUES (?, ?, ?, ?)",
                  (title, link, summary, explainer))
    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    data = fetch_cases()
    store_cases(data)
    print(f"Fetched and stored {len(data)} cases.")
