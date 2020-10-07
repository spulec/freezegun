

DEFAULT_IGNORE = [
    'nose.plugins',
    'six.moves',
    'django.utils.six.moves',
    'google.gax',
    'threading',
    'Queue',
    'selenium',
    '_pytest.terminal.',
    '_pytest.runner.',
    'gi',
]


class Settings:
    def __init__(self, default_ignore=None):
        self.default_ignore = default_ignore or DEFAULT_IGNORE[:]


settings = Settings()


def configure(default_ignore=None):
    settings.default_ignore = default_ignore
