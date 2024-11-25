import datetime
import time
import json
import os
import glob


class DateUtil(object):

    @staticmethod
    def get_timestamp():
        return int(time.time())

    @staticmethod
    def timestamp_format(timestamp: int, format_str: str = '%Y-%m-%d %H:%M:%S'):
        return datetime.datetime.fromtimestamp(timestamp).strftime(format_str)


class DataReader:
    def __init__(self, json_directory):
        self.json_directory = json_directory
        
    def get_latest_json_files(self, num_files=3):
        json_files = glob.glob(os.path.join(self.json_directory, "*.json"))
        latest_files = sorted(json_files, key=os.path.getmtime, reverse=True)
        
        result = {
            'processed_data': None,  # 处理后数据
            'raw_data': None,   # 原始数据
            'titles': None    # 标题
        }
        
        for file in latest_files[:num_files]:
            print(f"Checking file: {file}")
            if '_processed_data' in file:
                result['processed_data'] = file
            elif '_raw_data' in file:
                result['raw_data'] = file
            elif '_titles' in file:
                result['titles'] = file

        print(f"Result: {result}")
        return result
    
    def _clean_data(self, item):
        if isinstance(item, dict):
            return {k: self._clean_data(v) for k, v in item.items()}
        elif isinstance(item, list):
            return [self._clean_data(i) for i in item]
        elif isinstance(item, str):
            return item.replace('\n', ' ')
        else:
            return item
    
    def _load_json_file(self, file_path):
        if not file_path:
            return None

        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return self._clean_data(data)
    
    def get_organized_data(self):
        """
        返回组织好的数据，包含主题、原始数据和处理后的数据
        返回格式：
        {
            "主题1": {
                "raw_content": [...],  # 原始数据
                "summary": [...],      # 处理后数据
            },
            "主题2": {
                "raw_content": [...],
                "summary": [...],
            },
            ...
        }
        """
        files = self.get_latest_json_files()

        processed_data = self._load_json_file(files['processed_data'])
        titles_data = self._load_json_file(files['titles'])
        raw_data = self._load_json_file(files['raw_data'])

        
        if not all([titles_data, raw_data, processed_data]):
            raise ValueError("无法加载所需的所有数据文件")
            
        organized_data = {}
        
        # 遍历titles_data中的主题列表
        for title in titles_data:
            title_name = title['title'] if isinstance(title, dict) else str(title)
            title_pub_time = title['pub_time'] if isinstance(title, dict) else None

            organized_data[title_name] = {
                "pub_time": title_pub_time
            }
            # 从raw_data中提取数据
            for raw in raw_data:
                for spider in raw['spider_data']:
                    for data in spider['data']:
                        if title_pub_time == data['pub_time']:
                            organized_data[title_name] = {
                                "raw_content": data['article']
                            }
                            break
            #从processed_data中提取数据
            for processed in processed_data:
                if title_pub_time == processed['pub_time']:
                    organized_data[title_name]['summary'] = processed['con']
                    break

            
        return organized_data



if __name__ == '__main__':
    try:
        # 创建DataReader实例
        reader = DataReader("C:\\Users\\21182\\Desktop\\low_sky_e_GUI\\spider_cache")

        # 测试获取最新JSON文件
        print("Testing get_latest_json_files():")
        latest_files = reader.get_latest_json_files()
        print("Latest files found:", latest_files)
        a=1
        print(a)

        # 测试获取组织好的数据
        print("Testing get_organized_data():")
        organized_data = reader.get_organized_data()

        # 打印组织好的数据结构
        print("\nOrganized Data Structure:")
        for topic, data in organized_data.items():
            print(f"\nTopic: {topic}")
            print(f"Number of raw content items: {len(data['raw_content'])}")
            print(f"Number of summary items: {len(data['summary'])}")

            # 打印第一条原始内容和总结示例（如果存在）
            if data['raw_content']:
                print("\nFirst raw content example:")
                print(str(data['raw_content'][0])[:200] + "...")

            if data['summary']:
                print("\nFirst summary example:")
                print(str(data['summary'][0])[:200] + "...")

    except Exception as e:
        print(f"Error occurred during testing: {str(e)}")