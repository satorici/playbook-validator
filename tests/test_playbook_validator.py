import pytest

from satorici.validator import validate_playbook
from satorici.validator.exceptions import PlaybookValidationError


def test_empty_settings():
    playbook = {
        "settings": {},
        "tests": {
            "cmd": [["echo"]],
        },
    }
    with pytest.raises(PlaybookValidationError):
        validate_playbook(playbook)


def test_playbook_without_executions():
    playbook = {
        "tests": {"input": ["1"]},
    }
    with pytest.raises(PlaybookValidationError):
        validate_playbook(playbook)
