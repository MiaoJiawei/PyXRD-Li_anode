# Py-XRD-D002
## Introduction
XRD衍射数据自动分析

石墨+硅内标样：测定石墨材料D002层间距

    1. D002 (Å) -- 石墨[002]层间距
    2. G% -- 石墨化度
    3. Graphite [002] Peak (deg) -- 石墨[002]峰位
    4. Graphite [002] FWHM (deg) -- 石墨[002]半峰宽 (实测值)
    5. Silicon [111] Peak (deg) -- 硅[111]峰位
    6. Silicon [111] FWHM (deg) -- 硅[111]半峰宽 (实测值)
    7. Graphite [002] FWHM NET.(deg) -- 石墨[002]半峰宽 (反卷积数值计算)
    8. Graphite [002] Lc NET.(Å) -- 石墨[002]Lc值 (反卷积数值计算)
    9. Graphite [002] Lc JIS(Å) -- 石墨[002]Lc值 (依据JIS R 7651:2027)

纳米硅：测定硅[111]晶向晶粒尺寸

石墨：测定OI值（[004]强度/[110]强度）

## Credits
- [xylib](http://github.com/wojdyr/xylib/) - 数据读取模块部分使用该项目相关逻辑
- [deepseek](https://www.deepseek.com/) - 部分代码使用AI构建

## Reference
- [A Correction for the Alpha-1, Alpha-2 Doublet in tin Measurement of Width of X-ray Diffraction Lines](https://iopscience.iop.org/article/10.1088/0950-7671/25/7/125)
- [The Synthesis of X‐Ray Spectrometer Line Profiles with Application to Crystallite Size Measurements](https://doi.org/10.1063/1.1721595)
- [JIS R 7651:2027](https://kikakurui.com/r7/R7651-2007-01.html)
