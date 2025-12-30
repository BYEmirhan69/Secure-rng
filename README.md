🔐 SecureRNG – Rastgele Sayı Üreteci (Python)

Bu proje, güvenli rastgele bayt üretimi amacıyla geliştirilmiş bir CSPRNG (Cryptographically Secure Random Number Generator) uygulamasıdır.


🎯 Amaç

Güvenli bir next_bytes(n) arayüzü sağlamak

Açık kaynak olmasına rağmen tahmin edilemez çıktı üretmek

Seed tahminine ve basit istatistiksel saldırılara karşı dayanıklı olmak

🧠 Tasarım Özeti

Bu RNG aşağıdaki prensiplere dayanır:

Entropy Kaynağı:

İşletim sistemi CSPRNG (secrets.token_bytes)

Çekirdek Mekanizma:

ChaCha20 tabanlı DRBG (Deterministic Random Bit Generator)

Anahtar / Nonce Türetilmesi:

HKDF-SHA256

State Güvenliği:

İç durum (key, nonce) hiçbir şekilde dışarı sızdırılmaz

Otomatik Reseed:

Belirli miktarda çıktı üretildikten sonra state yenilenir

DoS Koruması:

Tek çağrıda üretilebilecek maksimum byte sınırı vardır

🧩 Sağlanan Arayüz
SecureRNG.new()              # Yeni RNG oluşturur
rng.next_bytes(n)            # n adet rastgele byte üretir
rng.randbelow(k)             # 0 <= x < k olacak şekilde sayı üretir
rng.reseed(extra=b"...")     # (opsiyonel) state yeniler

🧪 Testler

Proje pytest kullanılarak test edilmiştir.

Test edilen başlıca durumlar:

Üretilen çıktının uzunluğu

Ardışık çıktılar arasında tekrar olmaması

Reseed sonrası çıktının değişmesi

randbelow(k) fonksiyonunun doğru aralıkta değer üretmesi

Testleri çalıştırmak için:

python -m pytest -q

📦 Kurulum
pip install -r requirements.txt

📁 Proje Yapısı
Rastgele Sayı Üreteci/
│
├── rng.py          # SecureRNG implementasyonu
├── test_rng.py     # Testler
├── README.md
├── requirements.txt
└── .gitignore

⚠️ Güvenlik Notları

Bu proje eğitim ve akademik çalışma amacıyla hazırlanmıştır

Çıktı örnekleri veya demo çıktıları özellikle paylaşılmamıştır

RNG, kriptografik standartlara uygun şekilde tasarlanmıştır ancak resmî bir sertifikasyona sahip değildir

👤 Yazar

Emirhan Aydemir

Bilgisayar / Siber Güvenlik odaklı akademik çalışma