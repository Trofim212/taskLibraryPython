from .errors import NotConvertError, ToManyValuesError, InputError, BaseTaskError
from datetime import date, time
from typing import Any, Iterable, Type


class Argument:
    "Basic class for all arguments"
    name: str
    input_message: str = None
    resp: str | Iterable[str] = None
    error: BaseTaskError = None

    def __init__(self, name: str, input_message=None, *args, **kwargs) -> None:
        self.name = name
        if input_message:
            self.input_message = input_message + ": "
        if self.input_message is not None:
            self.input_message += ": "

    # after is_valid instance shoud have value attribute, if string converts to this type
    # if error, should set attribute self.error
    def is_valid(self) -> bool:
        pass

    # self.resp is begin
    def get_input(self) -> None:
        self.resp = input(self.input_message)


class BasicArgument(Argument):
    type: Type = None

    def is_valid(self) -> bool:
        try:
            self.value = self.type(self.resp)
            return True
        except:
            self.error = NotConvertError(self.resp, self.type)
            return False


class Str(BasicArgument):
    input_message = "Write string"
    type = str


class Int(BasicArgument):
    input_message = "Write integer"
    type = int


class Float(BasicArgument):
    input_message = "Write float"
    type = float


class Date(Argument):
    separator = "-"

    def __init__(self, name: str, input_message=None, *args, **kwargs) -> None:
        if sep := kwargs.get("sep"):
            self.separator = sep
        else:
            sep = self.separator

        self.input_message = f"Write date in format dd{sep}mm{sep}yyyy"
        super().__init__(name, input_message, *args, **kwargs)

    def is_valid(self) -> bool:
        try:
            day, month, year = map(int, self.resp.split(self.separator))
        except ValueError:
            self.error = InputError(self.resp,"Incorrect data format")
            return False

        try:
            self.value = date(year, month, day)
            return True
        except:
            self.error = InputError("Incorrect data format")
            return False


class List(Argument):
    separator = ","
    input_message = f"Write arguments throw `{separator}`"
    count: None|int = None

    def __init__(self, name: str, input_message=None, *types: type, **kwargs) -> None:
        super().__init__(name, input_message)
        self.types = types
        if sep := kwargs.get("sep"):
            self.separator = sep
        if count := kwargs.get("count"):
            self.count = count
    
    def is_valid(self) -> bool:
        args = self.resp.split(self.separator)

        if len(self.types) == 1:
            types = self.types * len(args)
            if self.count and len(args) != self.count:
                self.error = InputError(self.resp,f"Need {self.count} arguments")
                return False
        else:
            types = self.types

        value = []
        for arg, type in zip(args,types):
            try:
                value.append(type(arg))
            except ValueError:
                self.error = NotConvertError(self.resp, f"Type {type} not converts to string", self.type)
                return False
            
        self.value = value
        return True