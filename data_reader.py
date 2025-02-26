import xml.dom.minidom
import xml.parsers.expat
import numpy as np

# 基础数据读取接口
class BaseReader:
    @staticmethod
    def read_data(file_path):
        raise NotImplementedError("必须实现read_data方法")

# .xrdml 读取模块
class XRDMLReader(BaseReader):
    @staticmethod
    def read_data(file_path):
        try:
            """读取.xrdml文件并返回处理后的数据"""
            DOMTree = xml.dom.minidom.parse(file_path)
            collection = DOMTree.documentElement
            scan_start = float(collection.getElementsByTagName('startPosition')[0].childNodes[0].data)
            scan_end = float(collection.getElementsByTagName('endPosition')[0].childNodes[0].data)
            if len(collection.getElementsByTagName('counts')) > 1:
                data_point = collection.getElementsByTagName('counts')[0].childNodes[0].data.split(" ")
            else:
                data_point = collection.getElementsByTagName('intensities')[0].childNodes[0].data.split(" ")
            scan_number = len(data_point)
            scan_step = (scan_end - scan_start) / (scan_number - 1)
            scan_x = np.array([scan_start + i * scan_step for i in range(scan_number)])
            scan_y = np.array([float(pt) for pt in data_point])
            return scan_x, scan_y
        except RuntimeError as e:
            print(f"读取失败: {e}")
            return None, None
        except xml.parsers.expat.ExpatError as e:
            return None, None

# .rd 读取模块
class PhilipsRDReader(BaseReader):
    @staticmethod
    def read_data(file_path):
        """读取.rd文件并返回处理后的数据"""
        with open(file_path, 'rb') as f:
            head = f.read(4)
            if head not in [b"V3RD", b"V5RD"]:
                raise ValueError("无效的RD文件")
            
            f.seek(214)
            x_step = np.frombuffer(f.read(8), dtype=np.float64)[0]
            x_start = np.frombuffer(f.read(8), dtype=np.float64)[0]
            x_end = np.frombuffer(f.read(8), dtype=np.float64)[0]
            
            pt_cnt = int((x_end - x_start) / x_step)
            f.seek(810 if head == b"V5RD" else 250)
            ycol = np.frombuffer(f.read(pt_cnt * 2), dtype=np.uint16)
            ycol = 0.01 * ycol * ycol
            
            xcol = np.linspace(x_start + x_step / 2, x_end - x_step / 2, pt_cnt)
            return xcol, ycol

# 文件读取工厂函数
def get_reader(file_type):
    """根据文件类型返回对应的读取器"""
    if file_type == "1":
        return PhilipsRDReader()
    elif file_type == "2":
        return XRDMLReader()
    else:
        raise ValueError("无效的文件类型选择")