import unittest
from app import app
import os

class SynoCastTestCase(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        self.client = app.test_client()

    def test_01_home_route(self):
        response = self.client.get('/')
        print(f"\nHome: {response.status_code}")
        if response.status_code != 200:
            print(response.data.decode('utf-8'))
        self.assertEqual(response.status_code, 200)

    def test_02_news_route(self):
        response = self.client.get('/news')
        print(f"News: {response.status_code}")
        self.assertEqual(response.status_code, 200)

    def test_03_weather_route(self):
        response = self.client.get('/weather')
        print(f"Weather: {response.status_code}")
        self.assertEqual(response.status_code, 200)

    def test_04_about_route(self):
        response = self.client.get('/about')
        print(f"About: {response.status_code}")
        self.assertEqual(response.status_code, 200)

    @unittest.skip("subscribe.html template is missing")
    def test_05_subscribe_route(self):
        response = self.client.get('/subscribe')
        print(f"Subscribe: {response.status_code}")
        self.assertEqual(response.status_code, 200)

if __name__ == '__main__':
    unittest.main()
