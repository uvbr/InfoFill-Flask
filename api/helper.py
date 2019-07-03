import secrets
from app import app
from flask_mail import Mail, Message
from .config import Configurations as config

def generate_secret(token_type, string_len=50):
    """
    This method generates random unique tokens.
    Args:
        @token_type - type of token to generate

    Response - string
    """
    attr= getattr(secrets, token_type)
    code= attr(string_len)
    return code

def send_mail(To,url):
    app.config.update(
        MAIL_SERVER=config.MAIL_SERVER,
        MAIL_PORT=config.MAIL_PORT,
        MAIL_USE_SSL=config.MAIL_USE_SSL,
        MAIL_USERNAME = config.MAIL_USERNAME,
        MAIL_PASSWORD = config.MAIL_PASSWORD
        )
    mail = Mail(app)
    try:
        msg = Message("Send Mail Tutorial!",
                sender=config.MAIL_USERNAME,
                recipients=[To])
        msg.body = "To Activate your account click on"+url           
        mail.send(msg)
        return True
    except Exception:
        return False 