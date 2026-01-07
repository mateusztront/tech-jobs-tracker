# Git Setup & GitHub Deployment Guide

## Initial Git Setup

### 1. Initialize Git Repository (if not already done)

```bash
cd nofluffjobs-dashboard
git init
```

### 2. Configure Git (first time only)

```bash
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"
```

### 3. Stage All Files

```bash
# Add all project files
git add .

# Verify what will be committed
git status
```

### 4. Create Initial Commit

```bash
git commit -m "Initial commit: NoFluffJobs IT Market Dashboard

Complete data engineering project with:
- Web scraper with ethical rate limiting
- ETL pipeline for data processing
- Streamlit dashboard with 19 visualizations
- GitHub Actions for daily automation
- Comprehensive documentation

Tech stack: Python, SQLite, Streamlit, Plotly, BeautifulSoup, GitHub Actions"
```

## Create GitHub Repository

### Option A: Via GitHub Website

1. Go to https://github.com/new
2. Fill in repository details:
   - **Name**: `nofluffjobs-dashboard`
   - **Description**: "IT job market analytics dashboard scraping NoFluffJobs daily"
   - **Visibility**: Public (recommended for portfolio) or Private
   - **DO NOT** initialize with README (you already have one)
3. Click "Create repository"

### Option B: Via GitHub CLI

```bash
# Install GitHub CLI first: https://cli.github.com/

# Login
gh auth login

# Create repository
gh repo create nofluffjobs-dashboard --public --source=. --remote=origin --push
```

## Connect Local Repository to GitHub

If you used Option A (website), run these commands:

```bash
# Add remote
git remote add origin https://github.com/YOUR_USERNAME/nofluffjobs-dashboard.git

# Rename branch to main (if needed)
git branch -M main

# Push to GitHub
git push -u origin main
```

## Verify Upload

```bash
# Check remote connection
git remote -v

# Should show:
# origin  https://github.com/YOUR_USERNAME/nofluffjobs-dashboard.git (fetch)
# origin  https://github.com/YOUR_USERNAME/nofluffjobs-dashboard.git (push)
```

## Important: Database Handling

The database file (`data/jobs.db`) is configured to be committed by GitHub Actions.

### For Local Development

If you want to ignore the database locally but let GitHub Actions commit it:

```bash
# Add to .git/info/exclude (local gitignore)
echo "data/jobs.db" >> .git/info/exclude
```

### For Initial Push

The sample database should be committed for the first push:

```bash
# Ensure database is included
git add -f data/jobs.db
git commit -m "Add sample database for initial deployment"
git push
```

## Enable GitHub Actions

### 1. Set Repository Permissions

1. Go to your repository on GitHub
2. Click **Settings** tab
3. In left sidebar, click **Actions** → **General**
4. Scroll to "Workflow permissions"
5. Select **"Read and write permissions"**
6. Check **"Allow GitHub Actions to create and approve pull requests"**
7. Click **Save**

### 2. Verify Workflows

1. Go to **Actions** tab
2. You should see 2 workflows:
   - Daily NoFluffJobs Scraper
   - Update Dashboard Statistics
3. They will show as "Waiting" or "Scheduled"

### 3. Manual Test Run

1. Click "Daily NoFluffJobs Scraper"
2. Click "Run workflow" button (top right)
3. Select branch: `main`
4. Click "Run workflow"
5. Wait for completion
6. Check logs and results

## Typical Git Workflow

### Making Changes

```bash
# Create feature branch (optional but recommended)
git checkout -b feature/your-feature-name

# Make changes to files...

# Stage changes
git add .

# Commit with descriptive message
git commit -m "feat: add new visualization for skill trends

- Added skill trend chart to dashboard
- Updated data loader with new query
- Added documentation for new feature"

# Push to GitHub
git push origin feature/your-feature-name

# Or if on main branch:
git push origin main
```

### Syncing with GitHub Actions Changes

GitHub Actions will automatically commit database updates. To sync:

```bash
# Pull latest changes (includes database updates from Actions)
git pull origin main

# If you have local changes, use rebase
git pull --rebase origin main
```

### Resolving Conflicts

If database was modified both locally and by Actions:

```bash
# Fetch latest
git fetch origin

# Use GitHub Actions version (recommended)
git checkout origin/main -- data/jobs.db

# Or keep local version
git checkout HEAD -- data/jobs.db

# Commit resolution
git commit -m "Resolve database conflict"
git push
```

## Branch Strategy

### Simple (Recommended for Solo Project)

```bash
# Work directly on main
git add .
git commit -m "Your changes"
git push
```

### Feature Branches (Best Practice)

```bash
# Create feature branch
git checkout -b feature/new-chart

# Make changes, commit
git add .
git commit -m "Add new salary comparison chart"

# Push feature branch
git push -u origin feature/new-chart

# Create PR on GitHub, review, then merge
```

## Useful Git Commands

### Status & Information

```bash
# Check status
git status

# View commit history
git log --oneline --graph --all

# View recent changes
git log -5 --oneline

# See what changed
git diff
```

### Undoing Changes

```bash
# Undo unstaged changes
git checkout -- filename

# Unstage file
git reset HEAD filename

# Undo last commit (keep changes)
git reset --soft HEAD~1

# Undo last commit (discard changes) - BE CAREFUL!
git reset --hard HEAD~1
```

### Cleaning Up

```bash
# Remove untracked files (dry run first!)
git clean -n

# Actually remove
git clean -f

# Remove directories too
git clean -fd
```

