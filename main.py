from flask import Flask, jsonify
from threading import Thread
import smtplib
from email.mime.text import MIMEText
from datetime import datetime
import pytz
import os
from playwright.sync_api import sync_playwright

app = Flask(__name__)

def format_number(n):
    if n >= 1_000_000_000:
        return f"{n / 1_000_000_000:.2f}B"
    elif n >= 1_000_000:
        return f"{n / 1_000_000:.2f}M"
    elif n >= 1_000:
        return f"{n / 1_000:.2f}K"
    else:
        return f"{n:.2f}"

def fetch():
    print("🔍 [FETCH] Launching Playwright")
    url = "https://chartink.com/screener/volumeshocker-p-100-2"
    data = []
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(url, timeout=60000)
            page.wait_for_selector("table.table tbody tr", timeout=15000)
            rows = page.query_selector_all("table.table tbody tr")
            print(f"📊 [FETCH] Total rows: {len(rows)}")
            for row in rows:
                cols = row.query_selector_all("td")
                if len(cols) < 7:
                    continue
                try:
                    symbol = cols[2].inner_text().strip()
                    name = cols[1].inner_text().strip()
                    pct_chg_str = cols[4].inner_text().strip().replace("%", "")
                    price_str = cols[5].inner_text().strip().replace(",", "")
                    volume_str = cols[6].inner_text().strip().replace(",", "")
                    pct_chg = float(pct_chg_str)
                    price = float(price_str)
                    volume = float(volume_str)
                    turnover = format_number(price * volume)
                    stock = {
                        "nsecode": symbol,
                        "name": name,
                        "price": price,
                        "pct_chg": f"{pct_chg:.2f}%",
                        "turnover": turnover
                    }
                    print(f"📦 Parsed: {stock}")
                    data.append(stock)
                except Exception as e:
                    print(f"⚠️ [PARSE] {e}")
                    continue
            browser.close()
            print("🛑 [FETCH] Browser closed.")
    except Exception as e:
        print(f"❌ [FETCH ERROR] {e}")
    return data

def send(data):
    print("✉️ [SEND] Preparing to send email")
    me = os.environ.get("EMAIL_SENDER")
    pwd = os.environ.get("EMAIL_PASSWORD")
    you = os.environ.get("EMAIL_RECEIVER")

    if not me or not pwd or not you:
        print(f"❌ [SEND] Missing env vars: {me=} {pwd=} {you=}")
        return

    now = datetime.now(pytz.timezone("Asia/Kolkata")).strftime("%Y-%m-%d %H:%M:%S")
    body = f"📈 Chartink Volume Shocker Update — {now}\n\n"
    if not data:
        body += "No stocks triggered in this scan."
        print("⚠️ [SEND] No data")
    else:
        for s in data:
            line = f"**{s['nsecode']}** | {s['name']} | ₹{s['price']} | **{s['pct_chg']}** | Turnover: **₹{s['turnover']}**"
            body += line + "\n"
            print(f"📩 {line}")

    try:
        msg = MIMEText(body)
        msg["Subject"] = "🔔 Chartink Volume Shockers"
        msg["From"] = me
        msg["To"] = you
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(me, pwd)
            smtp.send_message(msg)
            print("✅ [SEND] Email sent successfully")
    except Exception as e:
        print(f"❌ [SEND ERROR] {e}")

@app.route("/")
def home():
    return jsonify({"message": "✅ Chartink Emailer is Live!", "status": "OK"})

@app.route("/run")
def run():
    def background():
        print("🚀 [RUN] Triggered!")
        data = fetch()
        send(data)
    Thread(target=background).start()
    return jsonify({"message": "📬 Script triggered", "status": "STARTED"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
