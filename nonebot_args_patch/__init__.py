"""
commmand参数模块

模块需要打补丁
在bot.py的第一行写入：

import nonebot_args_patch.patch
"""

from .commandarg import AtRequire as AtRequire
from .commandarg import CommandGroup as CommandGroup
from .commandarg import Default as Default
from .commandarg import Require as Require
from .commandarg import get_args as get_args
from .commandarg import on_command as on_command
