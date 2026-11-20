import time
import webbrowser
import requests
from playwright.sync_api import sync_playwright

# --- CONFIGURATION ---
BOOKING_URL = "https://in.bookmyshow.com/cinemas/hyderabad/prasads-multiplex-hyderabad/buytickets/PRHN/20261217"

# Add the X handles you want to watch (without '@')
X_HANDLES = ["PrasadsCinemas"]
X_KEYWORDS = ["doomsday", "pcx", "screen 6", "bookings"]

# Subscribe to this exact topic in your phone's ntfy app with Priority 5 alarm mode enabled
NTFY_TOPIC = "abhi_pcx_screen6_alarm_8842"

# Stores your X login session locally so you only sign in once
BROWSER_PROFILE_DIR = "./watcher_chrome_profile"
# ---------------------

seen_tweets = set()

def trigger_phone_alarm(title: str, message: str, click_url: str):
    """Sends a Priority 5 (Max/Urgent) alert that loops like an alarm in the ntfy app."""
    try:
        requests.post(
            f"https://ntfy.sh/{NTFY_TOPIC}",
            data=message.encode("utf-8"),
            headers={
                "Title": title,
                "Priority": "5",
                "Tags": "rotating_light,alarm_clock,ticket",
                "Click": click_url,
            },
            timeout=5,
        )
    except Exception as e:
        print(f"Failed to send ntfy alert: {e}")

def check_bookmyshow(page) -> bool:
    page.goto(BOOKING_URL, wait_until="domcontentloaded", timeout=15000)
    page.wait_for_timeout(2000)

    movie_blocks = page.locator("li:has-text('Avengers: Doomsday')").all_inner_texts()
    for block in movie_blocks:
        if "PCX" in block.upper():
            summary = " ".join(block.split())[:120]
            print(f"\n[{time.strftime('%H:%M:%S')}] 🔥 BMS PCX DETECTED! Ringing phone alarm...")
            trigger_phone_alarm(
                "🚨 PRASADS PCX TICKETS OPEN!",
                f"PCX Screen 6 is LIVE on BookMyShow! {summary}",
                BOOKING_URL,
            )
            webbrowser.open(BOOKING_URL)
            return True
    return False

def check_x_handles(page) -> bool:
    for handle in X_HANDLES:
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
                print(f"\n[{time.strftime('%H:%M:%S')}] 🐦 X ALERT from @{handle}! Ringing phone alarm...")
                trigger_phone_alarm(
                    f"🚨 @{handle} TWEETED PCX UPDATE!",
                    f"{clean[:180]} — Tap to open BookMyShow.",
                    BOOKING_URL,
                )
                webbrowser.open(BOOKING_URL)
                return True
    return False

def main():
    with sync_playwright() as p:
        # First-time setup: launch visible browser if needed so you can log into X once
        context = p.chromium.launch_persistent_context(
            user_data_dir=BROWSER_PROFILE_DIR,
            headless=False,  # Change to True after you sign into x.com on the first run
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        )
        page = context.new_page()

        print("Watcher started (BookMyShow PRHN + X Handles). Press Ctrl+C to stop.\n")
        cycle = 0

        while True:
            try:
                # 1. Check BookMyShow every cycle (~15s)
                if check_bookmyshow(page):
                    break

                # 2. Check X handles every 3rd cycle (~45s) to avoid X rate limits
                if cycle % 3 == 0:
                    if check_x_handles(page):
                        break

                print(f"[{time.strftime('%H:%M:%S')}] Checked BMS + X — no PCX drop yet.")
            except Exception as e:
                print(f"[{time.strftime('%H:%M:%S')}] Hiccup, retrying: {e}")

            cycle += 1
            time.sleep(15)

        context.close()

if __name__ == "__main__":
    main()
