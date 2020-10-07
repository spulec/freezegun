from unittest import mock
import freezegun
import freezegun.config


def setup_function():
    freezegun.config.reset_config()


def teardown_function():
    freezegun.config.reset_config()


def test_default_ignore_list_is_overridden():
    freezegun.configure(default_ignore_list=['threading', 'tensorflow'])

    with mock.patch("freezegun.api._freeze_time.__init__", return_value=None) as _freeze_time_init_mock:

        freezegun.freeze_time("2020-10-06")

        expected_ignore_list = [
            'threading',
            'tensorflow',
        ]

        _freeze_time_init_mock.assert_called_once_with(
            time_to_freeze_str="2020-10-06",
            tz_offset=0,
            ignore=expected_ignore_list,
            tick=False,
            as_arg=False,
            as_kwarg='',
            auto_tick_seconds=0,
        )

def test_extend_default_ignore_list():
    freezegun.configure(extend_ignore_list=['tensorflow'])

    with mock.patch("freezegun.api._freeze_time.__init__", return_value=None) as _freeze_time_init_mock:

        freezegun.freeze_time("2020-10-06")

        expected_ignore_list = [
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
            'tensorflow',
        ]

        _freeze_time_init_mock.assert_called_once_with(
            time_to_freeze_str="2020-10-06",
            tz_offset=0,
            ignore=expected_ignore_list,
            tick=False,
            as_arg=False,
            as_kwarg='',
            auto_tick_seconds=0,
        )
