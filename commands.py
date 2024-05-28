import os
import importlib
from functools import wraps
from pathlib import Path

from event import Event

# 用于存储命令名和对应的处理函数
command_registry = {}
# 增加一个新的字典来注册正则表达式处理器
regex_registry = {}

def command_handler(command):
    """
        command装饰器
    :param command: 匹配命令
    :return:
    """

    def decorator(func):
        @wraps(func)
        def wrapped(*args, **kwargs):
            e = Event(*args, **kwargs)
            return func(e)

        command_registry[command] = wrapped
        return wrapped

    return decorator


def regex_handler(pattern):
    """
        MessageHandler(filters.Regex)正则装饰器
    :param pattern: 正则表达式
    :return:
    """
    def decorator(func):
        @wraps(func)
        def wrapped(*args, **kwargs):
            e = Event(*args, **kwargs)
            return func(e)
        regex_registry[pattern] = wrapped
        return wrapped

    return decorator

def load_plugins():
    """
    加载plugins/下所有插件
    :return:
    """
    plugins_dir = Path(__file__).parent / "plugins"
    for root, dirs, files in os.walk(plugins_dir):
        for file in files:
            if file == '__init__.py':
                # 构建模块路径
                module_path = os.path.relpath(root, Path(__file__).parent).replace(os.sep, ".")
                importlib.import_module(module_path)
