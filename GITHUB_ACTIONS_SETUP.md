# GitHub Actions Setup Guide

This guide explains how to set up automated daily scraping using GitHub Actions.

## Overview

The project includes two GitHub Actions workflows:

1. **Daily Scraper** (`.github/workflows/daily_scrape.yml`)
   - Runs daily at 6:00 AM UTC (8:00 AM Poland time)
   - Scrapes job boards for new postings (currently NoFluffJobs)
   - Processes data through ETL pipeline
   - Commits updated database to repository
   - Creates GitHub issues on failure

2. **Statistics Updater** (`.github/workflows/update_stats.yml`)
   - Runs after successful scrape
   - Updates README with latest statistics
   - Commits changes automatically

## Prerequisites

### 1. GitHub Repository Setup

Your project must be in a GitHub repository:

```bash
# Initialize git if not already done
git init

# Add all files
git add .

# Create initial commit
git commit -m "Initial commit: Tech Jobs Tracker"

# Create GitHub repository (via GitHub website)
# Then push to GitHub
git remote add origin https://github.com/YOUR_USERNAME/tech-jobs-tracker.git
git branch -M main
git push -u origin main
```

### 2. Enable GitHub Actions

GitHub Actions is enabled by default on public repositories. For private repositories:

1. Go to repository **Settings** → **Actions** → **General**
2. Under "Actions permissions", select **Allow all actions and reusable workflows**
3. Under "Workflow permissions", select **Read and write permissions**
4. Check **Allow GitHub Actions to create and approve pull requests**
5. Click **Save**

### 3. Database Considerations

**Option A: Commit Database (Recommended for small datasets)**

The database is configured to be committed to the repository:
- Good for: Datasets under 100 MB
- Pros: Simple, no external dependencies
- Cons: Repository size grows over time

**Option B: Use Git LFS (For large datasets)**

If your database grows beyond 50 MB:

```bash
# Install Git LFS
git lfs install

# Track database file
git lfs track "data/jobs.db"

# Add .gitattributes
git add .gitattributes
git commit -m "Add Git LFS for database"
```

**Option C: External Storage (For very large datasets)**

Store database in external service (S3, Cloudflare R2, etc.) and download/upload in workflow.

## Workflow Configuration

### Daily Scraper Workflow

**File:** `.github/workflows/daily_scrape.yml`

**Schedule:**
- Runs daily at 6:00 AM UTC (8:00 AM Poland time)
- Can be triggered manually from Actions tab

**What it does:**
1. Checks out repository code
2. Sets up Python 3.11
3. Installs dependencies
4. Initializes database if needed
5. Runs ETL pipeline (scrape → extract → transform → load)
6. Commits updated database to repository
7. Uploads logs as artifacts
8. Creates GitHub issue on failure

**Configuration Options:**

Edit `.github/workflows/daily_scrape.yml` to customize:

```yaml
# Change schedule (use cron format)
schedule:
  - cron: '0 6 * * *'  # 6:00 AM UTC daily

# Change maximum jobs to scrape
env:
  MAX_JOBS: 1000
```

**Cron Schedule Examples:**
- `0 6 * * *` - Daily at 6:00 AM UTC
- `0 */12 * * *` - Every 12 hours
- `0 6 * * 1` - Every Monday at 6:00 AM UTC
- `0 6 1 * *` - First day of month at 6:00 AM UTC

### Statistics Update Workflow

**File:** `.github/workflows/update_stats.yml`

**Triggers:**
- Automatically after successful scraper run
- Manual trigger from Actions tab

**What it does:**
1. Generates database statistics
2. Updates README with latest stats
3. Commits changes

## Manual Triggering

### Run Scraper Manually

1. Go to your repository on GitHub
2. Click **Actions** tab
3. Select **Daily NoFluffJobs Scraper** workflow
4. Click **Run workflow** button
5. (Optional) Set maximum jobs to scrape
6. Click **Run workflow**

### View Results

1. Click on the running/completed workflow
2. View job logs in real-time
3. Check **Summary** for overview
4. Download artifacts (logs) if needed

## Monitoring & Notifications

### Viewing Logs

**In GitHub Actions:**
1. Go to **Actions** tab
2. Click on workflow run
3. Click on job name
4. Expand step to view logs

**Download Logs:**
1. Scroll to bottom of workflow run page
2. Under **Artifacts**, download `scraper-logs-XXX`
3. Unzip to view log files

### Failure Notifications

When scraper fails:
1. **GitHub Issue** is automatically created
   - Labels: `automation`, `bug`, `scraper-failure`
   - Contains link to failed workflow run

2. **Email Notification** (if enabled)
   - Go to GitHub **Settings** → **Notifications**
   - Enable "Actions" notifications

### Success Verification

After successful run:
1. Check repository commits for new "chore: update job data" commit
2. View updated database in `data/jobs.db`
3. Check workflow summary for statistics

## Troubleshooting

### Workflow Fails: Permission Denied

**Problem:** Workflow can't commit changes

**Solution:**
1. Go to repository **Settings** → **Actions** → **General**
2. Under "Workflow permissions", select **Read and write permissions**
3. Save and re-run workflow

### Workflow Fails: Database Error

**Problem:** Database initialization fails

**Solution:**
1. Check if `data/` directory exists in repository
2. Run workflow with manual trigger
3. Check logs for specific error message
4. May need to initialize database manually:
   ```bash
   python scripts/init_database.py
   git add data/jobs.db
   git commit -m "Initialize database"
   git push
   ```

