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
from urllib.parse import unquote

cookies = None


def search_xiaomi_positions(
    page_index=1,
    page_size=10,
):
    """
    使用构造好的 Session 对象发送请求
    """
    url = "https://xiaomi.jobs.f.mioffice.cn/api/v1/search/job/posts"
    params = {
        "keyword": "",
        "limit": page_size,
        "offset": page_size * (page_index - 1),
        "job_category_id_list": "",
        "tag_id_list": "",
        "location_code_list": "",
        "subject_id_list": "",
        "recruitment_id_list": "",
        "portal_type": "6",
        "job_function_id_list": "",
        "storefront_id_list": "",
        "portal_entrance": "1",
    }
    # 请求头
    headers = {
        "accept": "application/json, text/plain, */*",
        "accept-language": "zh-CN",
        "content-type": "application/json",
        "env": "undefined",
        "origin": "https://xiaomi.jobs.f.mioffice.cn",
        "portal-channel": "saas-career",
        "portal-platform": "pc",
        "priority": "u=1, i",
        "referer": "https://xiaomi.jobs.f.mioffice.cn/index",
        "sec-ch-ua": '"Not(A:Brand";v="8", "Chromium";v="144", "Google Chrome";v="144"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36",
        "website-path": "internship",
        "x-csrf-token": unquote(cookies["atsx-csrf-token"]),
    }
    data = {
        "keyword": "",
        "limit": page_size,
        "offset": page_size * (page_index - 1),
        "job_category_id_list": [],
        "tag_id_list": [],
        "location_code_list": [],
        "subject_id_list": [],
        "recruitment_id_list": [],
        "portal_type": 6,
        "job_function_id_list": [],
        "storefront_id_list": [],
        "portal_entrance": 1,
    }

    # 6. 发起 POST 请求
    try:
        response = requests.post(
            url, params=params, headers=headers, cookies=cookies, json=data
        )

        if response.status_code == 200:
            return response.json()["data"]["job_post_list"]

    except Exception as e:
        print(f"请求发生错误: {e}")


@dataclass
class WebXiaomiInternshipSource:
    web_page: WebPage
    start_page: int = 1

    def __post_init__(self):
        self._skip_count = 0

    def skip_pages(self, n: int):
        self._skip_count += n

    def fetch_items(self) -> Iterator[Item]:
        global cookies
        table = self.web_page.new_tab()
        table.get("https://xiaomi.jobs.f.mioffice.cn/internship/")
        cookies = {x["name"]: x["value"] for x in table.cookies()}
        i = self.start_page
        while True:
            print(f"开始抓取小米第 {i} 页数据...")
            res_list = search_xiaomi_positions(
                page_index=i,
            )

            if not res_list:
                print("未能获取到职位数据，可能是反爬风控或参数错误。")
                break
            if res_list == None or len(res_list) == 0:
                break
            for item in res_list:
                t = Item(
                    job_id=str(item.get("id", uuid.uuid4())),
                    company_name="小米",
                    source_platform="小米官网",
                    work_type="实习",
                    job_url=f"https://xiaomi.jobs.f.mioffice.cn/internship/position/{item.get('id', uuid.uuid4())}/detail",
                    title=item.get("title", ""),
                    city=item.get("city_list", ""),
                    category=item.get("job_function", {}).get("name", "未知"),
                    description=item.get("description", ""),
                    requirement=item.get("requirement", ""),
                    publish_date=int(item.get("publish_time", time.time() * 1000))
                    // 1000,
                    crawl_date=int(time.time()),
                )
                # 访存需求动态变化，难以确定，需要构建访存特征
                if isinstance(t.city, str):
                    t.city = [t.city]
                elif not t.city:
                    t.city = []
                else:
                    t.city = [x["name"] for x in t.city]
                h = t
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
            filters["source_platform"] = "小米官网"
        return data_storage.fetch_all_fingerprints(filters)
