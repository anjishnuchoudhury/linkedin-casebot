# app.py
import os, sqlite3, requests
from flask import Flask, request, redirect, render_template_string, session
from datetime import datetime

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "dev")

DB_PATH = os.getenv("DB_PATH", "casebot.db")
LINKEDIN_ACCESS_TOKEN = os.getenv("LINKEDIN_ACCESS_TOKEN")
LINKEDIN_ORG_ID = os.getenv("LINKEDIN_ORG_ID")
ADMIN_USER = os.getenv("ADMIN_USER", "admin")
ADMIN_PASS = os.getenv("ADMIN_PASS", "password")

HTML_TEMPLATE = """
<!doctype html>
<title>CaseBot Approvals</title>
<h1>Pending Cases</h1>
{% for case in cases %}
<div style="border:1px solid #ccc; padding:10px; margin-bottom:10px;">
    <h3>{{ case[1] }}</h3>
    <p>{{ case[4] }}</p>
    <a href="/approve/{{ case[0] }}">Approve</a> | <a href="/reject/{{ case[0] }}">Reject</a>
</div>
{% else %}
<p>No pending cases.</p>
{% endfor %}
"""

def get_db():
    return sqlite3.connect(DB_PATH)

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        if request.form["username"] == ADMIN_USER and request.form["password"] == ADMIN_PASS:
            session["logged_in"] = True
            return redirect("/pending")
    return '''<form method="post">
              Username: <input name="username"><br>
              Password: <input type="password" name="password"><br>
              <input type="submit" value="Login">
              </form>'''

@app.route("/pending")
def pending():
    if not session.get("logged_in"):
        return redirect("/login")
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM cases WHERE status='pending' ORDER BY created_at DESC")
    cases = c.fetchall()
    conn.close()
    return render_template_string(HTML_TEMPLATE, cases=cases)

@app.route("/approve/<int:case_id>")
def approve(case_id):
    if not session.get("logged_in"):
        return redirect("/login")
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT title, explainer FROM cases WHERE id=?", (case_id,))
    row = c.fetchone()
    if row:
        post_to_linkedin(row[0], row[1])
        c.execute("UPDATE cases SET status='posted' WHERE id=?", (case_id,))
    conn.commit()
    conn.close()
    return redirect("/pending")

@app.route("/reject/<int:case_id>")
def reject(case_id):
    if not session.get("logged_in"):
        return redirect("/login")
    conn = get_db()
    c = conn.cursor()
    c.execute("UPDATE cases SET status='rejected' WHERE id=?", (case_id,))
    conn.commit()
    conn.close()
    return redirect("/pending")

def post_to_linkedin(title, content):
    if not LINKEDIN_ACCESS_TOKEN or not LINKEDIN_ORG_ID:
        print("LinkedIn credentials missing")
        return
    url = "https://api.linkedin.com/v2/ugcPosts"
    headers = {
        "Authorization": f"Bearer {LINKEDIN_ACCESS_TOKEN}",
        "X-Restli-Protocol-Version": "2.0.0",
        "Content-Type": "application/json"
    }
    payload = {
        "author": f"urn:li:organization:{LINKEDIN_ORG_ID}",
        "lifecycleState": "PUBLISHED",
        "specificContent": {
            "com.linkedin.ugc.ShareContent": {
                "shareCommentary": {
                    "text": f"{title}\n\n{content}"
                },
                "shareMediaCategory": "NONE"
            }
        },
        "visibility": {
            "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
        }
    }
    r = requests.post(url, headers=headers, json=payload)
    print("LinkedIn API response:", r.status_code, r.text)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
