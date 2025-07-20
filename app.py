import os
from collections import defaultdict
from datetime import datetime, timedelta

import pytz
import requests
from dotenv import load_dotenv
from flask import Flask, redirect, render_template, request, url_for
from flask_sqlalchemy import SQLAlchemy

load_dotenv()

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///users.db"
app.secret_key = os.environ.get("SECRET_KEY", "insecure-dev-key")
db = SQLAlchemy(app)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    display_name = db.Column(db.String(100))
    team_lead = db.Column(db.String(100))
    gitlab_username = db.Column(db.String(100))
    token = db.Column(db.String(200))
    job_title = db.Column(db.String(100))


@app.before_request
def create_tables_once():
    if not hasattr(app, "db_initialized"):
        db.create_all()
        app.db_initialized = True


@app.route("/")
def dashboard():
    users = User.query.all()
    if not users:
        return redirect(url_for("add_user"))

    first_user = users[0]
    today = datetime.utcnow().date()
    start_date = (today - timedelta(days=14)).isoformat()
    end_date = today.isoformat()

    try:
        headers = {"PRIVATE-TOKEN": first_user.token}
        res = requests.get(
            f"{os.getenv('GITLAB_API_BASE', 'https://gitlab.com')}/api/v4/user",
            headers=headers,
        )
        user_id = res.json().get("id")
        contributions = get_user_contributions(
            user_id, first_user.token, start_date, end_date
        )
        labels = sorted(contributions.keys())
        values = [contributions[d] for d in labels]
    except Exception as e:
        labels = []
        values = []
        print(f"Error fetching contributions: {e}")

    return render_template("index.html", labels=labels, values=values)


@app.route("/task", methods=["GET", "POST"])
def task_view():
    users = User.query.all()
    if not users:
        return redirect(url_for("add_user"))

    selected_user = None
    issues_by_category = None

    if request.method == "POST":
        user_id = request.form.get("user_id")
        if not user_id:
            return redirect(url_for("task_view"))
        selected_user = User.query.get(user_id)
        issues = fetch_gitlab_issues(selected_user.gitlab_username, selected_user.token)
        issues_by_category = organize_issues_by_category(issues)

    return render_template(
        "task.html",
        users=users,
        user=selected_user,
        issues_by_category=issues_by_category,
    )


@app.route("/admin/add-user", methods=["GET", "POST"])
def add_user():
    if request.method == "POST":
        new_user = User(
            display_name=request.form["display_name"],
            team_lead=request.form["team_lead"],
            gitlab_username=request.form["gitlab_username"],
            token=request.form["token"],
            job_title=request.form["job_title"],
        )
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for("dashboard"))
    return render_template("add_user.html")


@app.route("/admin/users")
def list_users():
    users = User.query.all()
    return render_template("list_users.html", users=users)


@app.route("/admin/users/<int:user_id>/update", methods=["POST"])
def update_user(user_id):
    user = User.query.get_or_404(user_id)
    user.display_name = request.form["display_name"]
    user.team_lead = request.form["team_lead"]
    user.gitlab_username = request.form["gitlab_username"]
    user.token = request.form["token"]
    user.job_title = request.form["job_title"]
    db.session.commit()
    return redirect(url_for("list_users"))


@app.context_processor
def inject_users():
    return {"nav_users": User.query.all()}


def fetch_gitlab_issues(username, token):
    base_url = os.getenv("GITLAB_API_BASE", "https://gitlab.com")
    headers = {"Private-Token": token}
    all_issues = []
    page = 1
    while True:
        params = {
            "scope": "all",
            "assignee_username": username,
            "page": page,
            "per_page": 100,
        }
        response = requests.get(
            f"{base_url}/api/v4/issues", headers=headers, params=params, timeout=5
        )
        if response.status_code != 200:
            break
        issues = response.json()
        if not issues:
            break
        all_issues.extend(issues)
        page += 1
    return all_issues


def organize_issues_by_category(issues):
    categories = {
        "TODO": [],
        "DOING": [],
        "READY FOR REVIEW": [],
        "DEPLOYED": [],
        "Uncategorized": [],
    }
    for issue in issues:
        labels = issue["labels"]
        if issue["state"] == "closed":
            category = "DEPLOYED"
        elif "DO::Approved" in labels:
            category = "READY FOR REVIEW"
        elif "DO::Doing" in labels:
            category = "DOING"
        elif "DO::To Do" in labels:
            category = "TODO"
        else:
            category = "Uncategorized"

        priority = next((label for label in labels if label.startswith("P")), "P?")
        categories[category].append(
            {
                "priority": priority,
                "title": issue["title"],
                "author": issue["author"]["name"],
                "created_at": convert_dt(issue["created_at"]),
                "web_url": issue["web_url"],
            }
        )
    return categories


def get_user_contributions(user_id, token, start_date, end_date):
    headers = {"PRIVATE-TOKEN": token}
    contributions = defaultdict(int)
    page = 1
    while True:
        url = (
            f"{os.getenv('GITLAB_API_BASE', 'https://gitlab.com')}/api/v4/users/{user_id}/events?"
            f"after={start_date}&before={end_date}&per_page=100&page={page}"
        )
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            break
        events = response.json()
        if not events:
            break
        for event in events:
            date = event["created_at"][:10]
            contributions[date] += 1
        page += 1
    return dict(contributions)


def convert_dt(dt_str):
    naive_dt = datetime.strptime(dt_str, "%Y-%m-%dT%H:%M:%S.%f%z")
    local_dt = naive_dt.astimezone(pytz.timezone("Asia/Kuala_Lumpur"))
    return local_dt.strftime("%d-%m-%Y %H:%M:%S")


if __name__ == "__main__":
    host = os.environ.get("FLASK_RUN_HOST", "127.0.0.1")
    port = int(os.environ.get("FLASK_RUN_PORT", 5000))
    debug = os.environ.get("FLASK_DEBUG", "False") == "True"
    app.run(debug=debug, host=host, port=port)
