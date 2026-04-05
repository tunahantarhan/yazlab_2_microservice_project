# YazLab II Proje I - API Gateway (Dispatcher) ve Mikroservis Mimarisi

**Ekip Üyeleri:** 
- Tunahan Tarhan 
- Şükran Başaran

**Tarih:** 5 Nisan 2026

---

## İçindekiler
1. [Proje Hakkında ve Problem Tanımı](#giris)
2. [Kullanılan Teknolojiler](#teknolojiler)
3. [Sistem Mimarisi ve Bileşenler](#mimari)
   * [3.1. Ağ İzolasyonu (Network Isolation)](#izolasyon)
   * [3.2. Sınıf Yapıları (Veri Modelleri)](#sinif-yapilari)
4. [Yetkilendirme ve Güvenlik](#guvenlik)
5. [İstek Akışı (Sequence Diagram)](#istek)
6. [API Tasarımı ve Richardson Olgunluk Modeli (RMM) Seviye 2](#api)
   * [6.1. Algoritma ve Karmaşıklık Analizi](#karmasiklik)
7. [Test-Driven Development (TDD) Süreci](#tdd)
8. [Sistem Nasıl Çalıştırılır ve Test Edilir?](#kurulum)
9. [Performans Testleri ve Gözlemlenebilirlik](#performans)
   * [9.1. Locust Yük Testi Sonuçları](#locust)
   * [9.2. Grafana İzleme Paneli](#grafana)
10. [Sonuç ve Değerlendirme](#sonuc)

---

## 1. Proje Hakkında ve Problem Tanımı <a id="giris"></a>
Bu proje, Kocaeli Üniversitesi Bilişim Sistemleri Mühendisliği bölümü **Yazılım Geliştirme Laboratuvarı-II** dersi kapsamında geliştirilmiş bir mikroservis mimarisi uygulamasıdır.

Geleneksel monolitik uygulamalarda tüm iş mantığının tek bir yapı altında toplanması, sistem büyüdükçe bakım, geliştirme ve ölçekleme açısından çeşitli zorluklara yol açmaktadır. Bu projenin amacı, bağımsız çalışan servislerin (Auth, User, Ticket) trafiğini tek bir merkezden (Dispatcher/API Gateway) yöneten, ağ düzeyinde izole edilmiş, güvenli ve izlenebilir bir backend ekosistemi geliştirmektir. 

Sistem, bilet yönetimi senaryosu üzerine kurulmuştur. Kullanıcı işlemleri, kimlik doğrulama ve bilet işlemleri birbirinden bağımsız servisler halinde tasarlanarak hem ölçeklenebilirlik hem de servisler arası görev ayrımı (separation of concerns) sağlanmıştır. Ayrıca sistem, yetkisiz erişimleri engellemekte ve artan yük altında darboğazları tespit edebilmek için anlık metrikler (Prometheus/Grafana) sağlamaktadır.

**Literatür İncelemesi:**
Mikroservis mimarisi, Martin Fowler ve James Lewis'in tanımladığı üzere, tek bir uygulamayı küçük, bağımsız çalışan ve birbirleriyle hafif mekanizmalarla (genellikle HTTP REST API) iletişim kuran servisler paketi olarak geliştirme yaklaşımıdır. Bu projede literatürdeki RMM (Richardson Maturity Model) standartları temel alınarak, monolitik yapıların getirdiği sıkı bağımlılık (tight coupling) sorunu çözülmüş ve servisler arası veri izolasyonu sağlanmıştır.

---

## 2. Kullanılan Teknolojiler <a id="teknolojiler"></a>
Projenin geliştirilmesinde, test edilmesinde ve yayınlanmasında aşağıdaki teknolojiler kullanılmıştır:
- **Dil & Framework:** Python, FastAPI
- **Veritabanı:** MongoDB (Motor Asyncio)
- **Güvenlik:** JWT (JSON Web Token), Bcrypt
- **Orkestrasyon & Dağıtım:** Docker, Docker Compose
- **Test Araçları:** Pytest, Locust (Yük Testi)
- **Gözlem (Observability):** Prometheus, Grafana

---

## 3. Sistem Mimarisi ve Bileşenler <a id="mimari"></a>
Sistem toplamda bir Dispatcher, üç temel mikroservis, üç ayrı MongoDB veritabanı, bir Prometheus ve bir Grafana servisi olacak şekilde tasarlanmıştır.

- **Dispatcher (API Gateway):** Sistemin dış dünyaya açık tek giriş noktasıdır. İstemciden gelen istekleri ilgili servislere yönlendirir ve yetkilendirme kontrolü yapar.
- **Auth Service:** Kullanıcı giriş işlemlerini ve token doğrulamasını gerçekleştirir.
- **Ticket Service:** Bilet oluşturma, listeleme, güncelleme ve silme işlemlerini yönetir.
- **User Service:** Kullanıcı oluşturma, listeleme, güncelleme ve silme işlemlerini yönetir.
- **MongoDB:** Veri izolasyonunu sağlamak için her servisin kendine ait bağımsız bir veritabanı vardır.

```mermaid
graph TD
    Client((İstemci / Locust)) -->|Port 8002| Dispatcher[Dispatcher / API Gateway]
    
    subgraph S1 ["İç Ağ Yönlendirmesi (Network Isolation)"]
    Dispatcher -->|JWT Doğrulama| Auth[Auth Service]
    Dispatcher -->|CRUD İşlemleri| Ticket[Ticket Service]
    Dispatcher -->|CRUD İşlemleri| User[User Service]
    end
    
    subgraph S2 ["Veritabanı Katmanı"]
    Auth --> AuthDB[(Auth MongoDB)]
    Ticket --> TicketDB[(Ticket MongoDB)]
    User --> UserDB[(User MongoDB)]
    end
    
    subgraph S3 ["Gözlem ve İzleme"]
    Prometheus[Prometheus] -.->|/metrics| Dispatcher
    Grafana[Grafana Dashboard] -.->|Veri Kaynağı| Prometheus
    end
```

### 3.1. Ağ İzolasyonu (Network Isolation) <a id="izolasyon"></a>
Sistemde sadece `Dispatcher` servisi `8002` portu üzerinden dış dünyaya açıktır. Diğer tüm servisler ve veritabanları Docker `yazlab_net` iç ağı üzerinden haberleşmektedir. İstemciler doğrudan User, Auth veya Ticket servisine ulaşamazlar.

<br>
<img width="800" alt="Ağ İzolasyonu" src="https://github.com/user-attachments/assets/12cd5a3c-05cd-4787-9d2c-3b36bb2494bd" />
<br>

### 3.2. Sınıf Yapıları (Veri Modelleri) <a id="sinif-yapilari"></a>
Servisler arasındaki veri akışı Pydantic modelleri ile doğrulanmakta ve MongoDB'de aşağıdaki sınıf yapılarına uygun olarak saklanmaktadır:

```mermaid
classDiagram
    class TicketModel {
        +int id
        +string event_name
        +float price
        +boolean available
    }
    class UserModel {
        +int id
        +string username
        +string email
        +float balance
    }
    class Token {
        +string access_token
        +string token_type
    }
```

---

## 4. Yetkilendirme ve Güvenlik <a id="guvenlik"></a>
Sistemde yetkilendirme işlemleri merkezi olarak **Auth Service** üzerinden gerçekleştirilmektedir. Kullanıcı giriş yaptıktan sonra kendisine bir **JWT (JSON Web Token)** verilir. Bu token, istemcinin sonraki tüm isteklerinde `Authorization` header'ı içerisinde (Bearer) gönderilmektedir.

Dispatcher, gelen her istekte token doğrulaması yaparak:
- Geçerli token ise isteği ilgili mikroservise iletir.
- Geçersiz veya eksik token durumunda isteği reddeder (HTTP 401/403).

---

## 5. İstek Akışı (Sequence Diagram) <a id="istek"></a>
Dışarıdan gelen bir isteğin sistem içinde nasıl işlendiği aşağıdaki akış diyagramında gösterilmiştir. 

```mermaid
sequenceDiagram
    participant C as İstemci
    participant D as Dispatcher
    participant A as Auth Service
    participant T as Ticket/User Service
    
    C->>D: İstek At (Bearer Token)
    D->>A: /auth/verify (Token Kontrolü)
    
    alt Token Geçersiz
        A-->>D: HTTP 401/403
        D-->>C: HTTP 401/403 (Unauthorized)
    else Token Geçerli
        A-->>D: {valid: true, role: admin}
        D->>T: İlgili Rota İsteği
        T-->>D: HTTP 200/201 (JSON Yanıtı)
        D-->>C: HTTP 200/201 (İşlem Başarılı)
    end
```

---

## 6. API Tasarımı ve Richardson Olgunluk Modeli (RMM) Seviye 2 <a id="api"></a>
Projede RESTful API tasarım prensiplerine tam uyum sağlanmış ve kaynaklar URI üzerinden temsil edilmiştir. Parametre üzerinden işlem (örn: `/deleteUser?id=1`) yapılmamıştır.

**Kullanılan HTTP Metotları ve Rotasyonlar:**
* **Oluşturma (POST):** `/tickets` veya `/users` (HTTP 201 Created)
* **Okuma (GET):** `/tickets` veya `/users` (HTTP 200 OK)
* **Kısmi Güncelleme (PATCH):** `/tickets/{id}` veya `/users/{id}` (HTTP 200 OK) - *Sadece değişen veriler güncellenir.*
* **Silme (DELETE):** `/tickets/{id}` veya `/users/{id}` (HTTP 200 OK veya HTTP 404 Not Found)

**Kullanılan HTTP Durum Kodları:**
* `200 OK` / `201 Created` (Başarılı işlemler)
* `400 Bad Request` / `422 Unprocessable Entity` (Geçersiz veri formatı)
* `401 Unauthorized` (Token eksik veya geçersiz)
* `404 Not Found` (Kaynak bulunamadı)
* `500 Internal Server Error` (Sunucu hatası)

### 6.1. Algoritma ve Karmaşıklık Analizi (Time Complexity) <a id="karmasiklik"></a>
Projedeki algoritmalar ağırlıklı olarak CRUD (Create, Read, Update, Delete) operasyonlarından oluşmaktadır.
* **Okuma (Tekil ID ile):** MongoDB'de `id` alanı üzerinden yapılan spesifik aramalar ve token doğrulama algoritmaları **O(1)** zaman karmaşıklığına sahiptir.
* **Listeleme:** Tüm biletlerin veya kullanıcıların listelendiği uç noktalar, veritabanı boyutuna bağlı olarak **O(N)** karmaşıklığı ile çalışmaktadır.
* **Şifreleme:** Auth servisinde kullanılan `Bcrypt` algoritması, güvenlik amacıyla CPU'yu yoracak şekilde tasarlanmış olup (work factor), login işlemlerinde maliyetli ama güvenli bir **O(1)** sabiti ile çalışır.

---

## 7. Test-Driven Development (TDD) Süreci <a id="tdd"></a>
Dispatcher servisinin geliştirilmesinde Red-Green-Refactor döngüsü izlenmiştir. Tüm endpoint'ler `pytest` ve `AsyncMock` kullanılarak test edilmiş, yönlendirme (proxy) mantığı garanti altına alınmıştır. Test kodlarının commit zaman damgaları, fonksiyonel kodlardan önce gerçekleştirilmiştir.

> **Dispatcher:**<br>
> <img width="800" alt="Dispatcher Test" src="https://github.com/user-attachments/assets/25eb6edd-19f4-4bba-89a7-2c7e24604626" />
> <br><br>**Auth Service:**<br>
> <img width="800" alt="Auth Test" src="https://github.com/user-attachments/assets/5ee4df34-78eb-419c-a94e-3629007dacf2" />
> <br><br>**User Service:**<br>
> <img width="800" alt="User Test" src="https://github.com/user-attachments/assets/f459991b-d455-445e-9921-0fe82b19b500" />
> <br><br>**Ticket Service:**<br>
> <img width="800" alt="Ticket Test" src="https://github.com/user-attachments/assets/4b838018-dd1e-46ef-b8b6-a318c4956aad" />

---

## 8. Sistem Nasıl Çalıştırılır ve Test Edilir? <a id="kurulum"></a>
Projenin ayağa kaldırılması ve yetkilendirmeli veri akışının test edilmesi için aşağıdaki adımlar izlenmelidir:

1. **Sistemi Başlatma:** Proje ana dizininde terminal üzerinden `docker-compose up --build` komutu çalıştırılarak tüm mimari (veritabanları ve servisler) tek seferde ayağa kaldırılır.
2. **Swagger Arayüzüne Erişim:** Tarayıcıdan `http://localhost:8002/docs` adresine gidilir.
3. **Yetkilendirme (Auth):** Swagger üzerindeki `/auth/login` rotası kullanılarak `admin` kullanıcı adı ve `1234` şifresiyle giriş yapılır. Dönen `access_token` kopyalanıp arayüzün sağ üst köşesindeki "Authorize" butonuna tıklanarak ilgili alana yapıştırılır.
4. **Veri Ekleme:** Sisteme yük testi yapabilmek için `/tickets` ve `/users` rotaları (POST) üzerinden birkaç sahte bilet ve kullanıcı kaydı manuel olarak oluşturulur.
5. **Yük Testini Başlatma:** Yeni bir terminal sekmesinde `locust -f locustfile.py` komutu çalıştırılır. Ardından tarayıcıdan `http://localhost:8089` adresine gidilerek yük testi başlatılır. *(Detaylı HTML test raporları `load_tests` klasöründe yer almaktadır.)*
6. **Metrik İzleme:** Eş zamanlı olarak tarayıcıdan `http://localhost:3000` adresine gidilir. Grafana giriş bilgileri: **Kullanıcı Adı:** `admin` | **Şifre:** `admin`.

---

## 9. Performans Testleri ve Gözlemlenebilirlik <a id="performans"></a>
Sistem performansı `Locust` aracı kullanılarak test edilmiş ve oluşan anlık veriler otomatik ayağa kalkan `Grafana` dashboard'u üzerinden izlenmiştir.

### 9.1. Locust Yük Testi Sonuçları <a id="locust"></a>
Sistem, 100 ile 1000 eş zamanlı sanal kullanıcı arasında değişen senaryolarla test edilmiştir. Kullanıcı sayısı arttıkça mikroservis mimarisinin doğası gereği yanıt sürelerinde beklenen artışlar gözlemlenmiş, ancak hata oranları asgari düzeyde tutulmuştur.

| Kullanıcı Sayısı | Ortalama Yanıt Süresi | Maksimum Yanıt Süresi | Hata Oranı |
| :--- | :--- | :--- | :--- |
| **100** | ~120-200 ms | ~300 ms | %0 |
| **200** | ~150-250 ms | ~400 ms | %0-1 |
| **500** | ~200-400 ms | ~600 ms | %1-3 |
| **1000** | ~300-700 ms | ~1000+ ms | %3-5 |

<br>

> **100 Kullanıcı Testi Grafikleri:**<br>
> <img width="800" alt="100 Kullanıcı Tablo" src="https://github.com/user-attachments/assets/0d6dcfa8-a08e-4dff-af81-c95c172f677b" /><br>
> <img width="800" alt="100 Kullanıcı Grafik" src="https://github.com/user-attachments/assets/3a63e7f3-3286-4414-8ad0-d22ad99ad8bc" />
> <br><br>**200 Kullanıcı Testi Grafikleri:**<br>
> <img width="800" alt="200 Kullanıcı Tablo" src="https://github.com/user-attachments/assets/8f970098-fd3d-424c-a8cd-82d5b042ad0c" /><br>
> <img width="800" alt="200 Kullanıcı Grafik" src="https://github.com/user-attachments/assets/e0063214-5a57-4ac5-a6be-6f9d1576d05a" />
> <br><br>**500 Kullanıcı Testi Grafikleri:**<br>
> <img width="800" alt="500 Kullanıcı Tablo" src="https://github.com/user-attachments/assets/8712ceb2-fd8d-4e5a-9fb8-1dddbdc85704" /><br>
> <img width="800" alt="500 Kullanıcı Grafik" src="https://github.com/user-attachments/assets/9127326b-a724-4ffb-b567-516dfb763918" />
> <br><br>**1000 Kullanıcı Testi Grafikleri:**<br>
> <img width="800" alt="1000 Kullanıcı Tablo" src="https://github.com/user-attachments/assets/780a6724-a2e7-431b-9db6-a98eb392d52f" /><br>
> <img width="800" alt="1000 Kullanıcı Grafik" src="https://github.com/user-attachments/assets/52287f33-b776-430c-9aeb-00ee1007b5e2" />

### 9.2. Grafana İzleme Paneli (Observability) <a id="grafana"></a>
Sistemdeki toplam istek sayısı, HTTP statü kodlarının (2xx, 4xx, 5xx) yüzdelik dağılımı ve 99th Percentile gecikme süreleri Prometheus üzerinden çekilerek Grafana'da görselleştirilmiştir.

<br>
<img width="800" alt="Grafana Paneli" src="https://github.com/user-attachments/assets/fe0778c7-44f0-4258-9833-e46fa26ded52" />
<br>

---

## 10. Sonuç ve Değerlendirme <a id="sonuc"></a>
Bu projede mikroservis mimarisi kullanılarak ölçeklenebilir ve modüler bir sistem geliştirilmiştir. Dispatcher yapısı sayesinde tüm istekler merkezi olarak yönetilmiş ve güvenlik kontrolü sağlanmıştır.

**Başarılar:** * Sistem API Gateway mimarisine tam olarak oturtulmuş, yetkilendirme merkezileştirilmiştir.
* TDD standartlarına uyulmuş ve hatalar geliştirme aşamasında yakalanmıştır.
* Sistem, Prometheus ve Grafana altyapısıyla tam izlenebilir hale getirilmiştir.

**Sınırlılıklar:**
* Yüksek trafik (1000+ eşzamanlı kullanıcı) altında ağ gecikmelerinden kaynaklı performans düşüşleri gözlemlenmiştir.

**Gelecek Çalışmalar (Future Works):**
* Kubernetes entegrasyonu ile container orkestrasyonunun otomatikleşmesi.
* Redis tabanlı bir Blacklist / Cache mekanizması kurularak logout işlemlerinin ve sık okunan verilerin hızlandırılması.
* Servisler arası iletişimde HTTP protokolü yerine mesaj kuyrukları (RabbitMQ/Kafka) kullanılarak asenkron hız artışı sağlanması.
* CI/CD (Sürekli Entegrasyon ve Dağıtım) süreçlerinin projeye dahil edilmesi.
