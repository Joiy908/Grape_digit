import math
import random
from abc import ABC, abstractmethod
from datetime import datetime, timedelta, timezone

from influxdb_client import Point

from .influxdb import INFLUXDB_BUCKET, INFLUXDB_ORG, write_api
from .tools import TZ_UTC8, assert_china_time, assert_timezone_aware


# Base Sensor class
class Sensor(ABC):
    def __init__(self, id: str):
        self.id = id

    @abstractmethod
    def get_value(self, dt: datetime):
        """dt is a datetime object representing the current time"""
        pass


# Virtual Sensor class
class VirtualSensor(Sensor):
    def __init__(self, id: str, model_func):
        super().__init__(id)
        self.model_func = model_func

    def get_value(self, dt):
        "dt must be timezone-aware"
        # check if dt is UTC+8
        assert_timezone_aware(dt)
        dt = dt.astimezone(TZ_UTC8)  # Convert to Shanghai time (UTC+8)
        return self.model_func(dt)


# Helper functions
def get_time_of_day(dt: datetime):
    """Return time of day in hours (0-23.999) for datetime dt."""
    assert_china_time(dt)
    return dt.hour + dt.minute / 60 + dt.second / 3600


def hours_since_epoch(dt):
    """Convert datetime to hours since 2000-01-01 00:00."""
    assert_china_time(dt)
    epoch = datetime(2000, 1, 1, tzinfo=timezone.utc)
    return (dt - epoch).total_seconds() / 3600


# Temperature model with fixed parameters
def temperature_model(dt):
    """Air temperature model with diurnal, seasonal variation and noise."""
    assert_china_time(dt)
    T_mean = 10  # Average temperature (°C)
    A_diurnal = 7  # Diurnal amplitude (°C)
    t_max_diurnal = 13  # Peak time of day (1 PM)
    A_seasonal = 6  # Seasonal amplitude (°C)
    t_max_seasonal = 215  # Peak day of year (early August)
    noise_std = 1  # Noise standard deviation

    day_of_year = dt.timetuple().tm_yday
    time_of_day = get_time_of_day(dt)
    diurnal = A_diurnal * math.cos(2 * math.pi * (time_of_day - t_max_diurnal) / 24)
    seasonal = A_seasonal * math.cos(2 * math.pi * (day_of_year - t_max_seasonal) / 365.25)
    noise = random.gauss(0, noise_std)
    return T_mean + diurnal + seasonal + noise


# Humidity model with fixed parameters
def humidity_model(dt):
    """Humidity model with diurnal variation and noise."""
    assert_china_time(dt)
    H_mean = 60  # Average humidity (%)
    A_diurnal_H = 20  # Diurnal amplitude (%)
    t_max_H = 4  # Peak time of day (4 AM)
    noise_std = 5  # Noise standard deviation

    time_of_day = get_time_of_day(dt)
    diurnal = A_diurnal_H * math.cos(2 * math.pi * (time_of_day - t_max_H) / 24)
    noise = random.gauss(0, noise_std)
    return H_mean + diurnal + noise


# Light intensity model with fixed parameters
def light_model(dt):
    """Light intensity model with daylight variation and noise."""
    assert_china_time(dt)
    max_light = 1000  # Maximum light intensity (lux)
    sunrise = 6  # Sunrise time (6 AM)
    sunset = 18  # Sunset time (6 PM)
    noise_std = 50  # Noise standard deviation

    time_of_day = get_time_of_day(dt)
    if time_of_day < sunrise or time_of_day > sunset:
        return 0
    total_daylight = sunset - sunrise
    x = 2 * math.pi * (time_of_day - sunrise) / total_daylight
    light = max_light * (1 - math.cos(x)) / 2
    noise = random.gauss(0, noise_std)
    return max(0, light + noise)


# Soil temperature model with fixed parameters
def soil_temperature_model(dt):
    """Soil temperature model with lag, seasonal variation and noise."""
    assert_china_time(dt)
    T_mean_soil = 15  # Average soil temperature (°C)
    A_diurnal_soil = 5  # Diurnal amplitude (°C)
    t_max_diurnal_air = 14  # Peak air temp time (2 PM)
    delta_t = 3  # Time lag (hours)
    A_seasonal_soil = 5  # Seasonal amplitude (°C)
    t_max_seasonal_soil = 196  # Peak day of year (mid-July)
    noise_std = 1  # Noise standard deviation

    day_of_year = dt.timetuple().tm_yday
    time_of_day = get_time_of_day(dt)
    diurnal = A_diurnal_soil * math.cos(2 * math.pi * (time_of_day - (t_max_diurnal_air + delta_t)) / 24)
    seasonal = A_seasonal_soil * math.cos(2 * math.pi * (day_of_year - t_max_seasonal_soil) / 365.25)
    noise = random.gauss(0, noise_std)
    return T_mean_soil + diurnal + seasonal + noise


