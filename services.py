import requests
import time

class FiveSimService:
    BASE_URL = "https://5sim.net/v1"
    
    def __init__(self, api_key):
        self.api_key = api_key
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {self.api_key}',
            'Accept': 'application/json'
        })
    
    def get_user_profile(self):
        response = self.session.get(f"{self.BASE_URL}/user/profile")
        response.raise_for_status()
        return response.json()
    
    def buy_number(self, country, service):
        response = self.session.get(
            f"{self.BASE_URL}/user/buy/activation/{country}/{service}"
        )
        response.raise_for_status()
        return response.json()
    
    def check_order(self, order_id):
        response = self.session.get(f"{self.BASE_URL}/user/check/{order_id}")
        response.raise_for_status()
        return response.json()
    
    def cancel_order(self, order_id):
        response = self.session.get(f"{self.BASE_URL}/user/cancel/{order_id}")
        response.raise_for_status()
        return response.json()
    
    def get_prices(self, country=None, service=None):
        url = f"{self.BASE_URL}/guest/prices"
        if country:
            url += f"/{country}"
            if service:
                url += f"/{service}"
        response = self.session.get(url)
        response.raise_for_status()
        return response.json()
