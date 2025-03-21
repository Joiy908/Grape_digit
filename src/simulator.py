import math
import random
from datetime import datetime, timedelta 

# Base Sensor class
class Sensor:
    def get_value(self, dt: datetime):
        """dt is a datetime object representing the current time"""
        raise NotImplementedError("Subclasses must implement get_value(dt)")

# Helper function
def get_time_of_day(dt: datetime):
    """Return time of day in hours (0-23.999) for datetime dt."""
    return dt.hour + dt.minute / 60 + dt.second / 3600

def hours_since_epoch(dt):
    """将datetime转换为自2000-01-01 00:00起的小时数"""
    epoch = datetime(2000, 1, 1)
    return (dt - epoch).total_seconds() / 3600


# Virtual Sensor class
class VirtualSensor(Sensor):
    def __init__(self, model_func, params):
        self.model_func = model_func
        self.params = params

    def get_value(self, dt):
        return self.model_func(dt, **self.params)

# 温度模型
def temperature_model(dt, T_mean, A_diurnal, t_max_diurnal, A_seasonal, t_max_seasonal, noise_std=1):
    """Air temperature model with diurnal, seasonal variation and noise."""
    day_of_year = dt.timetuple().tm_yday
    time_of_day = get_time_of_day(dt)
    diurnal = A_diurnal * math.cos(2 * math.pi * (time_of_day - t_max_diurnal) / 24)
    seasonal = A_seasonal * math.cos(2 * math.pi * (day_of_year - t_max_seasonal) / 365.25)
    noise = random.gauss(0, noise_std)  # 生成正态分布的随机噪声
    return T_mean + diurnal + seasonal + noise

# 湿度模型
def humidity_model(dt, H_mean, A_diurnal_H, t_max_H, noise_std=5):
    """Humidity model with diurnal variation and noise."""
    time_of_day = get_time_of_day(dt)
    diurnal = A_diurnal_H * math.cos(2 * math.pi * (time_of_day - t_max_H) / 24)
    noise = random.gauss(0, noise_std)  # 生成正态分布的随机噪声
    return H_mean + diurnal + noise

# 光照模型
def light_model(dt, max_light, sunrise, sunset, noise_std=50):
    """Light intensity model with daylight variation and noise."""
    time_of_day = get_time_of_day(dt)
    if time_of_day < sunrise or time_of_day > sunset:
        return 0
    total_daylight = sunset - sunrise
    x = 2 * math.pi * (time_of_day - sunrise) / total_daylight
    light = max_light * (1 - math.cos(x)) / 2
    noise = random.gauss(0, noise_std)  # 生成正态分布的随机噪声
    return max(0, light + noise)  # 确保光照强度不小于0

# 土壤温度模型
def soil_temperature_model(dt, T_mean_soil, A_diurnal_soil, t_max_diurnal_air, delta_t, A_seasonal_soil, t_max_seasonal_soil, noise_std=1):
    """Soil temperature model with lag, seasonal variation and noise."""
    day_of_year = dt.timetuple().tm_yday
    time_of_day = get_time_of_day(dt)
    diurnal = A_diurnal_soil * math.cos(2 * math.pi * (time_of_day - (t_max_diurnal_air + delta_t)) / 24)
    seasonal = A_seasonal_soil * math.cos(2 * math.pi * (day_of_year - t_max_seasonal_soil) / 365.25)
    noise = random.gauss(0, noise_std)  # 生成正态分布的随机噪声
    return T_mean_soil + diurnal + seasonal + noise

# 风速模型
def wind_speed_model(dt, monthly_wind_speed, noise_std=1):
    """Wind speed model with monthly average, diurnal variation, and noise."""
    month = dt.month
    time_of_day = get_time_of_day(dt)
    # Monthly wind speed data (mph)
    monthly_data = {
        1: 6.7, 2: 6.9, 3: 7.2, 4: 7.5, 5: 7.7, 6: 7.9,
        7: 7.7, 8: 7.3, 9: 6.7, 10: 6.4, 11: 6.5, 12: 7.0
    }
    
    W_mean = monthly_data[month]
    A_diurnal_W = 2.5
    t_max_W = 14  # Peak at 2 PM
    diurnal = A_diurnal_W * math.sin(2 * math.pi * (time_of_day - t_max_W) / 24)
    random_component = random.gauss(0, noise_std)  # 生成正态分布的随机噪声
    return max(0, W_mean + diurnal + random_component)  # 确保风速不小于0

