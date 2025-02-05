import imaplib
import email
from email.header import decode_header
import os


username = "yourmail_id@gmail.com"
password = "APP PASSWORD"


mail = imaplib.IMAP4_SSL("imap.gmail.com")
mail.login(username, password)
mail.select("inbox")


status, messages = mail.search(None, "ALL")
email_ids = messages[0].split()


for email_id in email_ids[-1:]:
    status, msg_data = mail.fetch(email_id, "(RFC822)")
    for response_part in msg_data:
        if isinstance(response_part, tuple):
            msg = email.message_from_bytes(response_part[1])
            subject = decode_header(msg["Subject"])[0][0]
            if isinstance(subject, bytes):
                subject = subject.decode()
            

            if msg.is_multipart():
                for part in msg.walk():
                    if part.get_content_disposition() == "attachment":
                        filename = part.get_filename()
                        if filename:
                            filepath = os.path.join("attachments", filename)
                            os.makedirs("attachments", exist_ok=True)
                            with open(filepath, "wb") as f:
                                f.write(part.get_payload(decode=True))
                            
mail.logout()
