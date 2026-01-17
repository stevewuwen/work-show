# Role
你是一名数据集成专家。正在编写一个从「招聘平台爬虫数据」到「标准数仓表」的字段映射配置。

# Task
生成一个 JSON 映射对象。
Key = 标准数仓表的字段名。
Value = 提取源数据的 JsonPath 表达式（以 `$.` 开头）。

# Source Data (Sample)
```json
{{
  "auditApplies": null,
  "id": 18602,
  "name": "HR实习生",
  "departmentCode": "D2098",
  "departmentName": null,
  "workLocationCode": "Beijing",
  "positionCategoryCode": "J0002",
  "workExperienceCode": "1",
  "salaryMin": null,
  "salaryMax": null,
  "description": "...",
  "positionDemand": "...",
  "updateTime": "2024-10-12...",
  "channelCode": "official"
}}
```

# Target Schema (Keys)
job_id, company_name, source_platform, job_url, title, department, city, category, experience_req, education_req, job_level, salary_min, salary_max, description, requirement, publish_date, crawl_date, extra_info

# Rules
1. **映射语法**：
   - 如果源字段存在，Value 格式为 `$.字段名` (例如 `$.name`)。
   - 如果源字段**不存在**或需**外部传入**，Value 格式为 `null` (不要带引号)。
2. **语义匹配**：根据字段含义进行匹配（例如 `name` -> `title`，`updateTime` -> `publish_date`）。
3. **Extra Info 策略**：
   - `extra_info` 的 Value 应该是一个嵌套的 JSON 对象。
   - 请扫描源数据，将所有**未被映射到顶层 Key** 的字段，放入 `extra_info` 中。
   - `extra_info` 内部的格式同样为 `"原字段名": "$.原字段名"`。
   - **注意**：源数据中值为 `null` 的字段（如 `auditApplies`），**不要**包含在 `extra_info` 中，以保持精简。

# Output Example
{
  "job_id": "$.id",
  "company_name": null,
  ...
  "extra_info": {
     "reserved_field": "$.some_field"
  }
}

# 源数据

```json
{
  "id": "7595187765260732725",
  "title": "服务商运营实习生（市场营销）-抖音电商",
  "sub_title": null,
  "description": "日常实习：面向全体在校生，为符合岗位要求的同学提供为期3个月及以上的项目实践机会。\n团队介绍：抖音电商致力于成为用户发现丰富好物的首选平台。众多抖音创作者通过短视频、直播、商城等丰富的形式，给用户提供更个性化、更生动、更高效的消费体验。同时，抖音电商积极引入优质合作伙伴，为商家变现提供多元的选择。\n\n1、协助电商商家端沟通和运营维护；\n2、协助部门电商频道进行货品盘点、招商、比价及审核工作；\n3、协助部门进行活动方案设计及落地运营工作；\n4、协助部门进行信息梳理、项目跟进和其他日常运营，专项数据整理和及时复盘；\n5、协助部门分析业务数据，通过数据分析及市场反馈不断推进业务迭代，推动重点商家的成交及GMV数据上涨。",
  "requirement": "1、本科及以上学历在读；\n2、学习能力强、洞察力强、思路清晰、文笔流畅，具有较强的独立思考能力和自我驱动力，熟悉使用各种办公及分析软件，有较强的沟通能力、数据分析能力，工作高效；\n3、对国内主流电商平台特别是内容电商平台的商业模式有基本认知和思考，有电商平台或自媒体运营等经历优先；\n4、能尽快到岗优先。",
  "job_category": {
    "id": "6704215882479962371",
    "name": "运营",
    "en_name": "Operations",
    "i18n_name": "运营",
    "depth": 1,
    "parent": null,
    "children": null
  },
  "city_info": {
    "code": "CT_125",
    "name": "上海",
    "en_name": "Shanghai",
    "location_type": null,
    "i18n_name": "上海",
    "py_name": null,
    "mdm_code": null,
    "node_status": null
  },
  "recruit_type": {
    "id": "202",
    "name": "实习",
    "en_name": "Intern",
    "i18n_name": "实习",
    "depth": 2,
    "parent": {
      "id": "2",
      "name": "校招",
      "en_name": "Campus",
      "i18n_name": "校招",
      "depth": 1,
      "parent": null,
      "children": null,
      "active_status": 1,
      "selectability": 1
    },
    "children": null,
    "active_status": 1,
    "selectability": 1
  },
  "publish_time": 1768392559043,
  "job_hot_flag": null,
  "job_subject": {
    "id": "7194661644654577981",
    "name": {
      "zh_cn": "日常实习",
      "en_us": null,
      "i18n": "日常实习"
    },
    "limit_count": null,
    "active_status": 1,
    "subject_group_info": null
  },
  "code": "A228848",
  "department_id": null,
  "job_function": null,
  "job_process_id": "20000",
  "recommend_id": null,
  "city_list": [
    {
      "code": "CT_125",
      "name": "上海",
      "en_name": "Shanghai",
      "location_type": null,
      "i18n_name": "上海",
      "py_name": null,
      "mdm_code": null,
      "node_status": null
    }
  ],
  "job_post_info": {
    "id": null,
    "job_id": null,
    "title": null,
    "sub_title": null,
    "address_id": null,
    "address": null,
    "city": null,
    "education": null,
    "experience": null,
    "description": null,
    "requirement": null,
    "min_salary": null,
    "max_salary": null,
    "currency": null,
    "head_count": null,
    "crator_id": null,
    "expiry_time": null,
    "progress": null,
    "department_id": null,
    "job_type": null,
    "recruitment_type": {
      "id": "202",
      "name": "实习",
      "en_name": "Intern",
      "i18n_name": "实习",
      "depth": 2,
      "parent": {
        "id": "2",
        "name": "校招",
        "en_name": "Campus",
        "i18n_name": "校招",
        "depth": 1,
        "parent": null,
        "children": null,
        "active_status": 1,
        "selectability": 1
      },
      "children": null,
      "active_status": 1,
      "selectability": 1
    },
    "job_process_time": null,
    "job_in_charge_user_id": null,
    "biz_create_time": null,
    "HighlightList": null,
    "JobChannelPublishList": null,
    "required_degree": null,
    "never_expiry": null,
    "job_hot_flag": null,
    "subject": null,
    "sequence": null,
    "min_level": null,
    "max_level": null,
    "job_post_object_value_map": {},
    "code": null,
    "job_active_status": null,
    "job_process_type": null,
    "biz_modify_time": null,
    "job_function": null,
    "job_process": null,
    "job_process_id": null,
    "job_category": null,
    "address_list": null,
    "city_list": null,
    "correlation_job_list": null,
    "tag_list": null,
    "department": null,
    "job_storefront_mode": null,
    "storefront_list": null,
    "target_major_list": null,
    "schema": null,
    "job_post_process_time_list": null,
    "job_level_id_list": null
  },
  "storefront_mode": 1,
  "storefront_list": null,
  "process_type": 2
}

```

# Final Action
请分析源数据，直接生成最终的 JSON 映射代码。