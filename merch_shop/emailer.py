import django.core.mail as mail


class Email():
    '''A class for handling email sending.'''

    def __init__(self, subject, message, recipient_list):
        self.subject: str = subject
        self.message: str = message
        self.recipient_list: list[str] = recipient_list

    def send(self):
        mail.send_mail(
            subject=self.subject,
            message=self.message,
            from_email='lakeshorelabradoodles@gmail.com',
            recipient_list=self.recipient_list,
            fail_silently=False,
        )
