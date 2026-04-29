import imaplib
import email
from email.header import decode_header
from email.utils import parseaddr, parsedate_to_datetime
from datetime import timezone
from bs4 import BeautifulSoup
import re

from backend.domain.interns import is_registered_intern
from backend.state.email_state import get_last_uid, set_last_uid


def clean_reply(body: str) -> str:
    body = body.replace("\r", "")

    reply_pattern = r"\nOn .* wrote:\n"
    split_result = re.split(reply_pattern, body, maxsplit=1)

    cleaned = split_result[0]

    lines = cleaned.splitlines()
    cleaned_lines = []

    for line in lines:
        stripped = line.strip()
        if stripped.startswith(">"):
            continue
        cleaned_lines.append(line)

    cleaned = "\n".join(cleaned_lines)
    cleaned = re.sub(r"\n{2,}", "\n", cleaned)

    return cleaned.strip()


class IMAPFetcher:

    def __init__(self, host: str, username: str, password: str):
        self.host = host
        self.username = username
        self.password = password

    def fetch_all_emails(self):

        mail = imaplib.IMAP4_SSL(self.host)
        mail.login(self.username, self.password)

        mail.select("INBOX")

        last_uid = get_last_uid()

        status, messages = mail.uid("search", None, f"UID {last_uid + 1}:*")

        if status != "OK":
            print("[ERROR] Failed to search inbox.")
            mail.logout()
            return []

        email_uids = messages[0].split()

        emails = []

        for uid in email_uids:

            status, msg_data = mail.uid("fetch", uid, "(RFC822)")

            if status != "OK":
                continue

            for response_part in msg_data:

                if not isinstance(response_part, tuple):
                    continue

                msg = email.message_from_bytes(response_part[1])

                message_id = msg.get("Message-ID")
                if not message_id:
                    continue

                # ---------- DATE ----------
                date_header = msg.get("Date")
                email_date = None

                if date_header:
                    try:
                        parsed_date = parsedate_to_datetime(date_header)

                        if parsed_date.tzinfo:
                            parsed_date = parsed_date.astimezone(timezone.utc)

                        email_date = parsed_date.replace(tzinfo=None)

                    except Exception:
                        email_date = None

                # ---------- SUBJECT ----------
                subject = ""
                subject_header = msg.get("Subject")

                if subject_header:
                    decoded_header = decode_header(subject_header)

                    subject_parts = []

                    for part, encoding in decoded_header:
                        if isinstance(part, bytes):
                            subject_parts.append(
                                part.decode(encoding or "utf-8", errors="ignore")
                            )
                        else:
                            subject_parts.append(part)

                    subject = "".join(subject_parts)

                # ---------- SENDER ----------
                _, sender = parseaddr(msg.get("From"))
                sender = sender.lower().strip()

                if not is_registered_intern(sender):
                    continue

                # ---------- BODY ----------
                html_content = None
                text_content = None

                if msg.is_multipart():

                    for part in msg.walk():

                        content_type = part.get_content_type()
                        payload = part.get_payload(decode=True)

                        if not payload:
                            continue

                        decoded = payload.decode("utf-8", errors="ignore")

                        if content_type == "text/html":
                            html_content = decoded

                        elif content_type == "text/plain":
                            text_content = decoded

                else:

                    payload = msg.get_payload(decode=True)

                    if payload:
                        text_content = payload.decode("utf-8", errors="ignore")

                if html_content:

                    soup = BeautifulSoup(html_content, "html.parser")

                    table = soup.find("table")

                    if table:
                        body = table.get_text(separator="\n")
                    else:
                        body = soup.get_text(separator="\n")

                else:
                    body = text_content or ""

                body = body.replace("*", "")
                body = body.replace("•", "")
                body = re.sub(r"[–—]", "-", body)
                body = re.sub(r"\n+", "\n", body)

                body = clean_reply(body)

                emails.append({
                    "sender": sender,
                    "subject": subject.strip(),
                    "body": body.strip(),
                    "message_id": message_id.strip(),
                    "email_date": email_date
                })

                # update UID tracker
                set_last_uid(int(uid))

        mail.logout()

        return emails