from django.conf import settings
from django.contrib.staticfiles.storage import staticfiles_storage
from django.urls import reverse
from django.utils import translation
from django.template.defaultfilters import slugify
from jinja2 import Environment


def fupper(text):
    """First letter upper.

    :param text: Text to be capitalized
    :return Text: Capitalized's text
    """
    text = str(text)

    if not text:
        return text
    if len(text) > 1:
        return text[0].upper() + text[1:]
    else:
        return text.upper()


def environment(**options):
    """Get jinja2 environment.

    :param options: Options
    :return env: return environment instance
    """
    env = Environment(**options)
    env.globals.update({
        'static': staticfiles_storage.url,
        'url': reverse,
        'LANGUAGES': settings.LANGUAGES,
        'translation': translation,
    })

    # add django filters
    env.filters['slugify'] = slugify

    # use django-bootstrap-form on jinja
    from bootstrapform.templatetags import bootstrap
    env.filters['bootstrap'] = bootstrap.bootstrap
    env.filters['bootstrap_horizontal'] = bootstrap.bootstrap_horizontal
    env.filters['bootstrap_inline'] = bootstrap.bootstrap_inline

    # add custom filters
    env.filters['fupper'] = fupper

    env.install_gettext_translations(translation)
    return env
