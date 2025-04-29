# strategy_trade
策略交易

## 项目概述
`strategy_trade` 是一个基于 Python 开发的股票策略交易项目，旨在通过自动化的方式获取股票市场数据，并根据预设的策略进行股票交易操作。项目整合了东方财富的股票数据接口，实现了股票数据的获取、缓存管理以及交易操作等功能。

## 项目结构
```plaintext
.gitignore
README.md
app/
  core/
    log_config.py       # 日志配置文件，支持文件和控制台日志输出，并带有颜色标记
    stock_cache.py      # 股票数据缓存类，用于管理昨日涨停股票池、持仓和余额信息的内存缓存
    stock_service.py    # 股票服务类，负责与东方财富 API 交互，获取各种股票数据
    trade_service.py    # 交易服务类，负责与交易接口交互，实现账户余额查询、持仓查询和股票买入等操作
  first_board.py        # 首板策略执行文件，根据股票数据筛选符合条件的股票并执行买入操作
  quant_program.py      # 量化交易程序，使用 APScheduler 调度任务，定时更新缓存和执行交易策略
  test_log.py           # 日志测试文件，用于验证日志配置是否正常工作
requirements.txt        # 项目依赖文件
```
