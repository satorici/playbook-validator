import json
import re
import shlex
import warnings
from copy import deepcopy
from pathlib import Path
from urllib.parse import urlsplit

from aws_cron_expression_validator.validator import AWSCronExpressionValidator
from fastjsonschema import JsonSchemaValueException, compile

from .exceptions import (
    InvalidCommandError,
    NoExecutionsError,
    PlaybookValidationError,
    PlaybookVariableError,
)
from .warnings import MissingAssertionsWarning, MissingNameWarning, NoLogMonitorWarning

INPUT_REGEX = re.compile(r"\$\{\{([\w-]+)\}\}")

SCHEMAS = Path(__file__).parent / "schemas"

with (
    open(SCHEMAS / "command.json") as commands,
    open(SCHEMAS / "input.json") as inputs,
    open(SCHEMAS / "import.json") as imports,
    open(SCHEMAS / "settings.json") as settings,
    open(SCHEMAS / "test.json") as test,
):

    def file_ref_loc(uri: str):
        _, _, path, *_ = urlsplit(uri)

        with Path(SCHEMAS, path[1:]).open() as f:
            return json.loads(f.read())

    commands_schema = compile(json.loads(commands.read()))
    inputs_schema = compile(json.loads(inputs.read()))
    imports_schema = compile(json.loads(imports.read()))
    settings_schema = compile(json.loads(settings.read()))
    test_schema = compile(
        definition=json.loads(test.read()),
        handlers={"file": file_ref_loc},
    )


def _validate(schema, value):
    try:
        schema(value)
    except JsonSchemaValueException as e:
        raise PlaybookValidationError(e.message)


def _is(validator, value):
    try:
        validator(value)
        return True
    except PlaybookValidationError:
        return False


def validate_input_group(inputs: list):
    _validate(inputs_schema, inputs)


def is_input_group(inputs: list):
    return _is(validate_input_group, inputs)


def validate_command_group(commands: list):
    _validate(commands_schema, commands)


def is_command_group(commands: list):
    return _is(validate_command_group, commands)


def validate_import_group(imports: list):
    _validate(imports_schema, imports)


def is_import_group(imports: list):
    return _is(validate_import_group, imports)


def validate_test(test: dict):
    _validate(test_schema, test)


def is_test(test: dict):
    return _is(validate_test, test)


def validate_settings(settings: dict):
    _validate(settings_schema, settings)

    if "cron" in settings:
        try:
            AWSCronExpressionValidator.validate(settings["cron"])
        except Exception as e:
            raise PlaybookValidationError(f"Invalid cron expression: {e}")

    if "name" not in settings:
        warnings.warn(MissingNameWarning("Your playbook has no name defined"))

    if "cron" in settings or "rate" in settings:
        if not any(k.startswith("log") for k in settings):
            warnings.warn(NoLogMonitorWarning("Monitor without notifications."))

    if "timeout" in settings and "commandTimeout" in settings:
        if settings["timeout"] < settings["commandTimeout"]:
            raise PlaybookValidationError("timeout must be greater than commandTimeout")


def is_settings(settings: dict):
    return _is(validate_settings, settings)


def has_input(d: dict[str]):
    stack = [v for k, v in d.items() if "^" not in k]

    while stack:
        current = stack.pop()

        if is_input_group(current):
            return True
        elif isinstance(current, dict):
            stack.extend(v for k, v in current.items() if "^" not in k)

    return False


def get_reference_names(command_block: list[str]):
    variables: set[str] = set()

    for command in command_block:
        variables.update(INPUT_REGEX.findall(command))

    return variables


def validate_references(node: dict[str], cmd_key: str):
    variables = get_reference_names(node[cmd_key])

    current = node
    limit_key = cmd_key
    valid: set[str] = set()
    failed = False

    while current and not failed:
        if current.get("^key") in variables:
            if has_input(current["^dict"][current["^key"]]):
                valid.add(current["^key"])
            else:
                failed = True
                break

        for key, value in (i for i in current.items() if "^" != i[0][0]):
            if key == limit_key:
                limit_key = current.get("^key")
                current = current.get("^dict")
                break

            if key in variables:
                if is_input_group(value) or (
                    isinstance(value, dict) and has_input(value)
                ):
                    valid.add(key)
                else:
                    failed = True
                    break

    if valid != variables:
        v = variables - valid
        raise PlaybookVariableError(
            f"No valid inputs for variable: {', '.join(v)}.", parameter=v
        )


def iterate_dict(d: dict):
    stack = [((), d)]

    execution_found = False
    assertion_found = False

    while stack:
        path, current = stack.pop()

        for k, v in (i for i in current.items() if "^" != i[0][0]):
            if isinstance(v, dict):
                stack.append((path + (k,), v))
            elif k.startswith("assert"):
                assertion_found = True
            elif is_command_group(v):
                execution_found = True

                for cmd in v:
                    try:
                        _ = shlex.split(cmd)
                    except ValueError as e:
                        raise InvalidCommandError(f"{e} on {cmd}.")

                if get_reference_names(v):
                    validate_references(current, k)

    if not assertion_found:
        warnings.warn(MissingAssertionsWarning("No assertions found."))

    if not execution_found:
        raise NoExecutionsError("No executions found.")


def add_parent_info(d: dict):
    stack = [(d, None, None)]

    while stack:
        current, current_parent_key, current_parent_dict = stack.pop()
        current["^key"] = current_parent_key
        current["^dict"] = current_parent_dict

        for key, value in (i for i in current.items() if "^" not in i[0]):
            if isinstance(value, dict):
                stack.append((value, key, current))


def validate_playbook(config: dict):
    """
    Validate yaml loaded playbook config and return corresponding dict

    Raises `PlaybookValidationError` on invalid playbook

    Raises `PlaybookVariableError` on invalid playbook variables
    """

    if not isinstance(config, dict):
        raise TypeError("config must be a dict")

    config_copy = deepcopy(config)

    validate_settings(config_copy.pop("settings", {}))

    validate_test(config_copy)

    add_parent_info(config_copy)
    iterate_dict(config_copy)


def is_playbook(config: dict):
    _is(validate_playbook, config)
