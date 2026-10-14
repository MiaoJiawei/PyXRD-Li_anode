import xml.dom.minidom
import xml.parsers.expat
import numpy as np
import struct

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
            if collection.getElementsByTagName('counts') != []:
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
        
# 理学 .raw 读取模块
class RigakuRawReader(BaseReader):
    @staticmethod
    def read_data(file_path):
        try:
            with open(file_path, 'rb') as f:
                header = f.read(3158)
                f.seek(0x0B92)
                start_angle = struct.unpack('<f', f.read(4))[0]
                f.seek(0x0B96)
                end_angle = struct.unpack('<f', f.read(4))[0]
                f.seek(0x0B9A)
                step = struct.unpack('<f', f.read(4))[0]
                num_points = int(round((end_angle - start_angle) / step)) + 1
                scan_x = np.arange(start_angle, end_angle + step/2, step)

                f.seek(0x0C56)
                scan_y = []
                for _ in range(num_points):
                    value = struct.unpack('<f', f.read(4))[0]
                    scan_y.append(value)
                scan_y = np.array(scan_y)
            return scan_x, scan_y
        except RuntimeError as e:
            print(f"读取失败: {e}")
            return None, None

# Bruker .raw (V4, RAW4.00) 读取模块
class BrukerRawV4Reader(BaseReader):
    """Bruker/Siemens RAW V4（文件头 magic 为 "RAW4.00"）读取器。

    文件布局（本批 0962 数据逆向并交叉校验得到）：
      1) 固定头 61 字节（0x00~0x3C）：magic + 日期/时间 + 若干标量；
      2) 参数块链（自 0x3D 起），每块为
         [u32 tag][u32 size][u32 id][24 字节名称][size-36 字节载荷]；
         其中 tag=50 为驱动参数块（id=1 为 Theta、id=2 为 2Theta，载荷 +20 处为 double 值），
         tag=0 为扫描描述块（第 2、3 字段均等于数据点数 N）；
      3) 扫描描述块 +0x48/+0x50/+0x58 处为 double 起始 2θ、double 步长、u32 点数；
      4) 数据段位于文件末尾，为 N 个 little-endian float32 强度值。
    """

    MAGIC = b"RAW4.00"
    FIXED_HEADER_SIZE = 0x3D
    # 扫描描述块内字段相对块起始的偏移
    OFFSET_START = 0x48
    OFFSET_STEP = 0x50
    OFFSET_COUNT = 0x58

    @staticmethod
    def _param_block_ends_at(raw, search_from, position):
        """完整性自校验：参数区内应存在恰好结束于 position（=数据段起点）的合法参数块。

        文件数据段按「末尾 4N 字节」定位，若文件被截断或结构不同，会整体错位而读出错误 2θ 轴，
        因此在此做一次结构校验，校验不过则拒绝返回数据。
        """
        for offset in range(search_from, position - 35):
            tag, size, _ = struct.unpack_from('<III', raw, offset)
            if tag in (0, 10, 30, 50) and size >= 36 and offset + size == position:
                return True
        return False

    @staticmethod
    def read_data(file_path):
        try:
            with open(file_path, 'rb') as f:
                raw = f.read()

            if raw[:len(BrukerRawV4Reader.MAGIC)] != BrukerRawV4Reader.MAGIC:
                # 仅保留可打印 ASCII，避免非文本文件头在控制台打印时报编码错误
                version = ''.join(chr(b) if 32 <= b < 127 else '?' for b in raw[:8])
                raise ValueError(f"不是 Bruker RAW4.00 文件（文件头为 \"{version}\"）")

            # 遍历顶层参数块链：收集驱动参数（2Theta/Theta），定位扫描描述块
            offset = BrukerRawV4Reader.FIXED_HEADER_SIZE
            drive_params = {}
            descriptor = None
            while offset + 36 <= len(raw):
                tag, size, _ = struct.unpack_from('<III', raw, offset)
                name = raw[offset + 12:offset + 36].split(b'\x00')[0].decode('latin1', 'replace')
                if tag == 50 and name in ('2Theta', 'Theta'):
                    drive_params[name] = struct.unpack_from('<d', raw, offset + 36 + 20)[0]
                elif tag == 0:
                    # 扫描描述块：第 2、3 字段同为数据点数
                    if struct.unpack_from('<I', raw, offset + 4)[0] == struct.unpack_from('<I', raw, offset + 8)[0]:
                        descriptor = offset
                        break
                if size < 36 or offset + size > len(raw):
                    raise ValueError("参数块链损坏（块长度非法）")
                offset += size

            if descriptor is None:
                raise ValueError("未找到扫描描述块")

            num_points = struct.unpack_from('<I', raw, descriptor + BrukerRawV4Reader.OFFSET_COUNT)[0]
            start_angle = struct.unpack_from('<d', raw, descriptor + BrukerRawV4Reader.OFFSET_START)[0]
            step = struct.unpack_from('<d', raw, descriptor + BrukerRawV4Reader.OFFSET_STEP)[0]

            # 交叉校验：点数、2Theta/Theta 驱动参数必须自洽，否则不返回（避免给出错误 2θ 轴）
            count_in_block = struct.unpack_from('<I', raw, descriptor + 4)[0]
            if num_points <= 0 or num_points != count_in_block:
                raise ValueError(f"数据点数不自洽（描述块 {count_in_block}，字段 {num_points}）")
            if not np.isfinite(start_angle) or not np.isfinite(step) or step <= 0:
                raise ValueError(f"扫描参数非法（起始 {start_angle}，步长 {step}）")
            if '2Theta' in drive_params and abs(drive_params['2Theta'] - start_angle) > 1e-6:
                raise ValueError(f"2Theta 驱动参数 {drive_params['2Theta']} 与起始角 {start_angle} 不一致")
            if 'Theta' in drive_params and abs(drive_params['Theta'] - start_angle / 2) > 1e-6:
                raise ValueError(f"Theta 驱动参数 {drive_params['Theta']} 与起始角 {start_angle} 不一致")

            data_start = len(raw) - num_points * 4
            if data_start <= descriptor + 36:
                raise ValueError(f"数据段起点非法（{data_start} 不在描述块之后）")
            if not BrukerRawV4Reader._param_block_ends_at(raw, descriptor, data_start):
                raise ValueError("参数区末端与数据段起点不吻合（文件可能被截断或结构不同）")

            scan_y = np.frombuffer(raw, dtype='<f4', count=num_points, offset=data_start).astype(float)
            scan_x = start_angle + step * np.arange(num_points)
            return scan_x, scan_y
        except (OSError, RuntimeError, ValueError, struct.error) as e:
            print(f"读取失败 {file_path}: {e}")
            return None, None

# 文件读取工厂函数
def get_reader(file_type):
    """根据文件类型返回对应的读取器"""
    if file_type == "1":
        return PhilipsRDReader()
    elif file_type == "2":
        return XRDMLReader()
    elif file_type == "3":
        return RigakuRawReader()
    elif file_type == "4":
        return BrukerRawV4Reader()
    else:
        raise ValueError("无效的文件类型选择")
