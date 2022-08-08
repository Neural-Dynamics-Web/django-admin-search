from django.contrib.admin.views.main import SEARCH_VAR
from django.template import Library
from django.template.loader import render_to_string

register = Library()  # pylint: disable=C0103


# @register.inclusion_tag('admin/custom_search_form.html', takes_context=True)
@register.simple_tag(takes_context=True)
def advanced_search_form(context, cl):  # pylint: disable=invalid-name
    """
    Displays a search form for searching the list.
    """
    if not context.get('form', None):
        return ''

    context = {
        # 'show_result_count': cl.result_count != cl.full_result_count,
        # 'fieldsets': context['fieldsets'],
        # 'search_var': SEARCH_VAR,
        # 'form': context['form'],
        # 'cl': cl,
    }

    return render_to_string('admin/custom_search_form.html', context)
