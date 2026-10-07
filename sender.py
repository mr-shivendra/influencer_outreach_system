import os
import smtplib, pandas as pd
from email.message import EmailMessage
from datetime import datetime

LOG = "data/outreach_log.csv"
SIMULATE = True   # switch to False for real sending

def already_sent(email):
    try:
        return email in pd.read_csv(LOG)["email"].values
    except FileNotFoundError:
        return False

def init_log():
    if not os.path.exists(LOG):
        pd.DataFrame(columns=["influencer", "email", "message_generated",
                              "sent", "date", "status"]).to_csv(LOG, index=False)

        
def log_outreach(name, email, generated, sent, status):
    row = pd.DataFrame([{
        "influencer": name,
        "email": email,
        "message_generated": generated,
        "sent": sent,
        "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "status": status,
    }])
    row.to_csv(LOG, mode="a", header=not os.path.exists(LOG), index=False)

def send_email(to, subject, body):
    if SIMULATE:
        print(f"[SIMULATED] To: {to}\n{body}\n")
        return "Simulated"
    msg = EmailMessage()
    msg["From"], msg["To"], msg["Subject"] = os.getenv("GMAIL_USER"), to, subject
    msg.set_content(body)
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as s:
        s.login(os.getenv("GMAIL_USER"), os.getenv("GMAIL_APP_PASSWORD"))
        s.send_message(msg)
    return "Sent"