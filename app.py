import os
import re
from urllib.parse import urlparse, unquote
from urllib.parse import quote
from collections import defaultdict
from datetime import datetime, timedelta

import pytz
import requests
from dotenv import load_dotenv
from flask import Flask, redirect, render_template, request, url_for, flash
from flask_caching import Cache
from flask import jsonify
from email.utils import formataddr

from models.user import User, UserStatus, db

load_dotenv()

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///users.db"
app.secret_key = os.environ.get("SECRET_KEY", "insecure-dev-key")
app.config["CACHE_TYPE"] = "SimpleCache"
app.config["CACHE_DEFAULT_TIMEOUT"] = 300
cache = Cache(app)
db.init_app(app)


@app.before_request
def create_tables_once():
    if not hasattr(app, "db_initialized"):
        with app.app_context():
            db.create_all()
        app.db_initialized = True


@cache.cached(timeout=300, query_string=True)
@app.route("/", methods=["GET", "POST"])
def dashboard():
    users = User.query.filter(User.status == UserStatus.ACTIVE).all()
    if not users:
        return redirect(url_for("add_user"))

    selected_user = users[0]
    start_date = (
        request.form.get("start")
        or (datetime.utcnow().date() - timedelta(days=7)).isoformat()
    )
    end_date = request.form.get("end") or datetime.utcnow().date().isoformat()

    if request.method == "POST":
        user_id = request.form.get("user_id")
        if user_id:
            selected_user = User.query.get(user_id)

    try:
        headers = {"PRIVATE-TOKEN": selected_user.token}
        res = requests.get(
            f"{os.getenv('GITLAB_API_BASE', 'https://gitlab.com')}/api/v4/user",
            headers=headers,
            timeout=5,
        )
        user_id = res.json().get("id")
        contributions = get_user_contributions(
            user_id, selected_user.token, start_date, end_date
        )
        labels = sorted(contributions.keys())
        values = [contributions[d] for d in labels]
    except Exception as e:
        labels = []
        values = []
        print(f"Error fetching contributions: {e}")

    return render_template(
        "index.html",
        labels=labels,
        values=values,
        users=users,
        selected_user=selected_user,
        start_date=start_date,
        end_date=end_date,
    )


@app.route("/task", methods=["GET", "POST"])
def task_view():
    users = User.query.filter(User.status == UserStatus.ACTIVE).all()
    if not users:
        return redirect(url_for("add_user"))

    selected_user = None
    issues_by_category = None
    start_date = (datetime.utcnow().date() - timedelta(days=7)).isoformat()
    end_date = datetime.utcnow().date().isoformat()

    if request.method == "POST":
        user_id = request.form.get("user_id")
        start_date = request.form.get("start_date") or start_date
        end_date = request.form.get("end_date") or end_date
        if not user_id:
            return redirect(url_for("task_view"))
        selected_user = User.query.get(user_id)
        items = fetch_gitlab_items(selected_user)
        issues_by_category = organize_issues_by_category(items, selected_user)

    return render_template(
        "task.html",
        users=users,
        user=selected_user,
        issues_by_category=issues_by_category,
        start_date=start_date,
        end_date=end_date,
    )
    

# @app.route("/calendar")
# def calendar_view():
#     users = User.query.filter(User.status == UserStatus.ACTIVE).all()
#     if not users:
#         flash("No users found.", "danger")
#         return redirect(url_for("dashboard"))

#     week_events = []
#     today = datetime.utcnow().date()
#     start_of_week = today - timedelta(days=today.weekday())  # Monday
#     end_of_week = start_of_week + timedelta(days=6)  # Sunday

#     for user in users:
#         print(f"[INFO] Fetching GitLab issues for user: {user.gitlab_username}", flush=True)
#         issues = fetch_gitlab_items(user)

#         for issue in issues:
#             due_date = issue.get("due_date")
#             if not due_date:
#                 continue

#             due = datetime.strptime(due_date, "%Y-%m-%d").date()
#             if start_of_week <= due <= end_of_week:
#                 print(f"[DEBUG] Including issue: {issue['title']} due on {due_date}", flush=True)
#                 week_events.append({
#                     "id": issue["id"],
#                     "title": issue["title"],
#                     "start": due_date,
#                     "url": issue["web_url"],
#                     "extendedProps": {
#                         "author": issue["author"]["name"],
#                         "state": issue["state"],
#                         "web_url": issue["web_url"],
#                         "labels": issue.get("labels", [])
#                     }
#                 })

#     print(f"[INFO] Total issues for calendar: {len(week_events)}", flush=True)
#     return render_template("calendar.html", events=week_events)

