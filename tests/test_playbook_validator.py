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


def test_bad_timeout_settings():
    playbook = {
        "settings": {
            "timeout": 1,
            "commandTimeout": 2,
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
