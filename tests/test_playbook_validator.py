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
