GitLab Daily Task Viewer

A lightweight Flask-based web app that fetches daily GitLab issues and formats them for team standups. Each user is associated with a GitLab token, role, and metadata for categorizing their tasks into TODO, DOING, REVIEW, or DEPLOYED sections.
🚀 Features

    📋 Categorizes issues from GitLab by label and state (TODO, DOING, REVIEW, DEPLOYED)

    ✂️ One-click copyable task summary

    🧑‍💼 Admin UI to add and update users

    🧠 Role-aware support for Programmers, QA, PM, etc.

    📊 Contributions Analytics Chart using Chart.js

    📅 Date range picker for GitLab contributions

    📁 SQLite-based lightweight local storage

    🐳 Dockerized with .env configuration

    🔐 Secure admin access in production mode

🛠️ Setup Instructions
1. Clone the Repo

git clone https://your.repo.url.git
cd gitlab-task-viewer

2. Add a .env file

FLASK_ENV=dev
SECRET_KEY=super-secret-key
ADMIN_PASSWORD=your_admin_password
GITLAB_API_BASE=https://gitlab.com

    Set FLASK_ENV=prod in production to enable admin login.

3. Build and Run via Docker

docker build -t gitlab-task-viewer .
docker run -p 5000:5000 gitlab-task-viewer

Or using Docker Compose:

docker-compose up --build

🔗 Routes
Route	Description
/	📊 Contributions Analytics Dashboard
/task	✅ Daily task viewer and categorizer
/admin/add-user	➕ Add new user to the system
/admin/users	📝 List and update existing users
👤 User Model Fields

    display_name

    team_lead

    gitlab_username

    token

    job_title (e.g., Programmer, QA, PM)

📈 Analytics Dashboard

The homepage includes a contributions bar chart with:

    ⏱️ Custom date range selection (default = last 7 days)

    📊 Chart.js visualization of daily activity

    🧠 Auto-selects the first user for display

🧠 Task Categorization Logic

GitLab labels determine which category the issue goes into:
Label	Category
DO::To Do	TODO
DO::Doing	DOING
DO::Approved	READY FOR REVIEW
state=closed	DEPLOYED
others	Uncategorized
📝 Sample Output (Copied)

MEMBER : Puvaan Raaj  [TL: Singh]
========================== TODO ============================
❗ [P1] Implement login
🗣 Team: Puvaan
🕙 Opened: 20-09-2024 14:22:10
🔗 https://...

========================== DOING ============================
❗ [P2] Add Tailwind UI
...

🔐 Security Notes

    Admin routes are password-protected in prod

    Tokens stored in SQLite — encrypt in production

    Use a strong SECRET_KEY and ADMIN_PASSWORD

🧪 CI/CD (Planned or Suggested)

    ✅ [x] Python formatting via ruff

    ✅ [x] Basic Flask healthcheck

    🔜 [ ] GitLab pipeline integration

    🔜 [ ] End-to-end test with pytest + requests

📬 License

MIT — free to use and customize for your team.