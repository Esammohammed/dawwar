import logging
from celery import shared_task
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings

logger = logging.getLogger(__name__)

@shared_task
def send_otp_email_task(email, raw_code):
    # Never put the code in the subject: it leaks to notifications and mail logs.
    subject = "Dawwar Verification Code"
    html_message = render_to_string('accounts/otp_email.html', {'otp_code': raw_code})
    plain_message = strip_tags(html_message)
    from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'Dawwar <noreply@dawwar.com>')

    try:
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=from_email,
            recipient_list=[email],
            html_message=html_message,
            fail_silently=False,
        )
        logger.info(f"OTP email sent successfully to {email}")
        return True
    except Exception as e:
        logger.error(f"Failed to send OTP email to {email}: {str(e)}")
        return False
