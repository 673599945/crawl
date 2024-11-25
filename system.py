# 系统导入
import os
from PyQt6.QtCore import QThread, pyqtSignal

# 本地UI导入
from ui.mainwindow import Ui_mainwindow
from qframelesswindow import FramelessWindow, StandardTitleBar
from qfluentwidgets import MessageBox

# 核心功能导入
from core.handler import Handler
from core.utils import DataReader



class SpiderWorker(QThread):
    finished = pyqtSignal()  # 完成信号
    progress = pyqtSignal(str)  # 进度信号
    error = pyqtSignal(str)  # 错误信号

    def __init__(self, keywords,target_urls):
        super().__init__()
        self.keywords = keywords
        self.target_urls = target_urls
        self.handler = None

    def run(self):
        try:
            self.handler = Handler(self.keywords,self.target_urls)
            self.handler.progress_signal.connect(self.on_progress)  # 连接进度信号
            self.handler.run_spider()
            self.finished.emit()
        except Exception as e:
            self.error.emit(str(e))

    def on_progress(self, msg):
        self.progress.emit(msg)


class System:
    def __init__(self):
        super().__init__()

        # main window ui
        self.mw_widget = FramelessWindow()
        self.mw_ui = Ui_mainwindow()
        self.mw_ui.setupUi(self.mw_widget)
        self.mw_widget.setTitleBar(StandardTitleBar(self.mw_widget))
        self.mw_widget.titleBar.raise_()

        # data initialization
        self.title = ""
        self.brief = ""
        self.summary = ""
        self.keywords = ""
        self.target_urls = {} # 目标URL字典

        self.handler_thread = None
        cache_path = "D:\爬虫程序\crawl\spider_cache"
        self.reader = DataReader(cache_path)
        self.spider_worker = None

        self.__mw_init()
        self.__init_config()

    def __mw_init(self):
        self.mw_widget.resize(900, 675)
        self.mw_ui.lineEdit_keywords.searchSignal.connect(self.search)

    def __init_config(self):
        # 设置默认的API密钥
        os.environ.setdefault("DASHSCOPE_API_KEY", "sk-c9afb103f90f4fc79a0db9796d3cec8f")
        os.environ.setdefault("ARTICLE_SPIDER_NUMBER", "10")  # 每次采集的新闻文章数量

        # 添加去重相关配置
        os.environ.setdefault("TITLE_SIMILARITY_THRESHOLD", "0.8")  # 标题相似度阈值
        os.environ.setdefault("DEDUP_CACHE_TIME", "86400")  # 去重缓存时间(秒)，默认24小时

    def search(self):
        if self.mw_ui.lineEdit_keywords.text() == "":
            w = MessageBox(
                title='警告',
                content='请输入关键词',
                parent=self.mw_widget
            )
            w.exec()
            return
            
        # 禁用搜索按钮，防止重复点击
        self.mw_ui.lineEdit_keywords.setEnabled(False)
        
        self.keywords = self.mw_ui.lineEdit_keywords.text()
        self.update_target_urls()
        self.mw_ui.label_search.setText(f"{self.keywords}")
        self.run_spider()

    def update_target_urls(self):
        # 初始化目标 URL 字典
        self.target_urls = {}
        
        # 定义所有新闻源的 URL
        urls = {
            "sina": "https://search.sina.com.cn/news",
            "jin10": "https://search.jin10.com/?keyword={keyword}",
            "rmw": "http://search.people.cn/",
            "rbw": "https://newssearch.chinadaily.com.cn/cn/search?query={keyword}",
            "xhw": "https://so.news.cn/#search/0/{keyword}/1/0",
            "cfw": "https://so.eastmoney.com/news/s?keyword={keyword}",
            "cls": "https://www.cls.cn/searchPage?keyword={keyword}&type=depth",
            "ljb": "https://search.kjrb.com.cn:8888/founder/NewSearchServlet.do?siteID=1&content={keyword}"
        }

        # 检查各个新闻源的复选框状态并添加到字典中
        if self.mw_ui.checkBox_cfw.isChecked():
            self.target_urls["cfw"] = urls["cfw"]
        if self.mw_ui.checkBox_sina.isChecked():
            self.target_urls["sina"] = urls["sina"]
        if self.mw_ui.checkBox_jin10.isChecked():
            self.target_urls["jin10"] = urls["jin10"]
        if self.mw_ui.checkBox_rmw.isChecked():
            self.target_urls["rmw"] = urls["rmw"]
        if self.mw_ui.checkBox_rbw.isChecked():
            self.target_urls["rbw"] = urls["rbw"]
        if self.mw_ui.checkBox_xhw.isChecked():
            self.target_urls["xhw"] = urls["xhw"]
        if self.mw_ui.checkBox_cls.isChecked():
            self.target_urls["cls"] = urls["cls"]
        if self.mw_ui.checkBox_ljb.isChecked():
            self.target_urls["ljb"] = urls["ljb"]

        # 如果没有选择任何新闻源，默认选择东方财富网
        if not self.target_urls:
            self.target_urls["cfw"] = urls["cfw"]
            self.mw_ui.checkBox_cfw.setChecked(True)

    def run_spider(self):
        # 创建并启动工作线程
        self.spider_worker = SpiderWorker(self.keywords.split(','),self.target_urls)
        
        # 连接信号
        self.spider_worker.finished.connect(self.on_spider_finished)
        self.spider_worker.progress.connect(self.on_spider_progress)
        self.spider_worker.error.connect(self.on_spider_error)
        
        # 启动线程
        self.spider_worker.start()

    def on_spider_finished(self):
        # 爬虫完成后的处理
        self.mw_ui.lineEdit_keywords.setEnabled(True)
        self.update()
        w = MessageBox(
            title='提示',
            content='数据采集完成！',
            parent=self.mw_widget
        )
        w.exec()

    def on_spider_progress(self, msg):
        # 更新进度信息
        self.mw_ui.label_progress.setText(msg)

    def on_spider_error(self, error_msg):
        # 处理错误
        self.mw_ui.lineEdit_keywords.setEnabled(True)
        w = MessageBox(
            title='错误',
            content=f'发生错误：{error_msg}',
            parent=self.mw_widget
        )
        w.exec()

    def update(self):
        # 更新数据
        try:
            data = self.reader.get_organized_data()
            
            # 清空现有列表
            self.mw_ui.listWidget_title.clear()
            
            # 添加所有主题到listWidget
            for title in data.keys():
                self.mw_ui.listWidget_title.addItem(title)
            
            # 连接列表项选择信号（如果还没连接）
            if not hasattr(self, '_list_connected'):
                self.mw_ui.listWidget_title.currentItemChanged.connect(self._on_topic_selected)
                self.listWidget_title = True
            
            # 默认选择第一项
            if self.mw_ui.listWidget_title.count() > 0:
                self.mw_ui.listWidget_title.setCurrentRow(0)
                
        except Exception as e:
            w = MessageBox(
                title='错误',
                content=f'更新数据失败：{str(e)}',
                parent=self.mw_widget
            )
            w.exec()

    def _on_topic_selected(self, current, previous):
        """处理主题选择变化"""
        if not current:
            return
            
        try:
            # 获取选中的主题
            selected_topic = current.text()
            
            # 获取数据
            data = self.reader.get_organized_data()
            topic_data = data.get(selected_topic, {})
            
            # 更新概要
            summary_text = topic_data.get("summary", [])
            self.mw_ui.textBrowser_brief.setText(summary_text)
            
            # 更新原始内容
            raw_content = topic_data.get("raw_content", [])
            content_text = ""
            
            # 格式化原始内容
            if isinstance(raw_content, list):
                for item in raw_content:
                    if isinstance(item, dict):
                        # 假设原始内容是字典格式，包含标题和内容
                        content_text += f"标题：{item.get('title', '')}\n"
                        content_text += f"内容：{item.get('article', '')}\n"
                        content_text += f"来源：{item.get('detail_url', '')}\n"
                        content_text += f"时间：{item.get('pub_time', '')}\n"
                        content_text += "-" * 50 + "\n\n"
                    else:
                        # 如果是其他格式，直接添加
                        content_text += str(item) + "\n\n"
            else:
                # 如果不是列表，直接转换为字符串
                content_text = str(raw_content)

            self.mw_ui.textBrowser_content.setText(content_text)
            
        except Exception as e:
            w = MessageBox(
                title='错误',
                content=f'更新内容失败：{str(e)}',
                parent=self.mw_widget
            )
            w.exec()

    def show(self):
        self.mw_widget.show()
