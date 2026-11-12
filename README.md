# RidGuard

MT303'ün canlı kaydını izler. Sahte drone yayınına sahte der.

ESP kart havaya sahte kimlik basar. MT303 bu yayını da yazar. RidGuard satırı okur. Bilinen ESP kalıbını **sahte** gösterir. Onu haritaya koymaz.

Uçuş bağlantısı gelirse onu gösterir.

## Ekran

```bash
python3 -m rid_guard.ekran
```

Tarayıcıda [http://127.0.0.1:8765](http://127.0.0.1:8765) açılır. **Bağlan** deyince MT303'ün o anki satırları solda akar. MT303 susunca liste silinir.

Sağda üç işaret vardır.

- **sahte:** ESP kalıbı, ya da hız, yön, irtifa birbiriyle uyuşmayan yayın. Uçuş bağlantısı varken beacon 200 metreden uzak yer gösterirse o da sahte sayılır.
- **sürü:** Dört kimlik 15 saniye ve 80 metre içindedir. Yan yana uçuş tek başına sahte sayılmaz.
- **şüpheli:** Seri düzgün durur. Uçuş bağlantısı yoktur.

Üçü de haritaya konmaz. Yayın kesilince satır kaybolur.

Ne yaptığımız: [YAPTIKLARIMIZ.md](YAPTIKLARIMIZ.md). Kurallar: [OKU.md](OKU.md).
