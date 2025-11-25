from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.decorators import permission_classes

from rest_framework_simplejwt.tokens import RefreshToken

from .serializer import RegisterSerializer, AuthenticateSerialiser
from .models import CustomUser


# Create your views here.



class RegisterView(APIView):
    permission_classes =[AllowAny]

    def post(self, request):
        serializer=RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user=serializer.save()
            user.send_email()
            return Response('user created succcessfully', status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    





class LoginView(APIView):
    permission_classes=[AllowAny]


    def post(self, request):
        serializer=AuthenticateSerialiser(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]

        if serializer.is_valid():
            refresh = RefreshToken.for_user(user)

            return Response({
                'refresh': str(refresh),
                'access': str(refresh.access_token),
                'message': 'login successful',
                'user': serializer.validated_data["username"],
                'role': user.role,
            }, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)    







