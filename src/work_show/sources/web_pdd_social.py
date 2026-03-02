from DrissionPage import ChromiumPage, SessionPage, SessionOptions, WebPage
from DrissionPage._pages.mix_tab import MixTab
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
import requests
import uuid
from DrissionPage import ChromiumPage

outer_tab = None


def get_detail(job_id):
    if not outer_tab:
        return None, None
    outer_tab.get(f"https://careers.pddglobalhr.com/jobs/detail?code={job_id}")
    res = outer_tab.listen.wait().response.body["result"]
    return res.get("jobDuty", None), res.get("serveRequirement", None)


@dataclass
class WebPDDSocialSource:
    web_page: WebPage
    start_page: int = 1

    def __post_init__(self):
        self._skip_count = 0

    def skip_pages(self, n: int):
        self._skip_count += n

    def fetch_items(self) -> Iterator[Item]:
        global outer_tab
        table = self.web_page.new_tab()
        outer_tab = self.web_page.new_tab()
        outer_tab.listen.start("api/recruit/position/detail")
        table.listen.start("api/recruit/position/list")
        table.get("https://careers.pddglobalhr.com/jobs")
        i = self.start_page
        while True:
            print(f"开始抓取pdd第 {i} 页数据...")
            res = table.listen.wait()
            if isinstance(res, list):
                res = res[-1]
            res_list = res.response.body["result"].get("list", [])

            if not res_list:
                print("未能获取到职位数据，可能是反爬风控或参数错误。")
                break
            if res_list == None or len(res_list) == 0:
                break
            for item in res_list:
                t = Item(
                    job_id=str(item.get("code", uuid.uuid4())),
                    company_name="拼多多",
                    source_platform="拼多多官网",
                    work_type="社招",
                    job_url=f"https://careers.pddglobalhr.com/jobs/detail?code={item.get('code', uuid.uuid4())}",
                    title=item.get("name", ""),
                    city=item.get("workLocation", ""),
                    category=item.get("job", ""),
                    description="",
                    requirement="",
                    publish_date=int(item.get("updateDate", time.time() * 1000))
                    // 1000,
                    crawl_date=int(time.time()),
                )
                # 访存需求动态变化，难以确定，需要构建访存特征
                if isinstance(t.city, str):
                    t.city = [t.city]
                elif not t.city:
                    t.city = []
                h = t
                yield t
                i += self._skip_count
                while self._skip_count > 0:
                    if self._skip_count >= 5:
                        table(
                            'xpath://*[@id="__next"]/div/div[4]/div/div/div[2]/div[2]/div/div/ul/li[7]'
                        ).click()
                        self._skip_count -= 5
                    else:
                        table(
                            'xpath://*[@id="__next"]/div/div[4]/div/div/div[2]/div[2]/div/div/ul/li[9]/a'
                        ).click()
                        self._skip_count -= 1
                    time.sleep(1 + random.random() * 2)
            i += 1
            table(
                'xpath://*[@id="__next"]/div/div[4]/div/div/div[2]/div[2]/div/div/ul/li[9]/a'
            ).click()
            time.sleep(1 + random.random() * 2)
        return "没有任何数据了"

    def extract_by_llm(self, item: Item) -> Item:
        """用llm来提取一些信息，也可以看作是后处理"""
        item.description, item.requirement = get_detail(item.job_id)
        if item.description:
            (
                item.experience_req,
                item.education_req,
                item.description_keywords,
                item.requirement_keywords,
            ) = get_json_data(item.description, item.requirement)
            return item
        else:
            return None

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
            filters["source_platform"] = "拼多多官网"
        return data_storage.fetch_all_fingerprints(filters)
