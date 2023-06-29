import pytest

from satorici.validator import validate_playbook
from satorici.validator.exceptions import PlaybookValidationError
from satorici.validator.warnings import NoLogMonitorWarning


def test_empty_settings():
    playbook = {
        "settings": {},
        "tests": {
            "cmd": [["echo"]],
        },
    }
    with pytest.raises(PlaybookValidationError):
        validate_playbook(playbook)


no_execs = [
    {
        "tests": {"input": ["1"]},
    },
    {
        "input": ["1"],
    },
]


@pytest.mark.parametrize("playbook", no_execs)
def test_playbook_without_executions(playbook):
    with pytest.raises(PlaybookValidationError):
        validate_playbook(playbook)


with_execs = [
    {
        "tests": {"cmd": [["echo"]]},
    },
    {
        "cmd": [["echo"]],
    },
]


@pytest.mark.parametrize("playbook", with_execs)
def test_playbook_with_executions(playbook):
    validate_playbook(playbook)


def test_wrong_assert():
    playbook = {
        "assertStdoutGibberish": 1,
        "cmd": [
            ["echo"],
        ],
    }

    with pytest.raises(PlaybookValidationError):
        validate_playbook(playbook)


def test_correct_assert():
    playbook = {
        "assertReturnCode": 1,
        "cmd": [
            ["echo"],
        ],
    }

    validate_playbook(playbook)


def test_monitor_without_notification():
    playbook = {
        "settings": {
            "name": "aaaa",
            "cron": "0 0 0 0 0",
        },
        "cmd": [
            ["echo"],
        ],
    }

    with pytest.warns(NoLogMonitorWarning):
        validate_playbook(playbook)


def test_cron_monitor():
    playbook = {
        "settings": {
            "name": "aaaa",
            "cron": "0 0 0 0 0",
            "rate": "0 minutes",
        },
        "cmd": [
            ["echo"],
        ],
    }

    with pytest.raises(PlaybookValidationError):
        validate_playbook(playbook)


def test_unnamed_monitor():
    playbook = {
        "settings": {
            "rate": "0 minutes",
        },
        "cmd": [
            ["echo"],
        ],
    }

    with pytest.raises(PlaybookValidationError):
        validate_playbook(playbook)


def test_bad_timeout_settings():
    playbook = {
        "settings": {
            "timeout": 1,
            "commandTimeout": 2,
        },
        "cmd": [
            ["echo"],
        ],
    }

    with pytest.raises(PlaybookValidationError):
        validate_playbook(playbook)


def test_bad_settings():
    playbook = {
        "settings": {
            "timeout": 1,
        },
        "cmd": [
            ["echo"],
        ],
    }

    validate_playbook(playbook)
