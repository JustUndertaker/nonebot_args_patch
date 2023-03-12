from typing import Any, Callable, Optional, Union

from nonebot.dependencies import Dependent
from nonebot.message import RUN_PREPCS_PARAMS


class Arg:
    """参数基类"""

    name: Optional[str]
    """参数提示名"""
    optional: bool
    """是否可选"""

    def __init__(self, name: str, optional: bool) -> None:
        self.name = name
        self.optional = optional


class Require(Arg):
    """
    说明:
        该参数需要用户提供

    参数:
        * `help`：帮助指令提示的参数显示名称
    """

    def __init__(self, help: str = None) -> None:
        super().__init__(help, False)


class AtRequire(Arg):
    """
    说明:
        * 该参数表示需要获取机器人at的目标，获取到的会是`MessageSegment`
        * 此外，`AtRequire`的顺序不重要，只看数量；但是`AtRequire`之间是有顺序的

    参数:
        * `help`：帮助指令提示的参数显示名称

    注意:
        * nb2在消息开头at机器人时会将at去掉
    """

    def __init__(self, help: str = None) -> None:
        super().__init__(help, False)


class Default(Arg):
    """
    说明:
        该参数在用户不提供时会有默认值

    参数:
        * `default`：该参数可以是Callable，也可以是任意值，当类型为
            `Callable`时，可以使用依赖注入，并拥有`bot`，`matcher`，`event`，`state`等注入参数
        * `help`：帮助指令提示的参数显示名称
        * `priority`: 优先级，在缺少参数时，优先级越高的Default更优先获取参数，参数越小优先级越高，默认为1

    注意:
        * 在使用`get_args`获取该参数时，类型注解需要保持一致

    例子:

    ```python
    matcher = on_command("test", value=Default(123))

    @matcher.handle()
    async def _( value:int = get_args("value") ): # value的类型为 int
    ```
    """

    is_callable: bool
    """是否为callable函数"""
    func: Dependent[Any]
    """依赖容器"""
    value: Any
    """默认值"""
    priority: int
    """优先级"""
    matched: bool
    """已完成匹配"""

    def __init__(
        self,
        default: Union[Callable[..., Any], Any],
        help: str = None,
        priority: int = 1,
    ) -> None:
        if callable(default):
            self.is_callable = True
            self.func = Dependent[Any].parse(
                call=default, allow_types=RUN_PREPCS_PARAMS
            )
        else:
            self.is_callable = False
            self.value = default
        self.priority = priority
        self.matched = False
        super().__init__(name=help, optional=True)
