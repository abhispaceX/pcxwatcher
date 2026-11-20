import threading
import time
import requests
import logging
import sys
from flask import Flask
from playwright.sync_api import sync_playwright
from playwright.sync_api import BrowserContext

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

BOOKING_URL = "https://in.bookmyshow.com/cinemas/hyderabad/prasads-multiplex-hyderabad/buytickets/PRHN/20261217"
X_HANDLES = ["PrasadsCinemas"]
X_KEYWORDS = ["doomsday", "pcx", "screen 6", "bookings"]
NTFY_TOPIC = "abhi_pcx_screen6_alarm_8842"

seen_tweets = set()

def trigger_alarm(title: str, message: str):
    """Sends a Priority 5 (Max/Urgent) alert to ntfy."""
    try:
        requests.post(
            f"https://ntfy.sh/{NTFY_TOPIC}",
            data=message.encode("utf-8"),
            headers={
                "Title": title,
                "Priority": "5",
                "Tags": "rotating_light,alarm_clock,ticket",
                "Click": BOOKING_URL,
            },
            timeout=5,
        )
        logger.info("🔔 Alert sent to phone!")
    except Exception as e:
        logger.error(f"Failed to send ntfy alert: {e}")

def check_bookmyshow(page) -> bool:
    """Check BookMyShow for PCX availability."""
    try:
        page.goto(BOOKING_URL, wait_until="domcontentloaded", timeout=15000)
        page.wait_for_timeout(2000)

        movie_blocks = page.locator("li:has-text('Avengers: Doomsday')").all_inner_texts()
        for block in movie_blocks:
            if "PCX" in block.upper():
                summary = " ".join(block.split())[:120]
                logger.warning("🔥 BMS PCX DETECTED!")
                trigger_alarm("🚨 PRASADS PCX TICKETS OPEN!", f"PCX Screen 6 is LIVE! {summary}")
                return True
    except Exception as e:
        logger.debug(f"BMS check error: {e}")
    return False

def check_x_handles(page) -> bool:
    """Check X handles for PCX updates."""
    for handle in X_HANDLES:
        try:
            url = f"https://x.com/{handle}"
            page.goto(url, wait_until="domcontentloaded", timeout=15000)
            page.wait_for_timeout(2500)

            tweets = page.locator("article[data-testid='tweet']").all_inner_texts()[:3]
            for raw_tweet in tweets:
                clean = " ".join(raw_tweet.split())
                tweet_key = f"{handle}:{clean[:80]}"
                if tweet_key in seen_tweets:
                    continue
                seen_tweets.add(tweet_key)

                lower = clean.lower()
                if "doomsday" in lower and any(k in lower for k in X_KEYWORDS):
                    logger.warning(f"🐦 X ALERT from @{handle}!")
                    trigger_alarm(f"🚨 @{handle} TWEETED PCX UPDATE!", clean[:180])
                    return True
        except Exception as e:
            logger.debug(f"X check error for @{handle}: {e}")
    return False

def watcher_loop():
    """Main watcher loop running in background."""
    max_retries = 5
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            with sync_playwright() as p:
                logger.info("🚀 Launching Chromium browser...")
                browser = p.chromium.launch(headless=True)
                page = browser.new_page(
                    user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/131.0.0.0 Safari/537.36"
                )
                
                logger.info("✅ Watcher started! Checking every 20s (X every 60s)")
                
                cycle = 0
                while True:
                    try:
                        # Check BookMyShow every cycle
                        if check_bookmyshow(page):
                            browser.close()
                            logger.info("🎉 PCX found! Stopping watcher.")
                            return

                        # Check X handles every 3rd cycle to avoid rate limits
                        if cycle % 3 == 0:
                            if check_x_handles(page):
                                browser.close()
                                logger.info("🎉 X alert found! Stopping watcher.")
                                return

                        logger.info("✓ Checked BMS + X — no PCX drop yet.")
                        cycle += 1
                        time.sleep(20)
                    except Exception as e:
                        logger.error(f"⚠️ Check error: {e}")
                        cycle += 1
                        time.sleep(20)
        except Exception as e:
            retry_count += 1
            logger.error(f"🔴 Watcher crashed (attempt {retry_count}/{max_retries}): {e}")
            if retry_count < max_retries:
                logger.info(f"Retrying in 30 seconds...")
                time.sleep(30)
            else:
                logger.critical(f"Max retries exceeded. Watcher stopped.")
                break

# Start background watcher thread on app startup
logger.info("🌐 PCX Watcher Flask server starting...")
threading.Thread(target=watcher_loop, daemon=True).start()

@app.route("/")
def health():
    """Health check endpoint for Render keep-alive."""
    return "✅ PCX Watcher Active (checks every 20s, X every 60s)", 200

@app.route("/status")
def status():
    """Extended status endpoint."""
    return {
        "status": "running",
        "booking_url": BOOKING_URL,
        "ntfy_topic": NTFY_TOPIC,
        "x_handles": X_HANDLES,
        "timestamp": time.strftime('%Y-%m-%d %H:%M:%S')
    }, 200

if __name__ == "__main__":
    logger.info("🚀 Starting Flask server on 0.0.0.0:5000")
    app.run(host="0.0.0.0", port=5000, debug=False)
