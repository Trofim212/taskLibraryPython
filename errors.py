class BaseTaskError(Exception):
    message: str = None
    resp: str = None

    def __init__(self, resp: str, message: str | None = None) -> None:
        self.resp = resp
        if message:
            self.message = message

    def __str__(self) -> str:
        return self.message


class InputError(BaseTaskError):
    "Needle, if user write incorrect input value"
    message = "Your value is not correct"


class ToManyValuesError(BaseTaskError):
    "Needle if values is a big count, and iterable type doesn't expect this"
    message = "You write to many values"


class NotConvertError(BaseTaskError):
    "Needle, if user input value does not converts to string"

    def __init__(self, resp: str, type: type, message: str | None = None) -> None:
        super().__init__(resp, message)
        self.type = type

    def __str__(self) -> str:
        return f"Type {type} not converts to string"


class TaskError(Exception):
    "This error say this was an exception in your task function"

    def __init__(self, exc: Exception, task_name: str) -> None:
        self.exc = exc
        self.task_name = task_name

    def __str__(self) -> str:
        return f"In {self.task_name} : {self.exc.__class__} - {self.exc}"
