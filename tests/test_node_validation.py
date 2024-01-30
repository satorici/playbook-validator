from satorici.validator import validate_input_group, validate_command_group


def test_is_input():
    validate_input_group([["1", "2"]])


def test_is_command():
    validate_command_group(["1", "2"])
