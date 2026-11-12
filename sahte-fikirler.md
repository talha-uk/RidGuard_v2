# Sahte sinyal fikirleri

Bu dosya kural listesi sayılmaz. Ölçülmeden yazılan fikir buradadır. Koda yalnız ölçülen satır girer.

## Wi-Fi taramasında görünmek

Talha, 2026-11-12: Drone Wi-Fi ağı açamaz. Taramada görünüyorsa sahtedir.

Bu cümle ölçüldü diye koda girmedi.

Uçuş bağlantısı Wi-Fi listesine düşmez. MT bunu `$Feature` diye yazar. Örnek O3 frekansı 5796 MHz'dir. Bu, standart bir Wi-Fi kanalı sayılmaz.

ESP kart Wi-Fi beacon basar. Logda `protocol:beacon, channel:6` diye durur. Bu beacon tarama listesine düşebilir.

Gerçek Remote ID de beacon olarak yayınlanır. O da taramada görünebilir. Bazı küçük dronelar katılınabilir Wi-Fi ağı da açar.

Bu yüzden "taramada varsa sahtedir" kuralı konmadı. Gerçek yayını da sahte sayar.

Bu masada gerçek bir DJI ile ESP yan yana taranmadı. Ağ adının açık mı gizli mi olduğu modele göre değişir.

MT beacon'ı zaten `$RID` diye yazar. Laptop taraması aynı yayını bir kez daha görür. Sahte ile gerçeği ayıran şey taramada görünmek sayılmaz. Ayrım, serideki kalıptır: `1581F` + 3 karakter + `RID` + iki rakam + yedi `X`.

Şimdilik tarama tek başına hüküm olmaz. Seri kalıba uyuyorsa zaten sahte sayılır.
