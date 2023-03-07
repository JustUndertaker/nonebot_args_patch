import shlex
from datetime import datetime, timedelta
from typing import (
    Any,
    Callable,
    Dict,
    Generic,
    List,
    Optional,
    Set,
    Tuple,
    Type,
    TypeVar,
    Union,
)

from nonebot import Bot, logger, on_message
from nonebot.consts import CMD_ARG_KEY, PREFIX_KEY
from nonebot.dependencies import Dependent
from nonebot.internal.adapter.event import Event
from nonebot.internal.adapter.message import Message
from nonebot.internal.matcher import Matcher
from nonebot.internal.permission import Permission
from nonebot.internal.rule import Rule
from nonebot.params import Depends
from nonebot.rule import command
from nonebot.typing import T_Handler, T_PermissionChecker, T_RuleChecker, T_State

from .args import Arg, AtRequire, Default, Require
from .consts import ARGS, ARGSTYPE
from .exception import CommandArgException
from .helper import CommandHelp, CommandHelper, OneArgHelp
from .provider import DefaultManager
from .rule import space_command

T = TypeVar("T", bound=Arg)


class Args(Generic[T]):
    """
    命令参数类
    """

    args_list: List[Tuple[str, T]] = []
    """命令元组列表"""
    default_manager: DefaultManager
    """默认参数的管理器"""
    num_args: int
    """参数数量"""
    is_matched: bool
    """是否匹配完成"""
    need_at: bool
    """是否需要获取at目标"""
    num_at: int
    """at目标数量"""
    at_name_list: List[str]
    """at的参数名列表"""
    result: Dict[str, Any]
    """匹配结果字典"""

    @classmethod
    def new(cls, cmd: Set[str], need_help: bool, **kwargs: T) -> Type["Args"]:
        """
        创建一个Args类
        """
        args_list: List[Tuple[str, T]] = []
        at_name_list: List[str] = []
        command_help_list: List[OneArgHelp] = []
        default_manager = DefaultManager()
        need_at = False
        for name, arg in kwargs.items():
            if not isinstance(arg, Arg):
                raise TypeError(
                    f"命令传入参数类型错误，{name} 的类型必须为'Require','AtRequire'或'Default'"
                )
            command_help_list.append(
                OneArgHelp(name=arg.name if arg.name else name, optional=arg.optional)
            )
            if isinstance(arg, AtRequire):
                need_at = True
                at_name_list.append(name)
            else:
                args_list.append((name, arg))
                if isinstance(arg, Default):
                    default_manager[arg.priority].append(arg)
        CommandHelper.add_command(
            names=cmd,
            command=CommandHelp(
                command=cmd, need_help=need_help, args_help=command_help_list
            ),
        )
        num_args = len(args_list)
        num_at = len(at_name_list)
        new_args = type(
            "Args",
            (Args,),
            {
                "args_list": args_list,
                "num_args": num_args,
                "default_manager": default_manager,
                "is_matched": False,
                "need_at": need_at,
                "num_at": num_at,
                "at_name_list": at_name_list,
                "result": {},
            },
        )
        return new_args

    @classmethod
    def check_is_all_default(cls) -> bool:
        """检测该args是否全为Default"""
        return all(isinstance(arg, Default) for _, arg in cls.args_list)

    async def match(
        self,
        bot: Bot,
        event: Event,
        matcher: Matcher,
    ) -> None:
        """进行匹配"""
        args_msg: Message = matcher.state[PREFIX_KEY][CMD_ARG_KEY]
        # 匹配at参数
        if self.need_at:
            at_msg: Message = args_msg["at"]
            if len(at_msg) != self.num_at:
                msg = "at目标数量不对"
                logger.error(msg)
                raise CommandArgException(msg)
            for name, segment in zip(self.at_name_list, at_msg):
                self.result[name] = segment

        # 匹配字符串参数
        arg_text = args_msg.extract_plain_text()
        args_list = shlex.split(arg_text)
        required_arg = [arg for _, arg in self.args_list if isinstance(arg, Require)]
        if len(args_list) < len(required_arg):
            msg = "命令传入参数不足"
            logger.error(msg)
            raise CommandArgException(msg)

        need_default_num = self.num_args - len(args_list)
        if need_default_num < 0:
            msg = "命令传入参数过多"
            logger.error(msg)
            raise CommandArgException(msg)

        default_gennerate = self.default_manager.get_arg()
        need_get_defult_num = len(self.default_manager) - need_default_num
        get_default_arg = [next(default_gennerate) for _ in range(need_get_defult_num)]
        count = 0
        for name, arg in self.args_list:
            if isinstance(arg, Default):
                if arg in get_default_arg:
                    self.result[name] = args_list[count]
                    count += 1
                else:
                    if arg.is_callable:
                        self.result[name] = await arg.func(
                            bot=bot,
                            event=event,
                            matcher=matcher,
                            state=matcher.state,
                        )
                    else:
                        self.result[name] = arg.value
            else:
                self.result[name] = args_list[count]
                count += 1
        self.is_matched = True


