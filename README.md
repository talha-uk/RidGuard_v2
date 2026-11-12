# RidGuard_v2

MT303 tespit ekranının Wi-Fi Remote ID yayınıyla dolmaması için karar katmanı.

Kurallar ve çalıştırma: [OKU.md](OKU.md). Yapılan işin anlatımı: [YAPTIKLARIMIZ.md](YAPTIKLARIMIZ.md).

```bash
cd /home/talha/Desktop/RidGuard_v2
python3 -m unittest discover -s tests -v
python3 -m rid_guard --only-screen --file fixtures/lab_and_link.jsonl
python3 -m rid_guard.ekran
```

Operasyon resmi `--only-screen` çıktısıdır. ESP şablonu orada `mark: sahte` diye durur ve uçak iğnesi almaz. `display: false` olan satır orada yoktur.
