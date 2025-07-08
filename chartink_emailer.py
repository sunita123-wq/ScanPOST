import requests
from bs4 import BeautifulSoup
import smtplib
from email.mime.text import MIMEText
from datetime import datetime
import pytz
import os

def fetch():
    url = "https://chartink.com/screener/volumeshocker-p-100-2"
    headers = {
        "User-Agent": "Mozilla/5.0"
    }
    r = requests.get(url, headers=headers)
    r.raise_for_status()

    soup = BeautifulSoup(r.text, "html.parser")
    table = soup.find("table", {"class": "table"})

    if not table:
        return []

    headers_row = table.find("thead").find_all("th")
    col_indices = {th.text.strip(): i for i, th in enumerate(headers_row)}

    required = ["Symbol", "Stock Name", "Price"]
    for col in required:
        if col not in col_indices:
            print(f"❌ Column '{col}' not found in table.")
            return []

    data = []
    for row in table.find("tbody").find_all("tr"):
        cols = row.find_all("td")
        symbol = cols[col_indices["Symbol"]].text.strip()
        name = cols[col_indices["Stock Name"]].text.strip()
        price = cols[col_indices["Price"]].text.strip()
        data.append({
            "nsecode": symbol,
            "name": name,
            "close": price
        })

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
            body += f"{s['nsecode']} | {s['name']} | ₹{s['close']}\n"

    msg = MIMEText(body)
    msg["Subject"] = "🔔 Chartink Volume Shockers"
    msg["From"] = me
    msg["To"] = you

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(me, pwd)
        smtp.send_message(msg)

def main():
    print("🚀 Fetching Chartink HTML results (no CSRF)")
    data = fetch()
    send(data)

if __name__ == "__main__":
    main()
