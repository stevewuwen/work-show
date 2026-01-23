import sqlite3
import json
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
        self.conn = sqlite3.connect(self.sqlite_path, check_same_thread=False)
        self.cursor = self.conn.cursor()

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
        with self.lock:
            try:
                # 21 个字段，对应 21 个占位符
                sql = f"""
                    INSERT INTO {self.table_name} (
                        job_id, company_name, source_platform, work_type, job_url,
                        title, city, category, experience_req,
                        education_req, job_level, salary_min, salary_max, description,
                        description_keywords, requirement, requirement_keywords, publish_date, crawl_date
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """
                self.cursor.execute(sql, self._adapt_item(item))
                self.conn.commit()
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
                self.cursor.executemany(sql, data)
                self.conn.commit()
            except Exception as e:
                logger.error(
                    f"sqlite3 DB Batch Save Error, sqlite path {self.sqlite_path}: \n{e}"
                )
                raise e

    def fetch_all_fingerprints(self, filters: dict[str, Any] | None = None) -> set[str]:
        try:
            sql = f"SELECT job_id FROM {self.table_name}"
            params = []
            if filters:
                where_clauses = []
                for key, value in filters.items():
                    where_clauses.append(f"{key} = ?")
                    params.append(value)
                sql += " WHERE " + " AND ".join(where_clauses)

            self.cursor.execute(sql, params)
            rows = self.cursor.fetchall()
            return set([row[0] for row in rows])
        except Exception as e:
            logger.error(f"Failed to fetch fingerprints: {e}")
            return set()

    def close(self) -> None:
        self.conn.close()