def on_command(
    cmd: Union[str, Tuple[str, ...]],
    rule: Optional[Union[Rule, T_RuleChecker]] = None,
    permission: Optional[Union[Permission, T_PermissionChecker]] = None,
    aliases: Optional[Set[Union[str, Tuple[str, ...]]]] = None,
    handlers: Optional[List[Union[T_Handler, Dependent]]] = None,
    temp: bool = False,
    expire_time: Optional[Union[datetime, timedelta]] = None,
    priority: int = 1,
    block: bool = False,
    need_space: bool = False,
    need_help: bool = True,
    _depth: int = 0,
    **kwargs,
) -> Type[Matcher]:
    """注册一个消息事件响应器，并且当消息以指定命令开头时响应。

    命令匹配规则参考: `命令形式匹配 <rule.md#command-command>`_

    参数:
        * `cmd`: 指定命令内容
        * `rule`: 事件响应规则
        * `aliases`: 命令别名
        * `permission`: 事件响应权限
        * `handlers`: 事件处理函数列表
        * `temp`: 是否为临时事件响应器（仅执行一次）
        * `expire_time`: 事件响应器最终有效时间点，过时即被删除
        * `priority`: 事件响应器优先级
        * `block`: 是否阻止事件向更低优先级传递
        * `need_space`: 命令与参数之间是否需要空格
        * `need_help`: 是否需要相似命令检验

    命令参数:
        * `Require`：用户必须填写的参数
        * `AtRequire`：指令at的目标
        * `Default`：拥有默认值的参数
    """
    commands = {cmd} | (aliases or set())
    try:
        args = Args.new(commands, need_help, **kwargs)
        default_state: T_State = {ARGSTYPE: args}
    except TypeError as e:
        raise TypeError(e)
    _rule = (
        space_command(args.check_is_all_default(), *commands)
        if need_space
        else command(*commands)
    )
    return on_message(
        _rule & rule,
        permission=permission,
        block=block,
        handlers=handlers,
        temp=temp,
        expire_time=expire_time,
        priority=priority,
        state=default_state,
        _depth=_depth + 1,
    )


