from playwright.sync_api import sync_playwright
import smtplib
from email.mime.text import MIMEText
from datetime import datetime
import pytz
import os

def fetch():
    url = "https://chartink.com/screener/volumeshocker-p-100-2"
    data = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url, timeout=60000)
        page.wait_for_selector("table.table tbody tr", timeout=15000)
        rows = page.query_selector_all("table.table tbody tr")

        for row in rows:
            cols = row.query_selector_all("td")
            if len(cols) < 8:
                continue

            symbol = cols[2].inner_text().strip()
            name = cols[1].inner_text().strip()
            price_str = cols[4].inner_text().strip().replace(",", "")
            pct_chg = cols[5].inner_text().strip()
            volume_str = cols[7].inner_text().strip().replace(",", "")

            try:
                price = float(price_str)
                volume = float(volume_str)
                turnover = price * volume
            except ValueError:
                price = 0
                turnover = 0

            data.append({
                "symbol": symbol,
                "name": name,
                "price": price,
                "pct_chg": pct_chg,
                "turnover": turnover
            })

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
            turnover_str = f"{s['turnover']:,.0f}"
            body += f"{s['symbol']} | {s['name']} | ₹{s['price']} | {s['pct_chg']} | ₹{turnover_str}\n"

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
