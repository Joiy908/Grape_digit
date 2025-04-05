import unittest
from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient

from src.api_app import app  # Replace 'your_app_file' with actual filename
from src.tools import utc_to_shanghai_time


class APITestCase(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        self.valid_timestamp: str = utc_to_shanghai_time(datetime.now(timezone.utc))

    def test_create_record_success(self):
        # Test successful record creation
        record_data = {
            'type': 'irrigation',
            'amount': 10.5,
            'details': 'Test irrigation',
            'timestamp': self.valid_timestamp,
        }

        response = self.client.post('/api/v1/records', json=record_data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'status': 'success'})

    def test_create_record_missing_required_field(self):
        # Test with missing required field (amount)
        invalid_data = {'type': 'fertilizer', 'timestamp': self.valid_timestamp}

        response = self.client.post('/api/v1/records', json=invalid_data)
        self.assertEqual(response.status_code, 422)  # Unprocessable Entity
        self.assertIn('amount', response.json()['detail'][0]['loc'])

    def test_create_record_invalid_type(self):
        # Test with invalid type value
        invalid_data = {'type': 'invalid_type', 'amount': 5.0, 'timestamp': self.valid_timestamp}

        response = self.client.post('/api/v1/records', json=invalid_data)
        self.assertEqual(response.status_code, 422)
        self.assertIn('type', response.json()['detail'][0]['loc'])

    def test_get_records_success(self):
        # First create a record
        create_data = {'type': 'irrigation', 'amount': 10.5, 'timestamp': self.valid_timestamp}
        self.client.post('/api/v1/records', json=create_data)

        # Test getting records
        params = {
            'start_time': (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat(),
            'type': 'fertilizer',
        }

        response = self.client.get('/api/v1/records', params=params)
        self.assertEqual(response.status_code, 200)
        response_json = response.json()
        self.assertEqual(response_json['status'], 'success')
        # print(response_json)
        self.assertIsInstance(response_json['data'], list)

    def test_get_records_invalid_time_format(self):
        # Test with invalid timestamp format
        params = {'start_time': 'invalid-time', 'end_time': self.valid_timestamp, 'type': 'fertilizer'}

        response = self.client.get('/api/v1/records', params=params)
        self.assertEqual(response.status_code, 422)
        self.assertIn('start_time', response.json()['detail'][0]['loc'])

    def test_get_records_invalid_type(self):
        # Test with invalid type value
        params = {'start_time': self.valid_timestamp, 'end_time': self.valid_timestamp, 'type': 'invalid_type'}

        response = self.client.get('/api/v1/records', params=params)
        self.assertEqual(response.status_code, 422)
        self.assertIn('type', response.json()['detail'][0]['loc'])

    def test_create_record_optional_details(self):
        # Test creating record without details (optional field)
        record_data = {'type': 'fertilizer', 'amount': 20.0, 'timestamp': self.valid_timestamp}

        response = self.client.post('/api/v1/records', json=record_data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'status': 'success'})


if __name__ == '__main__':
    unittest.main()
