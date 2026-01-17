from DrissionPage import WebPage
import pandas as pd
from dataclasses import dataclass
from typing import Iterator
from ..core.models import Item
from ..utils.call_llm import get_json_data
import json
import time
import random
from rich import inspect
import os
from ..core.protocols import DataStorage
from typing import Any
from datetime import datetime


@dataclass
class WebByteDanceCampusSource:
    start_page: int = 1

    def __post_init__(self):
        self._skip_count = 0

    def skip_pages(self, n: int):
        self._skip_count += n

    def fetch_items(self) -> Iterator[Item]:
        p = WebPage()
        p.listen.start("api/v1/search/job/posts")
        i = self.start_page
        schema_dict = {
            "job_id": "$.id",
            "company_name": None,
            "source_platform": None,
            "work_type": "$.recruit_type.name",
            "job_url": None,
            "title": "$.title",
            "department": None,
            "city": "$.city_info.name",
            "category": "$.job_category.name",
            "experience_req": "$.job_post_info.experience",
            "education_req": "$.job_post_info.education",
            "job_level": None,
            "salary_min": None,
            "salary_max": None,
            "description": "$.description",
            "requirement": "$.requirement",
            "publish_date": "$.publish_time",
            "crawl_date": None,
            "extra_info": {
                "work_type": "$.recruit_type.parent.name",
                "city_info": "$.city_info",
                "job_subject": "$.job_subject",
                "city_list": "$.city_list",
            },
        }

        while True:
            if self._skip_count > 0:
                i += self._skip_count
                self._skip_count = 0

            p.get(
                f"https://jobs.bytedance.com/campus/position?keywords=&category=&location=&project=&type=&job_hot_flag=&current={i}&limit=100&functionCategory=&tag="
            )
            res = p.listen.wait()
            res_list = res.response.body.get("data")["job_post_list"]
            for item in res_list:
                t = Item.transform_with_jsonpath(schema_dict, item)
                t.source_platform = "字节官网"
                t.company_name = "字节跳动"
                if t.job_url == None or t.job_url == "":
                    t.job_url = (
                        f"https://jobs.bytedance.com/campus/position/{t.job_id}/detail"
                    )
                t.crawl_date = int(time.time())
                if t.extra_info and "city_list" in t.extra_info:
                    t.city = [x["name"] for x in t.extra_info["city_list"]]
                else:
                    t.city = [t.city]
                try:
                    t.publish_date = t.publish_date // 1000
                except Exception as e:
                    pass
                t.work_type = "校招" if t.work_type == "正式" else "实习"
                t.job_id = str(t.job_id)
                yield t
            i += 1
            time.sleep(1 + random.random() * 20)
        return "没有任何数据了"

    def extract_by_llm(self, item: Item) -> Item:
        """用llm来提取一些信息，也可以看作是后处理"""
        (
            item.experience_req,
            item.education_req,
            item.description_keywords,
            item.requirement_keywords,
        ) = get_json_data(item.description, item.requirement)
        return item

    def fetch_all_fingerprints(
        self, data_storage: DataStorage, filters: dict[str, Any] | None = None
    ) -> set:
        """从数据库中根据属性筛选并获取所有已存在的指纹"""
        if filters == None:
            filters = {}
        if (
            "source_platform" not in filters
            or filters["source_platform"] == None
            or filters["source_platform"] == ""
        ):
            filters["source_platform"] = "字节官网"
        return data_storage.fetch_all_fingerprints(filters)
