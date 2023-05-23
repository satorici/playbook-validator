class PlaybookValidationError(Exception):
    pass


class PlaybookVariableError(Exception):
    def __init__(self, *args: object, parameter: str) -> None:
        super().__init__(*args)
        self.parameter = parameter
