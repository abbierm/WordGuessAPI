from flask import render_template, current_app
from app.email import send_email


def send_password_reset_email(user):
    token = user.get_reset_password_token()
    send_email(
        subject = '[WordGuess] Reset Your Password',
        sender = 'abbie@v8_dev.com',
        recipients = [user.email],
        text_body = render_template('email/reset_password.txt', 
                                    user=user, token=token))
    

def send_confirmation_email(user):
    token = user.generate_confirmation_token()
    print(token)
    send_email(
        subject = '[WordGuess] Confirm Your Account',
        sender = 'abbie@v8_dev.com',
        recipients = [user.email],
        text_body = render_template('email/confirm_account.txt', 
                                    user=user, token=token))