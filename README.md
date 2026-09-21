# Ses Yazıcı

Windows üzerinde F8 global kısayoluyla mono 16 kHz ses kaydeden, yerel Whisper ile Türkçe metne çeviren ve odaktaki alana yapıştıran Tkinter uygulaması.

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

Normal kullanımda `baslat.bat`, sabit sanal ortamdaki `pythonw.exe` ile terminalsiz başlatır. Başlatma hataları uygulama klasöründeki `error.log` dosyasına yazılır ve bir iletişim kutusuyla bildirilir.

## Anahtar ve veri sınırı

Kombine mod yalnız 9Router LLM anahtarını kullanır. Ayar ekranındaki 9Router anahtarı başlangıçta maskelidir; Göster/Gizle düğmesi değeri değiştirmeden görünürlüğü değiştirir. Anahtar `config.json` içine yazılmaz; keyring üzerinden Windows Credential Manager içinde saklanır.

`combined` akışında ses cihazda yerel olarak yazıya çevrilir, yalnız transcript temizleme için 9Router'a gönderilir. `local_only` akışında ses ve transcript uzak servise gönderilmez. Geçici WAV kullanım sonrası silinir; transcript geçmişi tutulmaz.

## Kullanım

Varsayılan F8 ve `toggle` modunda ilk fiziksel basış kaydı başlatır, ikinci basış bitirir. Tuşu basılı tutmaktan doğan tekrarlar yutulur. `push_to_talk` modunda F8 basılıyken kayıt yapılır ve bırakınca bitirilir.

Durum satırı `Hazır`, `Dinleniyor`, `Düzenleniyor`, `Yazıldı` veya `Hata` gösterir. Form alanları ve Göster/Gizle düğmesi Tab ile dolaşılabilir; ttk düğmesi Space/Enter ile çalışır. Tray varsa pencereyi kapatmak gizler; tam çıkış için tray menüsündeki Çıkış kullanılır.

## Sorun giderme

- Mikrofon açılmıyorsa Windows Ayarlar > Gizlilik ve güvenlik > Mikrofon altında masaüstü uygulama iznini açın.
- Global kısayol çalışmıyorsa F8 çakışmasını ve uygulama/hedef editör yetki düzeylerini kontrol edin.
- Yerel backend bulunamazsa aynı ortamda `pip install -r requirements-local.txt` çalıştırın.
- Kombine temizleme hatasında 9Router adresini, modeli, ağı ve Windows Credential Manager kaydını kontrol edin. Hata halinde metin yapıştırılmaz.
- Clipboard koruması yalnız text içindir; görsel ve özel formatlar kapsam dışıdır.

## Test

    python -m pytest -q

Packaging, installer, otomatik güncelleme, VAD ve streaming kapsam dışıdır.
