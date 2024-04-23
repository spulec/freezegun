from unittest import mock
import pytest
import freezegun
import freezegun.config

from typing import List


def setup_function() -> None:
    freezegun.config.reset_config()


def teardown_function() -> None:
    freezegun.config.reset_config()


@pytest.mark.parametrize('ignorelist', (['threading', 'tensorflow'], []))
def test_default_ignore_list_is_overridden(ignorelist: List[str]) -> None:
    freezegun.configure(default_ignore_list=list(ignorelist))

    with mock.patch("freezegun.api._freeze_time.__init__", return_value=None) as _freeze_time_init_mock:

        freezegun.freeze_time("2020-10-06")

        _freeze_time_init_mock.assert_called_once_with(
            time_to_freeze_str="2020-10-06",
            tz_offset=0,
            ignore=ignorelist,
            tick=False,
            as_arg=False,
            as_kwarg='',
            auto_tick_seconds=0,
            real_asyncio=False,
        )


@pytest.mark.parametrize('ignorelist', (['tensorflow'], []))
def test_extend_default_ignore_list(ignorelist: List[str]) -> None:
    freezegun.configure(extend_ignore_list=list(ignorelist))

    with mock.patch("freezegun.api._freeze_time.__init__", return_value=None) as _freeze_time_init_mock:

        freezegun.freeze_time("2020-10-06")

        expected_ignore_list = [
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
        ] + ignorelist

        _freeze_time_init_mock.assert_called_once_with(
            time_to_freeze_str="2020-10-06",
            tz_offset=0,
            ignore=expected_ignore_list,
            tick=False,
            as_arg=False,
            as_kwarg='',
            auto_tick_seconds=0,
            real_asyncio=False,
        )

def test_extend_default_ignore_list_duplicate_items() -> None:
    freezegun.configure(extend_ignore_list=['tensorflow', 'pymongo', 'tensorflow','rabbitmq'])
    freezegun.configure(extend_ignore_list=['tensorflow'])

    with mock.patch("freezegun.api._freeze_time.__init__", return_value=None) as _freeze_time_init_mock:

        freezegun.freeze_time("2020-10-06")

        expected_ignore_list = [
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
            'tensorflow',
            'pymongo',
            'rabbitmq',
        ]

        _freeze_time_init_mock.assert_called_once_with(
            time_to_freeze_str="2020-10-06",
            tz_offset=0,
            ignore=expected_ignore_list,
            tick=False,
            as_arg=False,
            as_kwarg='',
            auto_tick_seconds=0,
            real_asyncio=False,
        )
