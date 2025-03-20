import math
import random
from datetime import datetime, timedelta

# Base Sensor class
class Sensor:
    def get_value(self, t):
        raise NotImplementedError("Subclasses must implement get_value(t)")

# Helper functions for time calculations
def get_current_datetime(t):
    """Convert t (hours since 2000-01-01 00:00:00) to datetime object."""
    epoch = datetime(2000, 1, 1)
    return epoch + timedelta(hours=t)

def get_day_of_year(t):
    """Return day of the year (1-365 or 366) for time t."""
    dt = get_current_datetime(t)
    return dt.timetuple().tm_yday

def get_month_number(t):
    """Return month number (1-12) for time t."""
    dt = get_current_datetime(t)
    return dt.month

def get_day_number(t):
    """Return day of the month for time t."""
    dt = get_current_datetime(t)
    return dt.day

def get_time_of_day(t):
    """Return time of day in hours (0-23.999) for time t."""
    return t % 24

# Virtual Sensor class
class VirtualSensor(Sensor):
    def __init__(self, model_func, params):
        self.model_func = model_func
        self.params = params

    def get_value(self, t):
        return self.model_func(t, **self.params)


def temperature_model(t, T_mean, A_diurnal, t_max_diurnal, A_seasonal, t_max_seasonal, noise_std=1):
    """Air temperature model with diurnal, seasonal variation and noise."""
    day_of_year = get_day_of_year(t)
    time_of_day = get_time_of_day(t)
    diurnal = A_diurnal * math.cos(2 * math.pi * (time_of_day - t_max_diurnal) / 24)
    seasonal = A_seasonal * math.cos(2 * math.pi * (day_of_year - t_max_seasonal) / 365.25)
    noise = random.gauss(0, noise_std)  # 生成正态分布的随机噪声
    return T_mean + diurnal + seasonal + noise

# def humidity_model(t, H_mean, A_diurnal_H, t_max_H):
#     """Humidity model with diurnal variation."""
#     time_of_day = get_time_of_day(t)
#     diurnal = A_diurnal_H * math.cos(2 * math.pi * (time_of_day - t_max_H) / 24)
#     return H_mean + diurnal

# def light_model(t, max_light, sunrise, sunset):
#     """Light intensity model with daylight variation."""
#     time_of_day = get_time_of_day(t)
#     if time_of_day < sunrise or time_of_day > sunset:
#         return 0
#     total_daylight = sunset - sunrise
#     x = 2 * math.pi * (time_of_day - sunrise) / total_daylight
#     return max_light * (1 - math.cos(x)) / 2

# def soil_temperature_model(t, T_mean_soil, A_diurnal_soil, t_max_diurnal_air, delta_t, A_seasonal_soil, t_max_seasonal_soil):
#     """Soil temperature model with lag and seasonal variation."""
#     day_of_year = get_day_of_year(t)
#     time_of_day = get_time_of_day(t)
#     diurnal = A_diurnal_soil * math.cos(2 * math.pi * (time_of_day - (t_max_diurnal_air + delta_t)) / 24)
#     seasonal = A_seasonal_soil * math.sin(2 * math.pi * (day_of_year - t_max_seasonal_soil) / 365.25)
#     return T_mean_soil + diurnal + seasonal

# def rainfall_model(t, monthly_rainfall, rainy_days):
#     """Rainfall model with monthly distribution and cumulative tracking."""
#     month = get_month_number(t)
#     day = get_day_number(t)
#     time_of_day = get_time_of_day(t)
    
#     # Monthly rainfall data (inches) and rainy days
#     monthly_data = {
#         1: (4.46, 10), 2: (4.21, 9), 3: (2.88, 8), 4: (1.35, 5), 5: (0.88, 3),
#         6: (0.23, 1), 7: (0.01, 0.2), 8: (0.05, 0.5), 9: (0.08, 1), 10: (1.30, 3),
#         11: (2.19, 6), 12: (4.51, 10)
#     }
    
#     total_rainfall_inches, num_rainy_days = monthly_data[month]
#     total_rainfall_mm = total_rainfall_inches * 25.4  # Convert to mm
    
#     # Simulate rainy days (simplified: first N days of month are rainy)
#     daily_rainfall_mm = total_rainfall_mm / num_rainy_days if num_rainy_days > 0 else 0
#     is_rainy_day = day <= num_rainy_days
    
