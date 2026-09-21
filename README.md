# Ses Yazıcı

Windows üzerinde F8 global kısayoluyla mono 16 kHz ses kaydeden, seçilen çalışma akışında Türkçe metne çeviren ve odaktaki alana yapıştıran hafif Tkinter uygulaması.

## Çalışma modları

| Ayardaki seçim | STT | Metin işlemi | Kimlik bilgisi ve ağ |
|---|---|---|---|
| Kombine (Yerel Whisper + 9Router LLM) | Yerel Whisper (`base` varsayılan) | Ham transcript 9Router ile temizlenir | Yalnız 9Router anahtarı ve LLM ağı gerekir |
| Yalnızca Yerel (Ham / Çevrimdışı) | Yerel Whisper | Ham metin karakterleri değiştirilmeden yapıştırılır | Model hazır olduktan sonra API anahtarı veya ağ gerektirmez |
| Yalnızca 9Router / API | Yapılandırılan STT API | Transcript 9Router ile temizlenir | STT ve 9Router anahtarları ile iki uzak endpoint gerekir |

## API-only kurulum

Python 3.11+ ve Windows mikrofon izni gerekir.

    python -m venv .venv
    .venv\Scripts\activate
    pip install -r requirements.txt
    python main.py

`Yalnızca 9Router / API` için ilk açılıştan önce STT ve 9Router anahtarlarını Windows Credential Manager'a uygulamanın ayar ekranından kaydedin. Kombine mod yalnız 9Router anahtarı ister; yerel mod hiçbir anahtar istemez. Anahtarlar `config.json` içine yazılmaz. Ayar dosyası `%USERPROFILE%\.ses-yazici\config.json` konumundadır.

## Yerel STT kurulumu

    pip install -r requirements-local.txt

Kombine veya Yalnızca Yerel çalışma modunu ve `tiny` ya da varsayılan `base` modelini seçin. Yerel Whisper ilk kullanımda modeli indirmek için bağlantı ve disk alanı gerektirebilir. Model önceden hazırsa Yalnızca Yerel dikte bütünüyle çevrimdışıdır; STT/LLM API anahtarı veya ağ kullanmaz. Kombine modda yerel STT için anahtar gerekmez, fakat temizleme için 9Router anahtarı ve ağ gerekir.

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
