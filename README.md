<h1 align="center">Nonebot-Args-Patch</h1>

<p align="center">
    <a href="https://github.com/JustUndertaker/adapter-ntchat/releases"><img src="https://img.shields.io/badge/release-0.2.0-blue.svg?" alt="release"></a>
    <a href="https://opensource.org/licenses/MIT"><img src="https://img.shields.io/badge/License-MIT-brightgreen.svg?" alt="License"></a>
</p>

## 简介

一款自用的nonebot2的参数处理器，主要用于处理nb2的命令参数，支持内容：

- 重写`on_command`：支持自定义数量的`必选`、`可选`、`at目标` 参数
- 支持`command_group`，方便管理
- 默认参数`Default()`支持默认值，可以为`Any`或者`Callable`，当为`Callable`时，可以使用nb2内置的`依赖注入`参数
- 所有参数都支持`help`信息，在参数检测错误时会返回指令帮助
- 在未检测到命令时，支持相似命令修正（这个需要占用一个`matcher`）

## 警告

本模块修改了nb2框架部分代码，所以需要在`bot.py`文件下打补丁补丁：

```python
# bot.py下需要加入以下代码
import nonebot_args_patch.patch
```

## 安装

使用pip进行安装

```bash
pip install nonebot_args_patch
```

## 构造matcher

需要使用补丁内的`on_command`或者`command_group`才能生效

```python
from nonebot_args_patch import on_command

matcher = on_command(cmd="xxx")
```

**注意**

`on_command`可以说是nb2内置的`on_command`加强版，依旧会使用nb2内置的`command_start`，默认为`/`；如果不想要命令前缀，需要修改`env`文件

```dotenv
# .env 或者 .env.xxx
command_start = [""]
```

### on_command

参数列表:

**nb2原来的**

* `cmd`: 指定命令内容
* `rule`: 事件响应规则
* `aliases`: 命令别名
* `permission`: 事件响应权限
* `handlers`: 事件处理函数列表
* `temp`: 是否为临时事件响应器（仅执行一次）
* `expire_time`: 事件响应器最终有效时间点，过时即被删除
* `priority`: 事件响应器优先级
* `block`: 是否阻止事件向更低优先级传递

**额外的参数**

* `need_space`，默认为`False` ：命令与参数之间是否需要空格

    * `True`：强制命令和参数直接需要加一个空格，比如

        ```python
        from nonebot_args_patch import on_command,Require
    
        matcher = on_command(cmd="测试",need_space=True,arg=Require())
    
        """
        > 测试 123
          可以触发,arg为123
    
        > 测试123
          不能触发
        """
        ```

* `need_help`，默认为`True`：是否需要相似命令检验

    * `True`：在未匹配到命令时，将额外触发一个`matcher`，用来检测相似的命令

        ```python
        from nonebot_args_patch import on_command,Require
        
        matcher = on_command(cmd="测试",need_help=True,arg=Require())
        
        """
        > a测试
          不能触发，但会返回一句msg提示：
        
          未知命令，你可能想要找：
          测试 arg
        """
        ```

- `**kwargs`：这里填写任意参数列表，参数必须是`Require`、`AtRequire`、`Default`

  ```py
  from nonebot_args_patch import on_command,Require,Default,AtRequire
  
  matcher = on_command(
  	cmd = "测试",
      arg1 = Require(),
      arg2 = Default(default="2"),
  )
  ```

### Require

使用此类表示这个参数是必须的。

参数:

- `help`，str：该参数在命令帮助时显示的内容，默认为`None`
  - `None`：在命令帮助时，会显示为参数变量名

```python
from nonebot_args_patch import on_command,Require

matcher = on_command(cmd="测试",arg=Require())

"""
> 测试
  不能触发，帮助信息为：

  失败，命令传入参数不足
  测试 arg
"""

matcher = on_command(cmd="测试",arg=Require(help="参数1"))

"""
> 测试
  不能触发，帮助信息为：

  失败，命令传入参数不足
  测试 参数1
"""
```

### Default

使用此类表示这个参数是可选的。

参数:

- `default`：可以是任意值，也可以是一个`Callable`

  - `Any`：在获取参数时，会将内容原样返回，需要注意`get_args`时的类型标注

  - `Callable`：将会执行该方法，同时方法也支持nb2的依赖注入

    ```python
    from nonebot_args_patch import on_command,Default
    from nonebot.params import Command
  
    matcher = on_command(cmd="测试",arg=Default(default="默认")) # 默认值构造
  
    """
    > 测试
      能触发，arg的值为'默认'
    """
  
    def get_default():
        return "默认"
  
    matcher = on_command(cmd="测试",arg=Default(default=get_default)) # 默认函数
  
    """
    > 测试
      能触发，arg的值为'默认'
    """
  
    def get_defaultarg(cmd:Message=Command()):
        return str(cmd)
  
    matcher = on_command(cmd="测试",arg=Default(default=get_default))	# 默认函数+依赖注入
  
    """
    > 测试
      能触发，arg的值为'测试'
    """
    ```

- `help`：该参数在命令帮助时显示的内容，默认为`None`

### AtRequire

使用此类表示这个参数是需要at目标的。

**注意**

- At需要adapter支持type为`at`的`MessageSegment`，比如`adapter-onebot`

- At不强调at的位置，但多个At会有先后顺序，同时在nb2中，如果开头at机器人，会被adapter将at干掉。

参数：

- 该参数在命令帮助时显示的内容，默认为`None`

## handler获取参数

### get_args

参数:

- `name`，str：你需要获取的参数名称，需要注意类型提示

```python
from nonebot_args_patch import on_command,Require,get_args

matcher = on_command(cmd="测试",arg1=Require())

@matcher.handle()
async def _(
arg:str = get_args("arg1")
):
    await matcher.finish(arg)

"""
> 测试 123
< 123
"""
```

**注意**

get_args也可用于子依赖

```python
from nonebot.params import Depends
from nonebot_args_patch import on_command,Require,get_args

def get_depend():
    def _get_depend(arg:str=get_args("arg1")):
        return arg
    return Depends(_get_depend)

matcher = on_command(cmd="测试",arg1=Require())

@matcher.handle()
async def _(
arg:str = get_depend()
):
    await matcher.finish(arg)

"""
> 测试 123
< 123
"""
```

## 命令帮助

在参数匹配失败时，会输出一条帮助信息，内容为：

`指令 [可选参数] 必选参数`

参数顺序与你定义`matcher`时一致，可选参数会加上`[]`

## 相似命令修正

在定义`matcher`，如果`need_help`为`True`，则会在未匹配到命令时尝试找到相似命令，使用的库为`difflib`。

- 该实现为`matcher`实现，priority为99
- 未找到相似命令时，event继续向下传播
- 如果找到了相似命令，将会输出提示并阻断event传播
