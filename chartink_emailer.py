from playwright.sync_api import sync_playwright
import smtplib
from email.mime.text import MIMEText
from datetime import datetime
import pytz
import os

def fetch():
    print("🔍 [FETCH] Launching Playwright Chromium...")
    url = "https://chartink.com/screener/volumeshocker-p-100-2"
    data = []

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            print("🧠 [FETCH] Chromium launched.")
            page = browser.new_page()
            page.goto(url, timeout=60000)
            print("🌐 [FETCH] Navigated to Chartink URL.")

            # Wait for table to appear
            page.wait_for_selector("table.table tbody tr", timeout=15000)
            print("✅ [FETCH] Table rows found.")

            rows = page.query_selector_all("table.table tbody tr")
            print(f"📊 [FETCH] Total rows fetched: {len(rows)}")

            for row in rows:
                cols = row.query_selector_all("td")
                if len(cols) < 5:
                    print("⚠️ [FETCH] Skipping row with insufficient columns")
                    continue

                symbol = cols[2].inner_text().strip()
                name = cols[1].inner_text().strip()
                price = cols[4].inner_text().strip()

                stock = {
                    "nsecode": symbol,
                    "name": name,
                    "close": price
                }
                print(f"🧾 [FETCH] Row parsed: {stock}")
                data.append(stock)

            browser.close()
            print("🛑 [FETCH] Browser closed.")

    except Exception as e:
        print(f"❌ [FETCH ERROR] {e}")
    
    return data

def send(data):
    print("📧 [SEND] Preparing email...")
    me = os.environ.get("EMAIL_SENDER")
    pwd = os.environ.get("EMAIL_PASSWORD")
    you = os.environ.get("EMAIL_RECEIVER")

    now = datetime.now(pytz.timezone("Asia/Kolkata")).strftime("%Y-%m-%d %H:%M:%S")
    body = f"📈 Chartink Volume Shocker Update — {now}\n\n"

    if not data:
        body += "No stocks triggered in this scan."
        print("⚠️ [SEND] No data to send.")
    else:
        for s in data:
            line = f"{s['nsecode']} | {s['name']} | ₹{s['close']}"
            print(f"📩 [SEND] {line}")
            body += line + "\n"

    msg = MIMEText(body)
    msg["Subject"] = "🔔 Chartink Volume Shockers"
    msg["From"] = me
    msg["To"] = you

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(me, pwd)
            smtp.send_message(msg)
            print("✅ [SEND] Email sent successfully.")
    except Exception as e:
        print(f"❌ [SEND ERROR] {e}")

def main():
    print("🚀 [MAIN] Starting Chartink Emailer at", datetime.now().isoformat())
    data = fetch()
    print(f"📦 [MAIN] Fetched {len(data)} entries.")
    send(data)
    print("🏁 [MAIN] Script completed.")

if __name__ == "__main__":
    main()
