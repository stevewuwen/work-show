from DrissionPage import ChromiumPage
from dataclasses import dataclass
from typing import Iterator
from ..core.models import Item
from ..utils.call_llm import get_json_data
import json
import time
import random
import os
from ..core.protocols import DataStorage
from typing import Any
from datetime import datetime
from rich import inspect


@dataclass
class WebTencentSocialSource:
    web_page: ChromiumPage
    start_page: int = 1

    def __post_init__(self):
        self._skip_count = 0

    def skip_pages(self, n: int):
        self._skip_count += n

    def fetch_items(self) -> Iterator[Item]:
        p = self.web_page.new_tab()
        p.listen.start("api/post/Query")
        i = self.start_page
        schema_dict = {
            "job_id": "$.PostId",
            "company_name": None,
            "source_platform": None,
            "job_url": "$.PostURL",
            "title": "$.RecruitPostName",
            "city": "$.LocationName",
            "category": "$.CategoryName",
            "experience_req": "$.RequireWorkYearsName",
            "education_req": None,
            "job_level": None,
            "salary_min": None,
            "salary_max": None,
            "description": "$.Responsibility",
            "requirement": None,
            "publish_date": "$.LastUpdateTime",
            "crawl_date": None,
        }
        i = 1
        while True:
            page_url = (
                f"https://careers.tencent.com/search.html?query=co_1&index={i}&sc=1"
            )
            p.get(page_url)
            res = p.listen.wait()
            res_list = res.response.body.get("Data")["Posts"]
            if res_list == None or len(res_list) == 0:
                break
            for item in res_list:
                t = Item.transform_with_jsonpath(schema_dict, item)
                t.source_platform = "腾讯官网"
                t.work_type = "社招"
                if t.crawl_date == None or t.crawl_date == "":
                    t.crawl_date = int(time.time())
                if t.company_name == None or t.company_name == "":
                    t.company_name = "腾讯"
                t.city = [t.city]
                t.publish_date = int(
                    datetime.strptime(t.publish_date, "%Y年%m月%d日").timestamp()
                )
                if not t.category:
                    t.category = "未知"
                t.job_id = str(t.job_id)
                yield t
                if self._skip_count > 0:
                    i += self._skip_count
                    self._skip_count = 0
                    break
            i += 1
            time.sleep(1 + random.random() * 2)
        return "没有任何数据了"

    def extract_by_llm(self, item: Item) -> Item:
        """用llm来提取一些信息，也可以看作是后处理"""
        (
            item.experience_req,
            item.education_req,
            item.description_keywords,
            _,
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
            filters["source_platform"] = "腾讯官网"
        return data_storage.fetch_all_fingerprints(filters)
