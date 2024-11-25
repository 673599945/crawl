# 系统导入
import json
import os
import typing

# 第三方库导入
from PyQt6.QtCore import QThread, pyqtSignal, QObject
from dashscope.api_entities.dashscope_response import Choice

# 本地导入
from core.requester import Requester
from core.spiders import Spiders
from core.utils import DateUtil


class Handler(QObject):
    progress_signal = pyqtSignal(str)  # 添加进度信号

    def __init__(self,_keywords,target_urls):
        super().__init__()
        self._keywords = _keywords
        self.target_urls = target_urls
        
    #定义爬虫运行方法
    def run_spider(self):
        try:
            timestamp = DateUtil.get_timestamp()
            time_str = DateUtil.timestamp_format(timestamp, "%Y-%m-%d_%H-%M-%S")

            self.progress_signal.emit("正在新闻数据采集...")
            spider_data = self._news_spider(time_str)

            self.progress_signal.emit("正在AI处理新闻...")
            self._ai_llm(spider_data, time_str)

            msg = "执行成功，数据已处理完毕。"
            self.progress_signal.emit(msg)
            print(f"{msg}\n\n")
            print("请等待下一次任务调度执行...\n\n")

        except Exception as e:
            error_msg = f"执行出错：{str(e)}"
            self.progress_signal.emit(error_msg)
            raise e


    def _ai_llm(self,spider_data, time_str):
        cn = list()
        themes = list()
        start_time = DateUtil.get_timestamp()
        print("开始处理新闻数据...")
        
        for _spider in spider_data:
            _keyword = _spider.get("keyword")
            _spider_data = _spider.get("spider_data")

            for _ in _spider_data:
                _data = _.get("data")
                for __data in _data:
                    _article: str = __data.get("article")
                    pub_time = __data.get("pub_time", "未知时间")
                    
                    choices: typing.List[Choice] = Requester.chat(
                        topic=_keyword,
                        content=_article,
                        pub_time=pub_time
                    )
                    
                    ai_article = json.loads(choices[0].message.content
                                         .replace("json\n", "")
                                         .replace("`", "")
                                         .replace(" ", "")
                                         .replace("\n", ""))

                    if _keyword == self._keywords[0]:
                        cn.append({
                            "pub_time": pub_time,
                            "title": ai_article.get("title"),
                            "con": ai_article.get("con"),
                            "used": True
                        })
                        
                        themes.append({
                            "pub_time": pub_time,
                            "title": ai_article.get("title")
                        })

        end_time = DateUtil.get_timestamp()
        print(f"耗时[{end_time - start_time}]秒，数据处理完成!!!")

        # 保存数据
        base_path = os.path.join("spider_cache", f"{time_str}_processed_data.json")
        with open(base_path, "w", encoding="utf-8") as f:
            json.dump(cn, f, ensure_ascii=False, indent=2)

        titles_path = os.path.join("spider_cache", f"{time_str}_titles.json")
        with open(titles_path, "w", encoding="utf-8") as f:
            json.dump(themes, f, ensure_ascii=False, indent=2)


    def _news_spider(self, time_str):
        spider_manager = Spiders(target_urls=self.target_urls)

        spider_manager.set_keywords(keywords=self._keywords)
        start_time = DateUtil.get_timestamp()
        print("开始采集...")
        spider_data = spider_manager.run_spider()
        end_time = DateUtil.get_timestamp()
        print(f"耗时[{end_time - start_time}]秒，采集完成!!!!")

        raw_data_path = os.path.join("spider_cache", f"{time_str}_raw_data.json")
        with open(raw_data_path, "w", encoding="utf-8") as f:
            f.write(json.dumps(spider_data, ensure_ascii=False))
        return spider_data


if __name__ == '__main__':
    # SpiderHandler.html_to_image([], [], [], [], "2024-10-29_21-39-39")
    pass