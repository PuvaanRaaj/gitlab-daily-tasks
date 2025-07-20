# 🧠 GitLab Daily Tasks Tracker

A Flask web application to help team leads and developers view daily GitLab issues categorized by status. The system supports user management, GitLab API integration, and task grouping based on custom labels.

## 🚀 Features

* 🧑‍💼 Manage users and assign GitLab usernames
* 📊 View GitLab issues categorized by:

  * TODO
  * DOING
  * READY FOR REVIEW
  * DEPLOYED
* 🔐 Secure token storage using environment variables
* 🗃️ SQLite database for user records
* 🌐 Web UI for admin tasks and issue views

## 📦 Requirements

* Python 3.11+
* GitLab API access token
* Docker (for containerized deployment)

## 🐳 Docker Setup

```bash
docker build -t gitlab-daily-tasks .
docker run -p 5000:5000 --env-file .env gitlab-daily-tasks
```

## 📝 .env Example

```
SECRET_KEY=your-super-secret-key
```

## 🛠️ Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run app locally
python app.py
```

## 📁 File Structure

* `app.py` - Main Flask app
* `templates/` - HTML templates
* `static/` - Static assets (optional)
* `users.db` - SQLite database (auto-created)

## 🤖 GitHub PR Code Review (Optional)

To enable AI-driven pull request reviews, use the provided GitHub Actions workflow (`.github/workflows/pr-review.yml`). It runs a containerized LLM to review diff changes.

## 🔄 In Process / Enhancements

* [x] GitLab issue integration
* [x] Basic user management
* [x] Docker containerization
* [x] CI/CD integration
* [x] Dark mode UI toggle
* [ ] Email notifications for tasks
* [ ] Role-based access control

## 📃 License

MIT License
