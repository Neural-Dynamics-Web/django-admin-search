# region				-----External Imports-----
import django
import typing
# endregion

# region		      -----Supporting Variables-----
MULTIPLE_CHOICE_FIELDS = (
    django.forms.ModelMultipleChoiceField, 
    django.forms.MultipleChoiceField
)

CHOICE_FIELDS = (
    django.forms.ModelChoiceField,
    django.forms.ChoiceField
)
# endregion


def format_data(
        value: django.forms.Field,
        key_value: typing.AnyStr
    ) -> typing.Any:
    # ? Get values from the input form so we can .clean them properly
    result = None
    if isinstance(value, django.forms.BooleanField):
        # ? https://code.djangoproject.com/ticket/31049
        result = bool(key_value)

    elif isinstance(value, MULTIPLE_CHOICE_FIELDS):
        result = key_value

    elif isinstance(value, django.forms.TextInput):
        result = str(key_value)
    
    elif isinstance(value, CHOICE_FIELDS):
        value.clean(key_value)
        result = key_value

    else:
        result = value.clean(key_value)


    return result
