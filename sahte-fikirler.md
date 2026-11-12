# Sahte sinyal fikirleri

Karar kuralı değildir. Ölçülmemiş cümle buraya yazılır. Teyit ayrı durur. Koda bağlanan yalnız buradaki "ölçüldü" satırlarıdır.

## 1. Wi-Fi taramasında görünmek

Talha, 2026-11-12:

Dronelar 2.4 ve 5.8 GHz'de yayın yapsa bile Wi-Fi ağı açamaz. MT'nin gördüğü dronelardan biri Wi-Fi taramasında varsa o sahte sayılır.

### Doğru parça

OcuSync, O3, O4 ve Lightbridge 2.4 ve 5.8 GHz'de durur. Bu yayın 802.11 ağı değildir. Telefonun Wi-Fi listesine SSID olarak düşmez. MT bunu `$Feature` ile görür.

5.8 GHz'deki O3 örneği 5796 MHz'dir. Standart Wi-Fi kanallarının ortası değildir. Normal tarama onu ağ diye listelemez. PAL analog görüntü de Wi-Fi ağı değildir.

ESP8266 sahte Remote ID'si Wi-Fi beacon basar. Logda bu `protocol:beacon, channel:6` diye durur. O beacon tarama listesine düşer.

### Yanlış parça

"Drone Wi-Fi ağı açamaz" genel kural değildir. Birçok küçük drone ve DJI'nin eski Wi-Fi modelleri katılınabilir ağ açar.

Güncel standart Remote ID, ASTM F3411 ile Bluetooth ya da Wi-Fi beacon olarak yayınlanır. DJI serisi bu iş için Wi-Fi kullanır. Beacon'ın işi çevredeki telefonlara görünmektir. Alıcı ağa katılmaz. Gerçek uçak da Wi-Fi taramasında görünebilir.

Bu yüzden "taramada varsa sahtedir" kuralı gerçek Remote ID'yi de sahte sayar.

### Eksik

Bu masada gerçek bir DJI ile ESP yan yana taranmadı. SSID'nin açık mı gizli mi olduğu modele ve yazılıma göre değişir. Mavic 3 Classic için açık anlatımlarda çelişen gözlem var.

MT beacon'ı zaten `$RID` diye yazar. Laptop taraması aynı yayını ikinci kez görür. Sahte ile gerçeği ayıran şey taramada görünmek değildir. Ayrım, serideki şablondur: `1581F` + üç karakter + `RID` + iki hane + yedi `X`. Katalog model adının SSID olması da aynı kalıba girer.

Katılınabilir açık ağ ile yalnız beacon olan Remote ID ayrı ölçülmeli. Bu ölçüm yok.

### Şimdilik kullanılacak hali

`$Feature` O3 veya O4, Wi-Fi ağı değildir. Onun frekansında SSID aramak o uçağı bulmaz.

Taramada SSID bir model adıysa veya seri şablona uyuyorsa bu, bilinen ESP kalıbıdır. Tarama bunu destekler. Tek başına hüküm olmaz.
