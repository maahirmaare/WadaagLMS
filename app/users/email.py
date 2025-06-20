from flask import render_template
from flask_mail import Message
from app import mail

def send_email(subject, sender, recipients, text_body, html_body):
    msg = Message(subject, sender=sender, recipients=recipients)
    msg.body = text_body
    msg.html = html_body
    mail.send(msg)

def send_email_confirmation(user):
    token = user.get_token(expires_in=60)
    send_email(subject="WadaagLMS - Email Confirmation",
                sender="other@javierperez.dev",
                recipients=[user.email],
               text_body=render_template('email/verify_email.txt',
                                         user=user, token=token),
               html_body=render_template('email/verify_email.html',
                                         user=user, token=token))

def send_password_reset(user):
    token = user.get_token(expires_in=600)
    send_email(subject="WadaagLMS - Password Reset",
                sender="other@javierperez.dev",
                recipients=[user.email],
               text_body=render_template('email/reset_password.txt',
                                         user=user, token=token),
               html_body=render_template('email/reset_password.html',
                                         user=user, token=token))