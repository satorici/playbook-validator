class PlaybookValidationError(Exception):
    pass


class PlaybookVariableError(PlaybookValidationError):
    def __init__(self, *args: object, parameter: str) -> None:
        super().__init__(*args)
        self.parameter = parameter


class NoExecutionsError(PlaybookValidationError):
    pass


class InvalidCommandError(PlaybookValidationError):
    pass
