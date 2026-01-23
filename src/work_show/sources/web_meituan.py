from DrissionPage import WebPage
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
class WebMeiTuanSource:
    web_page: WebPage
    start_page: int = 1

    def __post_init__(self):
        self._skip_count = 0

    def skip_pages(self, n: int):
        self._skip_count += n

    def fetch_items(self) -> Iterator[Item]:
        p = self.web_page.new_tab()
        p.listen.start("api/official/job/getJobList")
        i = self.start_page
        schema_dict = {
            "job_id": "$.jobUnionId",
            "company_name": None,
            "source_platform": None,
            "work_type": "$.jobType",
            "job_url": None,
            "title": "$.name",
            "city": "$.cityList",
            "category": "$.jobFamilyGroup",
            "experience_req": None,
            "education_req": None,
            "job_level": None,
            "salary_min": None,
            "salary_max": None,
            "description": "$.jobDuty",
            "requirement": "$.highLight",
            "publish_date": "$.refreshTime",
            "crawl_date": None,
            "extra_info": {
                "requirement": "$.jobRequirement",
            },
        }
        work_types = ["social", "campus"]
        while True:
            if self._skip_count > 0:
                i += self._skip_count
                self._skip_count = 0
            for work_type in work_types:
                # TODO 招聘字节的社招 https://jobs.bytedance.com/experienced/position
                p.get(f"https://zhaopin.meituan.com/web/{work_type}?pageNo={i}")
                # p.get(
                #     f"https://zhaopin.meituan.com/web/position?hiringType=1_1,1_3,1_4&pageNo=2"
                # )
                res = p.listen.wait()
                res_list = res.response.body.get("data")["list"]
                for item in res_list:
                    t = Item.transform_with_jsonpath(schema_dict, item)
                    t.source_platform = "美团官网"
                    t.company_name = "美团"
                    if t.job_url == None or t.job_url == "":
                        # https://zhaopin.meituan.com/web/position/detail?jobUnionId=2992997195
                        t.job_url = f"https://zhaopin.meituan.com/web/position/detail?jobUnionId={t.job_id}"
                    t.crawl_date = int(time.time())
                    if isinstance(t.city, list):
                        t.city = [x["name"] for x in t.city]
                    else:
                        t.city = [t.city]
                    try:
                        t.publish_date = t.publish_date // 1000
                    except Exception as e:
                        pass
                    if t.requirement is None or t.requirement == "":
                        if (
                            t.extra_info.get("requirement", "") is not None
                            and t.extra_info.get("requirement", "") != ""
                        ):
                            t.requirement = t.extra_info.get("requirement", "")
                    if t.work_type == "3":
                        t.work_type = "社招"
                    elif t.work_type == "2":
                        t.work_type = "实习"
                    else:
                        t.work_type = "校招"
                    t.job_id = str(t.job_id)
                    yield t
                    if self._skip_count > 0:
                        i += self._skip_count
                        self._skip_count = 0
                        break
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
            filters["source_platform"] = "美团官网"
        return data_storage.fetch_all_fingerprints(filters)