# Wind speed model with fixed parameters
def wind_speed_model(dt):
    """Wind speed model with monthly average, diurnal variation, and noise."""
    assert_china_time(dt)
    monthly_data = {1: 6.7, 2: 6.9, 3: 7.2, 4: 7.5, 5: 7.7, 6: 7.9, 7: 7.7, 8: 7.3, 9: 6.7, 10: 6.4, 11: 6.5, 12: 7.0}
    A_diurnal_W = 2.5  # Diurnal amplitude (mph)
    t_max_W = 14  # Peak time of day (2 PM)
    noise_std = 1  # Noise standard deviation

    month = dt.month
    time_of_day = get_time_of_day(dt)
    W_mean = monthly_data[month]
    diurnal = A_diurnal_W * math.sin(2 * math.pi * (time_of_day - t_max_W) / 24)
    random_component = random.gauss(0, noise_std)
    return max(0, W_mean + diurnal + random_component)


# Soil moisture model with fixed parameters
def soil_moisture_model(dt):
    """Soil moisture model using harmonic regression with fixed parameters and noise."""
    assert_china_time(dt)
    fitted_params = [0.2843, -0.0011, 0.0004, 0.0227, -0.0722]  # Fixed regression coefficients
    noise_std = 0.05  # Noise standard deviation

    t = hours_since_epoch(dt)
    beta0, beta1, beta2, beta3, beta4 = fitted_params
    daily_cycle = beta1 * math.cos(2 * math.pi * t / 24) + beta2 * math.sin(2 * math.pi * t / 24)
    yearly_cycle = beta3 * math.cos(2 * math.pi * t / (24 * 365.25)) + beta4 * math.sin(2 * math.pi * t / (24 * 365.25))
    noise = random.gauss(0, noise_std)
    moisture = beta0 + daily_cycle + yearly_cycle + noise
    return max(0, min(1, moisture))


# Define virtual sensors with fixed model parameters
virtual_temp_sensor = VirtualSensor('v_temp_1', temperature_model)
virtual_humidity_sensor = VirtualSensor('v_humidity_1', humidity_model)
virtual_light_sensor = VirtualSensor('v_light_1', light_model)
virtual_soil_temp_sensor = VirtualSensor('v_soil_temp_1', soil_temperature_model)
virtual_wind_speed_sensor = VirtualSensor('v_wind_1', wind_speed_model)
virtual_soil_moisture_sensor = VirtualSensor('v_soil_moisture_1', soil_moisture_model)


# Generate Line Protocol file
def generate_line_protocol_file(filename='data/2024_now_environment_data.txt'):
    start_time = datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
    end_time = datetime.now(timezone.utc)
    interval = timedelta(minutes=60)

    sensors = [
        ('temperature', virtual_temp_sensor),
        ('humidity', virtual_humidity_sensor),
        ('light_intensity', virtual_light_sensor),
        ('soil_temperature', virtual_soil_temp_sensor),
        ('wind_speed', virtual_wind_speed_sensor),
        ('soil_moisture', virtual_soil_moisture_sensor),
    ]

    with open(filename, 'w', newline='\n') as f:
        current_time = start_time
        while current_time <= end_time:
            timestamp_ns = int(current_time.timestamp() * 1_000_000_000)
            for field_name, sensor in sensors:
                value = sensor.get_value(current_time)
                line = f'env_data,sensor_id={sensor.id} {field_name}={value:.6f} {timestamp_ns}\n'
                f.write(line)
            current_time += interval

    print(f'Line Protocol file generated: {filename}')


def write_to_influxdb():
    current_time = datetime.now(timezone.utc)

    sensors = [
        ('temperature', virtual_temp_sensor),
        ('humidity', virtual_humidity_sensor),
        ('light_intensity', virtual_light_sensor),
        ('soil_temperature', virtual_soil_temp_sensor),
        ('wind_speed', virtual_wind_speed_sensor),
        ('soil_moisture', virtual_soil_moisture_sensor),
    ]

    for field_name, sensor in sensors:
        value = sensor.get_value(current_time)
        point = (
            Point('env_data').tag('sensor_id', sensor.id).field(field_name, float(f'{value:.6f}')).time(current_time)
        )
        write_api.write(bucket=INFLUXDB_BUCKET, org=INFLUXDB_ORG, record=point)

    print(f'Written data at {current_time.isoformat()}')


# Run the script
if __name__ == '__main__':
    # generate_line_protocol_file()
    import time

    import schedule

    schedule.every(5).seconds.do(write_to_influxdb)
    while True:
        schedule.run_pending()
        time.sleep(1)