# 土壤湿度模型（使用谐波回归模型）
def soil_moisture_model(dt, fitted_params, noise_std=0.05):
    """Soil moisture model using harmonic regression with fitted parameters and noise."""
    t = hours_since_epoch(dt)  # 转换为小时数
    beta0, beta1, beta2, beta3, beta4 = fitted_params
    daily_cycle = beta1 * math.cos(2 * math.pi * t / 24) + beta2 * math.sin(2 * math.pi * t / 24)
    yearly_cycle = beta3 * math.cos(2 * math.pi * t / (24 * 365.25)) + beta4 * math.sin(2 * math.pi * t / (24 * 365.25))
    noise = random.gauss(0, noise_std)
    moisture = beta0 + daily_cycle + yearly_cycle + noise
    return max(0, min(1, moisture))  # 限制在0-1之间

# 定义虚拟传感器及其参数
virtual_temp_sensor = VirtualSensor(temperature_model, {
    "T_mean": 10, "A_diurnal": 7, "t_max_diurnal": 13,
    "A_seasonal": 6, "t_max_seasonal": 215, "noise_std": 1
})

virtual_humidity_sensor = VirtualSensor(humidity_model, {
    "H_mean": 60, "A_diurnal_H": 20, "t_max_H": 4, "noise_std": 5
})

virtual_light_sensor = VirtualSensor(light_model, {
    "max_light": 1000, "sunrise": 6, "sunset": 18, "noise_std": 50
})

virtual_soil_temp_sensor = VirtualSensor(soil_temperature_model, {
    "T_mean_soil": 15, "A_diurnal_soil": 5, "t_max_diurnal_air": 14,
    "delta_t": 3, "A_seasonal_soil": 5, "t_max_seasonal_soil": 196, "noise_std": 1
})

virtual_wind_speed_sensor = VirtualSensor(wind_speed_model, {
    "monthly_wind_speed": None, "noise_std": 1  # 数据嵌入模型中
})

fitted_params = [0.2843, -0.0011, 0.0004, 0.0227, -0.0722]
virtual_soil_moisture_sensor = VirtualSensor(soil_moisture_model, {
    "fitted_params": fitted_params,
    "noise_std": 0.05
})

def generate_line_protocol_file(filename="2024_now_environment_data.txt"):
    start_time = datetime(2024, 1, 1, 0, 0, 0)
    end_time = datetime.now()
    interval = timedelta(minutes=60)

    sensors = [
        ("v_temp_1", "temperature", virtual_temp_sensor),
        ("v_humidity_1", "humidity", virtual_humidity_sensor),
        ("v_light_1", "light_intensity", virtual_light_sensor),
        ("v_soil_temp_1", "soil_temperature", virtual_soil_temp_sensor),
        ("v_wind_1", "wind_speed", virtual_wind_speed_sensor),
        ("v_soil_moisture_1", "soil_moisture", virtual_soil_moisture_sensor)
    ]

    with open(filename, "w") as f:
        current_time = start_time
        while current_time <= end_time:
            # 将 datetime 转换为纳秒时间戳 (Unix epoch)
            timestamp_ns = int(current_time.timestamp() * 1_000_000_000)
            
            for sensor_id, field_name, sensor in sensors:
                value = sensor.get_value(current_time)
                # 格式化 Line Protocol 行
                line = f"env_data,sensor_id={sensor_id} {field_name}={value:.6f} {timestamp_ns}\n"
                f.write(line)
            
            current_time += interval

    print(f"Line Protocol 文件已生成：{filename}")

# 调用函数生成文件
if __name__ == "__main__":
    generate_line_protocol_file()