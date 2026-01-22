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


def get_mapping_table():
    mp = {}
    p2 = WebPage()
    p2.listen.start(
        "api/v1/dictionary/batch?types=workLocation,positionCategory,positionExperience,positionNature"
    )
    p2.get(f"https://zhaopin.kuaishou.cn/recruit/e/#/official/social/job-info/28457")
    res = p2.listen.wait()
    res_key_list = res.response.body.get("result")
    for item in res_key_list:
        res_list = res_key_list[item]
        for item_info in res_list:
            mp[item_info["code"]] = item_info["name"]
    with open("test2.json", mode="w", encoding="utf-8") as f:
        f.write(json.dumps(mp, ensure_ascii=False, indent=2))
    p2.disconnect()


@dataclass
class WebKuaishouSocialSource:
    web_page: WebPage
    start_page: int = 1

    def __post_init__(self):
        self._skip_count = 0

    def skip_pages(self, n: int):
        self._skip_count += n

    def fetch_items(self) -> Iterator[Item]:
        p = self.web_page.new_tab()
        p.listen.start("api/v1/open/positions/simple")
        i = self.start_page
        schema_dict = {
            "job_id": "$.id",
            "company_name": None,
            "source_platform": "$.channelCode",
            "job_url": None,
            "title": "$.name",
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
        mp = json.loads(mapping_table)
        work_types = ["social", "trainee"]
        while True:
            if self._skip_count > 0:
                i += self._skip_count
                self._skip_count = 0
            for work_type in work_types:
                p.get(
                    f"https://zhaopin.kuaishou.cn/recruit/e/#/official/{work_type}/?workLocationCode=domestic&pageNum={i}"
                )
                print(i)
                res = p.listen.wait()
                res_list = res.response.body.get("result")["list"]
                if res_list == None or len(res_list) == 0:
                    break
                for item in res_list:
                    t = Item.transform_with_jsonpath(schema_dict, item)
                    t.source_platform = "快手官网"
                    if t.work_type == None or t.work_type == "":
                        t.work_type = "社招" if work_type == "social" else "实习"
                    if t.job_url == None or t.job_url == "":
                        t.job_url = f"https://zhaopin.kuaishou.cn/recruit/e/#/official/{work_type}/job-info/{t.job_id}"
                    if t.crawl_date == None or t.crawl_date == "":
                        t.crawl_date = int(time.time())
                    if t.company_name == None or t.company_name == "":
                        t.company_name = "快手"
                    if t.extra_info and "workLocationsCode" in t.extra_info:
                        t.city = [
                            mp.get(x, "未知") for x in t.extra_info["workLocationsCode"]
                        ]
                    else:
                        t.city = [mp.get(t.city, "未知")]
                    try:
                        t.publish_date = int(
                            datetime.fromisoformat(t.publish_date).timestamp()
                        )
                    except Exception as e:
                        pass
                    t.experience_req = mp.get(t.experience_req, "未知")
                    t.category = mp.get(t.category, "未知")
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
            filters["source_platform"] = "快手官网"
        return data_storage.fetch_all_fingerprints(filters)


mapping_table = """{
  "Beijing": "北京",
  "Shanghai": "上海",
  "Guangzhou": "广州",
  "Shenzhen": "深圳",
  "Tianjin": "天津",
  "Hangzhou": "杭州",
  "Chengdu": "成都",
  "Wuhan": "武汉",
  "Jinan": "济南",
  "qingdao": "青岛",
  "Yantai": "烟台",
  "xiamen": "厦门",
  "Taiyuan": "太原",
  "Xian": "西安",
  "Shenyang": "沈阳",
  "Haerbin": "哈尔滨",
  "changchun": "长春",
  "shijiazhuang": "石家庄",
  "kunming": "昆明",
  "Dalian": "大连",
  "Lanzhou": "兰州",
  "Wuxi": "无锡",
  "huaian": "淮安",
  "tongren": "铜仁",
  "jishou": "吉首",
  "Changsha": "长沙",
  "wulanchabu": "乌兰察布",
  "hongkong": "香港",
  "suzhou": "苏州",
  "Los Angeles": "洛杉矶",
  "chengmai": "澄迈",
  "San Jose": "硅谷",
  "New York": "纽约",
  "Seattle": "西雅图",
  "Washington, D.C.": "华盛顿特区",
  "Yancheng": "盐城",
  "San Diego": "圣地亚哥",
  "bengaluru": "班加罗尔",
  "saopaulo": "圣保罗",
  "gurugram": "古尔冈",
  "Jakarta": "雅加达",
  "Kualalumpur": "吉隆坡",
  "Egypt": "埃及",
  "Mexico": "墨西哥",
  "Argentina": "阿根廷",
  "Viet Nam": "越南",
  "Russia": "俄罗斯",
  "Singapore": "新加坡",
  "Seoul": "首尔",
  "islamabad": "伊斯兰堡",
  "zhengzhou": "郑州",
  "chongqing": "重庆",
  "Dongguan": "东莞",
  "Tangshan": "唐山",
  "Linyi": "临沂",
  "baoding": "保定",
  "Luoyang": "洛阳",
  "Suining": "遂宁",
  "Zhuhai": "珠海",
  "huhehaote": "呼和浩特",
  "yinchuan": "银川",
  "nanjing": "南京",
  "columbia": "哥伦比亚",
  "peru": "秘鲁",
  "Bangkok": "曼谷",
  "London": "伦敦",
  "Dubai": "迪拜",
  "Karachi": "卡拉奇",
  "Morocco": "摩洛哥",
  "Dhaka": "达卡",
  "Kathmandu": "加德满都",
  "Colombo": "科伦坡",
  "Moscow": "莫斯科",
  "Istanbul": "伊斯坦布尔",
  "Lahore": "拉合尔",
  "hefei": "合肥",
  "C001": "全职",
  "C002": "实习",
  "C003": "兼职",
  "1": "不限",
  "2": "应届毕业生",
  "3": "1年以下",
  "4": "1-3年",
  "5": "3-5年",
  "6": "5-10年",
  "7": "10年以上",
  "B012": "客服类",
  "J0001": "技术类",
  "B009": "工程类",
  "B008": "算法类",
  "B003": "产品类",
  "B004": "职能类",
  "B005": "运营类",
  "B006": "市场类",
  "B002": "设计类",
  "B010": "战略支持类",
  "J0012": "工程类",
  "B011": "战略分析类",
  "B001": "技术类",
  "J0011": "算法类",
  "J0005": "产品类",
  "J0004": "运营类",
  "J0003": "设计类",
  "J0014": "分析类",
  "J0013": "战略类",
  "J0006": "市场类",
  "J0002": "职能类",
  "J0007": "客服类",
  "J0008": "审核类",
  "J0009": "内容评级类",
  "J0015": "销售及支持类",
  "J0010": "其它类",
  "B007": "其他"
}"""
