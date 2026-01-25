from DrissionPage import ChromiumPage, SessionPage, SessionOptions, WebPage
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


home_url = "https://talent-holding.alibaba.com/off-campus/position-list?lang=zh"


def get_alibaba_talent_data(page_chrome: WebPage):
    # 1. 初始化 WebPage (默认启动浏览器)
    # 如果想无头运行，可以在 ChromiumOptions 中设置

    page = page_chrome.new_tab()
    print("正在通过浏览器访问主页获取环境信息...")
    page.get(home_url)

    # 2. 等待加载
    # 阿里巴巴网站通常有复杂的反爬js，建议稍作等待让cookie生成完整
    # 如果遇到滑块验证，可以在这里手动滑过，或者添加自动化过滑块的代码
    page.wait.doc_loaded()
    time.sleep(2)  # 额外等待2秒确保异步js执行完毕，cookie写入

    # 3. 提取关键信息
    # 从浏览器cookie中获取 XSRF-TOKEN，这对应 URL 中的 _csrf
    cookies_dict = page.cookies().as_dict()
    xsrf_token = cookies_dict.get("XSRF-TOKEN", "")

    if not xsrf_token:
        print("警告：未获取到 XSRF-TOKEN，请求可能会失败。可能需要手动通过验证码。")
    else:
        print(f"获取到 XSRF-TOKEN: {xsrf_token}")

    # 获取当前浏览器的 User-Agent，保持一致性

    # 4. 切换到 Session 模式 (此时会自动继承浏览器的 Cookies)
    print("切换为 SessionPage 模式发起 API 请求...")
    page.change_mode()
    return page, xsrf_token


def search_alibaba_positions(page, xsrf_token, page_index=1, page_size=10):
    """
    使用构造好的 Session 对象发送请求
    """
    # 动态构造 URL，将从浏览器获取的 token 填入
    # 注意：如果 xsrf_token 为空，可能需要处理异常
    api_url = f"https://talent-holding.alibaba.com/position/search?_csrf={xsrf_token}"
    user_agent = page.user_agent
    payload = {
        "channel": "group_official_site",
        "language": "zh",
        "batchId": "",
        "categories": "",
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
        "referer": home_url,
        "user-agent": user_agent,
        # 'priority': 'u=1, i', # 可选
    }

    # 6. 发起 POST 请求
    try:
        res = page.post(api_url, json=payload, headers=headers)

        if res.json():
            return res.json()

    except Exception as e:
        print(f"请求发生错误: {e}")
        # 调试用：查看当前的 Cookies
        print(page.cookies().as_dict())


@dataclass
class WebAlibabaSocialSource:
    web_page: WebPage
    start_page: int = 1

    def __post_init__(self):
        self._skip_count = 0

    def skip_pages(self, n: int):
        self._skip_count += n

    def fetch_items(self) -> Iterator[Item]:
        i = self.start_page
        page, xsrf_token = get_alibaba_talent_data(self.web_page)

        while True:
            # 直接在这里发起网络请求
            if not page or not xsrf_token:
                print("阿里巴巴获取失败")
                break
            # 2. 使用 Session 高速抓取 (模拟翻页)
            print("-" * 30)
            print(f"开始抓取阿里巴巴第 {i} 页数据...")
            data = search_alibaba_positions(page, xsrf_token, page_index=i)

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
                    work_type="社招",
                    job_url="https://talent-holding.alibaba.com"
                    + item.get("positionUrl", ""),
                    title=item.get("name", ""),
                    city=item.get("workLocations", ""),
                    category=item.get("categories", ["未知"]),
                    description=item.get("description", ""),
                    requirement=item.get("requirement", ""),
                    publish_date=int(item.get("publishTime", time.time() * 1000))
                    // 1000,
                    crawl_date=int(time.time()),
                )
                if isinstance(t.category, list):
                    t.category = t.category[0]
                if not t.category:
                    t.category = "未知"
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
