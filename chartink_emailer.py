from playwright.sync_api import sync_playwright
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime
import pytz
import os

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
    print("\U0001F50D [FETCH] Launching Playwright Chromium...")
    url = "https://chartink.com/screener/volumeshocker-p-100-2"
    data = []

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            print("\U0001F9E0 [FETCH] Chromium launched.")
            page = browser.new_page()
            page.goto(url, timeout=60000)
            print("\U0001F310 [FETCH] Navigated to Chartink URL.")

            page.wait_for_selector("table.table tbody tr", timeout=15000)
            print("✅ [FETCH] Table rows found.")

            rows = page.query_selector_all("table.table tbody tr")
            print(f"\U0001F4CA [FETCH] Total rows fetched: {len(rows)}")

            for row in rows:
                cols = row.query_selector_all("td")
                if len(cols) < 7:
                    print("⚠️ [FETCH] Skipping row with insufficient columns")
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
                    print(f"\U0001F9BE [FETCH] Row parsed: {stock}")
                    data.append(stock)

                except Exception as e:
                    print(f"⚠️ [FETCH] Error parsing row: {e}")
                    continue

            browser.close()
            print("\U0001F6D1 [FETCH] Browser closed.")

    except Exception as e:
        print(f"❌ [FETCH ERROR] {e}")

    return data

def send(data):
    print("✉️ [SEND] Preparing email...")
    me = os.environ.get("EMAIL_SENDER")
    pwd = os.environ.get("EMAIL_PASSWORD")
    you = os.environ.get("EMAIL_RECEIVER")

    now = datetime.now(pytz.timezone("Asia/Kolkata")).strftime("%Y-%m-%d %H:%M:%S")
    subject = f"🔔 Chartink Volume Shocker Update — {now}"

    html = f"<h3>📈 Chartink Volume Shocker Update — {now}</h3><br>"

    if not data:
        html += "<p>No stocks triggered in this scan.</p>"
        print("⚠️ [SEND] No data to send.")
    else:
        html += "<ul style='list-style:none;padding:0;'>"
        for s in data:
            line = f"<li><b>{s['nsecode']}</b> | {s['name']} | ₹{s['price']} | <b>{s['pct_chg']}</b> | Turnover: <b>₹{s['turnover']}</b></li>"
            print(f"📩 [SEND] {line}")
            html += line + "<br>"
        html += "</ul>"

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = me
    msg["To"] = you

    msg.attach(MIMEText(html, "html"))

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
    print("🌟 [MAIN] Script completed.")

if __name__ == "__main__":
    main()
