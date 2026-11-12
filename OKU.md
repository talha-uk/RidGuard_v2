# RidGuard_v2

Bu dosya teknik kurallardır. Kısa anlatım [README.md](README.md) ve [YAPTIKLARIMIZ.md](YAPTIKLARIMIZ.md) içindedir.

AD-TB MT303, ESP8266 Remote ID yayınını gerçek uçak sanmasın diye yazılmış karar katmanı. Sürüm 0.3.0. Bu sürüm RF basmaz, firmware yazmaz, seri port açmaz.

Eski `/home/talha/Desktop/RidGuard` bilgi kaynağıdır. Kodu buraya kopyalanmaz.

## Karar

| Kaynak | Seri ve hareket | Ekran | verdict |
| --- | --- | --- | --- |
| ocusync veya fingerprint | ESP8266 şablonu değil | çiz | confirmed |
| ocusync, fingerprint veya remote_id | `ridSerial()` şablonu | sahte yaz, iğne yok | spoof |
| remote_id | CTA-2063 dışı, dolgu, katalog operatör / Self-ID / SSID, 45 m/s üstü hız, aynı pilot etrafında 4 uçak | çizme | spoof |
| remote_id | yapı düzgün, tek başına | çizme | hold |

Konum iğnesi yalnız OcuSync veya parmak izi kaydından gelir. Remote ID satırı, seri aynı olsa bile iğneyi taşımaz.

Hold varsayılan kapalıdır. `--show-hold` inceleme katmanıdır ve o kayıtların konumunu da basar. Operasyon resmi `--only-screen` çıktısıdır.

## Kurallar

ESP8266 `ridSerial()` şablonu spoof olur ve ekranda `sahte` diye durur. Kaynak `ocusync` yazsa da uçak iğnesi almaz. Pilot konumu, iddia edilen operatör yeri olarak kalır.

- Ürün kodu: `1581F` + 3 karakter + `RID` + iki hane + yedi `X`. Örnek `1581F5YHRID01XXXXXXX`. Hane değişse de kalıp yeter.
- Ürün kodu yoksa model adı, boşluk ve `+` atılıp 20 karaktere `X` ile doldurulur. Örnek `DJIMINISEXXXXXXXXXXX`.

15'lik liste: Mini 3, Mini 3 Pro, Mini 4 Pro, Mini SE, Air 2S, Air 3, Mavic Air 2, Mavic 3, Mavic 3 Classic, Avata, Avata 2, FPV, Autel EVO Nano+, Autel EVO II Pro, Parrot Anafi. Eski yazılım için Mini 2, Skydio 2+ ve Holy Stone HS720E de aynı dolgu kuralıyla durur.

Seri, ANSI/CTA-2063-A yapısına bakılır: 4 karakter üretici, 1 uzunluk kodu, kodun dediği kadar üretici seri. Alfabe `I` ve `O` içermez. Uzunluk kodu `1..9`, `A=10` … `F=15`. Uyuşmayan Remote ID kaydı spoof olur.

Aynı karakter 7 kez veya daha uzun tekrar ederse dolgudur.

Operatör, Self-ID veya SSID katalog model adıysa Remote ID kaydı spoof olur. Aynı ad, şablonu bozuk olmayan bir OcuSync kaydını düşürmez.

Aynı 15 saniye ve 80 metre içinde 4 ayrı Remote ID pilotu bir kümedir. Dördüncüyle birlikte küme spoof olur. Küme, oluştuğu andan itibaren 15 saniye spoof kalır.

İki konumun gerektirdiği hız 45 m/s üstündeyse spoof olur. Bildirilen `airspeed` de aynı sınıra bakar ve m/s kabul edilir. 50 ms ve altı aralık hız hesabına girmez. Bu sınır tüketici çok rotorludur. Hızlı sabit kanat yanlış pozitif verebilir.

`source` boş veya bilinmeyen ise remote_id sayılır. `mode` içinde ocusync, o2, o3, o4 veya `drone id` bağdır. `fingerprint` parmak izidir. `protocol` tek başına bağ değildir.

Bağ kaydı 120 saniye hatırlanır. Bu pencerede gelen Remote ID iğneyi oynatmaz. Gerekçeye `remote_id_position_ignored` yazılır.

## Akış

1. MT303 pasif dinler. Bu yazılım RF basmaz.
2. Bilinen satır JSON olur. Okunan alanlar: `serial_number`, `latitude`, `longitude`, `altitude`, `airspeed`, `pilot_latitude`, `pilot_longitude`, `operator`, `self_id`, `ssid`, `mode`.
3. `python3 -m rid_guard` her satıra bir karar basar.
4. Tanınmayan satır stderr'e `verdict: reject` olarak düşer ve ekrana drone eklemez.

MT303 cümlesi `$tip,...,$end` okunur. `$RID` karara girer. `$heartbeat` ve `$Feature` uçak değildir, atlanır. `/dev/ttyUSB0` spoofer kartıdır. Portu açmak kartı resetler. Bu iş ayrı açık istek ister.

## Çalıştırma

Bu makinede Python 3.10 vardır. Karar motoru standart kütüphane ile çalışır.

```bash
cd /home/talha/Desktop/RidGuard_v2
python3 -m unittest discover -s tests -v
python3 -m rid_guard --only-screen --file fixtures/lab_and_link.jsonl
python3 -m rid_guard.ekran
```

Arayüz `http://127.0.0.1:8765` adresindedir. Soldaki Bağlan, MT303 ağdaysa `192.168.0.200:10123` akışını açar. Ekranda yalnız bu bağlantıdan sonra gelen satırlar durur. MT303 yaklaşık 3 saniye susunca bağlantı düşer ve liste boşalır. Sağda son 20 saniyede görülen sahte yayınlar durur. Aynı portu `izle.py` tutuyorsa bağlanma olmaz.

Laboratuvar fikstüründeki Remote ID satırı `display: true`, `mark: sahte` ve `verdict: spoof` olur. Uçak konumu boştur. OcuSync satırı `display: true` ve `mark` boş olur. `--only-screen` ikisini de basar.

## Bilinçli sınır

Dört gerçek Remote ID uçağı 80 metre içinde 15 saniyede görünürse onlar da spoof yazılır. Ana ekran zaten Remote ID çizmediği için operasyon resmi değişmez.

Tek ve yapısı düzgün bir Remote ID, hold kalır. Bağ çözülemeyen gerçek bir uçak da ana ekranda görünmez. Parmak izi veya OcuSync satırı gelince uçak confirmed olur.

Dedektör tam seri yerine kısa ürün kodu yollarsa şablon gerçek uçakla karışabilir. Ayrım 20 karakterlik seri ister.
