import json


class CityStandardizer:
    def __init__(self):
        self._raw_data = {
            "北京": ["beijing", "peking", "110000", "bj", "北京市"],
            "上海": ["shanghai", "310000", "sh", "上海市"],
            "广州": ["guangzhou", "canton", "440100", "gz", "广州市"],
            "深圳": ["shenzhen", "440300", "sz", "深圳市"],
            "杭州": ["hangzhou", "330100", "hz", "杭州市"],
            "成都": ["chengdu", "510100", "cd", "成都市"],
        }

        # 初始化查找表（反向索引）
        self.lookup_map = self._build_lookup_map()

    def _build_lookup_map(self):
        """构建一个巨大的扁平化字典，用于快速查找"""
        mapping = {}
        for standard_name, variants in self._raw_data.items():
            mapping[standard_name] = standard_name

            for variant in variants:
                key = str(variant).lower().strip()
                mapping[key] = standard_name
        return mapping

    def convert(self, input_val):
        """
        统一转换函数
        :param input_val: 输入的城市信息 (str 或 int)
        :return: 标准中文名，如果找不到则返回 None 或 原值
        """
        if input_val is None:
            return None

        query_key = str(input_val).strip().lower()

        return self.lookup_map.get(query_key, input_val)  # 如果找不到返回 None


city_standardizer = CityStandardizer()


def city_convert(input_city):
    return city_standardizer.convert(input_city)
