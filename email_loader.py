import csv
import random

# 🔹 Optional Gmail loader (safe fallback)
def load_from_gmail():
    try:
        from googleapiclient.discovery import build
        from google.oauth2.credentials import Credentials
        import base64

        creds = Credentials.from_authorized_user_file("token.json")
        service = build("gmail", "v1", credentials=creds)

        results = service.users().messages().list(userId="me", maxResults=5).execute()
        messages = results.get("messages", [])

        emails = []

        for msg in messages:
            data = service.users().messages().get(userId="me", id=msg["id"]).execute()
            payload = data["payload"]

            snippet = data.get("snippet", "")

            emails.append({
                "text": snippet,
                "label": "unknown"
            })

        return emails

    except Exception:
        return None


# 🔹 CSV fallback (main)
def load_from_csv():
    import csv
    emails = []

    with open("emails.csv") as f:
        reader = csv.DictReader(f)
        for row in reader:
            emails.append({
                "text": row["text"],
                "label": row["label"],
                "has_link": bool(int(row["has_link"])),
                "urgency": float(row["urgency"])
            })

    return emails


# 🔹 Hybrid loader
def get_emails():
    # Prefer CSV for consistent grading labels (spam/important)
    emails = load_from_csv()
    if emails and len(emails) > 0:
        # print("📄 Using CSV dataset")
        return emails

    # Fallback to Gmail (if no CSV or empty)
    # Caution: Gmail emails will have "unknown" labels
    print("📩 Falling back to Gmail data")
    return load_from_gmail()