@app.route("/calendar")
def calendar_view():
    users = User.query.filter(User.status == UserStatus.ACTIVE).all()
    if not users:
        flash("No users found.", "danger")
        return redirect(url_for("dashboard"))

    week_events = []
    today = datetime.utcnow().date()
    start_of_week = today - timedelta(days=today.weekday())  # Monday
    end_of_week = start_of_week + timedelta(days=6)  # Sunday

    for user in users:
        print(f"[INFO] Fetching GitLab issues for user: {user.gitlab_username}", flush=True)
        issues = fetch_gitlab_items(user)

        for issue in issues:
            due_date = issue.get("due_date")
            if not due_date:
                continue

            due = datetime.strptime(due_date, "%Y-%m-%d").date()
            if start_of_week <= due <= end_of_week:
                assignee = issue.get("assignee", {}).get("name", user.gitlab_username)
                print(f"[DEBUG] Including issue: {issue['title']} (assignee: {assignee})", flush=True)
                week_events.append({
                    "id": issue["id"],
                    "title": issue["title"],
                    "start": due_date,
                    "url": issue["web_url"],
                    "extendedProps": {
                        "assignee": assignee,
                        "state": issue["state"],
                        "web_url": issue["web_url"],
                        "labels": issue.get("labels", [])
                    }
                })

    print(f"[INFO] Total issues for calendar: {len(week_events)}", flush=True)
    return render_template("calendar.html", events=week_events)


@app.route("/api/close-issue", methods=["POST"])
def close_issue():
    print("[HIT] /api/close-issue")

    data = request.get_json()
    issue_url = data.get("issue_url")

    if not issue_url:
        print("[ERROR] Missing issue_url in request.")
        return jsonify(success=False, error="Missing issue URL")

    print(f"[INFO] Received issue_url: {issue_url}")

    try:
        parsed = urlparse(issue_url)
        path = unquote(parsed.path)  # decode %2F if present

        # Match: /group/subgroup/project/-/issues/123 or /work_items/456
        match = re.search(r'^/(.+)/-/(\w+)/(\d+)$', path)
        if not match:
            raise ValueError("URL format invalid")

        project_path = match.group(1)       # Backend/merchant-portal/backend/api
        resource_type = match.group(2)      # issues or work_items
        iid = match.group(3)                # 123 or 167

        print(f"[DEBUG] project_path: {project_path}")
        print(f"[DEBUG] resource_type: {resource_type}")
        print(f"[DEBUG] iid: {iid}")
    except Exception as e:
        print(f"[ERROR] Failed to parse issue URL: {e}")
        return jsonify(success=False, error="Invalid issue URL format")

    user = User.query.filter(User.display_name == "Puvaan Raaj").first()
    if not user:
        print("[ERROR] User not found.")
        return jsonify(success=False, error="User not found")

    headers = {"PRIVATE-TOKEN": user.token}
    base_url = os.getenv("GITLAB_API_BASE", "https://gitlab.com")

    # GitLab API uses "issues" endpoint even for work_items

    # Encode project_path before use
    encoded_path = quote(project_path, safe='')

    close_url = f"{base_url}/api/v4/projects/{encoded_path}/issues/{iid}"
    print(f"[INFO] PUT to: {close_url}")

    res = requests.put(close_url, headers=headers, json={"state_event": "close"}, timeout=5)
    print(f"[DEBUG] Status: {res.status_code}")

    if res.status_code != 200:
        print(f"[ERROR] GitLab response: {res.text}")
        return jsonify(success=False, error=f"Failed to close: {res.text}")

    print(f"[SUCCESS] {resource_type} #{iid} closed in project {project_path}")
    return jsonify(success=True)


@app.route("/admin/add-user", methods=["GET", "POST"])
def add_user():
    if request.method == "POST":
        gitlab_username = request.form["gitlab_username"].strip()

        if not gitlab_username:
            flash("GitLab Username is required.", "danger")
            return redirect(url_for("add_user"))

        # Optional: prevent duplicates
        existing = User.query.filter_by(gitlab_username=gitlab_username).first()
        if existing:
            flash("A user with that GitLab username already exists.", "warning")
            return redirect(url_for("add_user"))

        new_user = User(
            display_name=request.form.get("display_name"),
            team_lead=request.form.get("team_lead"),
            gitlab_username=gitlab_username,
            email=request.form.get("email"),
            token=request.form.get("token"),
            job_title=request.form.get("job_title"),
            status=UserStatus.ACTIVE,
        )
        db.session.add(new_user)
        db.session.commit()
        flash("User added successfully!", "success")
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
    user.email = request.form["email"]
    user.token = request.form["token"]
    user.job_title = request.form["job_title"]
    user.status = UserStatus(int(request.form.get("status", user.status.value)))
    db.session.commit()
    cache.clear()
    return redirect(url_for("list_users"))


@app.context_processor
def inject_users():
    return {"nav_users": User.query.filter(User.status == UserStatus.ACTIVE).all()}


# def fetch_gitlab_items(user):
#     base_url = os.getenv("GITLAB_API_BASE", "https://gitlab.com")
#     headers = {"Private-Token": user.token}
#     all_items = []
#     page = 1
#     is_qc = user.job_title.strip().lower() == "qa"

#     endpoint = "merge_requests" if is_qc else "issues"
#     print(f"[LOG] Fetching {'MRs' if is_qc else 'Issues'} for user: {user.gitlab_username}")

