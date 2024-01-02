# region				-----External Imports-----
from django.utils.translation import gettext_lazy as _
from django.apps import AppConfig
# endregion


class DjangoAdminSearchConfig(AppConfig):
    verbose_name = _('Django Admin Search')
    name = 'django_admin_search'
