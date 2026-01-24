from DrissionPage import ChromiumPage, SessionPage, SessionOptions
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


def get_info_by_id(job_id: str) -> Item:
    # 目标 URL（不带查询参数）
    url = "https://join.qq.com/api/v1/jobDetails/getJobDetailsByPostId"

    # 查询参数
    # 注意：timestamp 通常是当前的毫秒时间戳。
    # 如果原始的 timestamp 过期，你可以使用 int(time.time() * 1000) 生成新的。
    params = {"timestamp": str(int(time.time() * 1000)), "postId": job_id}

    # 请求头
    headers = {
        "accept": "application/json, text/plain, */*",
        "accept-language": "zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7,zh-TW;q=0.6,zh-HK;q=0.5",
        "priority": "u=1, i",
        "referer": f"https://join.qq.com/post_detail.html?postid={job_id}",
        "sec-ch-ua": '"Not(A:Brand";v="8", "Chromium";v="144", "Google Chrome";v="144"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36",
    }

    try:
        # 发送 GET 请求
        response = requests.get(url, params=params, headers=headers)

        # 检查响应状态码
        response.raise_for_status()

        # 打印 JSON 结果
        res = response.json()["data"]
        work_type = res["recruitLabelName"]
        if "实习" in res["recruitLabelName"]:
            work_type = "实习"
        if "应届" in res["recruitLabelName"]:
            work_type = "校招"
        if "毕业生" in res["recruitLabelName"]:
            work_type = "校招"
        item = Item(
            job_id=res["postId"],
            company_name="腾讯",
            source_platform="腾讯官网",
            work_type=work_type,
            job_url=f"https://join.qq.com/post_detail.html?postid={job_id}",
            title=res["title"],
            city=res["workCityList"],
            category=res["tidName"],
            description=res["desc"],
            requirement=res["request"],
            publish_date=int(time.time()),
            crawl_date=int(time.time()),
        )
        return item

    except requests.exceptions.RequestException as e:
        print(e)
        print("请求腾讯失败")
        return Item(job_id=job_id)


def get_list(p: ChromiumPage):
    so = SessionOptions()
    so.set_cookies(p.cookies())
    session = SessionPage(so)

    def get_positions(i: int) -> list:
        # 1. 初始化 SessionPage

        # 2. 定义请求 URL (这里为了稳妥，通常建议动态生成时间戳，但为了还原curl，我保留了原URL)
        # 这里的 timestamp 是 URL 参数
        url = f"https://join.qq.com/api/v1/position/searchPosition?timestamp={int(time.time() * 1000)}"

        # 3. 定义请求头 (Headers)
        headers = {
            "accept": "application/json, text/plain, */*",
            "accept-language": "zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7,zh-TW;q=0.6,zh-HK;q=0.5",
            "content-type": "application/json;charset=UTF-8",
            "origin": "https://join.qq.com",
            "priority": "u=1, i",
            "referer": "https://join.qq.com/post.html",
            # DrissionPage 会自动处理部分 sec-ch-ua，但为了完全模拟curl，这里手动加上
            "sec-ch-ua": '"Not(A:Brand";v="8", "Chromium";v="144", "Google Chrome";v="144"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36",
        }

        # 5. 定义数据载荷 (Payload)
        # 对应 curl 中的 --data-raw
        data = {
            "projectIdList": [],
            "projectMappingIdList": [1],
            "keyword": "",
            "bgList": [],
            "workCountryType": 0,
            "workCityList": [],
            "recruitCityList": [],
            "positionFidList": [],
            "pageIndex": i,
            "pageSize": 10,
        }

        # 6. 发送 POST 请求
        # 注意：发送 JSON 数据时，使用 json=data 参数
        response = session.post(url, headers=headers, json=data)

        # 7. 打印结果
        if response:
            return session.response.json()["data"]["positionList"]

    return get_positions


@dataclass
class WebTencentCampusSource:
    web_page: ChromiumPage
    start_page: int = 1

    def __post_init__(self):
        self._skip_count = 0

    def skip_pages(self, n: int):
        self._skip_count += n

    def fetch_items(self) -> Iterator[Item]:
        p = self.web_page.new_tab()
        i = self.start_page
        page_url = "https://join.qq.com/post.html"
        p.get(page_url)
        ll = get_list(p=p)
        while True:
            # 直接在这里发起网络请求
            res_list = ll(i)
            if res_list == None or len(res_list) == 0:
                break
            for item in res_list:
                t = get_info_by_id(item["postId"])
                if t.city:
                    t.city = [x.replace("总部", "") for x in t.city]
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
            filters["source_platform"] = "腾讯官网"
        return data_storage.fetch_all_fingerprints(filters)
