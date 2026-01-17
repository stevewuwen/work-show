from typing import Protocol, Iterator, Any, Iterable
from enum import Enum, auto
from dataclasses import dataclass
from pydantic import BaseModel
import hashlib

from .models import Item


class DedupAction(Enum):
    SAVE = auto()
    SKIP = auto()
    STOP = auto()
    SKIP_PAGES = auto()
    UPDATE = auto()


@dataclass
class DedupResponse:
    action: DedupAction
    args: Any = None


class DataStorage(Protocol):
    """
    只负责将 Item 持久化（如存入 SQL）。
    """

    def save(self, item: Item) -> None: ...

    def close(self) -> None:
        """关闭连接等资源清理"""
        ...

    def fetch_all_fingerprints(self, filters: dict[str, Any] | None = None) -> set:
        """从数据库中根据属性筛选并获取所有已存在的指纹"""
        ...


class DataSource(Protocol):
    """
    只负责从特定来源获取数据，并解析为 Item 对象。不关心去重，也不关心存储。
    """

    def fetch_items(self) -> Iterator[Item]:
        """生成器，逐个返回原始的被解析为dict的json对象"""
        ...

    def skip_pages(self, n: int) -> None:
        """重复后用于多跳过几页的"""
        ...

    def fetch_all_fingerprints(
        self, data_storage: DataStorage, filters: dict[str, Any] | None = None
    ) -> set:
        """从数据库中根据属性筛选并获取所有已存在的指纹"""
        ...

    def extract_by_llm(self, item: Item) -> Item:
        """将返回的json dict数据转化为一个Item对象"""
        ...


class Deduplicator(Protocol):
    def check_status(self, item: Item) -> DedupResponse:
        """检查Item状态，决定如何处理"""
        ...

    def merge_set(self, st: set) -> None:
        """合并重复的item"""
