from typing import Protocol, Iterator, Any, Iterable
import hashlib
import json
from jsonpath_ng import parse
from dataclasses import dataclass
from dataclasses import Field


# --- 1. 数据模型 (Model) ---
@dataclass
class Item:
    """标准数据传输对象。所有来源的数据最终都要转换为此格式。"""

    job_id: str  # 原始数据的工作id，如果没有则手动使用uuid生成
    company_name: str | None = None  # 公司名字
    source_platform: str | None = None  # 信息来源平台，如快手官方、boss等等
    work_type: str | None = None  # 工作种类，如 "trainee", "social", "campus"
    job_url: str | None = None
    title: str | None = None  # 工作的名称
    city: list[str] | None = None  # 工作的城市
    category: str | None = (
        None  # 工作分类， 如"工程类","算法类","产品类","运营类","设计类","分析类"
    )
    experience_req: str | None = None  # 工作的经验要求
    education_req: str | None = None  # 工作的学历要求, 如大专，本科，硕士
    job_level: str | None = None  # 工作职级
    salary_min: float | None = None  # 最低工资
    salary_max: float | None = None  # 最高工资
    description: str | None = None  # 工作描述
    description_keywords: list[str] | None = None  # 工作描述关键字
    requirement: str | None = None  # 工作要求
    requirement_keywords: list[str] | None = None  # 工作要求的关键字
    publish_date: int | None = None  # 保存为时间戳
    crawl_date: int | None = None  # 保存为时间戳
    extra_info: dict | None = None  # 保存一些额外的信息

    @staticmethod
    def get_jsonpath_value(data, jsonpath_expr):
        """
        使用 jsonpath-ng 从数据中提取值
        """
        try:
            # 解析 JSONPath 表达式
            jsonpath_expression = parse(jsonpath_expr)

            # 在数据中查找匹配项
            match = jsonpath_expression.find(data)

            # 如果找到了匹配项
            if match:
                # match 是一个列表，通常我们要取第一个匹配到的值
                # 如果路径指向一个具体的值（如int, str），value就是那个值
                # 如果路径指向一个数组（如 workLocationsCode），value就是那个列表
                return match[0].value
            else:
                return None
        except Exception as e:
            print(f"Error parsing {jsonpath_expr}: {e}")
            return None

    @staticmethod
    def _process_schema(schema, source_data):
        """
        递归遍历映射表，如果遇到以 $ 开头的字符串，则使用 jsonpath 提取
        Internal helper for recursive extraction.
        """
        if isinstance(schema, dict):
            # 如果是字典，递归处理每一个 key
            return {k: Item._process_schema(v, source_data) for k, v in schema.items()}

        elif isinstance(schema, list):
            # 如果是列表，递归处理列表中的每一项
            return [Item._process_schema(item, source_data) for item in schema]

        elif isinstance(schema, str) and schema.startswith("$"):
            # 核心逻辑：如果是 JSONPath 字符串，调用提取函数
            return Item.get_jsonpath_value(source_data, schema)

        else:
            # 其他情况（固定值、null、数字等），直接返回原值
            return schema

    @classmethod
    def transform_with_jsonpath(cls, schema, source_data) -> "Item":
        """
        根据 schema 从 source_data 中提取数据并转化为 Item 对象
        """
        data = cls._process_schema(schema, source_data)
        if not isinstance(data, dict):
            raise ValueError(
                "The root schema must result in a dictionary to create an Item."
            )
        return cls(**data)

    def get_fingerprint(self) -> str:
        return str(self.job_id)
