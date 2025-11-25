from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import CustomUser

@receiver(post_save, sender=CustomUser)
def send_approval_email(sender, instance, created, **kwargs):
   
    if not created:
     
        if instance.is_approved and instance.last_approval_status != instance.is_approved:
            instance.send_email()
