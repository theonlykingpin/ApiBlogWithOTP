from django.contrib.admin import display
from django.contrib.auth.models import BaseUserManager, PermissionsMixin, AbstractBaseUser
from django.core.validators import RegexValidator
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class CustomUserManager(BaseUserManager):
    """
    Custom manager for User model with no username field.
    """

    def _create_user(self, phone: str, **extra_fields) -> 'User':
        """
        Create and save a user or superuser with the given phone.
        """
        if not phone:
            raise ValueError(_('The given phone must be set'))
        user = self.model(phone=phone, **extra_fields)
        user.set_unusable_password()
        user.save(using=self._db)
        return user

    def create_user(self, phone: str, **extra_fields) -> 'User':
        """
        Create and save a regular user with the given phone.
        """
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(phone, **extra_fields)

    def create_superuser(self, phone: str, **extra_fields) -> 'User':
        """
        Create and save a superuser with the given phone.
        """
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        if not extra_fields.get('is_staff'):
            raise ValueError(_('Superuser must have is_staff=True.'))
        if not extra_fields.get('is_superuser'):
            raise ValueError(_('Superuser must have is_superuser=True.'))
        return self._create_user(phone, **extra_fields)


phone_number_validator = RegexValidator(
    regex=r"^989\d{2}\s*?\d{3}\s*?\d{4}$",
    message=_("Invalid phone number.")
)


class User(AbstractBaseUser, PermissionsMixin):
    """
    Custom user model where phone is the unique identifier
    for authentication instead of usernames.
    """
    phone = models.CharField(
        max_length=12,
        validators=[phone_number_validator],
        unique=True,
        verbose_name=_("phone")
    )
    first_name = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_("first name")
    )
    last_name = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_("last name")
    )
    author = models.BooleanField(
        default=False,
        blank=True,
        verbose_name=_("author")
    )
    special_user = models.DateTimeField(
        default=timezone.now,
        verbose_name=_("Special User")
    )
    is_staff = models.BooleanField(default=False)
    is_admin = models.BooleanField(default=False)
    date_joined = models.DateTimeField(
        default=timezone.now,
        verbose_name=_("date joined")
    )
    two_step_password = models.BooleanField(
        default=False,
        verbose_name=_("two step password"),
        help_text=_("is active two step password?")
    )

    objects = CustomUserManager()

    USERNAME_FIELD = "phone"
    REQUIRED_FIELDS = []

    def __str__(self) -> str:
        return self.phone

    @property
    def get_full_name(self) -> str:
        """
        Returns the full name of the user.
        """
        full_name = f"{self.first_name} {self.last_name}"
        return full_name.strip()

    @display(boolean=True, description=_("Special User"))
    def is_special_user(self) -> bool:
        """
        Returns True if the user is a special user.
        """
        return self.special_user > timezone.now()


class PhoneOtp(models.Model):
    """
    Model to store OTP for phone verification.
    """
    phone = models.CharField(
        max_length=12,
        validators=[phone_number_validator],
        unique=True,
        verbose_name=_("phone")
    )
    otp = models.CharField(max_length=6)
    count = models.PositiveSmallIntegerField(
        default=0,
        help_text=_("Number of otp sent")
    )
    verify = models.BooleanField(
        default=False,
        verbose_name=_("is verify")
    )

    def __str__(self) -> str:
        return self.phone