## GitHub Repository Settings

### Recommended Settings

1. **Branch Protection** (Settings → Branches)
   - Protect `main` branch
   - Require pull request reviews (optional for solo project)
   - Require status checks (optional)

2. **Topics** (main repository page)
   - Add topics: `python`, `data-engineering`, `web-scraping`, `streamlit`, `etl`, `dashboard`

3. **About Section**
   - Description: "IT job market analytics dashboard with automated daily scraping from NoFluffJobs"
   - Website: Your deployed Streamlit dashboard URL (if deployed)
   - Topics: data-engineering, web-scraping, etl-pipeline, streamlit, dashboard

4. **README Preview**
   - Ensure README.md renders correctly on GitHub
   - Add badges if desired (see below)

## Optional: Add Badges to README

Add at the top of README.md:

```markdown
![Python](https://img.shields.io/badge/Python-3.11+-blue)
![License](https://img.shields.io/badge/License-MIT-green)
![Status](https://img.shields.io/badge/Status-Active-success)
[![Scraper](https://github.com/YOUR_USERNAME/nofluffjobs-dashboard/actions/workflows/daily_scrape.yml/badge.svg)](https://github.com/YOUR_USERNAME/nofluffjobs-dashboard/actions/workflows/daily_scrape.yml)
```

## Deploying Dashboard to Streamlit Cloud

### 1. Prerequisites

- GitHub repository is public
- `requirements.txt` exists
- `src/dashboard/app.py` exists

### 2. Deployment Steps

1. Go to https://streamlit.io/cloud
2. Sign in with GitHub
3. Click "New app"
4. Select:
   - Repository: `YOUR_USERNAME/nofluffjobs-dashboard`
   - Branch: `main`
   - Main file path: `src/dashboard/app.py`
5. Click "Deploy"

### 3. Advanced Settings

Click "Advanced settings" before deploy:

- **Python version**: 3.11
- **Secrets**: None needed for this project
- **Resource settings**: Use defaults

### 4. Automatic Updates

Streamlit Cloud will automatically redeploy when you push to `main` branch.

## Troubleshooting Git Issues

### Large Files Warning

If you get "file too large" warning:

```bash
# Check file sizes
du -sh data/*

# If database is too large (>100 MB), use Git LFS
git lfs install
git lfs track "data/jobs.db"
git add .gitattributes
git commit -m "Add Git LFS for database"
git push
```

### Authentication Issues

```bash
# Use Personal Access Token instead of password
# Create token: GitHub → Settings → Developer settings → Personal access tokens
# Use token as password when prompted

# Or use SSH keys (recommended)
ssh-keygen -t ed25519 -C "your.email@example.com"
# Follow prompts
# Add SSH key to GitHub: Settings → SSH and GPG keys

# Change remote to SSH
git remote set-url origin git@github.com:YOUR_USERNAME/nofluffjobs-dashboard.git
```

### Commit History Messy

```bash
# Squash last N commits into one
git rebase -i HEAD~N

# In editor, change "pick" to "squash" for commits to combine
# Save and exit
# Edit commit message
# Force push (only if you haven't shared with others!)
git push --force
```

## Best Practices

1. **Commit Often**: Small, focused commits are better
2. **Descriptive Messages**: Explain why, not just what
3. **Pull Before Push**: Always `git pull` before `git push`
4. **Review Before Commit**: Use `git diff` and `git status`
5. **Don't Commit Secrets**: Never commit API keys, passwords, etc.
6. **Use `.gitignore`**: Already configured in project
7. **Backup Important Data**: Database is backed up in git, but keep local backups too

## Commit Message Convention

Use conventional commits format:

```
<type>: <subject>

<body>

<footer>
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting)
- `refactor`: Code refactoring
- `test`: Adding tests
- `chore`: Maintenance tasks

**Examples:**

```bash
git commit -m "feat: add technology co-occurrence analysis

- Implemented new chart showing which technologies appear together
- Added query to join job_technologies table
- Updated dashboard with new tab

Closes #23"
```

```bash
git commit -m "fix: resolve database locking issue in concurrent access

- Added connection pooling
- Implemented retry logic with backoff
- Updated documentation with threading notes"
```

```bash
git commit -m "docs: update README with deployment instructions

- Added Streamlit Cloud deployment section
- Included troubleshooting tips
- Fixed broken links"
```

## Checklist Before First Push

- [ ] Reviewed all files with `git status`
- [ ] Tested code locally (dashboard runs)
- [ ] Removed any secrets or API keys
- [ ] Updated README if needed
- [ ] Commit message is descriptive
- [ ] `.gitignore` is configured correctly
- [ ] Database is in acceptable state (sample data or empty)

## After Pushing

1. **Verify on GitHub**
   - Check files uploaded correctly
   - README displays properly
   - Code is readable

2. **Test GitHub Actions**
   - Go to Actions tab
   - Manually run workflow
   - Check for errors

3. **Deploy Dashboard** (optional)
   - Set up Streamlit Cloud
   - Test deployed version
   - Share link with others!

---

**Ready to push?** Run these commands:

```bash
git add .
git commit -m "Initial commit: Complete NoFluffJobs analytics dashboard"
git push -u origin main
```

Then visit your repository on GitHub and enable GitHub Actions!

**Questions?** Check:
- Git Documentation: https://git-scm.com/doc
- GitHub Guides: https://guides.github.com/
- Streamlit Cloud Docs: https://docs.streamlit.io/streamlit-community-cloud