### Workflow Doesn't Trigger on Schedule

**Problem:** Scheduled workflow doesn't run

**Possible causes:**
1. **Repository inactive:** GitHub disables scheduled workflows after 60 days of no activity
   - Solution: Make a commit or manually run workflow

2. **Incorrect cron syntax:** Verify cron expression
   - Use: https://crontab.guru/ to validate

3. **Actions disabled:** Check repository settings
   - Settings → Actions → General → Enable Actions

### Rate Limiting / Blocked by Website

**Problem:** Scraper gets blocked or rate limited

**Solution:**
1. Increase delays in `config/scraper_config.yaml`:
   ```yaml
   rate_limiting:
     min_delay_seconds: 5  # Increase from 2
     max_delay_seconds: 10  # Increase from 5
   ```

2. Reduce jobs per run:
   ```yaml
   scraping:
     max_jobs_per_run: 100  # Reduce from 1000
   ```

3. Check robots.txt compliance

4. Consider running less frequently (weekly instead of daily)

### Repository Size Too Large

**Problem:** Database makes repository too large

**Solutions:**
1. **Use Git LFS** (see Option B above)

2. **Clean old snapshots:**
   ```sql
   DELETE FROM job_snapshots WHERE snapshot_date < date('now', '-90 days');
   DELETE FROM salaries WHERE snapshot_date < date('now', '-90 days');
   DELETE FROM job_technologies WHERE snapshot_date < date('now', '-90 days');
   ```

3. **Vacuum database:**
   ```bash
   sqlite3 data/jobs.db "VACUUM;"
   ```

4. **Move to external storage** (Option C above)

## Best Practices

### 1. Monitor Workflow Runs

Check Actions tab weekly to ensure scraper is running successfully.

### 2. Review Issues

Address any auto-created issues promptly.

### 3. Database Maintenance

Run maintenance every 3-6 months:
```bash
# Backup database
cp data/jobs.db data/jobs_backup.db

# Vacuum to reduce size
sqlite3 data/jobs.db "VACUUM;"

# Remove old snapshots (keep 90 days)
sqlite3 data/jobs.db "DELETE FROM job_snapshots WHERE snapshot_date < date('now', '-90 days');"
```

### 4. Keep Dependencies Updated

Update dependencies monthly:
```bash
pip list --outdated
pip install --upgrade package-name
pip freeze > requirements.txt
```

### 5. Respect Website Terms

- Follow NoFluffJobs robots.txt
- Use respectful rate limiting
- Don't hammer server on failures
- Consider running during off-peak hours

## Advanced Configuration

### Custom Workflow Variables

Add repository secrets for sensitive configuration:

1. Go to **Settings** → **Secrets and variables** → **Actions**
2. Click **New repository secret**
3. Add secrets (e.g., API keys, database URLs)
4. Reference in workflow:
   ```yaml
   env:
     API_KEY: ${{ secrets.MY_API_KEY }}
   ```

### Multiple Schedules

Run different configurations at different times:

```yaml
on:
  schedule:
    # Full scrape daily at 6 AM
    - cron: '0 6 * * *'
    # Quick update at 2 PM
    - cron: '0 14 * * *'
```

Use workflow inputs to differentiate:
```yaml
jobs:
  scrape:
    steps:
      - name: Run scraper
        run: |
          if [ "${{ github.event.schedule }}" == "0 14 * * *" ]; then
            python scripts/run_etl.py --max-jobs 50
          else
            python scripts/run_etl.py
          fi
```

### Notifications to Slack/Discord

Add notification step:

```yaml
- name: Notify Slack
  if: failure()
  uses: slackapi/slack-github-action@v1
  with:
    webhook-url: ${{ secrets.SLACK_WEBHOOK_URL }}
    payload: |
      {
        "text": "Scraper failed: ${{ github.server_url }}/${{ github.repository }}/actions/runs/${{ github.run_id }}"
      }
```

## Testing Workflows Locally

Use `act` to test workflows locally before pushing:

```bash
# Install act
# Windows: choco install act
# Mac: brew install act
# Linux: See https://github.com/nektos/act

# Run workflow locally
act -j scrape-and-update

# Run with specific event
act workflow_dispatch
```

## Cost Considerations

GitHub Actions is **free** for public repositories with:
- Unlimited minutes
- Unlimited storage for artifacts (90-day retention)

For private repositories:
- **Free tier:** 2,000 minutes/month
- **Storage:** 500 MB free
- This project uses ~10-20 minutes per run (daily = ~300-600 minutes/month)

## Support

If you encounter issues:

1. Check workflow logs in Actions tab
2. Review troubleshooting section above
3. Check GitHub Actions status: https://www.githubstatus.com/
4. Create an issue in the repository

## Next Steps

1. **Push to GitHub:**
   ```bash
   git add .
   git commit -m "Add GitHub Actions automation"
   git push
   ```

2. **Verify Workflows:**
   - Go to Actions tab
   - Manually trigger "Daily NoFluffJobs Scraper"
   - Wait for completion
   - Check if database was updated

3. **Set Up Monitoring:**
   - Enable email notifications
   - Star repository to follow updates
   - Check Actions tab weekly

4. **Optional: Deploy Dashboard:**
   - Deploy to Streamlit Cloud
   - Connect to your GitHub repository
   - Auto-updates with new data!

---

**Happy Scraping! 🚀**
