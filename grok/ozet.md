# Özet

## Ne

RidGuard_v2, MT303 Remote ID süzgecinin en baştan yazıldığı klasördür. Depo https://github.com/talha-uk/RidGuard_v2 . Eski `/home/talha/Desktop/RidGuard` bilgi kaynağıdır. Kodu kopyalanmaz.

## Şu an

Karar motoru 0.6.0. Hız, yön ve irtifa uyuşmazsa sahte olur. Aynı seride uçuş bağlantısı varken beacon 200 metreden uzaksa beacon sahte olur. İğne bağlantıda kalır. Bağlantı yoksa düzgün beacon şüpheli kalır ve iğne almaz. Gövde bunu doğrulamaz. ESP kalıbı sahte kalır. Yerel ekran `python3 -m rid_guard.ekran` ile `http://127.0.0.1:8765` adresinde açılır. Solda Bağlan, MT303 ağdaysa `192.168.0.200:10123` akışını gösterir. Sağda son 20 saniyedeki sahte ve şüpheli yayınlar durur. UART, firmware ve yayın yok. Kurallar `OKU.md` içindedir.
