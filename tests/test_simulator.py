import unittest
from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient

from src.api_app import app  # Replace 'your_app_file' with actual filename
from src.tools import utc_to_shanghai_time
from src.simulator import VirtualSensor, light_model


class SimulatorTest(unittest.TestCase):
    def setUp(self):
        self.virtual_light_sensor = VirtualSensor('v_light_1', light_model)
        

    def test_virual_light_model(self):
        china_zero_time = datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc) - timedelta(hours=8)
        self.assertEqual(self.virtual_light_sensor.get_value(china_zero_time), 0.0)
