from django.contrib import admin
from .models import CustomUser

# Register your models here.



@admin.register(CustomUser)


class CustomUserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'role', 'is_staff', 'is_active','is_approved', 'is_superuser')
    list_filter = ('role', 'is_staff', 'is_active',"is_approved", 'is_superuser')

