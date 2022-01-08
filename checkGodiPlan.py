import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from gottesdienstplan import GoDiPlanChecker

MAIL_TEXT_TEMPLATE = """
Hallo,

im Gottesdienstplan scheint es einen Fehler, bzw. einen fehlenden Eintrag zu geben.
Bitte ergänze die fehlende Information oder korrigiere den falschen Eintrag.

Um was es sich genau handelt:

{message}

Liebe Grüße
Dein freundlicher Gottesdienstplan Checker
"""

MAIL_HTML_TEMPLATE = """
<p>Hallo,</p>
<p>
im Gottesdienstplan scheint es einen Fehler, bzw. einen fehlenden Eintrag zu geben.
Bitte ergänze die fehlende Information oder korrigiere den falschen Eintrag.
</p>
<p>
Um was es sich genau handelt:
</p>
<p><em>
{message}
</em></p>
<p>
<p>Liebe Grüße</p>
<p>Dein freundlicher Gottesdienstplan Checker</p>
"""


class Mailer:
    def __init__(self, my_addr, port: int = 25):
        self._server = None
        self._my_addr = my_addr
        self._port = port

    def __enter__(self):
        self._server = smtplib.SMTP("localhost", port=self._port)
        return self

    def __exit__(self, type, value, traceback):
        self._server.quit()
        self._server = None

    def handle_check_report(self, data):
        msg = data["message"]
        # FIXME: recp = data["recipient"]
        recp = f"webmaster@{MAIL_DOMAIN}"
        mail = MIMEMultipart("alternative")
        mail["Subject"] = "Gottesdienstplan Checker Nachricht"
        mail["From"] = self._my_addr
        mail["To"] = recp
        mail.attach(MIMEText(MAIL_TEXT_TEMPLATE.format(message=msg), "plain"))
        mail.attach(MIMEText(MAIL_HTML_TEMPLATE.format(message=msg), "html"))
        self._server.send_message(
            to_addrs=recp,
            from_addr=self._my_addr,
            msg=mail,
        )


if __name__ == "__main__":
    MAIL_DOMAIN = os.environ.get("MAIL_DOMAIN")

    p = GoDiPlanChecker(mail_domain=MAIL_DOMAIN)

    if MAIL_DOMAIN:
        with Mailer(my_addr=f"godiplanchecker@{MAIL_DOMAIN}", port=25) as m:
            p.check("1w", report=m.handle_check_report)
    else:
        p.check("1w", report=print)
