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

Sağ tarafta iki işaret durur. **sahte**: bilinen ESP kalıbı, ya da seri düzgün olsa bile hızı, kümesi veya adı bozuk olan yayın. **şüpheli**: seri düzgün durur, uçuş bağlantısı yoktur. İkisi de haritaya konmaz. Yayın kesilince satır kaybolur.

Ne yaptığımız: [YAPTIKLARIMIZ.md](YAPTIKLARIMIZ.md). Teknik kurallar: [OKU.md](OKU.md).
