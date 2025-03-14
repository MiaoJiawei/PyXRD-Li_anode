import numpy as np

from numpy.polynomial.chebyshev import Chebyshev
from scipy.interpolate import interp1d
from scipy.signal import convolve
from scipy.signal import savgol_filter
from scipy.optimize import curve_fit
from scipy.optimize import fsolve

# 定义 Split-Pearson VII 函数
def split_pearson_vii(x: np.ndarray, a: float, x0: float, w_L: float, w_R: float, m: float) -> np.ndarray:
    # Split-Pearson VII 函数：两侧具有同形状参数的 Pearson VII 函数
    return np.where(
        x <= x0,
        a / (1 + (4 * (x - x0)**2 / w_L**2) * (2**(1/m) - 1))**m,
        a / (1 + (4 * (x - x0)**2 / w_R**2) * (2**(1/m) - 1))**m
    )

# 定义 Lorentzian 函数
def lorentzian(x: np.ndarray, amplitude: float, center: float, sigma: float) -> np.ndarray:
    # Lorentzian 函数
    return amplitude / (1 + ((x - center) / sigma)**2)

# 定义 Gaussian 函数
def gaussian(x: np.ndarray, amplitude: float, center: float, sigma: float) -> np.ndarray:
    # Gaussian 函数
    return amplitude * np.exp(-((x - center) / sigma)**2)

# 定义 Pseudo-Voigt 函数
def pseudo_voigt(x: np.ndarray, amplitude: float, center: float, sigma: float, eta: float) -> np.ndarray:
    # Pseudo Voigt 函数：高斯函数和洛伦兹函数的线性组合
    return eta * lorentzian(x, amplitude, center, sigma) + (1 - eta) * gaussian(x, amplitude, center, sigma)

# 定义二阶切比雪夫多项式
def chebyshev(x: np.ndarray, c0, c1, c2):
    # 二阶切比雪夫多项式
    return Chebyshev([c0, c1, c2])(x)

#定义单峰拟合函数（Split-Pearson VII 峰 + 二阶切比雪夫背景）
def single_peak(x: np.ndarray, a1, x01, w_L1, w_R1, m1, c0, c1, c2):
    # Split-Pearson VII 峰 + 二阶切比雪夫背景
    return split_pearson_vii(x, a1, x01, w_L1, w_R1, m1) + chebyshev(x, c0, c1, c2)

# 定义双峰拟合函数（Split-Pearson VII 峰 + 二阶切比雪夫背景）
def double_peak(x, a1, x01, w_L1, w_R1, m1, a2, x02, w_L2, w_R2, m2, c0, c1, c2):
    # 两个 Split-Pearson VII 峰 + 二阶切比雪夫背景
    return (split_pearson_vii(x, a1, x01, w_L1, w_R1, m1) + split_pearson_vii(x, a2, x02, w_L2, w_R2, m2) + chebyshev(x, c0, c1, c2))

# 定义多峰拟合函数（Split-Pearson VII 峰 + 二阶切比雪夫背景）
def oi_peak(x, a1, x01, w_L1, w_R1, m1, a2, x02, w_L2, w_R2, m2, a3, x03, w_L3, w_R3, m3, a4, x04, w_L4, w_R4, m4, a5, x05, w_L5, w_R5, m5, c0, c1, c2):
    # 5个 Split-Pearson VII 峰 + 二阶切比雪夫背景
    return (split_pearson_vii(x, a1, x01, w_L1, w_R1, m1) + split_pearson_vii(x, a2, x02, w_L2, w_R2, m2) + split_pearson_vii(x, a3, x03, w_L3, w_R3, m3) + split_pearson_vii(x, a4, x04, w_L4, w_R4, m4) + split_pearson_vii(x, a5, x05, w_L5, w_R5, m5) + chebyshev(x, c0, c1, c2))

# 计算 Split-Pearson VII 函数的半峰宽
def calculate_fwhm_spv(w_L, w_R, m):
    a = 1
    x0 = 0
    left_x = fsolve(lambda x: split_pearson_vii(x, a, x0, w_L, w_R, m) - (a / 2), x0 - abs(w_L))[0]
    right_x = fsolve(lambda x: split_pearson_vii(x, a, x0, w_L, w_R, m) - (a / 2), x0 + abs(w_R))[0]
    return right_x - left_x

# 计算 Pseudo-Voigt 函数的半峰宽
def calculate_fwhm_pv(sigma, eta):
    fwhm_lorentz = 2 * sigma  # 洛伦兹成分的半峰宽
    fwhm_gauss = 2 * sigma * np.sqrt(2 * np.log(2))  # 高斯成分的半峰宽
    return eta * fwhm_lorentz + (1 - eta) * fwhm_gauss

