from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import CustomUser





class RegisterSerializer(serializers.ModelSerializer):
      username=serializers.CharField(required=True)
      email=serializers.EmailField(required=True)
      password=serializers.CharField(min_length=6, write_only=True) 
      class Meta:
            model=CustomUser
            fields=['username', 'email', 'password', 'role']

      def validate(self, data):
         username=data["username"]
     
         email=data["email"]
        
         if CustomUser.objects.filter(username=username).exists():
              raise serializers.ValidationError({"username":"Username is already in use."})
         if CustomUser.objects.filter(email=email).exists():
              raise serializers.ValidationError({"email":"Email is already in use."})
         
       


         return data
      
      def create(self, validated_data):
          user=CustomUser.objects.create_user(
                username=validated_data["username"],
                email=validated_data["email"],
                password=validated_data["password"],
                role=validated_data["role"]
           )
          return user





class AuthenticateSerialiser(serializers.ModelSerializer):
     username=serializers.CharField(required=True)
     password=serializers.CharField(min_length=6, write_only=True)


     class Meta:
          model=CustomUser
          fields=['username', 'password']


     def validate(self, data):
          username= data["username"]
          password= data["password"]

          if not username and not password:
               raise serializers.ValidationError("Both username and password are required to login.")
          user = authenticate(username=username, password=password)
          if not user:
               raise serializers.ValidationError("Invalid credentials, try again")
          # Block login if the account is not yet approved, except for superusers
          if not user.is_superuser and not getattr(user, "is_approved", False):
               raise serializers.ValidationError("Your account is awaiting approval by an administrator.")
          
          data["user"]=user
          return data 



            
