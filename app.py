from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
import json
import os
import requests

app = Flask(__name__)
app.secret_key = "supersecretkey"

SUBMISSIONS_FILE = "submissions.json"
USERS_FILE = "users.json"
DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/1401117057214447616/FxXRgqJIDxhR0-lvHFYDZEGylh7Cs4az3pW5mpXrrEzl0A8ylai0_4kKSnWelcCn1Io1"

# --- Helper functions ---

def load_json(file_path):
    if not os.path.exists(file_path):
        return []
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_json(file_path, data):
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

# --- Routes ---

@app.route("/")
def home():
    if "username" not in session:
        return redirect(url_for("login"))
    return render_template("index.html", username=session["username"])

@app.route("/", methods=["POST"])
def submit_idea():
    if "username" not in session:
        flash("Please log in to submit ideas.", "error")
        return redirect(url_for("login"))

    title = request.form.get("title", "").strip()
    description = request.form.get("description", "").strip()
    username = session["username"]

    if not title or not description:
        flash("Both title and description are required.", "error")
        return redirect(url_for("home"))

    submissions = load_json(SUBMISSIONS_FILE)
    submissions.append({
        "username": username,
        "title": title,
        "description": description
    })
    save_json(SUBMISSIONS_FILE, submissions)

    # Send to Discord
    message = f"📹 **New Video Idea by @{username}**\n**Title:** {title}\n**Description:** {description}"
    try:
        response = requests.post(DISCORD_WEBHOOK_URL, json={"content": message})
        if response.status_code != 204:
            print("Discord error:", response.text)
    except Exception as e:
        print("Discord send failed:", e)

    flash("Idea submitted successfully!", "success")
    return redirect(url_for("home"))

@app.route("/submissions")
def submissions():
    if "username" not in session:
        return redirect(url_for("login"))
    ideas = load_json(SUBMISSIONS_FILE)
    return render_template("submissions.html", submissions=ideas)

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()

        if not username or not password:
            flash("Username and password required.", "error")
            return redirect(url_for("signup"))

        users = load_json(USERS_FILE)
        if any(user["username"].lower() == username.lower() for user in users):
            flash("Username already exists.", "error")
            return redirect(url_for("signup"))

        hashed_pw = generate_password_hash(password)
        users.append({"username": username, "password": hashed_pw})
        save_json(USERS_FILE, users)

        flash("Account created. Please log in.", "success")
        return redirect(url_for("login"))

    return render_template("signup.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()

        users = load_json(USERS_FILE)
        user = next((u for u in users if u["username"].lower() == username.lower()), None)

        if user and check_password_hash(user["password"], password):
            session["username"] = user["username"]
            flash("Logged in successfully!", "success")
            return redirect(url_for("home"))
        else:
            flash("Invalid credentials.", "error")
            return redirect(url_for("login"))

    return render_template("login.html")

@app.route("/logout")
def logout():
    session.pop("username", None)
    flash("Logged out.", "success")
    return redirect(url_for("login"))

if __name__ == "__main__":
    app.run(debug=True)
