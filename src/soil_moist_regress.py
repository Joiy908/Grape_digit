import numpy as np
import pandas as pd
from scipy.optimize import leastsq
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

# 1. 时间转换函数
def hours_since_epoch(dt_str):
    """将时间字符串转换为自2000-01-01 00:00起的小时数"""
    epoch = datetime(2000, 1, 1)
    dt = datetime.strptime(dt_str, "%Y-%m-%dT%H:%M")
    return (dt - epoch).total_seconds() / 3600  # 转换为小时

# 2. 谐波回归模型
def harmonic_model(params, t):
    """谐波回归模型：包含每日和年度周期"""
    beta0, beta1, beta2, beta3, beta4 = params
    daily_cycle = beta1 * np.cos(2 * np.pi * t / 24) + beta2 * np.sin(2 * np.pi * t / 24)
    yearly_cycle = beta3 * np.cos(2 * np.pi * t / (24 * 365.25)) + beta4 * np.sin(2 * np.pi * t / (24 * 365.25))
    return beta0 + daily_cycle + yearly_cycle

def residuals(params, t, data):
    """计算模型与数据的残差"""
    return harmonic_model(params, t) - data



def fit_model(df) -> np.ndarray:
    # 将时间转换为小时数
    t = df["hours"].values
    moisture = df["soil_moisture"].values

    # 4. 初始参数猜测
    initial_params = [0.3, 0.05, 0.05, 0.1, 0.1]  # [平均值, 日周期cos, 日周期sin, 年周期cos, 年周期sin]

    # 5. 拟合模型
    result = leastsq(residuals, initial_params, args=(t, moisture))
    fitted_params = result[0]

    # 6. 输出结果
    print("拟合参数:")
    print(f"平均湿度 (beta0): {fitted_params[0]:.4f}")
    print(f"日周期 cos 幅度 (beta1): {fitted_params[1]:.4f}")
    print(f"日周期 sin 幅度 (beta2): {fitted_params[2]:.4f}")
    print(f"年周期 cos 幅度 (beta3): {fitted_params[3]:.4f}")
    print(f"年周期 sin 幅度 (beta4): {fitted_params[4]:.4f}")
    return fitted_params



def visualize_daily(df, start_index: int = 0, fitted_params: np.ndarray = None):
    """可视化某一天的土壤湿度数据"""
    day_start_idx = start_index  # 第一天的起始索引（假设数据从2024-01-01 00:00开始）
    day_t = df["hours"].values[day_start_idx:day_start_idx + 24]  # 提取24小时
    day_moisture = df["soil_moisture"].values[day_start_idx:day_start_idx + 24]
    fitted_values = harmonic_model(fitted_params, day_t)  # 使用拟合参数计算拟合值
    day_fitted = fitted_values[day_start_idx:day_start_idx + 24]

    plt.figure(figsize=(10, 6))
    plt.plot(day_t, day_moisture, 'b-', label='real soil moisture')
    plt.plot(day_t, day_fitted, 'r--', label='fitted soil moisture')
    plt.xlabel('hours since 2000-01-01')
    plt.ylabel('soil moisture')
    plt.legend()
    plt.grid(True)
    plt.show()

def visualize_annual(df, fitted_params: np.ndarray = None):
    """可视化全年土壤湿度数据"""
    t = df["hours"].values
    moisture = df["soil_moisture"].values
    fitted_values = harmonic_model(fitted_params, t)  # 使用拟合参数计算拟合值

    plt.figure(figsize=(12, 6))
    plt.plot(t, moisture, 'b-', label='real soil moisture', alpha=0.5)
    plt.plot(t, fitted_values, 'r--', label='fitted soil moisture')
    plt.xlabel('hours since 2000-01-01')
    plt.ylabel('soil moisture')
    plt.legend()
    plt.grid(True)
    plt.show()


if __name__ == "__main__":
    df = pd.read_csv('data/soil_moisture.csv')
    df["hours"] = df["time"].apply(hours_since_epoch)
    # params = fit_model(df)
    params = [0.2843, -0.0011, 0.0004, 0.0227, -0.0722]
    visualize_daily(df, start_index=0, fitted_params=params)
    visualize_annual(df, fitted_params=params)