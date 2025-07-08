import requests
import smtplib
from email.mime.text import MIMEText
from datetime import datetime
import pytz
import os

def fetch():
    url = "https://chartink.com/screener/process"
    payload = {"scan_name": "volumeshocker-p-100-2"}
    headers = {"X-Requested-With": "XMLHttpRequest"}
    r = requests.post(url, data=payload, headers=headers)
    r.raise_for_status()
    data = r.json().get("data", [])
    return data

def send(data):
    me = os.environ["EMAIL_SENDER"]
    pwd = os.environ["EMAIL_PASSWORD"]
    you = os.environ["EMAIL_RECEIVER"]
    now = datetime.now(pytz.timezone("Asia/Kolkata")).strftime("%Y-%m-%d %H:%M")

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
    print("🔧 Debug Mode: Running without time check")
    data = fetch()
    send(data)

if __name__ == "__main__":
    main()
