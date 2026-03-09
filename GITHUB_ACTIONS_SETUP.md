# GitHub Actions Setup - Adding Database Secret

To enable the automated weekly cleanup via GitHub Actions, you need to add your database connection string as a secret.

## Steps to Add the Secret

### 1. Go to Your Repository Settings

1. Open your GitHub repository: https://github.com/prismabots/telegramForward
2. Click on **Settings** (top menu)
3. In the left sidebar, click **Secrets and variables** → **Actions**

### 2. Add New Repository Secret

1. Click the **New repository secret** button
2. Fill in the form:
   - **Name:** `BACKUP_DB_ADMIN_URL`
   - **Secret:** Paste your full database connection string (from DigitalOcean)
3. Click **Add secret**

### 3. Verify the Workflow

Once the secret is added:

1. Go to the **Actions** tab in your repository
2. You should see "Weekly Message Cleanup" workflow
3. You can trigger it manually by:
   - Click on "Weekly Message Cleanup"
   - Click "Run workflow"
   - Select "main" branch
   - Click the green "Run workflow" button

### 4. Check the Results

After running:
1. Click on the workflow run to see details
2. Expand the "Run cleanup script" step
3. You'll see how many messages were deleted from each channel

## Automatic Schedule

The workflow will now run **automatically every Sunday at 2:00 AM UTC**.

You can also trigger it manually anytime from the Actions tab.

## What It Does

- ✅ Deletes messages older than 7 days
- ✅ Shows summary of what was deleted per channel
- ✅ Keeps recent messages for reply threading
- ✅ Runs securely using GitHub's infrastructure
- ✅ No need for server access or cron jobs

## Troubleshooting

### Workflow Fails

If the workflow fails, check:
1. Is the `BACKUP_DB_ADMIN_URL` secret set correctly?
2. Can GitHub reach your database? (Check firewall rules)
3. Look at the error message in the workflow logs

### Want to Change the Schedule?

Edit `.github/workflows/cleanup.yml` and change the cron expression:

```yaml
schedule:
  # Examples:
  - cron: '0 2 * * 0'   # Sunday at 2 AM (current)
  - cron: '0 3 * * 1'   # Monday at 3 AM
  - cron: '0 0 * * *'   # Daily at midnight
  - cron: '0 2 1 * *'   # 1st of every month at 2 AM
```

### Want to Change Retention Period?

Edit `.github/workflows/cleanup.yml` and change:

```yaml
env:
  MESSAGE_RETENTION_DAYS: 14  # Keep 14 days instead of 7
```

That's it! Your cleanup is now fully automated! 🎉
