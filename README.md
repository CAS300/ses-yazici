# Ses Yazıcı

Windows üzerinde tanımlı global kısayollar (`F8`, `F9`, `F10`, `F12`, `Ctrl+Alt+Space`, `Ctrl+Shift+D`) ile `pynput` tabanlı motor üzerinden mono 16 kHz ses kaydeden, yerel Whisper ile Türkçe metne çeviren ve odaktaki alana yapıştıran Tkinter uygulaması.

## Çalışma modları

| Ayardaki seçim | Değer | İşlem | Kimlik bilgisi ve ağ |
|---|---|---|---|
| Kombine (Yerel Whisper + 9Router LLM) | `combined` | Yerel Whisper ham metni üretir; 9Router bir kez temizler | Yalnız 9Router anahtarı ve LLM ağı gerekir |
| Yalnızca Yerel (Ham / Çevrimdışı) | `local_only` | Ham metin karakterleri değiştirilmeden yapıştırılır | Model hazır olduktan sonra anahtar veya ağ gerekmez |

## Kurulum ve başlatma

Python 3.11+, Windows mikrofon izni ve yerel Whisper gereklidir.

    python -m venv .venv
    .venv\Scripts\activate
    pip install -r requirements.txt
    pip install -r requirements-local.txt

Yerel model olarak yalnız `tiny` ve varsayılan `base` desteklenir. Yerel Whisper ilk kullanımda modeli indirmek için bağlantı ve disk alanı gerektirebilir. Model hazır olduktan sonra `local_only` dikte yolu ağ kullanmaz.

Normal kullanımda `baslat.bat`, sabit sanal ortamdaki `pythonw.exe` ile terminalsiz başlatır. Başlatma hataları uygulama klasöründeki `error.log` dosyasına yazılır ve bir iletişim kutusuyla bildirilir. Çalışma anı logları ise `app.log` dosyasına debug düzeyinde akar.

CMD penceresi göstermeden elle başlatmak için `baslat_arkaplan.vbs` dosyasına çift tıklayın. Script önce proje klasöründeki `.venv\Scripts\pythonw.exe` dosyasını, yoksa PATH üzerindeki `pythonw.exe` komutunu kullanır ve `main.py` dosyasını doğru çalışma dizininden açar.

Windows oturumu açıldığında uygulamanın otomatik başlaması için `otomatik_baslat_kur.bat` dosyasına çift tıklayın. Script, kullanıcının `shell:startup` klasörüne `Ses Yazıcı.lnk` kısayolunu oluşturur veya günceller. Otomatik başlangıcı kaldırmak için `otomatik_baslat_kaldir.bat` dosyasını çalıştırın. Repo taşınırsa kurulum scriptini yeniden çalıştırın; üç script ile `main.py` aynı proje klasörü içinde tutulmalıdır.

## Anahtar ve veri sınırı

Kombine mod yalnız 9Router LLM anahtarını kullanır. Ayar ekranındaki 9Router anahtarı CredentialStore'dan yüklenerek başlangıçta `show="*"` ile maskelenir; Göster/Gizle düğmesi değeri koruyarak görünürlüğü değiştirir. "Kaydet" butonuna basıldığında anahtar kutusu silinmez. Anahtar `config.json` içine yazılmaz; keyring üzerinden Windows Credential Manager içinde güvenle saklanır. Log dosyalarına (`app.log`) API anahtarları asla yazılmaz.

`combined` akışında ses cihazda yerel olarak yazıya çevrilir, yalnız transcript temizleme için 9Router'a gönderilir. `local_only` akışında ses ve transcript uzak servise gönderilmez. Geçici WAV kullanım sonrası silinir; transcript geçmişi tutulmaz.

## Kullanım ve Arayüz

- **Kısayol Seçimi:** Kısayol, serbest metin yerine readonly Combobox üzerinden seçilir (`F8`, `F9`, `F10`, `F12`, `Ctrl+Alt+Space`, `Ctrl+Shift+D`).
- **Kayıt Modu:** `toggle` modunda ilk basış kaydı başlatır, ikinci basış bitirir; autorepeat tekrarları yutulur. `push_to_talk` modunda kısayol basılıyken kayıt yapılır ve tuş bırakıldığında sonlandırılır.
- **Dinamik Buton Geri Bildirimi:** Arayüzdeki "Test Et" butonu kayıt başladığında "Durdur" ve durum metni "Dinleniyor..." olur; kayıt durdurulup işleme geçildiğinde buton "İşleniyor..." (devre dışı) olur; işlem bitince veya hata durumunda tekrar "Test Et" haline döner.
- **Logları Aç:** Arayüzdeki "Logları Aç" butonu ile `app.log` dosyası sistem editöründe tek tıkla incelenebilir.
- Durum satırı `Hazır`, `Dinleniyor...`, `Düzenleniyor`, `Yazıldı` veya `Hata` durumlarını yansıtır.
- Form alanları ve butonlar klavyeyle Tab ile dolaşılabilir; tray simgesi varsa pencereyi kapatmak gizler, tam çıkış için menü kullanılır.

## Sorun giderme

- Mikrofon açılmıyorsa Windows Ayarlar > Gizlilik ve güvenlik > Mikrofon altında masaüstü uygulama iznini açın.
- Global kısayol çalışmıyorsa diğer uygulamalarla kısayol çakışmasını veya uygulama/hedef editör yetki düzeylerini kontrol edin.
- Ayrıntılı hata teşhisi için arayüzdeki "Logları Aç" butonuna tıklayarak `app.log` dosyasını inceleyin.
- Yerel backend bulunamazsa aynı ortamda `pip install -r requirements-local.txt` çalıştırın.
- Kombine temizleme hatasında 9Router adresini, modeli, ağı ve Windows Credential Manager kaydını kontrol edin. Hata halinde metin yapıştırılmaz.
- Clipboard koruması yalnız text içindir; görsel ve özel formatlar kapsam dışıdır.

## Test

    python -m pytest -q

Packaging, installer, otomatik güncelleme, VAD ve streaming kapsam dışıdır.
