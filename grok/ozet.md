# Özet

## Ne

RidGuard_v2, MT303 Remote ID süzgecinin en baştan yazıldığı klasördür. Depo https://github.com/talha-uk/RidGuard_v2 . Eski `/home/talha/Desktop/RidGuard` bilgi kaynağıdır. Kodu kopyalanmaz.

## Şu an

Karar motoru 0.4.0. ESP kalıbı sahte kalır. Seri düzgün olsa bile bozuk hız, küme ve katalog adı sahte görünür. Düzgün tek Remote ID şüpheli görünür. İkisi de iğne almaz. Yerel ekran `python3 -m rid_guard.ekran` ile `http://127.0.0.1:8765` adresinde açılır. Solda Bağlan, MT303 ağdaysa `192.168.0.200:10123` akışını gösterir. Ekranda yalnız bu bağlantının satırları durur. MT303 susunca bağlantı düşer ve liste boşalır. Sağda son 20 saniyedeki sahte yayınlar durur. ESP şablonu `sahte` olur, uçak iğnesi almaz. JSONL ve `$RID` de okunur. UART, firmware ve yayın yok. Anlatım `YAPTIKLARIMIZ.md`, sahte fikirler `sahte-fikirler.md` içindedir. Wi-Fi taramasında görünmek tek başına sahte hükmü değildir.
