# Özet

## Ne

RidGuard_v2, MT303 Remote ID süzgecinin en baştan yazıldığı klasördür. Depo https://github.com/talha-uk/RidGuard_v2 . Eski `/home/talha/Desktop/RidGuard` bilgi kaynağıdır. Kodu kopyalanmaz.

## Şu an

Karar motoru 0.7.0. Dört kimlik 15 saniye ve 80 metre içindeyse sürü olur. Bu sahte hükmü değildir. ESP kalıbı, bozuk hız, yön, irtifa ve bağdan 200 metre sapma sahte kalır. Düzgün tek beacon şüpheli kalır. Üçü de iğne almaz. Yerel ekran `python3 -m rid_guard.ekran` ile `http://127.0.0.1:8765` adresinde açılır. Sağda son 20 saniyedeki sahte, şüpheli ve sürü yayınlar durur. UART, firmware ve yayın yok. Kurallar `OKU.md` içindedir.
