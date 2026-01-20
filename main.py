import yaml
import importlib
import threading
from work_show.engine.crawler import CrawlerEngine
from work_show.storage.sql_storage import SqliteStorage
from work_show.utils.logger import get_logger

# 获取日志记录器
logger = get_logger("Main")

def main():
    """
    主函数：动态加载、配置并多线程运行爬虫。
    """
    # 1. 加载配置
    config = yaml.safe_load(open("config/settings.yaml", encoding='utf-8'))
    db_config = config["database"]
    crawler_config = config["crawler"]
    sources_config = config.get("sources", [])

    if not sources_config:
        logger.warning("No sources found in the configuration file. Exiting.")
        return

    # 2. 创建线程安全的存储实例和线程锁
    db_lock = threading.Lock()
    storage = SqliteStorage(
        sqlite_path=db_config["url"],
        table_name=db_config["table_name"],
        lock=db_lock,  # 传入锁
    )

    threads = []
    # 3. 遍历配置中的每个源，为其创建和启动一个线程
    for source_info in sources_config:
        try:
            # 动态导入模块
            module = importlib.import_module(source_info["module"])
            # 获取类
            SourceClass = getattr(module, source_info["class"])
            # 使用提供的参数实例化
            source_instance = SourceClass(**source_info.get("params", {}))

            # 为每个源创建一个独立的引擎
            engine = CrawlerEngine(
                source=source_instance, storage=storage, config=crawler_config
            )

            # 创建并启动线程
            thread = threading.Thread(target=engine.run, name=SourceClass.__name__)
            threads.append(thread)
            thread.start()
            logger.info(f"Started thread for source: {SourceClass.__name__}")

        except Exception as e:
            logger.error(
                f"Failed to start source {source_info.get('class', 'Unknown')}: {e}"
            )

    
    
    # 4. 等待所有线程完成
    for thread in threads:
        thread.join()

    logger.info("All crawling threads have finished.")


if __name__ == "__main__":
    main()
