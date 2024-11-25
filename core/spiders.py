import os
import time
from urllib.parse import quote

from DrissionPage import ChromiumPage, ChromiumOptions


def run_browser() -> ChromiumPage or None:
    co = ChromiumOptions()
    co.auto_port(True)  # 此方法用于设置是否使用自动分配的端口，启动一个全新的浏览器
    co.headless()
    co.set_user_agent("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")

    co.set_argument('--no-sandbox')
    co.set_argument('--disable-dev-shm-usage')
    co.set_argument('--disable-gpu')

    max_retries = 3
    for i in range(max_retries):
        try:
            page: ChromiumPage = ChromiumPage(co)
            return page
        except Exception as e:
            print(f"浏览器启动失败 (尝试 {i+1}/{max_retries}): {str(e)}")
            if i < max_retries - 1:
                time.sleep(2)  # 等待2秒后重试
            else:
                raise e  # 最后一次尝试失败时抛出异常

    return None

class Spiders:

    def __init__(self,target_urls):
        self.keywords = list()
        self.page: ChromiumPage = run_browser()
        _slice = os.environ.get("ARTICLE_SPIDER_NUMBER") or 2
        _slice = int(_slice)
        self.slice = _slice

        self.target_urls = target_urls
        # self.target_urls = {
        #     "sina": "https://search.sina.com.cn/news",  # 新浪
        #     "jin10": "https://search.jin10.com/?keyword={keyword}",  # 金十
        #     "rmw": "http://search.people.cn/",  # 人民网
        #     "rbw": "https://newssearch.chinadaily.com.cn/cn/search?query={keyword}",  # 中国日报网
        #     "xhw": "https://so.news.cn/#search/0/{keyword}/1/0",  # 新华网
        #     "cfw": "https://so.eastmoney.com/news/s?keyword={keyword}",  # 东方财富网
        #     "cls": "https://www.cls.cn/searchPage?keyword={keyword}&type=depth",  # 财联社
        #     "ljb": "https://search.kjrb.com.cn:8888/founder/NewSearchServlet.do?siteID=1&content={keyword}"  # 科技日报
        # }

    # 设置关键词
    def set_keywords(self, keywords):
        self.keywords = keywords

    def run_spider(self):

        spider_data = []
        for keyword in self.keywords:
            _dict = dict()
            _dict["keyword"] = keyword
            _dict["spider_data"] = list()
            for key in self.target_urls.keys():
                _ = dict()
                _data = getattr(self, f"_{key}_spider")(keyword)
                _["data"] = _data
                _["key"] = key
                _dict["spider_data"].append(_)

            spider_data.append(_dict)

        self.page.close()
        self.page.quit()
        return spider_data

    def _create_tab(self, key: str, keyword: str):
        target_url = self.target_urls[key]

        if "{keyword}" in target_url:
            target_url = target_url.replace("{keyword}", keyword)

        tab = self.page.new_tab(url=target_url)
        return tab

    def _create_empty_tab(self):
        tab = self.page.new_tab()
        return tab

    # def _wind_spider(self, keyword: str):
    #     print(f"万得[{keyword}]采集中...")
    #     tab = self._create_tab("wind", keyword)

    def _sina_spider(self, keyword: str):
        print(f"新浪[{keyword}]采集中...")
        tab = self._create_tab("sina", keyword)
        tab.ele("tag:input@id=keyword").input(keyword)
        tab.listen.start("/news")
        tab.ele("tag:input@type=submit").click()
        tab.listen.wait(timeout=10)

        div_eles = tab.eles("tag:div@class=box-result clearfix")

        result = list()
        index = 0
        for div_ele in div_eles:
            if index >= self.slice:
                break
            try:
                a_ele = div_ele.child("tag:h2").child("tag:a")
                title = a_ele.text
                _url = a_ele.attr("href")
                new_tab = self.page.new_tab(_url)

                time.sleep(1)
                article = new_tab.s_ele("tag:div@class=article").text
                new_tab.close()
            except:
                continue

            _dict = {
                "title": title,
                "article": article,
                "detail_url": _url
            }
            index += 1

            result.append(_dict)

        tab.close()
        return result

    def _jin10_spider(self, keyword: str):
        tab = self._create_tab("jin10", keyword)
        pass

    def _rmw_spider(self, keyword: str):
        """
        人民网爬虫
        """
        print(f"人民网[{keyword}]采集中...")
        news_list = []
        
        try:
            # 直接构建搜索URL
            encoded_keyword = quote(keyword)
            url = f"http://search.people.cn/s?keyword={encoded_keyword}&st=0"
            
            # 创建新标签页并访问
            tab = self.page.new_tab(url)
            time.sleep(2)  # 等待页面加载
            
            # 获取新闻列表
            items = tab.s_eles('.news_list .list_item')
            
            # 如果找不到，尝试备用选择器
            if not items:
                items = tab.s_eles('.ej_list_box .news_item')
            
            # 如果还是找不到，再尝试其他选择器
            if not items:
                items = tab.s_eles('.result.clearfix')
            
            for item in items[:20]:  # 限制获取条数，提高速度
                try:
                    # 获取标题和链接
                    title_ele = (item.s_ele('h2 a') or 
                               item.s_ele('.title a') or 
                               item.s_ele('a'))
                    
                    if not title_ele:
                        continue
                        
                    title = title_ele.text.strip()
                    url = title_ele.attr('href')
                    
                    # 获取时间
                    time_ele = (item.s_ele('.date') or 
                              item.s_ele('.tim') or 
                              item.s_ele('.info span'))
                    pub_time = time_ele.text.strip() if time_ele else ''
                    
                    # 获取来源
                    source_ele = (item.s_ele('.source') or 
                                item.s_ele('.from') or 
                                item.s_ele('.info a'))
                    source = source_ele.text.strip() if source_ele else '人民网'
                    
                    if title and url:
                        news_list.append({
                            'title': title,
                            'url': url,
                            'pub_time': pub_time,
                            'source': source,
                            'platform': '人民网'
                        })
                        
                except Exception as e:
                    continue
                
            tab.close()
            return news_list
            
        except Exception as e:
            print(f"人民网爬虫出错: {str(e)}")
            if 'tab' in locals():
                tab.close()
            return []

    def _rbw_spider(self, keyword: str):
        print(f"中国日报网[{keyword}]采集中...")
        tab = self._create_tab("rbw", keyword)
        time.sleep(2)
        tab.listen.start("/rest/cn/search")
        tab.ele(".main_l").child("tag:div").child("tag:span@type=button").click(by_js=True)
        data_packet = tab.listen.wait(timeout=10)

        if not bool(data_packet):
            tab.close()
            return self._rbw_spider(keyword)

        resp = data_packet.response.body
        content = resp.get("content")

        result = list()
        for item in content[:self.slice:]:
            _dict = {"title": item.get("title"), "article": item.get("plainText"), "target_url": item.get("url")}
            result.append(_dict)

        tab.close()
        return result

    def _xhw_spider(self, keyword: str):
        print(f"新华网[{keyword}]采集中...")
        tab = self._create_tab("xhw", keyword)
        time.sleep(5)
        tab.listen.start("/getNews")
        tab.ele(".search-button").click(by_js=True)
        data_packet = tab.listen.wait(timeout=20)

        if not bool(data_packet):
            tab.close()
            return self._xhw_spider(keyword)

        resp = data_packet.response.body
        content = resp.get("content")
        results = content.get("results")

        result = list()
        index = 0
        for item in results:
            _url = item.get("url")
            title = item.get("title")
            pub_time = item.get("pubTime", "未知时间")

            if index >= self.slice:
                break

            try:
                new_tab = self.page.new_tab(_url)
                time.sleep(2)
                article = new_tab.ele("#detailContent").text

                # 优化时间获取逻辑
                if pub_time == "未知时间" or len(pub_time.split(':')) >= 4:
                    try:
                        pub_time_ele = (
                            new_tab.ele(".info .pub-tim") or
                            new_tab.ele(".pub-time") or
                            new_tab.ele("div.source-time") or
                            new_tab.ele("div[class*='pub']") or
                            new_tab.ele(".time")
                        )
                        if pub_time_ele:
                            full_time = pub_time_ele.text.strip()
                            # 如果获取到完整时间，直接使用
                            if '-' in full_time and ':' in full_time:
                                pub_time = full_time
                            # 如果只有时分秒，添加当前日期
                            elif ':' in full_time:
                                current_date = time.strftime("%Y-%m-%d")
                                pub_time = f"{current_date} {full_time}"
                            # print(f"提取到的时间: {pub_time}")
                    except Exception as e:
                        print(f"时间提取错误: {str(e)}")
                        pub_time = time.strftime("%Y-%m-%d %H:%M:%S")

                _dict = {
                    "title": title,
                    "article": article,
                    "detail_url": _url,
                    "pub_time": pub_time
                }
                new_tab.close()
            except Exception as e:
                print(f"页面处理错误: {str(e)}")
                continue

            index += 1
            result.append(_dict)

        tab.close()
        return result

    def _cfw_spider(self, keyword: str):
        print(f"东方财富网[{keyword}]采集中...")
        tab = self._create_tab("cfw", keyword)
        tab.ele(".dropdown_sorttype").hover()
        tab.ele(".sorttype_d").child("tag:ul").child("tag:li@text()=按时间排序").click()
        time.sleep(10)
        news_list = tab.s_ele(".news_list").children(".news_item")

        result = list()
        index = 0
        for item in news_list:
            if index >= self.slice:
                break

            try:
                a_ele = item.s_ele(".news_item_t").child("tag:a")
                title = a_ele.text
                _url = a_ele.attr("href")
                new_tab = self.page.new_tab(_url)
                time.sleep(2)
                article = new_tab.ele("#ContentBody").text
                
                # 提取并清理发布时间
                pub_time_ele = item.s_ele(".news_item_time")
                pub_time = pub_time_ele.text.strip() if pub_time_ele else "未知时间"
                pub_time = pub_time.replace(" -", "").strip()  # 清理多余的空格和横杠
                
                _dict = {
                    "title": title, 
                    "article": article, 
                    "target_url": _url,
                    "pub_time": pub_time
                }
                new_tab.close()
            except:
                continue

            index += 1
            result.append(_dict)

        tab.close()
        return result

    def _cls_spider(self, keyword: str):
        # print(f"财联社[{keyword}]采集中...")
        tab = self._create_empty_tab()
        target_url = self.target_urls["cls"]

        if "{keyword}" in target_url:
            target_url = target_url.replace("{keyword}", keyword)

        tab.listen.start("/api/sw")
        tab.get(target_url)
        data_packet = tab.listen.wait(timeout=10)

        if not bool(data_packet):
            tab.close()
            return self._cls_spider(keyword)

        response = data_packet.response.body
        data = response.get("data").get("depth").get("data")

        result = list()
        index = 0
        for item in data:
            if index >= self.slice:
                continue

            _id = item.get("id")
            _url = f"https://www.cls.cn/detail/{_id}"
            title = item.get("title")
            # 获取时间戳并转换
            timestamp = item.get("time") or item.get("ctime") or item.get("created_at")
            if timestamp and isinstance(timestamp, (int, float)):
                pub_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(timestamp))
            else:
                pub_time = time.strftime("%Y-%m-%d %H:%M:%S")
            
            try:
                new_tab = self.page.new_tab(_url)
                time.sleep(1)
                article = new_tab.s_ele(".:detail-content").child(".m-b-10").text
                
                _dict = {
                    "title": title, 
                    "article": article, 
                    "target_url": _url,
                    "pub_time": pub_time
                }
                new_tab.close()
            except Exception as e:
                continue

            index += 1
            result.append(_dict)

        tab.close()
        return result


    def _ljb_spider(self, keyword: str):
        print(f"科技日报[{keyword}]采集中...")
        tab = self._create_empty_tab()
        target_url = self.target_urls["ljb"]

        if "{keyword}" in target_url:
            target_url = target_url.replace("{keyword}", keyword)

        tab.listen.start("xy/Search.do")
        tab.get(target_url)
        data_packet = tab.listen.wait(timeout=10)

        if not bool(data_packet):
            tab.close()
            return self._ljb_spider(keyword)

        response = data_packet.response.body

        result = list()
        article_list = response.get("article")[:self.slice]
        for item in article_list:
            title = item.get("title")
            article = item.get("enpcontent")
            _url = item.get("url")

            _dict = {"title": title, "article": article, "target_url": target_url}
            result.append(_dict)

        tab.close()
        return result

    # def check_page_structure(self, url):
    #     """检查页面结构"""
    #     tab = self._create_empty_tab()
    #     try:
    #         tab.get(url)
    #         time.sleep(2)
    #
    #         # 打印页面标题
    #         print("页面标题:", tab.title)
    #
    #         # 打印所有可能的新闻容器
    #         containers = tab.s_eles("div")
    #         for container in containers[:5]:  # 只打印前5个
    #             print("\n容器类名:", container.cls_name)
    #             print("容器文本预览:", container.text[:100])
    #
    #         # 检查API请求
    #         requests = tab.listen.all
    #         for req in requests:
    #             if "api" in req.url:
    #                 print("\nAPI请求:", req.url)
    #                 print("请求方法:", req.method)
    #
    #     except Exception as e:
    #         print(f"检查页面结构时出错: {str(e)}")
    #     finally:
    #         tab.close()



if __name__ == "__main__":
    pass