class CommandGroup:
    """
    命令组，用于管理一组相同权限组
    """

    rule: Optional[Union[Rule, T_RuleChecker]]
    permission: Optional[Union[Permission, T_PermissionChecker]]
    handlers: Optional[List[Union[T_Handler, Dependent]]]
    temp: bool
    expire_time: Optional[Union[datetime, timedelta]]
    priority: int
    block: bool
    need_space: bool
    need_help: bool
    _depth: int

    def __init__(
        self,
        rule: Optional[Union[Rule, T_RuleChecker]] = None,
        permission: Optional[Union[Permission, T_PermissionChecker]] = None,
        handlers: Optional[List[Union[T_Handler, Dependent]]] = None,
        temp: bool = False,
        expire_time: Optional[Union[datetime, timedelta]] = None,
        priority: int = 1,
        block: bool = False,
        need_space: bool = False,
        need_help: bool = True,
        _depth: int = 0,
    ) -> None:
        self.rule = rule
        self.permission = permission
        self.handlers = handlers
        self.temp = temp
        self.expire_time = expire_time
        self.priority = priority
        self.block = block
        self.need_space = need_space
        self.need_help = need_help
        self._depth = _depth

    def on_command(
        self,
        cmd: Union[str, Tuple[str, ...]] = None,
        rule: Optional[Union[Rule, T_RuleChecker]] = None,
        permission: Optional[Union[Permission, T_PermissionChecker]] = None,
        aliases: Optional[Set[Union[str, Tuple[str, ...]]]] = None,
        handlers: Optional[List[Union[T_Handler, Dependent]]] = None,
        temp: bool = None,
        expire_time: Optional[Union[datetime, timedelta]] = None,
        priority: int = None,
        block: bool = None,
        need_space: bool = None,
        need_help: bool = None,
        _depth: int = None,
        **kwargs,
    ) -> Type[Matcher]:
        """注册一个消息事件响应器，并且当消息以指定命令开头时响应。

        命令匹配规则参考: `命令形式匹配 <rule.md#command-command>`_

        参数:
        * `cmd`: 指定命令内容
        * `rule`: 事件响应规则
        * `aliases`: 命令别名
        * `permission`: 事件响应权限
        * `handlers`: 事件处理函数列表
        * `temp`: 是否为临时事件响应器（仅执行一次）
        * `expire_time`: 事件响应器最终有效时间点，过时即被删除
        * `priority`: 事件响应器优先级
        * `block`: 是否阻止事件向更低优先级传递
        * `need_space`: 命令与参数之间是否需要空格
        * `need_help`: 是否需要相似命令检验

        命令参数:
            * `Require`：用户必须填写的参数
            * `AtRequire`：指令at的目标
            * `Default`：拥有默认值的参数
        """
        rule = rule or self.rule
        permission = permission or self.permission
        handlers = handlers or self.handlers
        temp = temp or self.temp
        expire_time = expire_time or self.expire_time
        priority = priority or self.priority
        block = block or self.block
        need_space = need_space or self.need_space
        need_help = need_help or self.need_help
        _depth = _depth or self._depth
        return on_command(
            cmd=cmd,
            rule=rule,
            permission=permission,
            aliases=aliases,
            handlers=handlers,
            temp=temp,
            expire_time=expire_time,
            priority=priority,
            block=block,
            need_space=need_space,
            need_help=need_help,
            _depth=_depth,
            **kwargs,
        )


def get_args(
    arg_name: str,
    result_type: Optional[Union[Type[str], Type[int], Callable[[Any], Any]]] = None,
) -> Any:
    """
    说明:
        获取命令参数

    参数:
        * `arg_name`：要获取的参数名，和on_command设置的一致
        * `result_type`：返回结果类型，默认为`None`：
            * `None`：将原样返回获取到的结果
            * `Type[str]`：尝试转换为`str`类型
            * `Type[int]`：尝试转换为`int`类型
            * `Callable`：会将获得的结果调用这个call之后返回

    返回:
        * `Any`：你获取到的参数
    """

    async def _get_args(
        matcher: Matcher,
        state: T_State,
    ) -> Any:
        try:
            args: Args = state[ARGS]
        except KeyError:
            logger.error("未获取到Args对象")
            matcher.skip()

        result = args.result.get(arg_name, None)
        if result is None:
            logger.error(f"未找到{arg_name}的参数")
            matcher.skip()
        if result_type == str:
            result = str(result)
        elif result_type == int:
            try:
                result = int(result)
            except ValueError:
                logger.error(f"在尝试将参数[{arg_name}]: {result} 转换为int时出错")
                matcher.skip()
        elif callable(result_type):
            try:
                result = result_type(result)
            except Exception:
                logger.error(f"在尝试将参数[{arg_name}]运行转换[{result_type.__name__}]时出错")
                matcher.skip()
        return result

    return Depends(_get_args)
