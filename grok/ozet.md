# Özet

## Ne

RidGuard_v2, MT303 Remote ID süzgecinin en baştan yazıldığı klasördür. Depo https://github.com/talha-uk/RidGuard_v2 . Eski `/home/talha/Desktop/RidGuard` bilgi kaynağıdır. Kodu kopyalanmaz.

## Şu an

Karar motoru 0.5.0. Hız en az 3 m/s iken konum 5–20 saniye o hızın dörtte birinden az giderse sahte olur. Yön dolu ve konum yerindeyse aynı sahte kayda girer. Gidiş, bildirilen yönden 60 dereceden fazla saparsa sahte olur. İrtifa 15 m/s üstü değişirse sahte olur. ESP kalıbı sahte kalır. Seri düzgün olsa bile bozuk hız, küme ve katalog adı sahte görünür. Düzgün tek Remote ID şüpheli görünür. İkisi de iğne almaz. Sayılar birbiriyle uyuşursa bu kontrol tutmaz. ESP yine OcuSync üretemez. Yerel ekran `python3 -m rid_guard.ekran` ile `http://127.0.0.1:8765` adresinde açılır. Solda Bağlan, MT303 ağdaysa `192.168.0.200:10123` akışını gösterir. Ekranda yalnız bu bağlantının satırları durur. MT303 susunca bağlantı düşer ve liste boşalır. Sağda son 20 saniyedeki sahte ve şüpheli yayınlar durur. JSONL ve `$RID` de okunur. UART, firmware ve yayın yok. Anlatım `YAPTIKLARIMIZ.md`, kurallar `OKU.md`, fikirler `sahte-fikirler.md` içindedir. Wi-Fi taramasında görünmek tek başına sahte hükmü değildir.
