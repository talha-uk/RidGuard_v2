# Ne yaptık

MT303'ün canlı kaydını izliyoruz ve sahte drone tespiti yapıyoruz.

ESP kart sahte drone kimliği yayıyor. MT303 bu yayını da yazıyor.

RidGuard bu kaydı okur. ESP kartın bilinen kalıbını **sahte** diye gösterir. Seri düzgünleşirse de bitmez. Hız söylenip konum yerinde kalırsa, yön ile gidiş uyuşmazsa, irtifa bir anda çok değişirse yine **sahte** olur. Dört kimlik yan yanaysa **sürü** olur. Bu sahte hükmü değildir. Seri düzgün ve tek başına ise **şüpheli** olur. Üçü de haritaya konmaz. Yayın gizlenmez.

Gerçek bir uçuş bağlantısı gelirse onu gösterir. Gövde yalan beacon da basabilir. Beacon, bağlantının yerinden 200 metreden fazla saparsa sahte olur. Bağlantı yoksa beacon şüpheli kalır.

Ekran iki parçadır. Solda MT303'ün canlı kaydı vardır. Sağda sahte, şüpheli ve sürü yayınlar vardır.

Program yalnız dinler. ESP kartın yayınını kendisi üretmez.

Teknik kurallar [OKU.md](OKU.md) içindedir.
