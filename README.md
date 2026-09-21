# Ses Yazıcı

Windows üzerinde F8 global kısayoluyla mono 16 kHz ses kaydeden, API veya yerel Whisper ile Türkçe metne çeviren, 9Router ile anlamı koruyarak düzenleyen ve odaktaki alana yapıştıran hafif Tkinter uygulaması.

## API-only kurulum

Python 3.11+ ve Windows mikrofon izni gerekir.

    python -m venv .venv
    .venv\Scripts\activate
    pip install -r requirements.txt
    python main.py

İlk açılıştan önce STT ve 9Router anahtarlarını Windows Credential Manager'a uygulamanın ayar ekranından kaydedin. Anahtarlar `config.json` içine yazılmaz. Ayar dosyası `%USERPROFILE%\.ses-yazici\config.json` konumundadır.

## Yerel STT kurulumu

    pip install -r requirements-local.txt

Ayar ekranında `local` ve `tiny` veya `base` seçin. İlk kullanım model indirebilir; bu nedenle bağlantı ve disk alanı gerekir. Yerel STT seçilince STT API anahtarı gerekmez. 9Router anahtarı yine gerekir.

## Kullanım: Toggle ve Push-to-Talk

Varsayılan F8 ve `toggle` modunda ilk basış kaydı başlatır, ikinci basış bitirir. `push_to_talk` modunda tuşa basılı tutun. Kısayol, mod, STT ve LLM ayarları label'lı formdan değiştirilebilir. Kaydetme başarısız olursa eski global binding çalışmaya devam eder.

Durum satırı renk dışında metinle de `Hazır`, `Dinleniyor`, `Düzenleniyor`, `Yazıldı` veya `Hata` gösterir. Alanlar Tab ile dolaşılabilir; API key alanları maskelidir.

## Tray ve çıkış

Tray kullanılabiliyorsa pencerenin kapatma düğmesi uygulamayı tray'e küçültür. Tray menüsünde `Göster`, `Kaydı başlat / bitir`, `Çıkış` bulunur. Tray başlatılamazsa pencereyi kapatmak uygulamadan çıkar. Tam çıkış için tray `Çıkış` kullanılmalıdır. Tray menüsünün ekran okuyucu/klavye desteği işletim sistemi ve pystray backend'iyle sınırlı olabilir.

## Güvenlik ve veri sınırları

- API anahtarları plaintext dosya, log veya traceback'e yazılmaz; keyring üzerinden Windows Credential Manager'da saklanır.
- Uzak endpoint yalnız HTTPS olabilir. Geliştirmede HTTP yalnız localhost/loopback için kabul edilir.
- Ses ve transcript geçmişi diskte tutulmaz. Yerel Whisper geçici WAV dosyasını kullanım sonrası siler.
- Ham konuşma API STT'ye ve metin 9Router'a gönderilebilir. Hassas içerikte servis politikalarını değerlendirin.
- LLM düşük temperature ve kısıtlı prompt kullanır; anlamı değiştirmeme hedefi mutlak garanti değildir. Sonucu kontrol edin.
- Clipboard koruması yalnız text içindir. Görsel/özel formatlar MVP kapsamında korunmaz. Pipeline sırasında panoyu siz değiştirirseniz yeni değer restore tarafından ezilmez.

## Windows izinleri ve sorun giderme

### Mikrofon açılmıyor
Windows Ayarlar > Gizlilik ve güvenlik > Mikrofon bölümünde masaüstü uygulama iznini açın. Doğru giriş aygıtını Windows'ta varsayılan yapın. Uygulama otomatik yönetici yükseltmesi yapmaz.

### Global kısayol çalışmıyor
F8 başka yazılımla çakışıyorsa ayarlardan farklı bir kısayol seçin. Güvenlik yazılımı `keyboard` hook'unu engelleyebilir. Uygulamayı ve hedef editörü aynı yetki düzeyinde çalıştırın.

### API/timeout veya boş yanıt
Base URL, model ve Windows Credential Manager kayıtlarını kontrol edin. Uygulama ağ, STT veya LLM hatasında hiçbir metin yapıştırmaz. Uzak HTTP endpoint reddedilir.

### Yerel backend bulunamadı
`pip install -r requirements-local.txt` komutunu aynı sanal ortamda çalıştırın. Yalnız `tiny` ve `base` desteklenir.

## Test

Gerçek ağ, mikrofon ve klavye gerektirmeyen suite:

    python -m pytest -q

Packaging, installer, otomatik güncelleme, floating overlay, VAD ve streaming bu MVP kapsamı dışındadır.
