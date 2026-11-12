# RidGuard

Sahte drone yayını ile gerçek drone yayınını ayıran bir ekran.

Küçük bir kart, havaya drone kimliği basabiliyor. Dinleme kutusu bunu da satır satır yazıyor. RidGuard bu satırları okur. Kartın bastığı kimliği **sahte** diye gösterir. Onu haritada gerçek drone diye işaretlemez.

Gerçek bir uçuş bağlantısı gelirse onu gösterir.

## Ekranı açmak

```bash
python3 -m rid_guard.ekran
```

Tarayıcıda [http://127.0.0.1:8765](http://127.0.0.1:8765) açılır.

Sol tarafta kutunun o an yazdığı satırlar durur. **Bağlan** deyince başlar. Kutu susunca liste silinir.

Sağ tarafta o anda duyulan sahte yayınlar durur. Yayın kesilince satır kaybolur.

Ne yaptığımız: [YAPTIKLARIMIZ.md](YAPTIKLARIMIZ.md). Teknik kurallar: [OKU.md](OKU.md).
