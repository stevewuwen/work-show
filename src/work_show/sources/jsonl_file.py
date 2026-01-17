from dataclasses import dataclass
from typing import Iterator
import pandas as pd
from ..core.protocols import DataStorage
from ..core.models import Item
import json
from typing import Any


@dataclass
class FileJsonlSource:
    """从jsonl里面读取数据"""

    jsonl_file_path: str
    _skip_count = 0

    def skip_pages(self, n) -> None:
        self._skip_count += n

    def fetch_items(self) -> Iterator[Item]:
        schema_dict = {
            "job_id": "$.id",
            "company_name": None,
            "source_platform": "$.channelCode",
            "job_url": None,
            "title": "$.name",
            "department": "$.departmentCode",
            "city": "$.workLocationCode",
            "category": "$.positionCategoryCode",
            "experience_req": "$.workExperienceCode",
            "education_req": "$.educationLimitCode",
            "job_level": "$.level",
            "salary_min": "$.salaryMin",
            "salary_max": "$.salaryMax",
            "description": "$.description",
            "requirement": "$.positionDemand",
            "publish_date": "$.updateTime",
            "crawl_date": None,
            "extra_info": {
                "applyNum": "$.applyNum",
                "entryNum": "$.entryNum",
                "recruitProjectCode": "$.recruitProjectCode",
                "positionNatureCode": "$.positionNatureCode",
                "ifSecret": "$.ifSecret",
                "headCountUsed": "$.headCountUsed",
                "workLocationsCode": "$.workLocationsCode",
            },
        }
        with open(self.jsonl_file_path, mode="r", encoding="utf-8") as f:
            for data_raw_str in f.readlines():
                if self._skip_count > 0:
                    self._skip_count -= 1
                    continue
                data_raw_dict = json.loads(data_raw_str)
                t = Item.transform_with_jsonpath(schema_dict, data_raw_dict)
                yield t

    def fetch_all_fingerprints(
        self, data_storage: DataStorage, filters: dict[str, Any] | None = None
    ) -> set:
        return data_storage.fetch_all_fingerprints(filters=filters)
