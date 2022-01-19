import smtplib, ssl
from configs import get_db_settings
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


settings = get_db_settings()

class Mail:

    def __init__(self):
        self.port = 465
        self.smtp_server_domain_name = "smtp.gmail.com"
        self.sender_mail = settings.EMAIL_USERNAME
        self.password = settings.EMAIL_PWD

    def send(self, emails, subject, content):
        ssl_context = ssl.create_default_context()
        service = smtplib.SMTP_SSL(self.smtp_server_domain_name, self.port, context=ssl_context)
        service.login(self.sender_mail, self.password)
        
        for email in emails:
            mail = MIMEMultipart('alternative')
            mail['Subject'] = subject
            mail['From'] = self.sender_mail
            mail['To'] = email

            html_content = MIMEText(content, 'html')
            mail.attach(html_content)

            service.sendmail(self.sender_mail, email, mail.as_string())

        service.quit()