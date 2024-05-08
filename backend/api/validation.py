import re

from django.core.exceptions import ValidationError


def validate_username(value):
    string = re.sub(r"[\w.@+-]", '', value)
    if string:
        raise ValidationError(
            f'В имени нельзя использовать следующие символы: {string}')
    return value
