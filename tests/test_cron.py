import pytest

from satorici.validator import validate_settings
from satorici.validator.exceptions import PlaybookValidationError


@pytest.mark.parametrize(
    "expression",
    [
        "* * * * *",
        "1 * * * *",
        "*/15 0-6 * * *",
        "0 9-17/2 * * MON-FRI",
        "30 4 1,15 * 5",
        "0 0 1 JAN,jul *",
        "0 0 * * 7",
        "59 23 31 12 6",
    ],
)
def test_valid_cron(expression):
    validate_settings({"name": "monitor", "cron": expression, "log": "x"})


@pytest.mark.parametrize(
    "expression",
    [
        "",
        "* * * *",
        "1 * * * ? *",
        "0 * * * * *",
        "0 0 0 0 0",
        "60 * * * *",
        "* 24 * * *",
        "* * 32 * *",
        "* * * 13 *",
        "* * * * 8",
        "*/0 * * * *",
        "* * * FOO *",
        "1,,2 * * * *",
        "@daily",
        "@hourly",
        "@reboot",
    ],
)
def test_invalid_cron(expression):
    with pytest.raises(PlaybookValidationError):
        validate_settings({"name": "monitor", "cron": expression, "log": "x"})
