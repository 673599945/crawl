# 系统导入
import os
import typing
import time

# 第三方库导入
import dashscope
from dashscope.api_entities.dashscope_response import (GenerationResponse,
                                                       Message, Role, Choice)


class Requester:

    def chat(topic, content, pub_time=None) -> typing.List[Choice]:

        # 提示词工程-prompt
        _base = f"""下面是一篇与主题{topic}相关的新闻内容，发布时间为{pub_time}。
                请使用10-20个字归纳出一个标题(title)，再用100-150个字归纳新闻的主要内容(con)。
                请将返回结果以json数据格式返回，包含pub_time、title和con字段。\n"""

        content = _base + content

        messages = [
            Message('system', 'You are a copywriter, responsible for summarizing and generalizing news.'),
            Message('user', content)
        ]

        response = dashscope.Generation.call(
            # 若没有配置环境变量，请用百炼API Key将下行替换为：api_key="sk-xxx",
            api_key="sk-06dc07b98e944d589ad477a5f10acdea",
            model="qwen-plus",  # 模型列表：https://help.aliyun.com/zh/model-studio/getting-started/models
            messages=messages,
            result_format='message'
        )

        return response.output.choices


if __name__ == '__main__':
    pass
