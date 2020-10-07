from unittest import mock
import freezegun


def teardown_function():
    freezegun.configure(default_ignore=None)


def test_default_ignore_is_overridden():
    freezegun.configure(default_ignore=['threading', 'tensorflow'])

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
