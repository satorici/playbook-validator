import json
import re
from copy import deepcopy
from pathlib import Path

from flatdict import FlatDict
from jsonschema import Draft7Validator, FormatChecker
from jsonschema.exceptions import ValidationError
from jsonschema.validators import RefResolver

from .exceptions import PlaybookValidationError, PlaybookVariableError

INPUT_REGEX = re.compile(r"\$\(([\w-]+)\)")

SCHEMAS = Path(__file__).parent / "schemas"

with (
    open(SCHEMAS / "command.json") as commands,
    open(SCHEMAS / "input.json") as inputs,
    open(SCHEMAS / "import.json") as imports,
    open(SCHEMAS / "settings.json") as settings,
    open(SCHEMAS / "test.json") as test,
):
    command_schema = Draft7Validator(json.loads(commands.read()))
    input_schema = Draft7Validator(json.loads(inputs.read()))
    import_schema = Draft7Validator(json.loads(imports.read()))
    settings_schema = Draft7Validator(json.loads(settings.read()))
    test_schema = Draft7Validator(
        schema=json.loads(test.read()),
        resolver=RefResolver(base_uri=f"{SCHEMAS.as_uri()}/", referrer=True),
        format_checker=FormatChecker(("regex",)),
    )

split_key = lambda key: str(key).split(":")
get_leaf = lambda key: split_key(key)[-1]


def validate_command_block(commands: list[list[str]], key: str, flat_config: dict[str]):
    variables = set()

    for command in commands:
        variables.update(INPUT_REGEX.findall(command[0]))

    if not variables:
        return

    keys: list[str] = flat_config.keys()
    previous_paths = list(reversed(keys[: keys.index(key)]))

    path = split_key(key)
    levels = len(path)

    for variable in variables:
        prefixes = list(":".join(path[:i] + [variable]) for i in range(levels))
        prefixes.reverse()
        found_prefix = None

        for prefix in prefixes:
            if not any((p.startswith(prefix) for p in previous_paths)):
                continue

            found_prefix = prefix

            for key, value in flat_config.items():
                if key.startswith(prefix) and input_schema.is_valid(value):
                    break
            else:
                raise PlaybookVariableError(
                    f"No valid inputs for variable: {variable}", parameter=variable
                )

        if not found_prefix:
            raise PlaybookVariableError(
                f"Can't resolve variable: {variable}", parameter=variable
            )


def validate_playbook(config: dict):
    """
    Validate yaml loaded playbook config and return corresponding dict

    Raises `PlaybookValidationError` on invalid playbook
    Raises `PlaybookVariableError` on invalid playbook variables
    """

    if not isinstance(config, dict):
        raise TypeError("config must be a dict")

    config_copy = deepcopy(config)

    try:
        if config_copy.get("settings"):
            settings_schema.validate(config_copy["settings"])
            del config_copy["settings"]

        test_schema.validate(config_copy)
    except ValidationError as e:
        raise PlaybookValidationError(e.message)

    flat_config = FlatDict(config_copy)

    for key, value in flat_config.items():
        if command_schema.is_valid(value):
            validate_command_block(value, key, flat_config)

    return config
