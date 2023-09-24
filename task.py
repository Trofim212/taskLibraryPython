from typing import Any, Iterable, Callable
from .arguments import Argument
from .errors import TaskError
from .arguments import Str, Int, Float, Date


class Result:
    "Ojbect allow get access to arguments and know if some arguments is not valid"

    args: list[Argument] = []
    error_args: list[Argument] = []

    def add(self, arg: Argument) -> None:
        self.args.append(arg)
        setattr(self, arg.name, arg.value)

    def add_error_arg(self, arg: Argument) -> None:
        self.error_args.append(arg)
        setattr(self, arg.name, None)

    def to_dict(self) -> dict[str, Any]:
        result = {}
        result["_errors"] = {arg.name: arg.error for arg in self.error_args}
        result.update({arg.name: arg.value for arg in self.args})
        return result

    def __len__(self) -> int:
        return len(self.args) + len(self.error_args)


class Task:
    def __init__(
        self,
        task: Callable[[Result], str],
        name: str,
        args: Iterable[Argument] = None,
        *options,
        **kwargs,
    ):
        self.task = task
        self.name = name
        self.args = args
        self.__check_args_repeat()
        self.kwargs = kwargs

    def __check_args_repeat(self) -> None:
        names = [arg.name for arg in self.args]
        if len(set(names)) != len(names):
            raise ValueError("Argument names must not repeated")

    def show_arg_input(self, arg: Argument) -> None:
        arg.get_input()
        if self.kwargs.get("repeat") == True:
            while not arg.is_valid():
                print(arg.error)
                arg.get_input()

    def get_result(self) -> Result:
        result = Result()

        for arg in self.args:
            self.show_arg_input(arg)
            if not arg.is_valid():
                result.add_error_arg(arg)
            else:
                result.add(arg)

        return result

    def get_task_result(self) -> str:
        result = self.get_result()

        if self.kwargs.get("dict"):
            result = result.to_dict()

        try:
            if len(result) == 0:
                task_result = self.task()
            else:
                task_result = self.task(result)
        except Exception as exc:
            raise TaskError(exc, self.name)

        try:
            return str(task_result)
        except Exception as e:
            raise TaskError(e, self.name)

    def run(self) -> None:
        print(f"________{self.name}________")
        print(f"Результат - {self.get_task_result()}")
        print("________Task End________")


class TaskLauncher:
    task_class: Task = Task

    types_dict: dict[str, Argument] = {
        "str": Str,
        "int": Int,
        "float": Float,
        "date": Date,
    }

    @classmethod
    def get_task_name(cls, raw_name: str):
        return " ".join([c.capitalize() for c in raw_name.split("_")])

    @classmethod
    def get_python_name(cls, name: str):
        return "_".join([x.lower() for x in name.replace(" ", "_").split("_")])

    @classmethod
    def get_task_params_by_func_name(cls, name: str) -> tuple([str, list, list, dict]):
        kwargs = {}
        options = []
        task_args = []

        task_name, *args = name.replace("task_", "", 1).split("__")
        task_name = cls.get_task_name(task_name)

        if not args:
            return task_name, task_args, options, kwargs

        for arg in args:
            arg = arg.split("_")
            if len(arg) == 1:
                options.append(arg[0])
            elif len(arg) > 2:
                arg = "_".join(arg)
                raise ValueError(f"Bad parameter for func name - {arg}")
            else:
                if arg_type := cls.types_dict.get(arg[1]):
                    task_args.append(arg_type(name=arg[0]))
                else:
                    if arg[1].lower() in ("true", "false"):
                        kwargs[arg[0]] = True if arg[1].lower() == "true" else False
                    else:
                        kwargs[arg[0]] = arg[1]

        return task_name, task_args, options, kwargs

    @classmethod
    @property
    def tasks(cls) -> dict[str, Task]:
        tasks = {}

        for name, task in cls.__dict__.items():
            if name.startswith("task_") and callable(task) and name != "task_class":
                task_name, args, options, kwargs = cls.get_task_params_by_func_name(
                    name
                )

                tasks[cls.get_python_name(task_name)] = cls.task_class(
                    task, task_name, args, *options, **kwargs
                )

            elif isinstance(task, Task):
                name = cls.get_python_name(task.name)
                tasks[name] = task

        return tasks

    @classmethod
    def run_all(cls):
        for task in cls.tasks.values():
            task.run()

    @classmethod
    def run(cls, *names):
        tasks = cls.tasks
        for name in names:
            if name not in tasks:
                raise KeyError(f"Not task with name {name}")
            tasks[name].run()


def task(
    name: str,
    args: Iterable[Argument] = [],
    task_class: Task = Task,
    *options,
    **kwargs,
):
    def wrap(task):
        return task_class(task, name, args, *options, **kwargs)

    return wrap
