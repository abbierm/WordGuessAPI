"""
test_email.py tests the basic email from flask-mailman inside of the 
application.  This file only tests basic email sending and not the 
entire email/forget password confirmation loop
"""
import pytest
from app import mail
from flask_mailman import EmailMessage


def test_send_email(test_client):
    with mail.get_connection(backend='locmem') as con:
        new = EmailMessage(
                subject="test_message",
                body="This is a test email",
                from_email="coalitionobscene@gmail.com",
                to=["fake_email@anEmail.com"]
            )
        new.send()
        assert len(con.mailman.outbox) == 1
        assert con.mailman.outbox[0].subject == "test_message"

