# RidGuard

MT303'ün canlı kaydını izler ve sahte drone tespiti yapar.

ESP kart, havaya sahte drone kimliği basabiliyor. MT303 bunu da satır satır yazar. RidGuard bu satırları okur. ESP kartın bastığı kimliği **sahte** diye gösterir. Onu haritada gerçek drone diye işaretlemez.

Gerçek bir uçuş bağlantısı gelirse onu gösterir.

## Ekranı açmak

```bash
python3 -m rid_guard.ekran
```

Tarayıcıda [http://127.0.0.1:8765](http://127.0.0.1:8765) açılır.

Sol tarafta MT303'ün o an yazdığı satırlar durur. **Bağlan** deyince başlar. MT303 susunca liste silinir.

Sağ tarafta üç işaret durur. **sahte**: bilinen ESP kalıbı, ya da seri düzgün olsa bile hareketi bozuk olan yayın. Hız söylenip konum 5 saniye yerinde kalırsa, yön ile gidiş uyuşmazsa, irtifa bir anda çok değişirse de sahte sayılır. Uçuş bağlantısı varken beacon 200 metreden uzak yer gösterirse o beacon da sahte sayılır. **sürü**: dört kimlik 15 saniye ve 80 metre içindedir. Yan yana uçuş tek başına sahte değildir. **şüpheli**: seri düzgün durur, uçuş bağlantısı yoktur. Üçü de haritaya konmaz. Yayın kesilince satır kaybolur.

Ne yaptığımız: [YAPTIKLARIMIZ.md](YAPTIKLARIMIZ.md). Teknik kurallar: [OKU.md](OKU.md).
