from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import os
import json
import requests

app = Flask(__name__)
app.secret_key = "your_secret_key"  # Change this in production
WEBHOOK_URL = "https://discord.com/api/webhooks/..."  # Replace with your webhook URL
DATA_FILE = "submissions.json"
USERS_FILE = "users.json"

# Load + Save Utilities
def load_users():
    if not os.path.exists(USERS_FILE):
        return {}
    with open(USERS_FILE, "r") as f:
        return json.load(f)

def save_users(users):
    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=4)

def load_submissions():
    if not os.path.exists(DATA_FILE):
        return []
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_submissions(submissions):
    with open(DATA_FILE, "w") as f:
        json.dump(submissions, f, indent=4)

# Routes
@app.route("/")
def index():
    submissions = load_submissions()
    return render_template("index.html", submissions=submissions, username=session.get("username"))

@app.route("/submit", methods=["POST"])
def submit():
    if "username" not in session:
        return redirect(url_for("login"))

    submissions = load_submissions()
    data = request.form
    new_id = max([s["id"] for s in submissions], default=0) + 1
    new_submission = {
        "id": new_id,
        "title": data.get("title"),
        "description": data.get("description"),
        "username": session["username"],
        "votes": {"upvotes": 0, "downvotes": 0},
        "comments": []
    }
    submissions.append(new_submission)
    save_submissions(submissions)

    # Send to Discord
    message = f"**New Idea by {session['username']}**\n**Title:** {new_submission['title']}\n**Description:** {new_submission['description']}"
    requests.post(WEBHOOK_URL, json={"content": message})

    return redirect(url_for("index"))

@app.route("/vote/<int:id>/<action>", methods=["POST"])
def vote(id, action):
    submissions = load_submissions()
    submission = next((s for s in submissions if s["id"] == id), None)
    if not submission:
        return jsonify({"error": "Idea not found"}), 404

    if action == "upvote":
        submission["votes"]["upvotes"] += 1
    elif action == "downvote":
        submission["votes"]["downvotes"] += 1
    else:
        return jsonify({"error": "Invalid action"}), 400

    save_submissions(submissions)
    return jsonify(submission)

@app.route("/comment/<int:id>", methods=["POST"])
def comment(id):
    submissions = load_submissions()
    submission = next((s for s in submissions if s["id"] == id), None)
    if not submission:
        return jsonify({"error": "Idea not found"}), 404

    data = request.json
    user = data.get("user")
    comment_text = data.get("comment")

    if not user or not comment_text:
        return jsonify({"error": "User and comment are required"}), 400

    submission["comments"].append({"user": user, "text": comment_text})
    save_submissions(submissions)
    return jsonify(submission)

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        users = load_users()
        username = request.form["username"]
        password = request.form["password"]

        if username in users and users[username] == password:
            session["username"] = username
            return redirect(url_for("index"))
        else:
            return render_template("login.html", error="Invalid credentials")

    return render_template("login.html")

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        users = load_users()
        username = request.form["username"]
        password = request.form["password"]

        if username in users:
            return render_template("signup.html", error="Username already exists")

        users[username] = password
        save_users(users)
        session["username"] = username
        return redirect(url_for("index"))

    return render_template("signup.html")

@app.route("/logout")
def logout():
    session.pop("username", None)
    return redirect(url_for("index"))

if __name__ == "__main__":
    app.run(debug=True)
