from locust import HttpUser, task, between

class DispatcherLoadTest(HttpUser):
    # kullanıcıların iki istek arası bekleme süresi
    wait_time = between(1, 3)

    # auth. için gerekli "şifre"
    headers = {"Authorization": "Bearer valid-token"}

    @task(2) # biletlere bakma ihtimali daha yüksek ağırlık (%66.7 - %33.3)
    def get_tickets(self):
        self.client.get("/tickets", headers=self.headers, name="Biletleri Listele")

    @task(1) # kullanıcılara bakma ihtimali daha yüksek ağırlık (%66.7 - %33.3)
    def get_users(self):
        self.client.get("/users", headers=self.headers, name="Kullanıcıları Listele")