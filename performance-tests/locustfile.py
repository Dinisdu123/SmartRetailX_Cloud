from locust import HttpUser, task, between
import json
import random

class UserManagementUser(HttpUser):
    host = "http://127.0.0.1:8001"
    wait_time = between(1, 3)
    token = None

    def on_start(self):
        email = f"loadtest_{random.randint(1,99999)}@example.com"
        self.client.post("/users/register", json={
            "name": "Load Test User",
            "email": email,
            "password": "testpassword123"
        })
        response = self.client.post("/users/login", json={
            "email": email,
            "password": "testpassword123"
        })
        if response.status_code == 200:
            self.token = response.json()["access_token"]

    @task(3)
    def login(self):
        self.client.post("/users/login", json={
            "email": "john@example.com",
            "password": "password123"
        })

    @task(2)
    def get_profile(self):
        if self.token:
            self.client.get("/users/profile", headers={
                "Authorization": f"Bearer {self.token}"
            })

    @task(1)
    def health_check(self):
        self.client.get("/health")


class ProductCatalogueUser(HttpUser):
    host = "http://127.0.0.1:8002"
    wait_time = between(1, 2)

    @task(5)
    def get_all_products(self):
        self.client.get("/products")

    @task(3)
    def get_products_by_category(self):
        self.client.get("/products?category=Electronics")

    @task(2)
    def search_products(self):
        self.client.get("/products?search=laptop")

    @task(2)
    def get_products_price_filter(self):
        self.client.get("/products?minPrice=50&maxPrice=500")

    @task(1)
    def health_check(self):
        self.client.get("/health")


class OrderProcessingUser(HttpUser):
    host = "http://127.0.0.1:8003"
    wait_time = between(1, 3)
    token = None

    def on_start(self):
        response = self.client.post(
            "http://127.0.0.1:8001/users/login",
            json={
                "email": "john@example.com",
                "password": "password123"
            }
        )
        if response.status_code == 200:
            self.token = response.json()["access_token"]

    @task(3)
    def get_orders(self):
        if self.token:
            self.client.get("/orders", headers={
                "Authorization": f"Bearer {self.token}"
            })

    @task(1)
    def health_check(self):
        self.client.get("/health")