from pydantic import BaseModel

from work_show.utils import call_llm


def test_get_json_res():
    class A(BaseModel):
        keywords: list[str]
        description: str

    a = call_llm.get_doubao_json_res(
        A,
        "你是一个友善的模型",
        "请使用一组关键词和一个简短的话来描述一下你自己，使用json进行回答，包含keywords和description两个key，其中keywords的value为list[str],description的value为str",
    )
    assert isinstance(a.keywords, list), f"{call_llm.__name__} 模型返回有问题"
    assert isinstance(a.description, str), f"{call_llm.__name__} 模型返回有问题"
