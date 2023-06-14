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
