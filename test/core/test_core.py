from work_show import Item
import json


def test_transform_with_jsonpath():
    """测试原始数据转化是否正常"""
    # 1. 原始数据 (Raw Data)
    raw_data_str = """
    {"auditApplies": null, "externals": null, "applyNum": 0, "entryNum": 0, "offerCount": null, "entryCount": null, "pendingTransferCount": null, "id": 23566, "code": null, "version": null, "positionStatusCode": null, "releaseTime": null, "closeTime": null, "closeUserNumber": null, "pauseTime": null, "name": "直播运营实习生", "recruitProjectCode": "socialr", "positionNatureCode": "C002", "ifParticipateEvaluate": null, "departmentCode": "D6585", "departmentName": null, "positionClassCode": null, "welfareLabelCode": null, "workingHoursNature": null, "positionRecruitNatureCode": null, "positionReplacer": null, "positionCategoryCode": "J0004", "workLocationCode": "Beijing", "educationLimitCode": null, "workExperienceCode": "1", "salaryMin": null, "salaryMax": null, "professionLevel": null, "managementLevel": null, "level": null, "ifManager": null, "positionLevelCode": null, "description": "1. 负责直播平台活动的日常管理、维护和更新...", "positionDemand": "1. 2026届毕业的在读本硕生...", "recruitStartDate": null, "recruitEndDate": null, "recruitNumber": null, "recruitLeaderNumber": null, "recruitLeaderName": null, "recruitLeaderEmail": null, "recruitLeaderPhone": null, "recruitLeaderAvatar": null, "recruitLeaderDeptName": null, "recruitLeaderUserName": null, "ifShowRecruitWebsite": null, "ifShowRecommendWebsite": null, "internalRemarks": null, "ifFreshWater": null, "ifUseHeadhunter": null, "isAuditHeadhunter": null, "useHeadHunterReason": null, "useHeadhunterTitle": null, "externalReleaseFlag": null, "externalChannelCodes": null, "positionAuditProcessId": null, "auditStartTime": null, "auditStartUser": null, "ifSecret": false, "auditType": null, "ifCollect": null, "rejectRemark": null, "ifExternalChannel": null, "recruitEmailCode": null, "businessAudit": null, "auditApply": null, "headCountBefore": null, "headCount": null, "headCountUsed": 0, "businessDirectory": null, "screenInterviewers": null, "finalInterviewerCode": null, "finalInterviewerUserName": null, "ifLongTermRelease": null, "ifFrontLineEmployee": null, "positionGenderLimitCode": null, "positionExperienceCode": null, "ifRecruitWebsiteHot": null, "ifRecommendWebsiteHot": null, "ifFreshWaterHot": null, "ifHeadhunterHot": null, "offerAuditProcessCode": null, "offerAuditProcessId": null, "createId": null, "createTime": null, "updateId": null, "updateTime": "2025-07-07T11:54:15.000+08:00", "prepareCloseTime": null, "positionRecruitNaturesCode": null, "positionReplacers": null, "levels": [], "workLocationsCode": ["Beijing"], "workLocations": null, "notes": null, "channelCode": "official", "personnelTagCode": null, "employmentManagers": null}
    """

    # 2. 映射表 (Mapping Schema)
    mapping_schema_str = """
    {
    "kuaishou": {
        "job_id": "$.id",
        "company_name": null,
        "source_platform": "$.channelCode",
        "job_url": null,
        "title": "$.name",
        "department": "$.departmentCode",
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
        "crawl_date": null,
        "extra_info": {
        "applyNum": "$.applyNum",
        "entryNum": "$.entryNum",
        "recruitProjectCode": "$.recruitProjectCode",
        "positionNatureCode": "$.positionNatureCode",
        "ifSecret": "$.ifSecret",
        "headCountUsed": "$.headCountUsed",
        "workLocationsCode": "$.workLocationsCode"
        }
    }
    }
    """

    raw_data = json.loads(raw_data_str)
    mapping_schema = json.loads(mapping_schema_str)["kuaishou"]
    res = Item.transform_with_jsonpath(mapping_schema, raw_data)
    # 检查res
    assert res.job_id == 23566, "job_id映射错误"
    assert res.title == "直播运营实习生", "title映射错误"
    assert res.extra_info["recruitProjectCode"] == "socialr", "extra_info映射错误"
