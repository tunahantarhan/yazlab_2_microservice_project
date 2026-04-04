from locust import HttpUser, task, between
import requests

# her simülasyon kullanıcısının tek tek token isteği atması yerine
# locust sadece 1 kere token alır ve onu tüm kullanıcalara verir.
try:
    print("Sisteme giriş yapılıyor, global token alınıyor...")
    response = requests.post("http://localhost:8002/auth/login", json={"username": "admin", "password": "1234"})
    GLOBAL_TOKEN = response.json().get("access_token")
    print("Global Token başarıyla alındı!")
except Exception as e:
    print("Token alınamadı.", e)
    GLOBAL_TOKEN = ""

class DispatcherLoadTest(HttpUser):
    # kullanıcıların iki istek arası bekleme süresi
    wait_time = between(1, 3)
    
    # biletlere bakma ihtimali daha yüksek ağırlık (%66.7 - %33.3)
    @task(2)
    def get_tickets(self):
        headers = {"Authorization": f"Bearer {GLOBAL_TOKEN}"}
        self.client.get("/tickets", headers=headers, name="Biletleri Listele")

    # kullanıcılara bakma ihtimali daha yüksek ağırlık (%66.7 - %33.3)
    @task(1)
    def get_users(self):
        headers = {"Authorization": f"Bearer {GLOBAL_TOKEN}"}
        self.client.get("/users", headers=headers, name="Kullanıcıları Listele")