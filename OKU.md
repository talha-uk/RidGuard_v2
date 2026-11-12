# Kurallar

Kısa anlatım [README.md](README.md) ve [YAPTIKLARIMIZ.md](YAPTIKLARIMIZ.md) içindedir.

Sürüm 0.7.0. Program radyo yayını yapmaz. Kart yazılımı yazmaz. Seri port açmaz.

Eski `/home/talha/Desktop/RidGuard` yalnız bakmak içindir. Kodu buraya kopyalanmaz.

## Ekranda ne yazar

| Gelen kayıt | Ekran | Sonuç |
| --- | --- | --- |
| Uçuş bağlantısı, ESP kalıbı yok | haritaya koy | confirmed |
| ESP kalıbı | sahte, iğne yok | spoof |
| Remote ID, hareketi bozuk | sahte, iğne yok | spoof |
| 15 saniye ve 80 metre içinde 4 pilot, başka bozukluk yok | sürü, iğne yok | swarm |
| Düzgün tek Remote ID | şüpheli, iğne yok | hold |

Harita iğnesi yalnız uçuş bağlantısından gelir. Remote ID aynı seriyi taşısa da iğneyi oynatmaz.

## Sahte

ESP kalıbı sahte olur. Kaynak uçuş bağlantısı yazsa da iğne almaz. Pilot konumu, iddia edilen operatör yeri olarak kalır.

- Seri `1581F` + 3 karakter + `RID` + iki rakam + yedi `X` ise kalıptır. Örnek `1581F5YHRID01XXXXXXX`. Rakam değişse de kalıp yeter.
- Ürün kodu yoksa model adı 20 karaktere `X` ile doldurulur. Örnek `DJIMINISEXXXXXXXXXXX`.

Modeller: Mini 3, Mini 3 Pro, Mini 4 Pro, Mini SE, Air 2S, Air 3, Mavic Air 2, Mavic 3, Mavic 3 Classic, Avata, Avata 2, FPV, Autel EVO Nano+, Autel EVO II Pro, Parrot Anafi. Eski yazılım için Mini 2, Skydio 2+ ve Holy Stone HS720E de aynı dolgu kuralına girer.

Seri CTA-2063 biçimine bakılır. Başta 4 karakter üretici kodu, sonra uzunluk, sonra seri gelir. `I` ve `O` harfi kullanılmaz. Uzunluk `1..9`, sonra `A=10` … `F=15`. Biçim uyuşmazsa sahte olur.

Aynı karakter 7 kez tekrar ederse sahte olur.

Operatör adı, kendi adı veya ağ adı katalogdaki bir model ise sahte olur. Aynı ad, kalıbı bozuk olmayan uçuş bağlantısını düşürmez.

Bildirilen hız 45 m/s üstündeyse sahte olur. İki konumun gerektirdiği hız da aynı sınıra bakar. Hız metre/saniye kabul edilir. 50 ms ve altı aralık hesaba girmez. Bu sınır küçük çok rotorlu dronelar içindir. Hızlı sabit kanat yanlış sahte görünebilir.

Hız en az 3 m/s iken, 5 ile 20 saniye arasında konum o hızın dörtte birinden az gittiyse sahte olur. Yön dolu ve konum yerindeyse aynı sahte kayda girer. Konum en az 20 metre gittiyse ve gidiş bildirilen yönden 60 dereceden fazla sapıyorsa sahte olur. İrtifa saniyede 15 metreden hızlı değişirse sahte olur.

Uçuş bağlantısı 120 saniye hatırlanır. Bu sürede gelen Remote ID iğneyi oynatmaz. Aynı seride beacon ile bağlantı 200 metreden fazla ayrılırsa beacon sahte olur. İğne bağlantıda kalır. Bağlantı yoksa düzgün beacon şüpheli kalır. Gövde mesajı doğrulamaz.

## Sürü

Aynı 15 saniye ve 80 metre içinde 4 ayrı pilot bir sürü olur. Küme 15 saniye daha sürü kalır. Başka bir bozukluk varsa sahte olur.

## Bağlantı sayılanlar

Kaynak boşsa veya bilinmiyorsa Remote ID sayılır. Kayıtta ocusync, o2, o3, o4 veya `drone id` varsa bağlantıdır. `fingerprint` parmak izidir. `protocol` tek başına bağlantı sayılmaz.

## Okunan satır

MT303 satırı `$tip,...,$end` biçimindedir. `$RID` karara girer. `$heartbeat` ve `$Feature` uçak sayılmaz.

JSON alanları: seri, enlem, boylam, irtifa, hız, pilot yeri, operatör, kendi adı, ağ adı, mod.

Tanınmayan satır ekrana drone eklemez.

`/dev/ttyUSB0` ESP kartıdır. Portu açmak kartı resetler. Açılmaz.

## Çalıştırma

```bash
cd /home/talha/Desktop/RidGuard_v2
python3 -m unittest discover -s tests -v
python3 -m rid_guard --only-screen --file fixtures/lab_and_link.jsonl
python3 -m rid_guard.ekran
```

Ekran `http://127.0.0.1:8765` adresindedir. Bağlan, MT303 ağdaysa `192.168.0.200:10123` akışını açar. Ekranda yalnız bu bağlantıdan sonra gelen satırlar durur. MT303 yaklaşık 3 saniye susunca liste boşalır. Sağda son 20 saniyenin sahte, şüpheli ve sürü yayınları durur. Aynı portu `izle.py` tutuyorsa bağlanma olmaz.

## Sınır

Düzgün tek Remote ID şüpheli kalır. Uçuş bağlantısı gelince gerçek sayılır.

Dedektör tam seri yerine kısa ürün kodu yollarsa kalıp gerçek uçakla karışabilir. Ayrım 20 karakterlik seri ister.
