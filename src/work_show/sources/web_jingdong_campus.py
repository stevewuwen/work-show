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

cookies = None


def search_jingdong_positions(
    page_index=1,
    page_size=10,
):
    """
    使用构造好的 Session 对象发送请求
    """
    url = "https://campus.jd.com/api/wx/position/page?type=present"

    # 请求头
    headers = {
        "accept": "*/*",
        "accept-language": "zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7,zh-TW;q=0.6,zh-HK;q=0.5",
        "content-type": "application/json; charset=UTF-8",
        "origin": "https://campus.jd.com",
        "referer": "https://campus.jd.com/home",
        "sec-ch-ua": '"Not(A:Brand";v="8", "Chromium";v="144", "Google Chrome";v="144"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36",
        "x-requested-with": "XMLHttpRequest",
    }
    payload = {
        "pageSize": page_size,
        "pageIndex": page_index - 1,
        "parameter": {
            "positionName": "",
            "planIdList": [],
            "jobDirectionCodeList": [],
            "workCityCodeList": [],
            "positionDeptList": [],
        },
    }

    # 6. 发起 POST 请求
    try:
        response = requests.post(
            url, headers=headers, cookies=cookies, json=payload, timeout=10
        )

        if response.status_code == 200:
            return response.json()["body"]["items"]

    except Exception as e:
        print(f"请求发生错误: {e}")


@dataclass
class WebJingdongCampusSource:
    web_page: WebPage
    start_page: int = 1

    def __post_init__(self):
        self._skip_count = 0

    def skip_pages(self, n: int):
        self._skip_count += n

    def fetch_items(self) -> Iterator[Item]:
        global cookies
        table = self.web_page.new_tab()
        table.get("https://campus.jd.com/home#/jobs")
        cookies = {x["name"]: x["value"] for x in table.cookies()}
        i = self.start_page
        while True:
            print(f"开始抓取京东第 {i} 页数据...")
            res_list = search_jingdong_positions(
                page_index=i,
            )

            if not res_list:
                print("未能获取到职位数据，可能是反爬风控或参数错误。")
                break
            if res_list == None or len(res_list) == 0:
                break
            for item in res_list:
                t = Item(
                    job_id=str(item.get("publishId", uuid.uuid4())),
                    company_name="京东",
                    source_platform="京东官网",
                    work_type=item.get("jobCategory", ""),
                    job_url=f"https://campus.jd.com/#/details?id={item.get('publishId', uuid.uuid4())}",
                    title=item.get("positionName", ""),
                    city=item.get("requirementVoList", ""),
                    category=item.get("jobCategory", ""),
                    description=item.get("workContent", ""),
                    requirement=item.get("qualification", ""),
                    publish_date=int(item.get("publishTime", time.time() * 1000))
                    // 1000,
                    crawl_date=int(time.time()),
                )
                try:
                    if isinstance(t.city, str):
                        t.city = [t.city]
                    elif not t.city:
                        t.city = []
                    else:
                        t.city = list(
                            set([x["workCity"].split("-")[0] for x in t.city])
                        )
                        t.city = [x.replace("省", "") for x in t.city]
                        t.city = [x.replace("市", "") for x in t.city]
                except Exception as e:
                    print(e)
                    t.city = []
                if t.work_type and "实习" in t.work_type:
                    t.work_type = "实习"
                else:
                    t.work_type = "校招"
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
            filters["source_platform"] = "京东官网"
        return data_storage.fetch_all_fingerprints(filters)
