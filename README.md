# PCX Watcher - BookMyShow + X Monitor

This watcher monitors BookMyShow and X (Twitter) for Prasads PCX ticket availability and sends alerts to your phone via ntfy.

## Setup & Usage

### Option 1: Run Locally (for testing)

```bash
# Install dependencies
pip install -r requirements.txt
playwright install chromium

# Run watcher
python watcher.py
```

**On first run:**
- The browser will open (headless=False in watcher.py)
- Sign into X.com and authorize the app
- After login, the script saves your session to `./watcher_chrome_profile`
- Change `headless=False` to `headless=True` and restart to run headless

---

### Option 2: Deploy on Render (24/7 Monitoring - FREE)

**Advantages:**
- Runs 24/7 without your MacBook powered on
- Free tier ($0/month)
- Automatically restarts if it crashes
- Phone alarms even when you're away

**Steps:**

1. **Push to GitHub:**
   ```bash
   git init
   git add app.py requirements.txt
   git commit -m "Add PCX Watcher"
   git push origin main
   ```

2. **Deploy on Render.com:**
   - Go to [render.com](https://render.com) → Sign in with GitHub
   - Click **New + → Web Service** → Select your repo
   - **Build Command:** 
     ```
     pip install -r requirements.txt && playwright install chromium
     ```
   - **Start Command:** 
     ```
     gunicorn app:app --bind 0.0.0.0:$PORT --workers 1
     ```
   - Select **Free** tier → Click **Deploy**
   - Wait 2-3 minutes. Check **Logs** tab—you should see "Checked BMS + X" every 20 seconds

3. **Prevent Render Sleep (1 Minute):**
   - Free tier sleeps after 15 minutes of no HTTP traffic
   - Go to [cron-job.org](https://cron-job.org) → Create account
   - Click **Create Cronjob**
   - Paste your Render URL: `https://your-app.onrender.com/`
   - Set schedule to **Every 5 minutes**
   - Click **Save** ✅

**Result:** Your watcher pings Render every 5 minutes → stays awake 24/7 while checking BookMyShow every 20 seconds nonstop. Completely free.

---

## Configuration

Edit the constants in `app.py` or `watcher.py`:

```python
BOOKING_URL = "https://in.bookmyshow.com/cinemas/hyderabad/prasads-multiplex-hyderabad/buytickets/PRHN/20261217"
X_HANDLES = ["PrasadsCinemas"]  # Add more X handles here
X_KEYWORDS = ["doomsday", "pcx", "screen 6", "bookings"]
NTFY_TOPIC = "abhi_pcx_screen6_alarm_8842"  # Must match your phone's ntfy subscription
```

---

## Phone Alerts

1. Install [ntfy.sh](https://ntfy.sh/) app on your phone
2. Subscribe to topic: `abhi_pcx_screen6_alarm_8842`
3. Set to **Priority 5** (Max Alarm) mode
4. When PCX drops, your phone will ring with an alarm + clicking the notification opens BookMyShow

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| "Chromium not found" | Run: `playwright install chromium` |
| Render keeps sleeping | Did you set up cron-job.org? Check it runs every 5 min |
| No ntfy alerts | Verify NTFY_TOPIC matches your phone subscription |
| Browser login fails (local) | Ensure `headless=False` on first run, then switch to `headless=True` |

---

## Files

- `app.py` - Flask server for Render deployment
- `watcher.py` - Standalone script for local testing
- `requirements.txt` - Python dependencies
- `README.md` - This file
