from pydantic import BaseModel
from work_show.utils import call_llm


def test_get_json_res():
    class A(BaseModel):
        keywords: list[str]
        description: str

    a = call_llm.get_json_res(
        A, "请使用一组关键词和一个简短的话来描述一下你自己", "deepseek/deepseek-chat"
    )
    assert isinstance(a.keywords, list), f"{call_llm.__name__} 模型返回有问题"
    assert isinstance(a.description, str), f"{call_llm.__name__} 模型返回有问题"
