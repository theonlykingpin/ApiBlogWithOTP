from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.generics import ListAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from extensions.code_generator import otp_generator
from extensions.permissions import IsSuperUser
from account.send_otp import send_otp
from account.serializers import UsersListSerializer, UserDetailUpdateDeleteSerializer, UserProfileSerializer, \
    AuthenticationSerializer, OtpSerializer, ChangeTwoStepPasswordSerializer, CreateTwoStepPasswordSerializer
from account.models import PhoneOtp

user = get_user_model()


class UsersList(ListAPIView):
    """
    get: Returns a list of all existing users.
    """
    queryset = user.objects.all()
    serializer_class = UsersListSerializer
    permission_classes = [IsSuperUser]
    filterset_fields = ["author"]
    search_fields = ["phone", "first_name", "last_name"]
    ordering_fields = ("id", "author")


class UsersDetailUpdateDelete(RetrieveUpdateDestroyAPIView):
    """
    get: Returns the detail of a user instance. parameters: [pk]
    put: Update the detail of a user instance. parameters: exclude[password,]
    delete: Delete a user instance. parameters: [pk]
    """
    serializer_class = UserDetailUpdateDeleteSerializer
    permission_classes = [IsSuperUser]

    def get_object(self):
        return get_object_or_404(user, pk=self.kwargs.get("pk"))


class UserProfile(RetrieveUpdateDestroyAPIView):
    """
    get: Returns the profile of user.
    put: Update the detail of a user instance. parameters: exclude[password,]
    delete: Delete user account. parameters: [pk]
    """

    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user


class Login(APIView):
    """
    post: Send mobile number for Login. parameters: [phone,]
    """

    permission_classes = [AllowAny]

    def post(self, request):
        serializer = AuthenticationSerializer(data=request.data)
        if serializer.is_valid():
            phone = serializer.validated_data.get("phone")
            user_is_exists: bool = user.objects.filter(phone=phone).values("phone").exists()
            if not user_is_exists:
                return Response({"No User exists.": "Please enter another phone number."},
                                status=status.HTTP_401_UNAUTHORIZED)
            code = otp_generator()
            user_otp, _ = PhoneOtp.objects.get_or_create(phone=phone)
            user_otp.otp = code
            user_otp.count += 1
            user_otp.save(update_fields=["otp", "count"])
            if user_otp.count >= 4:
                return Response({"Many Requests": "You requested too much."}, status=status.HTTP_429_TOO_MANY_REQUESTS)
            cache.set(phone, code, 300)
            # TODO: send_otp(phone, code)
            send_otp(phone=phone, otp=code)
            return Response({"code sent.": "The code has been sent to the desired phone number."},
                            status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class Register(APIView):
    """
    post: Send mobile number for Register. parameters: [phone,]
    """

    permission_classes = [AllowAny]

    def post(self, request):
        serializer = AuthenticationSerializer(data=request.data)
        if serializer.is_valid():
            phone = serializer.validated_data.get("phone")
            user_is_exists: bool = user.objects.filter(phone=phone).values("phone").exists()
            if user_is_exists:
                return Response({"User exists.": "Please enter a different phone number."},
                                status=status.HTTP_401_UNAUTHORIZED)
            code = otp_generator()
            user_otp, _ = PhoneOtp.objects.get_or_create(phone=phone)
            user_otp.otp = code
            user_otp.count += 1
            user_otp.save(update_fields=["otp", "count"])
            if user_otp.count >= 4:
                return Response({"Many Request": "You requested too much."}, status=status.HTTP_429_TOO_MANY_REQUESTS)
            cache.set(phone, code, 300)
            # TODO: send_otp(phone, code)
            send_otp(phone=phone, otp=code)
            return Response({"code sent.": "The code has been sent to the desired phone number."},
                            status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class VerifyOtp(APIView):
    """
    post: Send otp code to verify mobile number and complete authentication. If the user has a 2-step password,
    he must also send a password. parameters: [otp, password]
    """

    permission_classes = [AllowAny]
    confirm_for_authentication = False

    def post(self, request):
        serializer = OtpSerializer(data=request.data)
        if serializer.is_valid():
            received_code = serializer.validated_data.get("code")
            query = PhoneOtp.objects.filter(otp=received_code)
            if not query.exists():
                return Response({"Incorrect code.": "The code entered is incorrect."},
                                status=status.HTTP_406_NOT_ACCEPTABLE)
            object = query.first()
            code_in_cache = cache.get(object.phone)
            if code_in_cache is not None:
                if code_in_cache == received_code:
                    user, created = user.objects.get_or_create(phone=object.phone)
                    if user.two_step_password:
                        password = serializer.validated_data.get("password")
                        check_password: bool = user.check_password(password)
                        if check_password:
                            self.confirm_for_authentication = True
                        else:
                            return Response({"Incorrect password.": "The password entered is incorrect."},
                                            status=status.HTTP_406_NOT_ACCEPTABLE)
                    else:
                        self.confirm_for_authentication = True
                    if self.confirm_for_authentication:
                        refresh = RefreshToken.for_user(user)
                        cache.delete(object.phone)
                        object.verify, object.count = True, 0
                        object.save(update_fields=["verify", "count"])
                        return Response({"created": created, "refresh": str(refresh),
                                         "access": str(refresh.access_token)}, status=status.HTTP_200_OK)
                else:
                    return Response({"Incorrect code.": "The code entered is incorrect."},
                                    status=status.HTTP_406_NOT_ACCEPTABLE)
            else:
                return Response({"Code expired.": "The entered code has expired."},
                                status=status.HTTP_408_REQUEST_TIMEOUT)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ChangeTwoStepPassword(APIView):
    """
    post: Send a password to change a two-step-password. parameters: [old_password, new_password, confirm_new_password,]
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        if request.user.two_step_password:
            serializer = ChangeTwoStepPasswordSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            user = get_object_or_404(user, pk=request.user.pk)
            old_password = serializer.validated_data.get("old_password")
            check_password: bool = user.check_password(old_password)
            if check_password:
                new_password = serializer.validated_data.get("new_password")
                user.set_password(new_password)
                user.save(update_fields=["password"])
                return Response({"Successful.": "Your password was changed successfully."}, status=status.HTTP_200_OK)
            else:
                return Response({"Error!": "The password entered is incorrect."}, status=status.HTTP_406_NOT_ACCEPTABLE)
        return Response({"Error!": "Your request could not be approved."}, status=status.HTTP_401_UNAUTHORIZED)


class CreateTwoStepPassword(APIView):
    """
    post: Send a password to create a two-step-password. parameters: [new_password, confirm_new_password]
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        if not request.user.two_step_password:
            serializer = CreateTwoStepPasswordSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            new_password = serializer.validated_data.get("new_password")
            user = get_object_or_404(user, pk=request.user.pk)
            user.set_password(new_password)
            user.two_step_password = True
            user.save(update_fields=["password", "two_step_password"])
            return Response({"Successful.": "Your password was changed successfully."}, status=status.HTTP_200_OK)
        return Response({"Error!": "Your request could not be approved."}, status=status.HTTP_401_UNAUTHORIZED)
