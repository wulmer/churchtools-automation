import os
import smtplib
from email.message import EmailMessage

from gottesdienstplan import GoDiPlanChecker


class Mailer:
    def __init__(self, my_addr):
        self._server = None
        self._my_addr = my_addr

    def __enter__(self):
        self._server = smtplib.SMTP("localhost")
        return self

    def __exit__(self, type, value, traceback):
        self._server.quit()
        self._server = None

    def handle_check_report(self, data):
        msg = data["message"]
        # FIXME: recp = data["recipient"]
        recp = f"webmaster@{MAIL_DOMAIN}"
        mail = EmailMessage()
        mail.set_content(msg)
        mail["Subject"] = "Gottesdienstplan Checker Nachricht"
        mail["From"] = self._my_addr
        mail["To"] = recp
        self._server.send_message(
            to_addrs=recp,
            from_addr=self._my_addr,
            msg=mail,
        )


if __name__ == "__main__":
    MAIL_DOMAIN = os.environ.get("MAIL_DOMAIN")
    if MAIL_DOMAIN:
        p = GoDiPlanChecker(mail_domain=MAIL_DOMAIN)
        with Mailer(my_addr=f"godiplanchecker@{MAIL_DOMAIN}") as m:
            p.check("4w", reporter=m.handle_check_report)
    else:
        p = GoDiPlanChecker()
        p.check("4w", reporter=print)