# 迭代法Kα2校正
def correct_ka2(two_theta, intensity, lambda_ka1=1.54056, lambda_ka2=1.54439, iterations=8):
    sort_idx = np.argsort(two_theta)
    two_theta_sorted = two_theta[sort_idx]
    intensity_sorted = intensity[sort_idx]
    
    theta_rad = np.radians(two_theta_sorted / 2)
    sin_theta_ka1 = np.sin(theta_rad)
    sin_theta_ka2 = sin_theta_ka1 * (lambda_ka1 / lambda_ka2)
    
    valid = sin_theta_ka2 <= 1.0
    theta_ka2_rad = np.arcsin(sin_theta_ka2, where=valid, out=np.zeros_like(sin_theta_ka2))
    two_theta_ka2 = np.degrees(theta_ka2_rad) * 2
    
    corrected_intensity = intensity_sorted.copy()
    for _ in range(iterations):
        bg_fill = np.mean(corrected_intensity[:30])
        ka1_interp = interp1d(two_theta_sorted, corrected_intensity, kind='linear', bounds_error=False, fill_value=bg_fill)
        ka2_intensity = ka1_interp(two_theta_ka2) * 0.5
        ka2_intensity *= valid
        corrected_intensity = np.clip(intensity_sorted - ka2_intensity, 0, None)
    
    return two_theta_sorted, corrected_intensity

# G[002]+Si[111] 双峰模型拟合数据
def fit_data_d002(x, y):
    p0 = [max(y), 26.5, 0.1, 0.1, 1.5, max(y), 28.4, 0.1, 0.1, 1.5, 0, 0, 0]
    try:
        popt, _ = curve_fit(double_peak, x, y, p0=p0)
        return popt
    except RuntimeError as e:
        print(f"拟合失败: {e}")
        return None
    
# G[002]+Si[111] 双峰曲线计算
def fit_peak_d002(x, popt):
    fitted_curve = double_peak(x, *popt)
    background = chebyshev(x, popt[10], popt[11] , popt[12])
    graphite_peak = split_pearson_vii(x, popt[0], popt[1], popt[2], popt[3], popt[4])
    silicon_peak = split_pearson_vii(x, popt[5], popt[6], popt[7], popt[8], popt[9])

    # 反卷积计算净石墨半峰宽
    graphite_peak_shift = split_pearson_vii(x, popt[5], popt[6], popt[2], popt[3], popt[4])
    initial_guess = [1.0, 27.0, 0.1]
    def convolution_model(x, amplitude, center, sigma):
        gtaphite_net = lorentzian(x, amplitude, center, sigma)
        return convolve(silicon_peak, gtaphite_net, mode='same')
    params, _ = curve_fit(convolution_model, x, graphite_peak_shift, p0=initial_guess)
    fwhm = calculate_fwhm_pv(params[2], 1) # 锁定洛伦兹函数

    return fitted_curve, background, graphite_peak, silicon_peak, fwhm

# Si[111] 单峰模型拟合数据
def fit_data_sifwhm(x, y):
    p0 = [max(y)-min(y), 28.4, 0.3, 0.3, 0.6, 0, 0, 0]
    y = savgol_filter(y, 25, 3)
    try:
        popt, _ = curve_fit(single_peak, x, y, p0=p0)
        return popt, y
    except RuntimeError as e:
        print(f"拟合失败: {e}")
        return None, y

# Si[111] 单峰曲线计算
def fit_peak_sifwhm(x, popt):
    fitted_curve = single_peak(x, *popt)
    background = chebyshev(x, popt[5], popt[6] , popt[7])
    silicon_peak = split_pearson_vii(x, popt[0], popt[1], popt[2], popt[3], popt[4])
    return fitted_curve, background, silicon_peak

# OI值 多峰曲线拟合数据
def fit_data_oi(x, y):
    p0 = [max(y), 54.23, 0.1, 0.1, 1.5, max(y), 56.12, 0.1, 0.1, 1.5, max(y), 69.14, 0.1, 0.1, 1.5, max(y), 76.38, 0.1, 0.1, 1.5, max(y), 77.55, 0.1, 0.1, 1.5, 0, 0, 0]
    try:
        popt, _ = curve_fit(oi_peak, x, y, p0=p0)
        return popt
    except RuntimeError as e:
        print(f"拟合失败: {e}")
        return None
    
# OI值 多峰曲线计算
def fit_peak_oi(x, popt):
    fitted_curve = oi_peak(x, *popt)
    g004_peak = split_pearson_vii(x, popt[0], popt[1], popt[2], popt[3], popt[4])
    si311_peak = split_pearson_vii(x, popt[5], popt[6], popt[7], popt[8], popt[9])
    si400_peak = split_pearson_vii(x, popt[10], popt[11], popt[12], popt[13], popt[14])
    si331_peak = split_pearson_vii(x, popt[15], popt[16], popt[17], popt[18], popt[19])
    g110_peak = split_pearson_vii(x, popt[20], popt[21], popt[22], popt[23], popt[24])
    background = chebyshev(x, popt[25], popt[26] , popt[27])

    return fitted_curve, background, g004_peak, si311_peak, si400_peak, si331_peak, g110_peak