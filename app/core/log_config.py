import logging
from logging.handlers import TimedRotatingFileHandler
import os
from datetime import datetime

class ColorizedFileFormatter(logging.Formatter):
    def format(self, record):
        if record.levelno == logging.ERROR:
            return f"\033[41;37m{super().format(record)}\033[0m"  # 终端颜色标记
        return super().format(record)

def setup_logger(name):
    logger = logging.getLogger(name)
    if logger.handlers:  # 避免重复添加处理器
        logger.handlers = []
    logger.setLevel(logging.DEBUG)

    # 改为使用当前工作目录（沙盒环境更友好）
    log_dir = os.path.join(os.getcwd(), "log")  # 当前目录下的log文件夹
    log_dir = os.path.abspath(log_dir)  # 转换为绝对路径

    try:
        if not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)  # 安全创建目录
        if not os.access(log_dir, os.W_OK):
            raise PermissionError(f"无写入权限: {log_dir}")
    except Exception as e:
        print(f"日志目录创建失败: {e}")
        return None

    current_date = datetime.now().strftime('%Y%m%d')
    log_file = os.path.join(log_dir, f'trading_log_{current_date}.log')

    # 文件处理器（按天分割，保留30天日志）
    file_handler = TimedRotatingFileHandler(
        log_file,
        when='D',
        interval=1,
        backupCount=30,
        encoding='utf-8'
    )
    file_handler.setLevel(logging.INFO)
    file_formatter = ColorizedFileFormatter(
        '%(asctime)s - %(levelname)s - %(module)s:%(lineno)d - %(message)s'
    )
    file_handler.setFormatter(file_formatter)

    # 控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)
    console_formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s'
    )
    console_handler.setFormatter(console_formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger

if __name__ == "__main__":
    logger = setup_logger(__name__)
    if not logger:
        print("日志初始化失败")
        exit(1)
    
    # 测试日志输出
    logger.debug('调试日志（控制台可见）')
    logger.info('信息日志（文件和控制台可见）')
    logger.warning('警告日志（文件和控制台可见）')
    logger.error('错误日志（文件和控制台可见，带颜色）')
    logger.critical('严重错误日志（文件和控制台可见，带颜色）')
