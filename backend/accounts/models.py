from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.mail import send_mail
from django.conf import settings


# Create your models here.




class CustomUser(AbstractUser):


    ROLE_CHOICES =(
        ('staff', 'staff'),
        ('manager_1', 'manager_1'),
        ('manager_2', 'manager_2'),
        ('finance', 'finance')
    )

    role=models.CharField(max_length=30, choices=ROLE_CHOICES, default='staff')
    is_approved = models.BooleanField(default=False)

    def  is_staff_user(self):
        return self.role == 'staff'
    

    def is_approve(self):
        return self.role in ['manager_1', 'manager_2'] 
    


    def is_finance(self):
        return self.role == 'finance'
    
    def send_email(self):
        if self.is_approved:
            send_mail(
                subject="Your account has been approved",
                message=f"Hello {self.username}, your account has been approved. You can now login: https://procure-system.onrender.com/login",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[self.email],
                fail_silently=False,
            )
            
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.last_approval_status = self.is_approved
    
      

    