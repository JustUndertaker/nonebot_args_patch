from difflib import get_close_matches
from typing import Dict, List, Optional, Set

from pydantic import BaseModel


class OneArgHelp(BaseModel):
    name: str
    """提示内容"""
    optional: bool
    """是否可选"""

    def get_msg(self) -> str:
        """获取消息"""
        return f"[{self.name}]" if self.optional else self.name


class CommandHelp(BaseModel):
    """命令提示信息"""

    command: Set[str]
    """指令名"""
    need_help: bool
    """是否需要相似度检验"""
    args_help: List[OneArgHelp]
    """参数列表"""

    def get_help_msg(self) -> str:
        """获取指令提示消息"""
        arg_help = " ".join(one_arg.get_msg() for one_arg in self.args_help)
        command = "/".join(self.command)
        return f"{command} {arg_help}"


class CommandHelper:
    """命令帮助"""

    command_dict: Dict[str, CommandHelp] = {}
    """命令字典"""

    @classmethod
    def add_command(cls, names: Set[str], command: CommandHelp) -> None:
        """
        说明:
            添加一条指令
        """
        for name in names:
            if name in cls.command_dict:
                raise KeyError("注册了相同指令，引发冲突")
            cls.command_dict[name] = command

    @classmethod
    def get_similar_commands(cls, name: str) -> Optional[CommandHelp]:
        """获取相似的命令"""
        close_commands = get_close_matches(name, cls.command_dict.keys())
        if close_commands:
            return cls.command_dict[close_commands[0]]
        else:
            return None
