import unittest
from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient

from src.api_app import app, IrrigationEvent, Event
from src.tools import TZ_UTC8


class APITestCase(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        self.valid_timestamp: str = datetime.now(TZ_UTC8)

    def test_create_irrigation_success(self):
        # Test successful record creation
        record = IrrigationEvent(outlet='6号口', vineyard_id='1', amount='10', area='3', timestamp=self.valid_timestamp)

        response = self.client.post('/api/v1/irrigation_events', content=record.model_dump_json())
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'status': 'success'})

    def test_get_irrigation_success(self):
        # Test getting records
        response = self.client.get('/api/v1/irrigation_events')
        self.assertEqual(response.status_code, 200)
        response_json = response.json()
        self.assertEqual(response_json['status'], 'success')
        print(response_json)
        # self.assertIsInstance(response_json['data'], list)

    def test_create_events_success(self):
        # Test successful record creation
        record = Event(event_type='施肥', vineyard_id='1', details='施钾肥3kg', timestamp=self.valid_timestamp)

        response = self.client.post('/api/v1/events', content=record.model_dump_json())
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'status': 'success'})

    def test_get_events_success(self):
        res = self.client.get('/api/v1/events')
        self.assertEqual(res.status_code, 200)
        res_json = res.json()
        self.assertEqual(res_json['status'], 'success')
        print(res_json)

if __name__ == '__main__':
    unittest.main()
