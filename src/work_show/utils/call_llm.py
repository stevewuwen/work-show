import json
from google import genai
import os
import yaml
from pydantic import BaseModel
from typing import Type, TypeVar, Protocol
from openai import OpenAI
from .logger import get_logger

logger = get_logger("call_llm")

# 定义泛型变量为BaseModel的子类, 表示一个类而不是一个类的的对象
T = TypeVar("T", bound=BaseModel)

config = yaml.safe_load(open("config/settings.yaml"))
model = config["crawler"]["model"]

_model2func = {}

_client = None


def _register_model(key: str):
    def inner_wrapper(wrapped_class):
        _model2func[key] = wrapped_class
        return wrapped_class

    return inner_wrapper


@_register_model("gemini")
def get_gemini_json_res(cls: Type[T], system_prompt: str, user_prompt: str) -> T:
    global _client
    if not _client:
        _client = OpenAI(
            api_key=config["crawler"]["gemini_api_key"],
            base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
        )
    try:
        # 在 google.genai SDK 中，system_instruction 放在 config 中
        response = _client.beta.chat.completions.parse(
            model="gemini-3-flash-preview",
            messages=[
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": user_prompt,
                },
            ],
            response_format=cls,
        )

        # 解析返回结果
        return cls.model_validate_json(response.choices[0].message.parsed)

    except Exception as e:
        logger.error(f"Gemini API Error: {e}")
        # 如果解析失败或者API报错，抛出异常让上层处理，或者返回None
        raise e


@_register_model("deepseek")
def get_deepseek_json_res(cls: Type[T], system_prompt: str, user_prompt: str) -> T:
    global _client
    if not _client:
        _client = OpenAI(
            api_key=config["crawler"]["deepseek_api_key"],
            base_url="https://api.deepseek.com",
        )
    try:
        # 在 google.genai SDK 中，system_instruction 放在 config 中
        response = _client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": user_prompt,
                },
            ],
            response_format={"type": "json_object"},
        )

        # 解析返回结果
        return cls.model_validate_json(response.choices[0].message.content)

    except Exception as e:
        logger.error(f"Gemini API Error: {e}")
        # 如果解析失败或者API报错，抛出异常让上层处理，或者返回None
        raise e


def get_json_data(
    description: str, requirement: str
) -> tuple[str, str, list[str], list[str]]:
    # 定义响应结构
    class DescriptionKeyboard(BaseModel):
        experience_req: str
        education_req: str
        description_keywords: list[str]
        requirement_keywords: list[str]

    system_prompt = """Parse job data into JSON.

Rules:
1. experience_req: Map to ['应届毕业生', '0-1年', '1-3年', '3-5年', '5-10年', '10年以上', '不限']. Match start of range (e.g., "3y+" -> '3-5年'). Default: '不限'.
2. education_req: Min degree ['专科', '本科', '硕士', '博士', '不限']. Default: '不限'.
3. Keywords: Extract 5-15 Tech/Domain keywords for description/requirement. Normalize acronyms. Exclude soft skills/verbs.

Output JSON:
{
    "experience_req": "",
    "education_req": "",
    "description_keywords": [],
    "requirement_keywords": []
}"""
    user_prompt = f"""Data:
[description]: {description}
[requirement]: {requirement}"""

    try:
        # 调用注册的模型函数，传入拆分后的 prompt
        res = _model2func[model](DescriptionKeyboard, system_prompt, user_prompt)
        return (
            res.experience_req,
            res.education_req,
            res.description_keywords,
            res.requirement_keywords,
        )
    except Exception as e:
        logger.error(f"Failed to extract keywords: {e}")
        # 返回空列表而不是 None，防止解包报错
        return "", "", [], []