#     # Rainfall occurs from 6 AM to 6 PM
#     if is_rainy_day and 6 <= time_of_day <= 18:
#         hourly_rainfall = daily_rainfall_mm / 12  # Spread over 12 hours
#         return hourly_rainfall
#     return 0

# def wind_speed_model(t, monthly_wind_speed):
#     """Wind speed model with monthly average, diurnal variation, and noise."""
#     month = get_month_number(t)
#     time_of_day = get_time_of_day(t)
    
#     # Monthly wind speed data (mph)
#     monthly_data = {
#         1: 6.7, 2: 6.9, 3: 7.2, 4: 7.5, 5: 7.7, 6: 7.9,
#         7: 7.7, 8: 7.3, 9: 6.7, 10: 6.4, 11: 6.5, 12: 7.0
#     }
    
#     W_mean = monthly_data[month]
#     A_diurnal_W = 2.5
#     t_max_W = 14  # Peak at 2 PM
#     diurnal = A_diurnal_W * math.sin(2 * math.pi * (time_of_day - t_max_W) / 24)
#     random_component = random.gauss(0, 1)  # Normal distribution, std dev 1 mph
#     return max(0, W_mean + diurnal + random_component)  # Ensure non-negative

# Define virtual sensors with parameters
virtual_temp_sensor = VirtualSensor(temperature_model, {
    "T_mean": 15, "A_diurnal": 7, "t_max_diurnal": 14,
    "A_seasonal": 6, "t_max_seasonal": 196
})

# virtual_humidity_sensor = VirtualSensor(humidity_model, {
#     "H_mean": 60, "A_diurnal_H": 20, "t_max_H": 4
# })

# virtual_light_sensor = VirtualSensor(light_model, {
#     "max_light": 1000, "sunrise": 6, "sunset": 18
# })

# virtual_soil_temp_sensor = VirtualSensor(soil_temperature_model, {
#     "T_mean_soil": 15, "A_diurnal_soil": 5, "t_max_diurnal_air": 14,
#     "delta_t": 3, "A_seasonal_soil": 5, "t_max_seasonal_soil": 196
# })

# virtual_rainfall_sensor = VirtualSensor(rainfall_model, {
#     "monthly_rainfall": None, "rainy_days": None  # Data embedded in model
# })

# virtual_wind_speed_sensor = VirtualSensor(wind_speed_model, {
#     "monthly_wind_speed": None  # Data embedded in model
# })

# # Example usage with InfluxDB integration
# from influxdb_client import InfluxDBClient, Point, WritePrecision
# from influxdb_client.client.write_api import SYNCHRONOUS
# import time

# # InfluxDB configuration
# url = "http://localhost:8086"
# token = "your_token"
# org = "your_org"
# bucket = "your_bucket"

# client = InfluxDBClient(url=url, token=token, org=org)
# write_api = client.write_api(write_options=SYNCHRONOUS)

# def get_current_t():
#     """Calculate current time in hours since 2000-01-01 00:00:00."""
#     epoch = datetime(2000, 1, 1)
#     now = datetime.now()
#     delta = now - epoch
#     return delta.total_seconds() / 3600

# def collect_and_store_data():
#     t = get_current_t()
#     data = {
#         "temperature": virtual_temp_sensor.get_value(t),
#         "humidity": virtual_humidity_sensor.get_value(t),
#         "light_intensity": virtual_light_sensor.get_value(t),
#         "soil_temperature": virtual_soil_temp_sensor.get_value(t),
#         "rainfall": virtual_rainfall_sensor.get_value(t),
#         "wind_speed": virtual_wind_speed_sensor.get_value(t)
#     }
    
#     point = Point("environment_data") \
#         .tag("device_id", "device_001") \
#         .tag("location", "vineyard_A")
    
#     for key, value in data.items():
#         point.field(key, value)
    
#     point.time(datetime.now(), WritePrecision.NS)
#     write_api.write(bucket=bucket, record=point)
#     print(f"Data written at t={t}: {data}")

# # Run simulation every 15 minutes
# import schedule

# schedule.every(15).minutes.do(collect_and_store_data)

# while True:
#     schedule.run_pending()
#     time.sleep(1)