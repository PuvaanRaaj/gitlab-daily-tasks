# GitLab Daily Task Viewer

A lightweight Flask-based web app that fetches daily GitLab issues and formats them for team standups. Each user is associated with a GitLab token, role, and metadata for categorizing their tasks into TODO, DOING, REVIEW, or DEPLOYED sections.

---

## 🚀 Features

* Categorizes issues from GitLab by label and state
* One-click copyable task summary
* Admin UI to add and update users
* Role-aware (job title) support for programmers, QA, etc.
* SQLite-based lightweight storage
* Dockerized and environment-based configuration

---

## 🛠️ Setup Instructions

### 1. Clone the Repo

```bash
git clone https://your.repo.url.git
dcd gitlab-task-viewer
```

### 2. Add a `.env` file

```
FLASK_ENV=dev
SECRET_KEY=super-secret-key
ADMIN_PASSWORD=your_admin_password
```

Set `FLASK_ENV=prod` in production to enable admin login.

### 3. Build and Run via Docker

```bash
docker build -t gitlab-task-viewer .
docker run -p 5000:5000 gitlab-task-viewer
```

Or using Docker Compose:

```bash
docker-compose up --build
```

---

## 🔗 Routes

| Route             | Description                |
| ----------------- | -------------------------- |
| `/`               | Main task viewer page      |
| `/admin/add-user` | Add new user to the system |
| `/admin/users`    | List and update users      |

In `prod` mode, admin routes require login using `ADMIN_PASSWORD`.

---

## 👤 User Model Fields

* `display_name`
* `team_lead`
* `gitlab_username`
* `token`
* `job_title` (e.g., Programmer, QA, PM)

---

## 🧠 How Categorization Works

Based on GitLab labels:

* `DO::To Do` → TODO
* `DO::Doing` → DOING
* `DO::Approved` → READY FOR REVIEW
* `state=closed` → DEPLOYED
* others → Uncategorized

The output is rendered in monospace style and optimized for copy/paste in chat.

---

## 📝 Sample Output

```
MEMBER : Puvaan Raaj  [TL: Singh]
========================== TODO ============================
❗ [P1] Implement login
🗣 Team: Puvaan
🕙 Opened: 20-09-2024 14:22:10
🔗 https://...

========================== DOING ============================
❗ [P2] Add Tailwind UI
...
```

---

## 🔐 Security Notes

* Use a strong `ADMIN_PASSWORD` in `.env`
* Admin pages auto-protect in `prod`
* Tokens are stored in SQLite; use encryption for production if needed

---

## 📬 License

MIT — free to use and customize.