#     while True:
#         params = {
#             "scope": "all",
#             "assignee_username": user.gitlab_username,
#             "page": page,
#             "per_page": 100,
#         }
#         response = requests.get(
#             f"{base_url}/api/v4/{endpoint}", headers=headers, params=params, timeout=5
#         )
#         if response.status_code != 200:
#             print(f"[LOG] GitLab API error ({endpoint}): {response.status_code} {response.text}")
#             break
#         items = response.json()
#         if not items:
#             break
#         all_items.extend(items)
#         page += 1

#     print(f"[LOG] Total {endpoint} fetched for {user.gitlab_username}: {len(all_items)}")
#     return all_items

def fetch_gitlab_items(user):
    base_url = os.getenv("GITLAB_API_BASE", "https://gitlab.com")
    token_owner = User.query.filter(User.display_name == "Puvaan Raaj").first()  # use your own token
    headers = {"Private-Token": token_owner.token}
    all_items = []
    page = 1
    is_qc = user.job_title.strip().lower() == "qa"

    endpoint = "merge_requests" if is_qc else "issues"
    print(f"[LOG] Fetching {endpoint} for username: {user.gitlab_username}")

    while True:
        params = {
            "scope": "all",
            "assignee_username": user.gitlab_username,
            "page": page,
            "per_page": 100,
        }
        response = requests.get(
            f"{base_url}/api/v4/{endpoint}",
            headers=headers,
            params=params,
            timeout=5
        )
        if response.status_code != 200:
            print(f"[LOG] GitLab API error ({endpoint}): {response.status_code} {response.text}")
            break
        items = response.json()
        if not items:
            break
        all_items.extend(items)
        page += 1

    print(f"[LOG] Total {endpoint} fetched for {user.gitlab_username}: {len(all_items)}")
    return all_items



def organize_issues_by_category(items, user):
    PRIORITY_ORDER = {"P1": 1, "P2": 2, "P3": 3, "P4": 4, "P5": 5}
    is_qc = user.job_title.strip().lower() == "qa"
    print(f"[LOG] Organizing {'MRs' if is_qc else 'Issues'} for user: {user.display_name} | QA: {is_qc}")

    if is_qc:
        categories = {
            "DOING": [],
        }
        for mr in items:
            labels = mr.get("labels", [])
            print(f"[LOG][QC] MR: '{mr['title']}' | Labels: {labels}")
            if "DO::Deploy UAT" in labels and "DO::Rejected" not in labels:
                print(f"[LOG][QC] ✅ Included in DOING: '{mr['title']}'")
                priority = next((label for label in labels if label.startswith("P")), "P?")
                categories["DOING"].append(
                    {
                        "priority": priority,
                        "title": mr["title"],
                        "author": mr["author"]["name"],
                        "created_at": convert_dt(mr["created_at"]),
                        "web_url": mr["web_url"],
                    }
                )
            else:
                print(f"[LOG][QC] ❌ Excluded: '{mr['title']}'")
    else:
        categories = {
            "TODO": [],
            "DOING": [],
            "READY FOR REVIEW": [],
            "DEPLOYED": [],
            "Uncategorized": [],
        }
        for issue in items:
            labels = issue["labels"]
            print(f"[LOG][NON-QC] Issue: '{issue['title']}' | Labels: {labels}")
            if issue["state"] == "closed":
                category = "DEPLOYED"
            elif "DO::Doing" in labels:
                category = "DOING"
            elif "DO::To Do" in labels:
                category = "TODO"
            elif "DO::Approved" in labels:
                category = "READY FOR REVIEW"
            else:
                category = "Uncategorized"
            print(f"[LOG][NON-QC] Assigned to category: {category}")
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

    # Sort all categories by priority
    for cat in categories:
        categories[cat].sort(
            key=lambda x: PRIORITY_ORDER.get(x["priority"], 999)
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
        response = requests.get(url, headers=headers, timeout=5)
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


@app.route("/send-email", methods=["POST"])
def send_email():
    user_id = request.form.get("user_id")
    user = User.query.get_or_404(user_id)

    mailgun_domain = os.getenv("MAILGUN_DOMAIN")
    mailgun_api_key = os.getenv("MAILGUN_API_KEY")

    if not mailgun_domain or not mailgun_api_key:
        flash("Mailgun configuration is missing.", "danger")
        return redirect(url_for("task_view"))

    email_subject = f"GitLab Summary - {datetime.utcnow().date()}"
    email_body = f"Daily GitLab task summary for {user.display_name}"

    response = requests.post(
        f"https://api.mailgun.net/v3/{mailgun_domain}/messages",
        auth=("api", mailgun_api_key),
        data={
            "from": formataddr(("GitLab Reporter", os.getenv("MAIL_SENDER", f"noreply@{mailgun_domain}"))),
            "to": [user.email],
            "subject": email_subject,
            "text": email_body,
        },
        timeout=10
    )

    if response.status_code == 200:
        flash("Email sent successfully!", "success")
    else:
        flash(f"Failed to send email: {response.text}", "danger")

    return redirect(url_for("task_view"))


if __name__ == "__main__":
    host = os.environ.get("FLASK_RUN_HOST", "127.0.0.1")
    port = int(os.environ.get("FLASK_RUN_PORT", 5000))
    debug = os.environ.get("FLASK_DEBUG", "False") == "True"
    app.run(debug=debug, host=host, port=port)
