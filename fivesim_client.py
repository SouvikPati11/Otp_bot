import requests
import os
from dotenv import load_dotenv

load_dotenv()

FIVESIM_API_KEY = os.getenv("FIVESIM_API_KEY")
FIVESIM_BASE_URL = "https://5sim.net/v1"

if not FIVESIM_API_KEY:
    print("Warning: FIVESIM_API_KEY not found in .env file.")
    # raise ValueError("FIVESIM_API_KEY not found in .env file.")


class FiveSimClient:
    def __init__(self, api_key=None):
        self.api_key = api_key or FIVESIM_API_KEY
        if not self.api_key:
            raise ValueError("5sim API key must be provided.")
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Accept": "application/json",
        }

    def _request(self, method, endpoint, params=None, json_data=None):
        url = f"{FIVESIM_BASE_URL}{endpoint}"
        try:
            response = requests.request(method, url, headers=self.headers, params=params, json=json_data, timeout=20)
            response.raise_for_status() # Raise an exception for bad status codes
            return response.json()
        except requests.exceptions.HTTPError as e:
            print(f"HTTP Error: {e.response.status_code} - {e.response.text}")
            # Try to parse JSON error message from 5sim
            try:
                error_data = e.response.json()
                message = error_data.get("message", e.response.text)
            except ValueError:
                message = e.response.text
            raise Exception(f"5sim API Error ({e.response.status_code}): {message}")
        except requests.exceptions.RequestException as e:
            print(f"Request Exception: {e}")
            raise Exception(f"5sim API Request failed: {e}")

    def get_user_balance(self):
        """ Fetches the user's balance on 5sim.net. """
        return self._request("GET", "/user/profile") # The 'balance' field is what we need

    def get_countries(self):
        """ Lists all available countries. """
        # 5sim docs say /guest/countries, let's try that
        # Using guest endpoint as it doesn't require auth and might be more stable for this
        try:
            response = requests.get(f"{FIVESIM_BASE_URL}/guest/countries", timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error fetching countries: {e}")
            # Fallback or default if API fails
            return {
                "russia": {"text_en": "Russia", "iso": "RU", "prefix": "7"},
                "kazakhstan": {"text_en": "Kazakhstan", "iso": "KZ", "prefix": "7"},
                "ukraine": {"text_en": "Ukraine", "iso": "UA", "prefix": "380"},
                "india": {"text_en": "India", "iso": "IN", "prefix": "91"},
            }


    def get_products(self, country, operator="any"):
        """
        Fetches product prices and availability for a specific country and operator.
        `country` should be the short name (e.g., "russia", "india").
        `operator` can be "any" or a specific operator code.
        """
        return self._request("GET", f"/guest/products/{country}/{operator}")

    def buy_activation_number(self, country, operator, service_code):
        """
        Purchases an activation number.
        `country`: short name (e.g., "russia")
        `operator`: e.g., "any", "tele2", "mts"
        `service_code`: product code (e.g., "instagram", "telegram")
        """
        endpoint = f"/user/buy/activation/{country}/{operator}/{service_code}"
        return self._request("GET", endpoint) # 5sim uses GET for buy

    def check_order(self, order_id):
        """
        Checks the status of an order and retrieves SMS if available.
        `order_id`: The ID of the order received from the buy request.
        """
        return self._request("GET", f"/user/check/{order_id}")

    def finish_order(self, order_id):
        """
        Finishes an order. Useful if OTP is received and used.
        """
        return self._request("GET", f"/user/finish/{order_id}")

    def cancel_order(self, order_id):
        """
        Cancels an order. Use if no SMS received or number is bad.
        This should trigger a refund on 5sim's side.
        """
        return self._request("GET", f"/user/cancel/{order_id}")

    def ban_order(self, order_id):
        """
        Marks an order as 'ban', often used synonymously with cancel if number is unusable.
        """
        return self._request("GET", f"/user/ban/{order_id}")

# Example usage (for testing this file directly)
if __name__ == "__main__":
    if not FIVESIM_API_KEY or FIVESIM_API_KEY == "YOUR_5SIM_API_KEY_HERE":
        print("Please set your FIVESIM_API_KEY in .env to test fivesim_client.py")
    else:
        client = FiveSimClient()
        try:
            print("Fetching 5sim Balance:")
            balance_info = client.get_user_balance()
            print(balance_info)

            print("\nFetching Countries:")
            countries = client.get_countries()
            print(list(countries.keys())[:5]) # Print first 5 country codes

            print("\nFetching Products for India (any operator):")
            # Example: Fetch products for India. Find a valid service from 5sim.net for testing.
            # Common services: "telegram", "whatsapp", "instagram", "google"
            # The service name must be exactly as listed by 5sim (e.g. 'microsoft' not 'Microsoft')
            products_india = client.get_products("india", "any")
            if products_india:
                # Print details for a common service if available
                if "telegram" in products_india:
                    print("Telegram (India):", products_india["telegram"])
                elif "google" in products_india: # google, youtube, gmail
                    print("Google (India):", products_india["google"])
                else:
                    print("Telegram/Google not found for India, printing first available product:")
                    first_product_key = next(iter(products_india))
                    print(f"{first_product_key} (India):", products_india[first_product_key])
            else:
                print("No products found for India.")

        except Exception as e:
            print(f"An error occurred: {e}")