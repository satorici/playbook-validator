import pytest

from satorici.validator import validate_playbook
from satorici.validator.exceptions import PlaybookVariableError

failed_refs = [
    {
        # Non existing ref
        "cmd": ["${{input}}"],
    },
    {
        # Ref is not an input
        "other": ["echo dummy"],
        "cmd": ["${{other}}"],
    },
    {
        # The input exists after the ref
        "cmd": ["${{input}}"],
        "input": [["dummy"]],
    },
    {
        # Ref a test without inputs
        "test": {
            "cmd": ["${{test}}"],
        }
    },
    {
        # Ref an input after the parent
        "test": {
            "cmd": ["${{input}}"],
        },
        "input": [["dummy"]],
    },
    {
        # Nearest ref is not an input
        "root": {
            "input": [["dummy"]],
            "root": {
                "cmd": ["${{root}}"],
            },
        },
    },
    {
        # Ref a non visible input
        "root": {
            "sub1": {
                "input": [["dummy"]],
            },
            "sub2": {
                "cmd": ["${{input}}"],
            },
        },
    },
    {
        # Ref an adjacent test without inputs
        "root": {
            "sub1": {
                "cmd": ["echo"],
            },
            "sub2": {
                "cmd": ["${{sub1}}"],
            },
        },
    },
]


@pytest.mark.parametrize("playbook", failed_refs)
def test_failed_references(playbook):
    with pytest.raises(PlaybookVariableError):
        validate_playbook(playbook)


passed_refs = [
    {
        # Ref an adjacent input
        "input": [["1"]],
        "cmd": ["${{input}}"],
    },
    {
        # Ref a parent input
        "input": [["1"]],
        "root": {
            "cmd": ["${{input}}"],
        },
    },
    {
        # Ref a parent that has inputs
        "root": {
            "input": [["1"]],
            "cmd": ["${{root}}"],
        }
    },
    {
        # Ref a parent that has inputs before the caller
        "root": {
            "child1": {
                "cmd": ["${{root}}"],
            },
            "child2": {"input": [["1"]]},
        }
    },
    {
        # Ref an adjacent test that has one input
        "root": {
            "sub": {"input": [["1"]]},
            "cmd": ["$(sub)"],
        },
    },
]


@pytest.mark.parametrize("playbook", passed_refs)
def test_passed_references(playbook):
    validate_playbook(playbook)
