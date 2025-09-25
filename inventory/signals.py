import logging

from django.contrib.auth.signals import (
    user_logged_in,
    user_login_failed,
    user_logged_out,
)
from django.dispatch import receiver

# Configure logger
logger = logging.getLogger("inventory")


@receiver(user_logged_in)
def log_user_login(sender, request, user, **kwargs):
    """
    Log successful user login with relevant details
    """
    # logger.info
    logger.info(
        f"Successful login: User {user.username} "
        f"logged in from IP {request.META.get('REMOTE_ADDR')}"
    )


@receiver(user_logged_out)
def log_user_logout(sender, request, user, **kwargs):
    """
    Log successful user logout with relevant details
    """
    # logger.info
    logger.info(f"Successful logout: User {user.username} ")


@receiver(user_login_failed)
def log_user_failed_login(sender, request, **kwargs):
    """
    Log failed user login with relevant details
    """
    # logger.info
    logger.debug(
        f"Failed login " f"attempted from IP {request.META.get('REMOTE_ADDR')}"
    )
