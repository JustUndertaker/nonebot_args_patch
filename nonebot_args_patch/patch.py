"""
猴子补丁，需要在bot.py的第一行写入：

import nonebot_args_patch.patch
"""
import shlex
from contextlib import AsyncExitStack
from typing import Optional

from nonebot import Bot
from nonebot.consts import PREFIX_KEY, RAW_CMD_KEY
from nonebot.exception import SkippedException, StopPropagation
from nonebot.internal.adapter import Event
from nonebot.internal.matcher import Matcher, current_handler
from nonebot.log import logger
from nonebot.typing import T_DependencyCache, T_State

from .commandarg import Args
from .consts import ARGS, ARGSTYPE, PRIORITY
from .exception import CommandArgException
from .helper import CommandHelper


async def simple_run(
    self: Matcher,
    bot: Bot,
    event: Event,
    state: T_State,
    stack: Optional[AsyncExitStack] = None,
    dependency_cache: Optional[T_DependencyCache] = None,
):
    logger.trace(
        f"{self} run with incoming args: "
        f"bot={bot}, event={event!r}, state={state!r}"
    )

    with self.ensure_context(bot, event):
        try:
            # Refresh preprocess state
            self.state.update(state)
            if arg_type := self.state.get(ARGSTYPE):
                arg: Args = arg_type()
                try:
                    await arg.match(bot=bot, event=event, matcher=self)
                except CommandArgException as e:
                    command: str = self.state[PREFIX_KEY][RAW_CMD_KEY]
                    if help := CommandHelper.get_similar_commands(command):
                        msg = f"出错，{e.msg}：\n{help.get_help_msg()}"
                        self.stop_propagation()
                        await self.send(msg)
                    return
                self.state[ARGS] = arg
            while self.handlers:
                handler = self.handlers.pop(0)
                current_handler.set(handler)
                logger.debug(f"Running handler {handler}")
                try:
                    await handler(
                        matcher=self,
                        bot=bot,
                        event=event,
                        state=self.state,
                        stack=stack,
                        dependency_cache=dependency_cache,
                    )
                except SkippedException:
                    logger.debug(f"Handler {handler} skipped")
        except StopPropagation:
            self.block = True
        finally:
            logger.info(f"{self} running complete")


async def help_handle(matcher: Matcher, event: Event) -> None:
    """帮助指令处理"""
    msg = event.get_message()
    text = msg.extract_plain_text()
    args_list = shlex.split(text)
    if len(args_list) == 0:
        await matcher.finish()
    command = args_list[0]
    if help := CommandHelper.get_similar_commands(command):
        if help.need_help:
            msg = f"未知命令，你可能想要找：\n{help.get_help_msg()}"
            matcher.stop_propagation()
            await matcher.finish(msg)


Matcher.new(type_="message", priority=PRIORITY, handlers=[help_handle])

Matcher.simple_run = simple_run
