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

configs = [
    {
        "batchId": "100000060001",
        "categoryType": "freshman",
        "channel": "campus_group_official_site",
    },
    {
        "batchId": "201",
        "categoryType": "talentPlan",
        "channel": "campus_group_official_site",
    },
    {
        "batchId": "339",
        "categoryType": "talentPlan",
        "channel": "campus_group_official_site",
    },
]


def get_alibaba_talent_data(table: MixTab):
    # 1. 初始化 WebPage (默认启动浏览器)
    # 如果想无头运行，可以在 ChromiumOptions 中设置
    print("正在通过浏览器访问主页获取环境信息...")
    table.get("https://talent-holding.alibaba.com/campus/position-list")
    # 2. 等待加载
    # 阿里巴巴网站通常有复杂的反爬js，建议稍作等待让cookie生成完整
    # 如果遇到滑块验证，可以在这里手动滑过，或者添加自动化过滑块的代码
    table.wait.doc_loaded()
    time.sleep(2)  # 额外等待2秒确保异步js执行完毕，cookie写入

    # 3. 提取关键信息
    # 从浏览器cookie中获取 XSRF-TOKEN，这对应 URL 中的 _csrf
    cookies_dict = table.cookies().as_dict()
    xsrf_token = cookies_dict.get("XSRF-TOKEN", "")

    if not xsrf_token:
        print("警告：未获取到 XSRF-TOKEN，请求可能会失败。可能需要手动通过验证码。")
    else:
        print(f"获取到 XSRF-TOKEN: {xsrf_token}")
    # 获取当前浏览器的 User-Agent，保持一致性

    # 4. 切换到 Session 模式 (此时会自动继承浏览器的 Cookies)
    print("切换为 SessionPage 模式发起 API 请求...")
    table.change_mode()
    return table, xsrf_token


def search_alibaba_positions(
    table,
    xsrf_token,
    batchId: str,
    categoryType: str,
    channel: str,
    page_index=1,
    page_size=10,
):
    """
    使用构造好的 Session 对象发送请求
    """
    # 动态构造 URL，将从浏览器获取的 token 填入
    # 注意：如果 xsrf_token 为空，可能需要处理异常
    api_url = f"https://talent-holding.alibaba.com/position/search?_csrf={xsrf_token}"
    user_agent = table.user_agent
    payload = {
        "channel": channel,
        "language": "zh",
        "batchId": batchId,
        "categoryType": categoryType,
        "deptCodes": [],
        "key": "",
        "pageIndex": page_index,
        "pageSize": page_size,
        "regions": "",
        "subCategories": "",
        "shareType": "",
        "shareId": "",
        "myReferralShareCode": "",
    }
    headers = {
        "accept": "application/json, text/plain, */*",
        "accept-language": "en-US,en;q=0.9",
        "bx-v": "2.5.11",  # 注意：这个版本号可能会变，如果请求失败可能需要从页面JS中提取
        "content-type": "application/json",
        "origin": "https://talent-holding.alibaba.com",
        "referer": f"https://talent-holding.alibaba.com/campus/position-list?batchId={batchId}&campusType={categoryType}&lang=zh",
        "user-agent": user_agent,
        # 'priority': 'u=1, i', # 可选
    }

    # 6. 发起 POST 请求
    try:
        res = table.post(api_url, json=payload, headers=headers)

        if res.json():
            return res.json()

    except Exception as e:
        print(f"请求发生错误: {e}")
        # 调试用：查看当前的 Cookies
        print(table.cookies().as_dict())


@dataclass
class WebAlibabaCampusSource:
    web_page: WebPage
    start_page: int = 1

    def __post_init__(self):
        self._skip_count = 0

    def skip_pages(self, n: int):
        self._skip_count += n

    def fetch_items(self) -> Iterator[Item]:
        table = self.web_page.new_tab()
        table, xsrf_token = get_alibaba_talent_data(table)
        for config in configs:
            i = self.start_page
            print(config)
            batchId = config["batchId"]
            channel = config["channel"]
            categoryType = config["categoryType"]
            while True:
                # 直接在这里发起网络请求
                if not table or not xsrf_token:
                    print(f"{config}, 阿里巴巴获取失败")
                    break
                # 2. 使用 Session 高速抓取 (模拟翻页)
                print("-" * 30)
                print(f"开始抓取阿里巴巴第 {i} 页数据...")
                data = search_alibaba_positions(
                    table,
                    xsrf_token,
                    batchId=batchId,
                    categoryType=categoryType,
                    channel=channel,
                    page_index=i,
                )

                if not data:
                    print("未能获取到职位数据，可能是反爬风控或参数错误。")
                    break
                res_list = data.get("content", {}).get("datas", [])
                if res_list == None or len(res_list) == 0:
                    break
                for item in res_list:
                    t = Item(
                        job_id=str(item.get("id", uuid.uuid4())),
                        company_name="阿里巴巴",
                        source_platform="阿里官网",
                        work_type="实习"
                        if item.get("batchName", "")
                        and "实习" in item.get("batchName", "")
                        else "校招",
                        job_url=f"https://talent-holding.alibaba.com/campus/position-detail?lang=zh&positionId={str(item.get('id', ''))}",
                        title=item.get("name", ""),
                        city=item.get("workLocations", ""),
                        category=item.get("categoryName", ""),
                        description=item.get("description", ""),
                        requirement=item.get("requirement", ""),
                        publish_date=int(item.get("modifyTime", time.time() * 1000))
                        // 1000,
                        crawl_date=int(time.time()),
                    )
                    if "categories" in item and item["categories"] and not t.category:
                        t.category = item["categories"][0]
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
            filters["source_platform"] = "阿里官网"
        return data_storage.fetch_all_fingerprints(filters)
