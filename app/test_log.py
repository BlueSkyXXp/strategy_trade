from core.log_config import setup_logger

# 设置日志记录器
logger = setup_logger(__name__)

def test_logging():
    # 测试不同级别的日志记录
    logger.debug('这是一条调试级别的日志')
    logger.info('这是一条信息级别的日志')
    logger.warning('这是一条警告级别的日志')
    logger.error('这是一条错误级别的日志')
    logger.critical('这是一条严重错误级别的日志')

if __name__ == "__main__":
    test_logging()