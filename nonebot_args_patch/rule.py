from itertools import product
from typing import List, Optional, Tuple, Union

from nonebot import get_driver
from nonebot.consts import CMD_ARG_KEY, CMD_KEY, PREFIX_KEY, RAW_CMD_KEY
from nonebot.internal.adapter import Event
from nonebot.internal.rule import Rule
from nonebot.params import Command, T_State
from nonebot.rule import CMD_RESULT, TRIE_VALUE, CommandRule, TrieRule


class SpaceCommandRule(CommandRule):
    """带空格的command"""

    __slots__ = ("cmds", "all_default")

    def __init__(self, all_default: bool, cmds: List[Tuple[str, ...]]) -> None:
        self.all_default = all_default
        super().__init__(cmds)

    async def __call__(
        self, event: Event, state: T_State, cmd: Optional[Tuple[str, ...]] = Command()
    ) -> bool:
        command_result = await super().__call__(cmd)
        if command_result:
            return True
        elif not self.all_default:
            return False
        if event.get_type() != "message":
            return False
        try:
            msg = event.get_message()
            text = msg.extract_plain_text()
        except Exception:
            return False
        if not text:
            return False
        if (text,) in self.cmds:
            prefix = CMD_RESULT(
                command=None, raw_command=None, command_arg=None, command_start=None
            )
            argmsg = msg.copy()
            argmsg.clear()
            prefix[RAW_CMD_KEY] = text
            prefix[CMD_KEY] = text
            prefix[CMD_ARG_KEY] = argmsg.append("")
            state[PREFIX_KEY] = prefix
            return True
        return False


def space_command(all_default: bool, *cmds: Union[str, Tuple[str, ...]]) -> Rule:
    """匹配消息命令，命令与参数之间需要空格

    根据配置里提供的 {ref}``command_start` <nonebot.config.Config.command_start>`,
    {ref}``command_sep` <nonebot.config.Config.command_sep>` 判断消息是否为命令。

    可以通过 {ref}`nonebot.params.Command` 获取匹配成功的命令（例: `("test",)`），
    通过 {ref}`nonebot.params.RawCommand` 获取匹配成功的原始命令文本（例: `"/test"`），
    通过 {ref}`nonebot.params.CommandArg` 获取匹配成功的命令参数。

    参数:
        cmds: 命令文本或命令元组

    用法:
        使用默认 `command_start`, `command_sep` 配置

        命令 `("test",)` 可以匹配: `/test` 开头的消息
        命令 `("test", "sub")` 可以匹配: `/test.sub` 开头的消息

    :::tip 提示
    命令内容与后续消息间无需空格!
    :::
    """

    config = get_driver().config
    command_start = config.command_start
    command_sep = config.command_sep
    commands: List[Tuple[str, ...]] = []
    for command in cmds:
        if isinstance(command, str):
            command = (command,)

        commands.append(command)

        if len(command) == 1:
            for start in command_start:
                TrieRule.add_prefix(f"{start}{command[0]} ", TRIE_VALUE(start, command))
        else:
            for start, sep in product(command_start, command_sep):
                TrieRule.add_prefix(
                    f"{start}{sep.join(command)} ", TRIE_VALUE(start, command)
                )

    return Rule(SpaceCommandRule(all_default, commands))
