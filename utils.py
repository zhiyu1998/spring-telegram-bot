import os
import logging

from dotenv import load_dotenv


class CustomFileHandler(logging.FileHandler):
    """
        自定义logging处理
    """

    def __init__(self, filename, mode='a', max_lines=100, encoding=None, delay=False):
        self.max_lines = max_lines
        self.log_lines = 0
        super().__init__(filename, mode, encoding, delay)

    def emit(self, record):
        # 每次写入前检查是否达到最大行数
        if self.log_lines >= self.max_lines:
            self.stream.close()
            self.stream = self._open()  # 重新打开文件，用 'w' 模式清空
            self.log_lines = 0  # 重置行数计数器
        super().emit(record)
        self.log_lines += 1


class EnvConfig:
    """
        单例日志
    """
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(EnvConfig, cls).__new__(cls)
            load_dotenv(verbose=True)
            dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
            load_dotenv(dotenv_path)
        return cls._instance

    @staticmethod
    def get_env():
        return os.environ
