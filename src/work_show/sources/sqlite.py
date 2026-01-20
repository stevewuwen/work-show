"""这里是处理那些ai没能正常处理的数据"""

from typing import Protocol, Iterable
from ..core.models import Item
from dataclasses import dataclass


class SqliteSource(Protocol):
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
