import sys
import os
# 将项目根目录添加到 sys.path 中
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import time
import logging
from logging.handlers import TimedRotatingFileHandler
from datetime import datetime
import app.first_board as first_board
# 导入缓存类
from app.core.stock_cache import StockCache
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import app.core.stock_service as stock_service
from app.core.log_config import setup_logger


# 配置日志
logger = setup_logger(__name__)
logger.setLevel(logging.INFO)

# 创建 log 目录（如果不存在）
log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'log')
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

# 获取当前日期
current_date = datetime.now().strftime('%Y%m%d')
log_file_name = os.path.join(log_dir, f'trading_log_{current_date}.log')

log_handler = TimedRotatingFileHandler(log_file_name, when='midnight', interval=1, backupCount=0)
log_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
log_handler.setFormatter(log_formatter)
logger.addHandler(log_handler)

# 创建缓存类实例
cache_manager = StockCache()
# cache_manager.update_cache()

stock_api = stock_service.StockService()

scheduler = BackgroundScheduler()


# 仅在工作日 9:15 获取昨日涨停股票池
# 修改为不传入 misfire_grace_time 参数
scheduler.add_job(cache_manager.update_cache, CronTrigger(day_of_week='mon-fri', hour=9, minute=15))

# 定义添加间隔任务的函数
def add_interval_job():
    # 修改 args 参数，确保传递的是一个元组
    scheduler.add_job(first_board.run_job, 'interval', seconds=10, args=(cache_manager,))


# 仅在工作日 9:30 和 13:00 添加间隔任务
scheduler.add_job(add_interval_job, CronTrigger(day_of_week='mon-fri', hour=9, minute=30))
scheduler.add_job(add_interval_job, CronTrigger(day_of_week='mon-fri', hour=13, minute=0))
# scheduler.add_job(add_interval_job, CronTrigger(day_of_week='mon-fri', hour=10, minute=0))

# 仅在工作日 11:30 和 15:00 移除间隔任务
def remove_interval_jobs():
    from apscheduler.triggers.interval import IntervalTrigger
    for job in scheduler.get_jobs():
        if isinstance(job.trigger, IntervalTrigger):
            job.remove()

# 仅在工作日 11:30 和 15:00 移除间隔任务
scheduler.add_job(remove_interval_jobs, CronTrigger(day_of_week='mon-fri', hour=11, minute=30))
scheduler.add_job(remove_interval_jobs, CronTrigger(day_of_week='mon-fri', hour=15, minute=0))

cache_manager.update_cache()

scheduler.start()

try:
    while True:
        time.sleep(1)
except (KeyboardInterrupt, SystemExit):
    scheduler.shutdown()


