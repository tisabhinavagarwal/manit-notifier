# MANIT Notice Notifier

Checks https://www.manit.ac.in/notices-circulars every 10 minutes using free GitHub Actions
and sends a push notification to your phone through [ntfy](https://ntfy.sh) when a new notice is posted.
Tapping the notification opens the notice PDF.

## Setup (about 5 minutes)

1. **Phone:** install the **ntfy** app (Play Store / App Store). Tap **+** and subscribe to the topic
   `<your-topic>` (keep it secret; anyone who knows it can read your notifications).
   On Android, open the app's settings and turn off battery optimisation for ntfy so notifications arrive instantly.
2. **GitHub:** create a new repository (a **public** repo gets unlimited free Actions minutes) and push this folder:
   ```
   git init
   git add .
   git commit -m "MANIT notice notifier"
   git branch -M main
   git remote add origin https://github.com/<you>/<repo>.git
   git push -u origin main
   ```
3. In the repo go to **Settings → Secrets and variables → Actions → New repository secret**:
   name `NTFY_TOPIC`, value `<your-topic>`.
4. Go to the **Actions** tab, enable workflows if asked, open **MANIT notice check** and click **Run workflow**
   once to confirm it goes green.

## Test a notification

From any terminal: `curl -d "Test notice" ntfy.sh/<your-topic>` (it should appear on your phone).

## Notes

- `seen.json` holds the notices already seen. Delete it to re-seed (the first run never sends notifications).
- GitHub disables scheduled workflows in repos with no activity for 60 days. The bot's own commits on new notices
  normally keep it alive; if you ever get an email saying it was disabled, re-enable it from the Actions tab.
- If the run fails with "No notices parsed", the website's layout changed or the site was down.
