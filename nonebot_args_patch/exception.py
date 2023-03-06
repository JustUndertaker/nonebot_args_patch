from nonebot.exception import NoneBotException


class CommandArgException(NoneBotException):
    """命令参数匹配错误"""

    msg: str
    """返回消息"""

    def __init__(self, msg: str) -> None:
        self.msg = msg
