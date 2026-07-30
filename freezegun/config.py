from typing import List, Optional


DEFAULT_IGNORE_LIST = [
    'nose.plugins',
    'six.moves',
    'django.utils.six.moves',
    'google.gax',
    'threading',
    'multiprocessing',
    'queue',
    'selenium',
    '_pytest.terminal.',
    '_pytest.runner.',
    'gi',
    'prompt_toolkit',
]


class Settings:
    def __init__(self, default_ignore_list: Optional[List[str]]=None) -> None:
        self.default_ignore_list = default_ignore_list or DEFAULT_IGNORE_LIST[:]


settings = Settings()


class ConfigurationError(Exception):
    pass


def configure(default_ignore_list: Optional[List[str]]=None, extend_ignore_list: Optional[List[str]]=None) -> List[str]:
    """Update freezegun ignore-list settings.

    Returns a copy of the *previous* ``default_ignore_list`` so callers
    (e.g. pytest fixtures) can restore it later (issue #587)::

        prior = freezegun.configure(extend_ignore_list=["mypkg"])
        ...
        freezegun.configure(default_ignore_list=prior)
    """
    if default_ignore_list is not None and extend_ignore_list is not None:
        raise ConfigurationError("Either default_ignore_list or extend_ignore_list might be given, not both")
    prior = list(settings.default_ignore_list)
    if default_ignore_list is not None:
        settings.default_ignore_list = default_ignore_list
    if extend_ignore_list:
        settings.default_ignore_list = list(dict.fromkeys([*settings.default_ignore_list, *extend_ignore_list]))
    return prior


def reset_config() -> None:
    global settings
    settings = Settings()
