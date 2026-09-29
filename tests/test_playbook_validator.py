import warnings

import pytest

from satorici.validator import validate_playbook
from satorici.validator.exceptions import PlaybookValidationError
from satorici.validator.warnings import (
    MissingAssertionsWarning,
    MissingNameWarning,
    NoLogMonitorWarning,
)


def test_minimal_playbook():
    validate_playbook({"input": [["1"]], "cmd": ["echo $(input)"]})


no_execs = [
    {
        "tests": {"input": [["1"]]},
    },
    {
        "input": [["1"]],
    },
]


@pytest.mark.parametrize("playbook", no_execs)
def test_playbook_without_executions(playbook):
    with pytest.raises(PlaybookValidationError):
        validate_playbook(playbook)


with_execs = [
    {
        "tests": {"cmd": ["echo"]},
    },
    {"cmd": ["echo"]},
]


@pytest.mark.parametrize("playbook", with_execs)
def test_playbook_with_executions(playbook):
    validate_playbook(playbook)


def test_wrong_assert():
    playbook = {
        "assertStdoutGibberish": 1,
        "cmd": ["echo"],
    }

    with pytest.raises(PlaybookValidationError):
        validate_playbook(playbook)


def test_correct_assert():
    playbook = {
        "assertReturnCode": 1,
        "cmd": ["echo"],
    }

    validate_playbook(playbook)


def test_monitor_without_notification():
    playbook = {
        "settings": {
            "name": "aaaa",
            "cron": "1 * * * ? *",
        },
        "cmd": ["echo"],
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
        "cmd": ["echo"],
    }

    with pytest.raises(PlaybookValidationError):
        validate_playbook(playbook)


def test_unnamed_monitor():
    playbook = {
        "settings": {
            "rate": "0 minutes",
        },
        "cmd": ["echo"],
    }

    with pytest.raises(PlaybookValidationError):
        validate_playbook(playbook)


def test_bad_settings():
    playbook = {
        "settings": {
            "timeout": 1,
        },
        "cmd": ["echo"],
    }

    validate_playbook(playbook)


def test_invalid_command():
    playbook = {
        "settings": {
            "timeout": 1,
        },
        "cmd": ['"'],
    }

    with pytest.raises(PlaybookValidationError):
        validate_playbook(playbook)


def test_set_parallel():
    playbook = {
        "install": {"setParallel": True},
        "cmd": ['""'],
    }

    validate_playbook(playbook)


def test_playbook_without_asserts():
    playbook = {
        "cmd": ["echo"],
    }

    with pytest.warns(MissingAssertionsWarning):
        validate_playbook(playbook)


def test_playbook_without_name():
    playbook = {
        "assertReturnCode": 0,
        "cmd": ["echo"],
    }

    with pytest.warns(MissingNameWarning):
        validate_playbook(playbook)


failed_cpu_memory = [
    {"settings": {"cpu": 512}, "cmd": ["echo"]},
    {"settings": {"memory": 1023}, "cmd": ["echo"]},
    {"settings": {"cpu": 512, "memory": 1023}, "cmd": ["echo"]},
    {"settings": {"cpu": 513, "memory": 1024}, "cmd": ["echo"]},
]


@pytest.mark.parametrize("playbook", failed_cpu_memory)
def test_failed_cpu_memory(playbook):
    with pytest.raises(PlaybookValidationError):
        validate_playbook(playbook)


def test_imports():
    playbook = {
        "settings": {
            "name": "Import playbooks",
        },
        "import": ["file://pass.yml", "satori://secrets/trufflehog.yml"],
        "cmd": ["echo"],
    }

    validate_playbook(playbook)


valid_expire = [
    "1 hours",
    "7 days",
    "2 weeks",
    "100 days",
]


@pytest.mark.parametrize("expire", valid_expire)
def test_valid_expire(expire):
    playbook = {
        "settings": {
            "name": "Expire playbook",
            "expire": expire,
        },
        "cmd": ["echo"],
    }

    validate_playbook(playbook)


invalid_expire = [
    "7 minutes",
    "0 days",
    "days",
    "7",
    "1 day",
    "-1 days",
    7,
]


@pytest.mark.parametrize("expire", invalid_expire)
def test_invalid_expire(expire):
    playbook = {
        "settings": {
            "name": "Expire playbook",
            "expire": expire,
        },
        "cmd": ["echo"],
    }

    with pytest.raises(PlaybookValidationError):
        validate_playbook(playbook)


def test_valid_notify():
    playbook = {
        "settings": {
            "name": "Notify playbook",
            "notify": [
                {
                    "result": "fail",
                    "severity": ["high", "critical", "blocker"],
                    "to": "slack://ID1:ID2",
                },
                {
                    "result": "fail",
                    "to": "email://security@example.com",
                },
            ],
        },
        "cmd": ["echo"],
    }

    validate_playbook(playbook)


valid_notify_to = [
    "slack://ID1:ID2",
    "email://security@example.com",
    "discord://channel",
    "datadog://key",
    "telegram://bot:chat",
]


@pytest.mark.parametrize("to", valid_notify_to)
def test_valid_notify_schemes(to):
    playbook = {
        "settings": {
            "name": "Notify playbook",
            "notify": [{"result": "pass", "to": to}],
        },
        "cmd": ["echo"],
    }

    validate_playbook(playbook)


invalid_notify = [
    [{"result": "error", "to": "slack://ID1:ID2"}],
    [{"result": "fail", "severity": ["unknown"], "to": "slack://ID1:ID2"}],
    [{"result": "fail", "severity": [], "to": "slack://ID1:ID2"}],
    [{"result": "fail", "to": "http://example.com"}],
    [{"result": "fail"}],
    [{"result": "fail", "to": "slack://ID1:ID2", "extra": True}],
]


@pytest.mark.parametrize("notify", invalid_notify)
def test_invalid_notify(notify):
    playbook = {
        "settings": {
            "name": "Notify playbook",
            "notify": notify,
        },
        "cmd": ["echo"],
    }

    with pytest.raises(PlaybookValidationError):
        validate_playbook(playbook)


def test_monitor_with_notify():
    playbook = {
        "settings": {
            "name": "aaaa",
            "cron": "1 * * * ? *",
            "notify": [{"result": "fail", "to": "slack://ID1:ID2"}],
        },
        "cmd": ["echo"],
    }

    with warnings.catch_warnings():
        warnings.simplefilter("error", NoLogMonitorWarning)
        validate_playbook(playbook)
