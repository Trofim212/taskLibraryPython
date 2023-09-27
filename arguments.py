from .errors import NotConvertError, ToManyValuesError, InputError, BaseTaskError
from datetime import date, time
from typing import Any, Iterable, Type, Literal
import re


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

    # for is_valid method
    def get_input_error(self, message: str = None) -> Literal[False]:
        return self.get_error(InputError, message)

    def get_error(self, error: BaseTaskError, message: str = None, *args, **kwargs):
        self.error = error(self.resp, message=message, *args, **kwargs)
        return False


class BasicArgument(Argument):
    type: Type = None

    def is_valid(self) -> bool:
        try:
            self.value = self.type(self.resp)
            return True
        except:
            return self.get_error(NotConvertError)


class Str(BasicArgument):
    input_message = "Write string"
    type = str


class Int(BasicArgument):
    input_message = "Write integer"
    type = int


class Float(BasicArgument):
    input_message = "Write float"
    type = float


class ParseDataArgument(Argument):
    format_str: str
    format_names: dict[str, str]

    def __init__(self, name: str, input_message=None, *args, **kwargs) -> None:
        if format_str := kwargs.get("format"):
            self.format_str = format_str
        else:
            format_str = self.format_str

        self.sequence = self.get_format_sequence()

        if not input_message:
            for char, name in self.format_names.items():
                format_str = format_str.replace(char, name)

            self.input_message = f"Write in format: {format_str}"

        super().__init__(name, input_message, *args, **kwargs)

    def get_format_sequence(self) -> list[str]:
        sequence = {}
        for symbol, name in self.format_names.items():
            if (index := self.format_str.find(symbol)) != -1:
                sequence[name] = index

        sequence = sorted(sequence.items(), key=lambda a: a[1])
        return [s[0] for s in sequence]

    def get_reg_str(self) -> str:
        reg_str = re.escape(self.format_str) + "$"
        for char in self.format_names.keys():
            reg_str = reg_str.replace(char, r"(.+?)")
        return reg_str

    def has_matches(self) -> bool:
        matches = re.search(self.get_reg_str(), self.resp)
        if matches is None:
            return False
        self.matches = matches
        return True

    def get_args(self):
        args = {}
        for i, name in enumerate(self.sequence):
            arg = self.matches.group(i + 1)
            args[name] = arg
        return args

    def get_args_error_message(self):
        return "Incorrect arg:"

    def get_str_args(self, args):
        return ", ".join((f"{name} - {value}" for name, value in args))

    def get_arg_errors(self, args):
        str_args = self.get_str_args(args)
        message = self.get_args_error_message()
        return self.get_input_error(f"{message} - {str_args}")


class Date(ParseDataArgument):
    format_str = "%d/%m/%y"
    format_names = {"%d": "day", "%m": "month", "%y": "year"}

    def is_valid(self) -> bool:
        if len(self.sequence) != len(self.format_names):
            raise ValueError("")

        if not self.has_matches():
            return self.get_input_error("Incorrect data values")

        date_args = self.get_args()

        if any((not s.isdigit() for s in date_args.values())):
            return self.get_arg_errors(date_args)

        date_args = {n: int(v) for n, v in date_args.items()}

        try:
            self.value = date(**date_args)
            return True
        except:
            return self.get_arg_errors(date_args)


class List(Argument):
    separator = ","
    input_message = f"Write arguments throw `{separator}`"
    count: None | int = None

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
                return self.get_input_error(f"Need {self.count} arguments")
        else:
            types = self.types

        value = []
        for arg, type in zip(args, types):
            try:
                value.append(type(arg))
            except ValueError:
                return self.get_error(
                    NotConvertError,
                    f"Type {type} not converts to string",
                    type=self.type,
                )

        self.value = value
        return True


class Time(ParseDataArgument):
    format_names = {"%h": "hours", "%m": "minutes", "%s": "seconds"}
    format_str = "%h:%m:%s"

    def is_valid(self):
        if not self.has_matches():
            return self.get_input_error("Incorrect time input")

        time_args = self.get_args()
        if any((not s.is_digit() for s in time_args.values())):
            return self.get_arg_errors(time_args)

        time_args = {n: int(v) for n, v in time_args.items()}

        try:
            self.value = time(**time_args)
            return True
        except:
            return self.get_arg_errors()
