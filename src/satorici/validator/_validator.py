import json
import re
from copy import deepcopy
from pathlib import Path
from urllib.parse import urlsplit

from fastjsonschema import JsonSchemaValueException, compile

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


def _validate(schema, value, raise_exception=False):
    try:
        schema(value)
        return True
    except JsonSchemaValueException as e:
        if raise_exception:
            raise e

        return False


def validate_inputs(inputs: list, raise_exception=False):
    return _validate(inputs_schema, inputs, raise_exception)


def validate_commands(commands: list, raise_exception=False):
    return _validate(commands_schema, commands, raise_exception)


def validate_imports(inports: list, raise_exception=False):
    return _validate(imports_schema, inports, raise_exception)


def validate_test(test: dict, raise_exception=False):
    return _validate(test_schema, test, raise_exception)


def validate_settings(settings: dict, raise_exception=False):
    return _validate(settings_schema, settings, raise_exception)


def has_input(d: dict[str]):
    stack = [v for k, v in d.items() if "^" not in k]

    while stack:
        current = stack.pop()

        if validate_inputs(current):
            return True
        elif isinstance(current, dict):
            stack.extend(v for k, v in current.items() if "^" not in k)

    return False


def get_reference_names(command_block: list[list[str]]):
    variables: set[str] = set()

    for command in command_block:
        variables.update(INPUT_REGEX.findall(command[0]))

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

        for key, value in (i for i in current.items() if "^" not in i[0]):
            if key == limit_key:
                limit_key = current.get("^key")
                current = current.get("^dict")
                break

            if key in variables:
                if validate_inputs(value) or (
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

    while stack:
        path, current = stack.pop()

        for k, v in (i for i in current.items() if "^" not in i[0]):
            if isinstance(v, dict):
                stack.append((path + (k,), v))
            elif validate_commands(v):
                execution_found = True
                if get_reference_names(v):
                    validate_references(current, k)

    if not execution_found:
        raise PlaybookValidationError("No executions found.")


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

    try:
        test_schema(config_copy)
    except JsonSchemaValueException as e:
        raise PlaybookValidationError(e.message)

    add_parent_info(config_copy)
    iterate_dict(config_copy)

    return config
