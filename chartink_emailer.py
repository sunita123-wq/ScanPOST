from playwright.sync_api import sync_playwright, TimeoutError
import smtplib
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
    url = "https://chartink.com/screener/volumeshocker-p-100-2"
    data = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url, timeout=60000)

        for attempt in range(3):
            try:
                page.wait_for_selector("table.table tbody tr", timeout=30000)
                rows = page.query_selector_all("table.table tbody tr")
                for row in rows:
                    cols = row.query_selector_all("td")
                    if len(cols) == 8:
                        symbol = cols[2].inner_text().strip()
                        name = cols[1].inner_text().strip()
                        price_str = cols[5].inner_text().strip().replace(",", "")
                        pct_chg = cols[4].inner_text().strip()
                        volume_str = cols[7].inner_text().strip().replace(",", "")

                        try:
                            price = float(price_str)
                            volume = float(volume_str)
                            turnover = format_number(price * volume)
                        except ValueError:
                            price = 0
                            turnover = "0"

                        data.append({
                            "symbol": symbol,
                            "name": name,
                            "price": price,
                            "pct_chg": pct_chg,
                            "turnover": turnover
                        })
                if data:
                    break
            except TimeoutError:
                continue

        browser.close()
    return data

def send(data):
    me = os.environ["EMAIL_SENDER"]
    pwd = os.environ["EMAIL_PASSWORD"]
    you = os.environ["EMAIL_RECEIVER"]

    now = datetime.now(pytz.timezone("Asia/Kolkata")).strftime("%Y-%m-%d %H:%M:%S")
    body = f"📈 Chartink Volume Shocker Update — {now}\n\n"

    if not data:
        body += "No stocks triggered in this scan."
    else:
        for s in data:
            body += f"{s['symbol']} | {s['name']} | ₹{s['price']} | {s['pct_chg']} | ₹{s['turnover']}\n"

    msg = MIMEText(body)
    msg["Subject"] = "🔔 Chartink Volume Shockers"
    msg["From"] = me
    msg["To"] = you

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(me, pwd)
        smtp.send_message(msg)

def main():
    data = fetch()
    send(data)

if __name__ == "__main__":
    main()
