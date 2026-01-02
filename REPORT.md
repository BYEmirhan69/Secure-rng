# SecureRNG -- Güvenli Rastgele Sayı Üreteci

## Genişletilmiş Teknik Rapor

------------------------------------------------------------------------

## 1. Giriş

Bu rapor, ders kapsamında geliştirilen **SecureRNG** adlı güvenli
rastgele sayı üreteci algoritmasının tasarımını, güvenlik mimarisini,
saldırı modellerine karşı alınan önlemleri ve test sonuçlarını ayrıntılı
olarak açıklamak amacıyla hazırlanmıştır.

Çalışmanın temel hedefi, açık kaynak olarak paylaşılan bir algoritmanın
dahi, uygun kriptografik tasarım ilkeleri kullanıldığında tahmin
edilemez ve kırılması zor bir yapı sunabileceğini göstermektir.

------------------------------------------------------------------------

## 2. Algoritmaya Ön Değerler (Başlangıç Parametreleri)

Algoritmada kullanılan temel ön değerler aşağıda listelenmiştir:

-   **Entropy Kaynağı:**\
    İşletim sistemi kriptografik rastgele üreteci
    (`secrets.token_bytes`)

    -   256 bit (32 byte)

-   **Anahtar Türetme Fonksiyonu:**\
    HKDF (HMAC-based Key Derivation Function)

    -   Hash algoritması: SHA-256

-   **Akış Şifreleyici:**\
    ChaCha20

-   **Anahtar Uzunluğu:**\
    32 byte (256 bit)

-   **Nonce Uzunluğu:**\
    16 byte

-   **Sayaç (Counter):**\
    Başlangıç değeri: 0\
    Her blok üretiminde artırılır.

-   **Otomatik Reseed Mekanizması:**

    -   Çıktı miktarına bağlı: 1 MB\
    -   Zamana bağlı: 60 saniye

-   **Tek Çağrı Üretim Limiti:**\
    10 MB

------------------------------------------------------------------------

## 3. Algoritmanın Sözel Tanımı

SecureRNG, işletim sistemi tarafından sağlanan yüksek kaliteli entropy
ile başlatılan, ChaCha20 tabanlı bir **CSPRNG**'dir.

Algoritma aşağıdaki temel adımlarla çalışır:

1.  Başlangıçta entropy ve ek rastgelelik verileri toplanır.
2.  Bu veriler HKDF-SHA256 kullanılarak gizli anahtar ve nonce üretmek
    için kullanılır.
3.  Rastgele veri üretimi sırasında ChaCha20 akış şifreleyicisi
    kullanılarak kriptografik olarak güçlü bir keystream elde edilir.
4.  Her çıktı üretiminden sonra anahtar tek yönlü olarak evrilir.
5.  Belirli bir süre veya çıktı miktarı aşıldığında otomatik olarak
    reseed işlemi gerçekleştirilir.

Bu yapı sayesinde algoritma hem kısa hem de uzun süreli kullanımlarda
güvenliğini korur.

------------------------------------------------------------------------

## 4. Algoritmanın Sözde Kodu

``` text
Başlat:
  entropy ← OS_CSPRNG(32 byte)
  salt ← OS_CSPRNG(32 byte)
  key, nonce ← HKDF(entropy, salt)

next_bytes(n):
  Eğer PID değiştiyse veya reseed zamanı geldiyse:
      reseed()

  çıktı ← boş
  while çıktı uzunluğu < n:
      nonce_blok ← nonce || sayaç
      blok ← ChaCha20(key, nonce_blok)
      çıktı ← çıktı + blok
      sayaç ← sayaç + 1

  key ← HKDF(key || sayaç)   // Anahtar evrimi
  return çıktı[n byte]
```

------------------------------------------------------------------------

## 5. Algoritmanın Akış Şeması

Algoritmanın genel akışı aşağıdaki aşamalardan oluşur:

1.  Entropy toplama
2.  Anahtar ve nonce üretimi
3.  Rastgele veri üretimi
4.  Reseed koşullarının kontrolü
5.  Anahtar evrimi
6.  Çıktının kullanıcıya döndürülmesi

Bu akış, rapor eklerinde diyagram ile gösterilmektedir.

------------------------------------------------------------------------

## 6. Güvenlik Mekanizmaları

SecureRNG algoritmasında aşağıdaki güvenlik önlemleri uygulanmıştır:

### 6.1 Backtracking Koruması

Her çıktı üretiminden sonra anahtar evrilerek, mevcut iç durum ele
geçirilse bile geçmiş çıktılara ulaşılamaması sağlanır.

### 6.2 Fork-Safety (Süreç Güvenliği)

Süreç kimliği (PID) kontrol edilerek, `fork()` sonrası aynı rastgele
akışın üretilmesi engellenir.

### 6.3 Zaman ve Byte Bazlı Reseed

Uzun süre çalışan sistemlerde state'in eskimesini önlemek için zaman ve
çıktı miktarına bağlı otomatik reseed uygulanır.

### 6.4 Bellek Hijyeni

Hassas veriler `bytearray` kullanılarak best-effort şekilde bellekten
silinmektedir.

### 6.5 Thread-Safety

Çoklu iş parçacıklı ortamlarda state tutarlılığı kilitleme mekanizmaları
ile korunmaktadır.

------------------------------------------------------------------------

## 7. İstatistiksel Testler

Algoritmanın çıktılarında istatistiksel patern bulunmadığını göstermek
için aşağıdaki testler uygulanmıştır:

-   Pearson Chi-Square Testi
-   Wald--Wolfowitz Runs Testi
-   Kolmogorov--Smirnov Testi

Testler, üretilen byte dizileri üzerinde uygulanmıştır.

### Test Sonuçları

Test sonuçlarına göre: - Uniformluk hipotezi reddedilememiştir. -
Bağımsızlık hipotezi reddedilememiştir. - %95 güven düzeyinde
istatistiksel patern gözlemlenmemiştir.

------------------------------------------------------------------------

## 8. Birim Testler

Algoritmanın doğru çalıştığını doğrulamak için `pytest` kullanılarak
birim testler yazılmıştır.

Tüm testler başarıyla geçmiştir.

------------------------------------------------------------------------

## 9. Sonuç

Bu çalışma kapsamında geliştirilen SecureRNG algoritması;

-   Kriptografik olarak güvenli entropy kaynakları kullanır,
-   İleri seviye saldırı modellerine karşı koruma sağlar,
-   İstatistiksel olarak patern göstermeyen çıktılar üretir,
-   Akademik ve eğitim amaçlı kullanım için uygundur.

------------------------------------------------------------------------

## 10. Kaynak Kod

GitHub Repository:\
https://github.com/BYEmirhan69/Secure-rng

------------------------------------------------------------------------

### Not

Bu algoritma eğitim ve akademik amaçlarla geliştirilmiştir. Resmî bir
kriptografik standart veya sertifikasyon iddiası bulunmamaktadır.
