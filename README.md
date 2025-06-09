# Py-XRD-D002
## Introduction
XRD衍射数据自动分析
## Usage
1. 选择文件类型
    1. .rd (Philips RD文件，适用于V3设备，其余设备可能需要修改对应偏移量)
    2. .xrdml (帕纳科XRD文件，不同设备版本可能需要修改dr模块中对应xml元素)
2. 选择计算模块
    1. D002 (石墨D002)
    2. Si_FWHM (纳米硅FWHM)
    3. OI (石墨OI值 —— I004/I110)
3. 选择是否输出过程信息 (即拟合曲线及分峰结果)
    1. Yes
    2. No
## Output
### 石墨+硅内标样：测定石墨材料D002层间距

    1. D002 (Å) -- 石墨[002]层间距
    2. G% -- 石墨化度
    3. Graphite [002] Peak (deg) -- 石墨[002]峰位
    4. Graphite [002] FWHM (deg) -- 石墨[002]半峰宽 (实测值)
    5. Silicon [111] Peak (deg) -- 硅[111]峰位
    6. Silicon [111] FWHM (deg) -- 硅[111]半峰宽 (实测值)
    7. Graphite [002] FWHM NET.(deg) -- 石墨[002]半峰宽 (反卷积数值计算)
    8. Graphite [002] Lc NET.(Å) -- 石墨[002]Lc值 (反卷积数值计算)
    9. Graphite [002] FWHM JIS(deg) -- 石墨[002]半峰宽 (依据JIS R 7651:2007)
    10.Graphite [002] Lc JIS(Å) -- 石墨[002]Lc值 (依据JIS R 7651:2007)

### 纳米硅：测定硅[111]晶向晶粒尺寸

    1. Silicon [111] Peak (deg) -- 硅[111]峰位
    2. Silicon [111] FWHM (deg) -- 硅[111]半峰宽 (实测值)

### 石墨：测定OI值（[004]强度/[110]强度）

    1. Graphite OI value (-) -- 石墨OI值(I004/I110)
    2. Graphite [004] Peak (deg) -- 石墨[004]峰位
    3. Graphite [004] Intensity (counts) -- 石墨[004]峰强
    4. Graphite [004] FWHM (deg) -- 石墨[004]半峰宽
    5. Graphite [110] Peak (deg) -- 石墨[110]峰位
    6. Graphite [110] Intensity (counts) -- 石墨[110]峰强
    7. Graphite [110] FWHM (deg) -- 石墨[110]半峰宽

## Credits
- [xylib](http://github.com/wojdyr/xylib/) - 数据读取模块部分使用该项目相关逻辑
- [deepseek](https://www.deepseek.com/) - 部分代码使用AI构建

## Reference
- [A Correction for the Alpha-1, Alpha-2 Doublet in tin Measurement of Width of X-ray Diffraction Lines](https://iopscience.iop.org/article/10.1088/0950-7671/25/7/125)
- [The Synthesis of X‐Ray Spectrometer Line Profiles with Application to Crystallite Size Measurements](https://doi.org/10.1063/1.1721595)
- [炭素材料の格子定数及び結晶子の大きさ測定方法 JIS R 7651:2007](https://kikakurui.com/r7/R7651-2007-01.html)
