import sqlite3
import json
import threading
from dataclasses import dataclass, field
from typing import Any, Tuple
from threading import Lock

from ..core.protocols import DataStorage
from ..core.models import Item
from ..utils.logger import get_logger

logger = get_logger(__name__)


# 一个虚拟的锁，什么也不做，用于单线程向后兼容
class DummyLock:
    def __enter__(self):
        pass

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass


@dataclass
class SqliteStorage(DataStorage):
    sqlite_path: str
    table_name: str
    lock: Lock = field(default_factory=DummyLock)

    def __post_init__(self):
        # 使用 threading.local() 来存储每个线程独立的数据库连接
        self._local = threading.local()
        
        # 初始化数据库设置：启用 WAL 模式以提高并发性能
        try:
            with sqlite3.connect(self.sqlite_path) as conn:
                conn.execute("PRAGMA journal_mode=WAL;")
                conn.execute("PRAGMA synchronous=NORMAL;")
        except Exception as e:
            logger.warning(f"Failed to enable WAL mode: {e}")

    def _get_conn(self) -> sqlite3.Connection:
        """
        获取当前线程的数据库连接。如果不存在则创建一个。
        """
        if not hasattr(self._local, "conn"):
            # check_same_thread=False 虽然在 thread_local 下不是严格必需，但保持灵活性
            self._local.conn = sqlite3.connect(self.sqlite_path, check_same_thread=False)
            # 设置忙等待超时，防止 'database is locked' 错误
            self._local.conn.execute("PRAGMA busy_timeout = 30000;")  # 30秒
        return self._local.conn

    def _adapt_item(self, item: Item) -> Tuple[Any, ...]:
        """
        将 Item 对象转换为适合 SQLite 插入的元组。
        复杂类型 (list, dict) 被序列化为 JSON 字符串。
        """
        return (
            item.job_id,
            item.company_name,
            item.source_platform,
            item.work_type,
            item.job_url,
            item.title,
            json.dumps(item.city, ensure_ascii=False),  # list -> json
            item.category,
            item.experience_req,
            item.education_req,
            item.job_level,
            item.salary_min,
            item.salary_max,
            item.description,
            json.dumps(item.description_keywords, ensure_ascii=False),  # list -> json
            item.requirement,
            json.dumps(item.requirement_keywords, ensure_ascii=False),  # list -> json
            item.publish_date,
            item.crawl_date,
        )

    def save(self, item: Item) -> None:
        # 写入操作仍然建议加锁，以在应用层序列化写入，减轻数据库层的竞争
        with self.lock:
            try:
                conn = self._get_conn()
                cursor = conn.cursor()
                # 21 个字段，对应 21 个占位符
                sql = f"""
                    INSERT INTO {self.table_name} (
                        job_id, company_name, source_platform, work_type, job_url,
                        title, city, category, experience_req,
                        education_req, job_level, salary_min, salary_max, description,
                        description_keywords, requirement, requirement_keywords, publish_date, crawl_date
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """
                cursor.execute(sql, self._adapt_item(item))
                conn.commit()
                cursor.close()
            except Exception as e:
                logger.error(
                    f"sqlite3 DB Save Error, sqlite path {self.sqlite_path}: \n{e}"
                )
                raise e

    def save_batch(self, items: list[Item]) -> None:
        if not items:
            return
        with self.lock:
            try:
                conn = self._get_conn()
                cursor = conn.cursor()
                sql = f"""
                    INSERT INTO {self.table_name} (
                        job_id, company_name, source_platform, work_type, job_url,
                        title, city, category, experience_req,
                        education_req, job_level, salary_min, salary_max, description,
                        description_keywords, requirement, requirement_keywords, publish_date, crawl_date
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """
                # 将所有 item 转换为元组列表
                data = [self._adapt_item(item) for item in items]
                cursor.executemany(sql, data)
                conn.commit()
                cursor.close()
            except Exception as e:
                logger.error(
                    f"sqlite3 DB Batch Save Error, sqlite path {self.sqlite_path}: \n{e}"
                )
                raise e

    def fetch_all_fingerprints(self, filters: dict[str, Any] | None = None) -> set[str]:
        # 读取操作在 WAL 模式下可以并发进行，无需加锁
        try:
            conn = self._get_conn()
            cursor = conn.cursor()
            sql = f"SELECT job_id FROM {self.table_name}"
            params = []
            if filters:
                where_clauses = []
                for key, value in filters.items():
                    where_clauses.append(f"{key} = ?")
                    params.append(value)
                sql += " WHERE " + " AND ".join(where_clauses)

            cursor.execute(sql, params)
            rows = cursor.fetchall()
            cursor.close()
            return set([row[0] for row in rows])
        except Exception as e:
            logger.error(f"Failed to fetch fingerprints: {e}")
            return set()

    def close(self) -> None:
        # 仅关闭当前线程的连接
        if hasattr(self._local, "conn"):
            self._local.conn.close()
            del self._local.conn