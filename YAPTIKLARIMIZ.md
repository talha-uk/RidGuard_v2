# Yaptıklarımız

RidGuard_v2, AD-TB MT303'ün ESP8266 ile basılan sahte Remote ID'yi gerçek uçak sanmaması için yazıldı. Sürüm 0.3.0. Eski `/home/talha/Desktop/RidGuard` yalnız bilgi kaynağıdır. Kod oradan kopyalanmadı. Python 3.10 ve standart kütüphane yeter. Klasör git deposu değildir.

Bu yazılım RF basmaz, firmware yazmaz, seri port açmaz.

## Amaç

ESP8266, ASTM Remote ID'yi 2.4 GHz Wi-Fi beacon olarak basar. Seri, gerçek bir DJI modeli gibi görünür. Ekran bunu yok saymak yerine `sahte` diye gösterir. Uçak iğnesi koymaz. İddia edilen pilot yeri kayıtta kalır. Böylece yayın ifşa olur, haritada uçak olmaz.

OcuSync veya RF parmak izi olan ve şablona uymayan kayıt gerçek bağ sayılır. Onun konumu çizilir.

## Kutuya giden yol

İlk söylenen adres `192.168.10.1` idi. Kabloya bağlı kutu orada değildi. Ethernet arayüzü `enp4s0`, bağlantı adı `Coklu-IP`. Bu makineye `192.168.0.10/24` eklendi. Eski adresler duruyor.

Kutu `192.168.0.200`, TCP `10123`. Satır biçimi `$tip,alan:değer,...,$end`. Heartbeat kabaca saniyede bir gelir. Kutunun kendi serisi `3844BE214DAC`. GPS yokken enlem ve boylam `0.0` olur.

`$RID` uzaktan kimliktir. `$Feature` video bağıdır: O3, O4, Lightbridge, PAL, NTSC, Wifi. `$heartbeat` ve `$Feature` uçak kaydı değildir. `$DroneID` ve `$EncryptedDroneID` bu sürümde ayrıştırılmaz. Çözme sunucusu da çağrılmaz.

Ham kayıt `/home/talha/Desktop/MT303/izle/akis.log` içindedir. İzleyici `izle/izle.py`. Aynı TCP kapısını arayüz ile izleyici birlikte tutarsa bağlanma olmaz.

## Karar

Motor JSONL ve kutunun `$RID` cümlesini okur.

| Ne gelirse | Ne olur |
| --- | --- |
| OcuSync veya parmak izi, şablon değil | confirmed, iğne var |
| ESP `ridSerial()` şablonu | spoof, ekranda `sahte`, iğne yok |
| Bozuk seri, dolgu, katalog adı, 45 m/s üstü hız, 15 sn ve 80 m içinde 4 pilot | spoof, çizilmez |
| Yapısı düzgün tek Remote ID | hold, çizilmez |

Şablon iki biçimdir. Ürün kodu `1581F` + 3 karakter + `RID` + iki hane + yedi `X`. Kod yoksa model adı 20 karaktere `X` ile doldurulur. Listedeki modeller Mini 3, Mini 3 Pro, Mini 4 Pro, Mini SE, Air 2S, Air 3, Mavic Air 2, Mavic 3, Mavic 3 Classic, Avata, Avata 2, FPV, Autel EVO Nano+, Autel EVO II Pro ve Parrot Anafi'dir. Eski yazılım için Mini 2, Skydio 2+ ve Holy Stone HS720E de durur.

Kaynak alanı `ocusync` yazsa da şablon iğne almaz. Bu kart OcuSync üretmez.

Ayrıntılı tablo [OKU.md](OKU.md) içindedir.

## Logda görülen yayın

Canlı kayıtta heartbeat dışında sahte şablonlar düştü. Hepsi `mark: sahte` oldu. Gerçek uçak çıkmadı.

Görülenlerden bazıları:

- `1581F6Z9RID03XXXXXXX`, DJI Mini 4 Pro, yuva 03
- `1581F6N8RID06XXXXXXX`, DJI Air 3, yuva 06
- Mini 3, Mini 3 Pro, DJI FPV, Autel EVO Nano+ ve Autel EVO II Pro şablonları

Hepsi kanal 6 beacon. Seride `RID` ve yedi `X` var. Pilot konumu Ankara civarında, uçak konumu çoğu satırda boş veya sıfır.

O3 ve PAL satırları da geldi. Bunlarda seri ve konum yok. Onlardan iğne çıkmaz. O3, 5.8 GHz video bağıdır. ESP bunu basmaz.

## Arayüz

`python3 -m rid_guard.ekran` yerel sayfayı açar: [http://127.0.0.1:8765](http://127.0.0.1:8765). Şu an duruyor. İstenince aynı komutla açılır.

Sol yarı MT303. **Bağlan**, kutu ağdaysa `192.168.0.200:10123` oturumunu açar. Listede yalnız bu bağlantıdan sonra gelen satırlar durur. Eski oturum ve diskteki log ekrana taşınmaz. Kutu yaklaşık 3 saniye susunca bağlantı düşer, durum `bağlantı koptu` olur, liste boşalır. **Kes** de listeyi siler.

Sağ yarı tahmini sahte sinyallerdir. Son 20 saniyede görülen şablonlar durur. Model, seri, RSSI, pilot yeri, kanal ve kaç kez görüldüğü yazılır. Yayın kesilince satır listeden düşer.

Dar pencerede akış üstte, sahte liste altta kalır.

## Bilerek yazılmayanlar

ESP'nin yayın yazılımı yazılmadı. Şablon, ayırt edilmesi zorlaşsın diye değiştirilmedi. `/dev/ttyUSB0` açılmadı. O port spoofer kartıdır ve açılması kartı sıfırlar. UART kaydı yok. Firmware yok. RF yok.

Wi-Fi taramasında görünmek tek başına sahte hükmü değildir. OcuSync Wi-Fi ağı açmaz. Güncel Remote ID ise Wi-Fi beacon'dır ve gerçek uçak da taramada görünebilir. Bu tartışma [sahte-fikirler.md](sahte-fikirler.md) içindedir. Koda bağlanmadı.

## Çalıştırma

```bash
cd /home/talha/Desktop/RidGuard_v2
python3 -m unittest discover -s tests -v
python3 -m rid_guard --only-screen --file fixtures/lab_and_link.jsonl
python3 -m rid_guard.ekran
```

37 test geçti. Laboratuvar satırı `sahte` düşer ve iğne almaz. OcuSync satırı confirmed olur.
