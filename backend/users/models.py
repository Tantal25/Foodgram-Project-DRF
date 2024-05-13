from django.contrib.auth.models import AbstractUser
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.db import models

from foodgram_backend.constants import STANDARD_FIELD_LENGTH


class User(AbstractUser):
    """Переопределенная модель пользователя."""
    username_validator = UnicodeUsernameValidator()
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = [
        'username',
        'first_name',
        'last_name',
    ]

    email = models.EmailField(
        unique=True,
        verbose_name='Почта'
    )
    username = models.CharField(
        max_length=STANDARD_FIELD_LENGTH,
        unique=True,
        verbose_name='Имя пользователя',
        validators=(username_validator, )
    )
    first_name = models.CharField(
        max_length=STANDARD_FIELD_LENGTH,
        verbose_name='Имя'
    )
    last_name = models.CharField(
        max_length=STANDARD_FIELD_LENGTH,
        verbose_name='Фамилия'
    )
    password = models.CharField(
        max_length=STANDARD_FIELD_LENGTH,
        verbose_name='Пароль'
    )

    class Meta:
        verbose_name = 'пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ('username',)

    def __str__(self):
        return self.username


class Subscription(models.Model):
    """Модель для подписок на других пользователей."""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='subscriber'
    )
    subscribe = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        blank=True, null=True,
        related_name='subscribe'
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'subscribe'],
                name='unique_user_subscribe'),
            models.CheckConstraint(
                name='api_prevent_self_subscribe',
                check=~models.Q(user=models.F('subscribe')),
            ),
        ]
