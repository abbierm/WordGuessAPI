from threading import Thread
from flask import current_app
from flask_mailman import EmailMessage
from pydantic import BaseModel, ValidationError
from typing import Optional, List



class Email(BaseModel):
    subject: str
    sender: Optional[str] = 'abbie@v8_dev.com'
    recipients: List[str]
    text: str
    sync: Optional[bool] = False


def send_async_email(app, msg):
    with app.app_context():
        msg.send()


def send_email(subject, sender, recipients, text_body, sync=False):
    msg = EmailMessage(
        subject=subject,
        body=text_body, 
        from_email=sender, 
        to=recipients
    )
    if sync:
        msg.send()
    else:
        Thread(target=send_async_email, 
               args=(current_app._get_current_object(), msg)).start()
        

