from django.db import models
from django.contrib.auth.models import AbstractUser


# Create your models here.




class CustomUser(AbstractUser):


    ROLE_CHOICES =(
        ('staff', 'staff'),
        ('approver_level_1', 'approver_level_1'),
        ('approver_level_2', 'approver_level_2'),
        ('finance', 'finance')
    )

    role=models.CharField(max_length=30, choices=ROLE_CHOICES, default='staff')




    def  is_staff_user(self):
        return self.role == 'staff'
    

    def is_approve(self):
        return self.role in ['approver_level_1', 'approver_level_2'] 
    


    def is_finance(self):
        return self.role == 'finance'
    
      

    