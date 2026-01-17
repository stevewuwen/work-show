from typing import Protocol, Iterator, Any, Iterable
from pydantic import BaseModel
import hashlib


# --- 1. 数据模型 (Model) ---
class Item(BaseModel):
    """标准数据传输对象。所有来源的数据最终都要转换为此格式。"""

    uid: str  # 唯一标识符 (用于去重)
    content: dict  # 实际数据内容
    source_type: str  # 数据来源类型 (便于调试)


# --- 2. 接口协议 (Protocols) ---


class DataSource(Protocol):
    """
    [单一职责]: 只负责从特定来源获取数据，并解析为 Item 对象。
    不关心去重，也不关心存储。
    """

    def fetch_items(self) -> Iterator[Item]:
        """生成器，逐个返回 Item 对象"""
        ...


class Deduplicator(Protocol):
    """
    [单一职责]: 只负责判断指纹是否已存在，并记录新指纹。
    """

    def is_seen(self, fingerprint: str) -> bool:
        """判断是否存在"""
        ...

    def add(self, fingerprint: str) -> None:
        """记录指纹"""
        ...


class DataStorage(Protocol):
    """
    [单一职责]: 只负责将 Item 持久化（如存入 SQL）。
    """

    def save(self, item: Item) -> None: ...

    def close(self) -> None:
        """关闭连接等资源清理"""
        ...
