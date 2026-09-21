# Ses Yazıcı v3 Robust Engine — Implementation Plan

PLAN_ARTIFACT

scope_id: `ses-yazici-v3-robust-2026-09-21`
iteration: `1`
status: `READY_FOR_ASENA`

## Parent transfer block

- `parent_artifact`: `USER_REQUEST/2026-09-21/ses-yazici-v3-robust-engine`
- `scope_id`: `ses-yazici-v3-robust-2026-09-21`
- `acceptance_inventory`: Bu belgedeki "Locked acceptance inventory"; A1–A13 zorunlu, A14 isteğe bağlı kabul maddeleridir. Anlamları ve sınırları uygulama/review süresince değiştirilemez.
- `evidence_required`: Her kabul maddesi için tabloda tanımlanan tek satırlık kanıt zinciri; ardından taze hedefli pytest, tam pytest ve statik diff kanıtı. Bir worker'ın çıkış kodu veya öz bildirimi doğrulama sayılamaz.
- `out_of_scope`: Yeni STT/LLM sağlayıcısı ekleme, bulut STT API'si getirme, model listesini `tiny`/`base` dışına çıkarma, installer/exe/auto-updater derleme, yeni GUI framework dayatma, VPS/deploy/sync/rollback işlemleri, git commit/push, secrets/tokens/şifreleri loga veya metne yazma.
- `iteration`: `1`
- `blockers`: `Yok.` Kısayol Combobox'ı doğrudan izin verilen liste ile sunulacak, `keyboard` kütüphanesi repodan tamamen temizlenerek `pynput` standardına geçilecektir.

---

## 1. Goal · Architecture · Tech/repo

**Goal:** `ses-yazici` uygulamasını endüstri standardı dikte araçları (savbell/whisper-writer, OpenWhisper) mimarisine kavuşturarak; `pynput` tabanlı sağlam Windows kısayol motoru, tanımlı kısayol Combobox'ı, maskeli/kalıcı API anahtarı yönetimi, anlık görsel geri bildirimli Test/Durdur butonu ve `app_logger.py` ile `app.log` debug kayıt zinciri sağlamak.

**Architecture:** Kısayol dinleme ve tuş simülasyonu katmanı `keyboard` bağımlılığından tamamen arındırılarak `pynput` (`pynput.keyboard.Listener`, `HotKey` ve `Controller`) altyapısına geçirilir; tek basış ve kombinasyonlar (`F8`, `F9`, `F10`, `F12`, `Ctrl+Alt+Space`, `Ctrl+Shift+D`) için hem `toggle` (autorepeat filtreli) hem de `push_to_talk` (tuş bırakma algılamalı) kenar tetiklemesi garanti edilir. Tüm runtime adımları (hotkey, ses kayıt metrikleri, yerel Whisper transkripsiyonu, 9Router LLM temizleme ve pano yapıştırma) `app_logger.py` üzerinden API anahtarı sızdırmadan zaman damgalı olarak `app.log` dosyasına debug düzeyinde akar ve GUI üzerindeki "Logları Aç" butonuyla sistem editöründe görüntülenebilir. GUI katmanında serbest metin kısayol girişi readonly Combobox'a dönüştürülür, kayıtlı API anahtarı açılışta maskeli doldurulup kaydetme sonrasında temizlenmez, "Test Et" butonu ise `LISTENING` durumunda doğrudan "Durdur"a ve "Dinleniyor..." durumuna reaktif olarak evrilir.

**Tech / repo:** Python 3.11+, Tkinter/ttk, `pynput` (global hotkeys + text injection), `faster-whisper` (yerel STT), `sounddevice` (mikrofon), `pyperclip` (pano), `httpx` (yalnız 9Router LLM), `keyring` (yalnız 9Router anahtarı), `pytest`; kaynak repo `C:/Users/esahi/OneDrive/Masaüstü/git_r/ses-yazici`.

**TDD / DRY / YAGNI:** Her görevde önce failing test, ardından minimum implementasyon ve hedefli pass koşulur. Kısayol allowlist'i ve renk tokenları tek kaynaktan gelir; gereksiz aracı katmanlar, harici logging servisleri veya kullanılmayan konfigürasyon alanları eklenmez.

### Repo/source-build ayrımı

- **A) Kaynak feature + test:** Bu plan Python kaynak dosyalarını (`app_logger.py`, `hotkeys.py`, `settings.py`, `gui.py`, `text_injector.py`, `controller.py`, `audio_recorder.py`, `transcriber.py`, `llm_cleaner.py`, `main.py`), `requirements.txt`, `.gitignore`, `README.md` ve pytest testlerini kapsar.
- **B) Generated/release output:** Repoda derlenen ayrı binary/dist/deploy hedefi yoktur. `baslat.bat` kaynak başlatıcıdır; exe/installer oluşturma kapsam dışıdır.
- Test çıktısı veya statik kontrol doğrudan release onayı sayılamaz; her aşama kendi doğrulanmış kanıtını sunar.

### Davranış sınıflandırması

| İddia | Sınıf | Mevcut repo kanıtı | Hedef davranış |
|---|---|---|---|
| Hata olunca hiçbir iz yok | `diagnostics/trace` + `render/state` | Repoda yalnızca `main.py` başlangıç çökmeleri için `error.log` var; çalışma anı hotkey, mic, whisper, 9router ve pano olayları loglanmıyor; arayüzde log açma eylemi yok. | `app_logger.py` ile `app.log` dosyasına zaman damgalı yapılandırılmış log yazılır (hotkey, mic byte/süre, Whisper sonucu, 9Router yanıtı, pano); GUI'de "Logları Aç" butonu ile dosya tek tıkla açılır; API anahtarları asla loga düşmez. |
| Kısayol serbest metin kutusu olmamalı | `form/action` | `gui.py` `FIELD_SPECS` içinde `("Global kısayol", "hotkey", ())` serbest `ttk.Entry` açıyor; kullanıcı tanımsız veya hatalı string girebiliyor. | `hotkey` alanı `ALLOWED_HOTKEYS` seçenekleriyle readonly `ttk.Combobox` olur; serbest metin girişi engellenir; `settings.py` büyük/küçük harf toleransıyla canonical formata normalize eder. |
| Kısayol Windows'ta çalışmıyor | `input/hook` + `form/action` | `hotkeys.py` ve `text_injector.py` Windows'ta non-admin yetkilerde veya non-English klavyelerde kancaları düşebilen `keyboard` kütüphanesini kullanıyor. | Savbell/whisper-writer endüstri standardı olan `pynput` kütüphanesine geçilir; Windows'ta non-admin, non-English klavyelerde kararlı tuş dinleme ve simülasyonu sağlanır; `keyboard` tamamen kaldırılır. |
| API anahtarı kutusu siliniyor ve başlangıçta boş geliyor | `render/state` + `form/action` | `gui.py::_build` içinde `defaults["llm_key"] = ""` atanıyor; `save()` metodunda `self.vars["llm_key"].set("")` çağrılarak kullanıcının girdiği anahtar kutudan siliniyor. | Açılışta kayıtlı anahtar varsa Entry içine doldurulur ve `show="*"` ile maskeli gösterilir; kullanıcı "Kaydet"e bastığında anahtar kutusu silinmez; "Göster/Gizle" butonu `show` özelliğini `*` ↔ `""` yaparak değeri korur. |
| Kayıt alınamıyor algısı / Test butonu geri bildirimsiz | `render/state` | `gui.py` içindeki "Test Et" butonu anonim bir `ttk.Button` olup basıldığında metni değişmiyor; `controller.py` ise `AppState.LISTENING` için `"Dinleniyor"` tekdüze metnini veriyor. | Buton `self.test_btn` referansına bağlanır; kayıt başladığında buton metni `"Durdur"` olur ve durum metni açıkça `"Dinleniyor..."` yazar; kayıt durdurulunca buton `"İşleniyor..."` (disabled) olur; işlem bitince tekrar `"Test Et"` (normal) durumuna döner. |

---

## 2. Design surface

**Design surface:** `rasyon_web_ui` koyu yeşil masaüstü uygulama dilinin native Tk/ttk uyarlaması.

**Token source path:** Repo içi `ui_tokens.py`; kanonik tasarım kaynağı `Notlar/91 - AI Context/DESIGN_SYSTEM.md`, surface referansı `rasyon_web_ui/src/index.css`.

**Design read:** Sıkı, işlevsel ve yüksek kontrastlı Türkçe masaüstü ayar kartı; zemin ve kart `#1e1e2e`, input `#2d2d3f`, yazı `#ffffff`, yeşil aksan `#22c55e`, yardımcı mavi eylemler `#3b82f6`; renk literal'leri `gui.py`ye dağılmaz.

**Token kararı:** Tüm renk ve boşluk değerleri `ui_tokens.py` içerisindeki `COLORS` ve `SPACING` sözlüklerinden alınır. "Logları Aç" ve "Test Et" butonları `Secondary.TButton`, "Kaydet" butonu `Primary.TButton` stilini kullanır; superseded toprak/tarla paleti kesinlikle kullanılmaz.

---

## 3. Locked acceptance inventory

| ID | Sınıf | Kilitli kabul maddesi | Kanıt şekli |
|---|---|---|---|
| A1 | zorunlu | `app_logger.py` modülü `setup_logging()`, `get_logger()`, `get_log_path()` ve `open_log_file()` API'lerini sunar; zaman damgalı format `%(asctime)s [%(levelname)s] [%(name)s] %(message)s` ile `app.log` dosyasına UTF-8 debug log yazar; API anahtarlarını ASLA loglamayan redaction/güvenlik sözleşmesi bulunur. | unit test → logger config assertion → file write trace → secret sanitization check |
| A2 | zorunlu | Pipeline bileşenleri (hotkey basış/bırakış/tetikleme, ses kayıt byte/süre/chunk, transcriber model/süre/metin uzunluğu, LLM cleaner endpoint/süre/uzunluk, text injector pano/tuş, controller state geçişleri/traceback) `app.log`a debug/info log üretir; 9Router API anahtarı veya yetkilendirme başlığı log dosyasına yazılmaz. | pipeline execution trace → log file read → expected tags presence → secret absence regex scan |
| A3 | zorunlu | GUI'de "Logları Aç" butonu (`Secondary.TButton`) yer alır; tıklandığında `app.log` dosyası (mevcut değilse boş oluşturularak) platform standart aracıyla (`os.startfile` / fallback) açılır; GUI kilitlenmez veya hata vermez. | widget inventory → button style assertion → click action spy → file existence & open call trace |
| A4 | zorunlu | Kısayollar için kilitli allowlist tanımlanır: `ALLOWED_HOTKEYS = ("F8", "F9", "F10", "F12", "Ctrl+Alt+Space", "Ctrl+Shift+D")`; `AppSettings.hotkey` varsayılan `"F8"` olur; `normalize_hotkey()` büyük/küçük harf toleransıyla canonical formata dönüştürür; geçersiz değerler sanitize `SettingsError` fırlatır; eski config'teki `"f8"` hatasız `"F8"`e evrilir. | constant inventory → normalization matrix → legacy JSON load → invalid hotkey rejection test |
| A5 | zorunlu | GUI'deki `Global kısayol` alanı serbest metin Entry'den çıkarılarak readonly `ttk.Combobox` haline getirilir; sadece `ALLOWED_HOTKEYS` seçeneklerini sunar; ViewModel ve GUI bu değerleri canonical olarak bağlar. | `FIELD_SPECS` inspection → Combobox readonly state → dropdown values assertion → ViewModel round-trip |
| A6 | zorunlu | `hotkeys.py` kütüphane bağımlılığı `keyboard` yerine savbell/whisper-writer standardı olan `pynput` (`pynput.keyboard.Listener` & `HotKey`) mimarisine geçirilir; Windows'ta non-admin çalışır; `toggle` modunda tek basış tek eylem üretir, autorepeat yutulur; `push_to_talk` modunda basış başlatır, tuş bırakma durdurur; yeniden kayıt atomiktir. | pynput backend spy → toggle repeat trace → PTT press/release trace → atomic re-register trace |
| A7 | zorunlu | `text_injector.py` ve `main.py` içindeki `keyboard` bağımlılığı tamamen kaldırılır; pano yapıştırma tuşu (`ctrl+v`) `pynput.keyboard.Controller` tabanlı `PynputKeyboardAdapter` üzerinden gönderilir; `requirements.txt` dosyasından `keyboard` çıkarılır, `pynput>=1.7.7,<2` eklenir. | dependency scan (`keyboard` absent) → `requirements.txt` assertion → injector paste spy with pynput adapter |
| A8 | zorunlu | CredentialStore'da kayıtlı 9Router anahtarı varsa uygulama açılışında GUI `llm_key` alanına bu anahtar doldurulur ve varsayılan olarak `show="*"` ile maskeli gösterilir; kayıtlı anahtar yoksa alan boş başlar. | credential mock with key → GUI init → entry get equals key → entry show attribute is `*` |
| A9 | zorunlu | GUI'de "Kaydet" butonuna basıldığında `llm_key` giriş kutusundaki metin silinmez (`set("")` çağrılmaz); girilen anahtar CredentialStore'a kaydedilir, kutuda maskeli (veya seçili görünümde) kalmaya devam eder. | GUI save action → credential store verify → entry text retains value → no wipe assertion |
| A10 | zorunlu | 9Router anahtarı yanındaki "Göster/Gizle" butonu tıklandığında Entry widget'ının `show` özelliği `*` ↔ `""` arasında değişir; buton metni `Göster` ↔ `Gizle` olarak güncellenir; anahtar değeri korunur ve keyring çağrısı yapılmaz. | entry show `*` → click toggle → show `""` & label `Gizle` → click toggle → show `*` & label `Göster` |
| A11 | zorunlu | Arayüzdeki "Test Et" butonu tıklandığında veya hotkey ile kayıt başladığında buton metni `"Durdur"` olur ve durum metni açıkça `"Dinleniyor..."` yazar; kayıt durdurulup işleme geçildiğinde buton `"İşleniyor..."` (`disabled`) olur; işlem bitince veya hata oluşunca buton tekrar `"Test Et"` (`normal`) durumuna döner. | start event → button text `"Durdur"` & status `"Dinleniyor..."` → stop event → `"İşleniyor..."` disabled → finish event → `"Test Et"` normal |
| A12 | zorunlu | `.gitignore` dosyası `app.log`, `error.log` ve `*.log` desenlerini içerecek şekilde güncellenir; log dosyaları git izlemesine takılmaz. | `.gitignore` content scan → pattern match assertion |
| A13 | zorunlu | Dokümantasyon (`README.md`) ve test kontratı (`tests/test_readme.py`) V3 pynput mimarisi, tanımlı kısayol listesi, `app.log` loglama, "Logları Aç" butonu ve dinamik görsel geri bildirimlerle güncellenir; kaldırılan `keyboard` referansları temizlenir. | docs keyword scan → forbidden terms absence (`keyboard`) → example config verification |
| A14 | isteğe bağlı | `app_logger.py` için `RotatingFileHandler` kullanılarak log boyutu 5 MB ve maksimum 3 yedek dosya ile sınırlandırılır; disk taşması önlenir. | handler class assertion → maxBytes & backupCount check |

**Acceptance freeze:** Yargu yalnızca gerçek güvenlik açığı, veri kaybı veya yukarıdaki kilitli kabul maddelerinin ihlalinde `dosya:satır + somut etki` ile blocking hüküm verebilir. Diğer iyileştirme önerileri SARI/sonraki iş olarak işaretlenir.

---

## 4. Files

| Path | Create/Edit | Sorumluluk |
|---|---|---|
| `app_logger.py` | Create | Zaman damgalı dosya loglaması (`app.log`), logging kurulumu, `get_logger()`, API anahtarı maskeleme, `get_log_path()` ve `open_log_file()` yardımcıları. |
| `settings.py` | Edit | `ALLOWED_HOTKEYS` sabit kümesi, `normalize_hotkey()` fonksiyonu, hotkey validasyonu, geriye dönük uyumlu `SettingsStore.load()`. |
| `hotkeys.py` | Edit | `pynput.keyboard` tabanlı `HotkeyService` (savbell/whisper-writer standardı); toggle/push_to_talk modları, autorepeat koruması, atomik listener yaşam döngüsü. |
| `text_injector.py` | Edit | `pynput.keyboard.Controller` kullanan `PynputKeyboardAdapter` sınıfı; `keyboard` kütüphanesi bağımlılığının kaldırılması. |
| `requirements.txt` | Edit | `keyboard` kütüphanesinin kaldırılması, yerine `pynput>=1.7.7,<2` eklenmesi. |
| `audio_recorder.py` | Edit | Kayıt başlangıcı, audio chunk metrikleri, toplam byte/süre ve durma/iptal adımlarının debug loglanması. |
| `transcriber.py` | Edit | WAV boyutu, model bilgisi, transkripsiyon süresi ve metin uzunluğunun debug loglanması. |
| `llm_cleaner.py` | Edit | Model, endpoint, HTTP yanıt süresi ve metin uzunluğunun loglanması; API key'in ASLA loglanmaması. |
| `controller.py` | Edit | `STATUS_TEXT` güncellemesi (`"Dinleniyor..."`), durum geçişleri ve pipeline traceback loglaması. |
| `gui.py` | Edit | Kısayol Combobox'ı, açılışta maskeli API anahtarı yükleme, kaydetme anında anahtar kutusunu silmeme, "Logları Aç" butonu, "Test Et" / "Durdur" dinamik buton yönetimi. |
| `main.py` | Edit | `import keyboard` satırının kaldırılması, `setup_logging()` çağrısı, pynput tabanlı adapter kurulumu. |
| `.gitignore` | Edit | `app.log`, `error.log`, `*.log` desenlerinin eklenmesi. |
| `README.md` | Edit | V3 pynput mimarisi, izin verilen kısayol listesi, loglama, GUI butonları ve sorun giderme dokümantasyonu. |
| `tests/test_logger.py` | Create | `app_logger.py` birim testleri (format, log yazımı, secret redaction, path ve open kontratı). |
| `tests/test_settings.py` | Edit | `ALLOWED_HOTKEYS`, case-insensitive normalizasyon, legacy `f8` yükleme ve geçersiz hotkey testleri. |
| `tests/test_hotkeys.py` | Edit | `pynput` tabanlı `HotkeyService` testleri (mock listener, toggle repeat suppression, ptt release, hata yönetimi). |
| `tests/test_text_injector.py` | Edit | `PynputKeyboardAdapter` ve `TextInjector` testleri. |
| `tests/test_gui.py` | Edit | Kısayol Combobox, başlangıç maskeli key, silinmeyen key girişi, "Logları Aç" ve dinamik "Test Et"/"Durdur" buton testleri. |
| `tests/test_imports.py` | Edit | `app_logger` modülünün import listesine eklenmesi. |
| `tests/test_readme.py` | Edit | Yeni kısayol listesi, pynput, `app.log` varlığı ve `keyboard` kütüphanesi yokluğu kontrolleri. |
| Generated production output | N/A | Ayrı derlenmiş build dizini yoktur; repo masaüstü Python script projesidir. |
| VPS/deploy directory | N/A | Bu masaüstü yerel repo işi VPS deploy içermez. |

---

## 5. Tasks

### Task 1 — Yapılandırılmış Loglama Altyapısı (`app_logger.py`) ve Güvenlik Sınırı

**Done when:** `app_logger.py` modülü `setup_logging()`, `get_logger()`, `get_log_path()` ve `open_log_file()` fonksiyonlarını sunar; `app.log` dosyasına zaman damgalı formatta debug log yazar; secret redaction filtresi ile API anahtarlarının loga yazılmasını engeller; `.gitignore` log dosyalarını kapsar; `tests/test_logger.py` yeşil geçer.

- [ ] (2–5 dk) `tests/test_logger.py` dosyasını oluştur: log formatı, `app.log` dosyasına yazma, logger factory, API anahtarı maskeleme (`redact_secrets`), `get_log_path()` ve `open_log_file()` mock testlerini yaz (failing test).
- [ ] (2–5 dk) `app_logger.py` dosyasını oluştur:
  - `FORMAT = "%(asctime)s [%(levelname)s] [%(name)s] %(message)s"`
  - `get_log_path() -> Path`: Proje kökündeki `app.log` (veya `SES_YAZICI_LOG_PATH` env değişkeni).
  - `SecretFilter(logging.Filter)`: Mesaj içindeki `Bearer ...` veya bilinen hassas token desenlerini `[REDACTED]` ile filtreleyen logging filtresi.
  - `setup_logging(log_path: Path | None = None, level=logging.DEBUG)`: `RotatingFileHandler` (UTF-8, 5 MB, 3 backup) ve isteğe bağlı StreamHandler yapılandırır.
  - `get_logger(name: str) -> logging.Logger`: Modül bazlı logger döndürür.
  - `open_log_file(log_path: Path | None = None) -> None`: Dosya yoksa oluşturur, Windows'ta `os.startfile` (veya fallback) ile açar.
- [ ] (2–5 dk) `.gitignore` dosyasına `app.log`, `error.log` ve `*.log` satırlarını ekle.
- [ ] (2–5 dk) `tests/test_imports.py` içine `app_logger` modülünü ekle.
- [ ] Test komutu: `python -m pytest tests/test_logger.py tests/test_imports.py -q`

---

### Task 2 — Tanımlı Kısayol Allowlist'i ve Ayar Normalizasyonu (`settings.py`)

**Done when:** `settings.py` içinde `ALLOWED_HOTKEYS` sabiti tanımlanır; `normalize_hotkey()` fonksiyonu büyük/küçük harf toleransıyla girdileri canonical formata (`F8`, `F9`, `F10`, `F12`, `Ctrl+Alt+Space`, `Ctrl+Shift+D`) dönüştürür; geçersiz kısayollar sanitize `SettingsError` fırlatır; eski config'teki `"f8"` hatasız `"F8"`e evrilir.

- [ ] (2–5 dk) `tests/test_settings.py` içine `ALLOWED_HOTKEYS` tuple kontrolü, büyük/küçük harf normalizasyon testleri (`"f8"` → `"F8"`, `"ctrl+alt+space"` → `"Ctrl+Alt+Space"`), geçersiz kısayol (`"Ctrl+Shift+Z"`, `"F1"`, `""`) red testleri ve legacy JSON round-trip testlerini ekle (failing test).
- [ ] (2–5 dk) `settings.py` içinde `ALLOWED_HOTKEYS` tuple'ını tanımla:
  ```python
  ALLOWED_HOTKEYS = (
      "F8",
      "F9",
      "F10",
      "F12",
      "Ctrl+Alt+Space",
      "Ctrl+Shift+D",
  )
  ```
- [ ] (2–5 dk) `normalize_hotkey(hotkey: str) -> str` fonksiyonunu yaz:
  - Giriş metnini temizle (`strip()`).
  - Harf büyüklüğü duyarsız bir sözlük eşlemesi (`{k.lower(): k for k in ALLOWED_HOTKEYS}`) ile canonical formata çevir.
  - Eşleşme yoksa `SettingsError(f"Kısayol desteklenmiyor. İzin verilenler: {', '.join(ALLOWED_HOTKEYS)}")` fırlat.
- [ ] (2–5 dk) `AppSettings.hotkey` varsayılanını `"F8"` yap; `validate_settings()` içinde `normalize_hotkey()` çağır; `SettingsStore.load()` içinde okunan hotkey'i normalize ederek geriye dönük tam uyumluluk sağla.
- [ ] Test komutu: `python -m pytest tests/test_settings.py -q`

---

### Task 3 — Savbell Standardı `pynput` Tabanlı Global Hotkey Servisi (`hotkeys.py`)

**Done when:** `hotkeys.py` modülü `pynput.keyboard.Listener` ve `HotKey` mimarisiyle yeniden yapılandırılır; Windows'ta non-admin yetkilerle sorunsuz tuş dinler; hem tek tuş hem kombinasyonlarda `toggle` (autorepeat yutmalı) ve `push_to_talk` (tuş bırakma algılamalı) kenar tetiklemesini kusursuz sağlar; atomik yeniden kayıt ve temiz kaynak kapatma (`unregister`) garantilenir.

- [ ] (2–5 dk) `tests/test_hotkeys.py` dosyasını `pynput` mimarisine uygun mock listener/backend ile güncelle (failing test):
  - `toggle`: `down` → `down (repeat)` → `up` → `down` → `up` akışında yalnızca `["start", "stop"]` üretildiğini doğrula.
  - `push_to_talk`: `down` → `down (repeat)` → `up` akışında `["start", "stop"]` üretildiğini, komboda tuş bırakılınca `stop` tetiklendiğini doğrula.
  - Kombinasyon eşleme: `Ctrl+Alt+Space` ve `Ctrl+Shift+D` için canonical tuş kümesi doğrulaması.
  - Hata güvenliği: Callback istisnasında internal state bozulmaması, hatalı yeniden kayıtta eski listener'ın korunması.
- [ ] (2–5 dk) `hotkeys.py` içinde `pynput` formatına dönüştürücü yardımcıyı yaz:
  - `"F8"` → `"<f8>"`, `"Ctrl+Alt+Space"` → `"<ctrl>+<alt>+<space>"`, `"Ctrl+Shift+D"` → `"<ctrl>+<shift>+d"`.
- [ ] (2–5 dk) `HotkeyService` sınıfını `pynput.keyboard` üzerine kur:
  - `__init__(self, listener_factory=None)`: Enjekte edilebilir listener fabrikası (test edilebilirlik için).
  - `register(hotkey, mode, on_start, on_stop)`:
    - Normalleştirilmiş hotkey'i doğrula (`hotkey in ALLOWED_HOTKEYS`).
    - `pynput.keyboard.HotKey` nesnesi ve hedef tuş kümesini oluştur.
    - `_on_press(key)` ve `_on_release(key)` işleyicileri:
      - `HotKey.press(listener.canonical(key))` çağrısı (autorepeat pynput tarafından otomatik engellenir).
      - `toggle` modunda: `on_activate` anında aktif değilse `on_start()`, aktifse `on_stop()`.
      - `push_to_talk` modunda: `on_activate` anında `on_start()`; `_on_release(key)` anında bırakılan tuş hedef kombinasyonun parçasıysa `on_stop()`.
    - Yeni listener'ı başlatmadan önce eskisini durdur; kayıt hatasında eski listener'ı koru.
  - `unregister()`: Aktif listener'ı güvenle durdur ve sıfırla.
  - Her tetiklemede `app_logger` ile debug log üret.
- [ ] Test komutu: `python -m pytest tests/test_hotkeys.py -q`

---

### Task 4 — `text_injector.py` ve `requirements.txt`'den `keyboard` Bağımlılığını Kaldırma

**Done when:** `text_injector.py` içine `PynputKeyboardAdapter` eklenir; metin panoya kopyalanıp `pynput.keyboard.Controller` ile `ctrl+v` simüle edilir; `keyboard` kütüphanesine olan tüm kod ve paket bağımlılıkları sıfırlanır.

- [ ] (2–5 dk) `tests/test_text_injector.py` içine `PynputKeyboardAdapter` birim testini ekle: mock controller üzerinde `press(Key.ctrl)`, `press('v')`, `release('v')`, `release(Key.ctrl)` sıralamasını doğrula (failing test).
- [ ] (2–5 dk) `text_injector.py` içine `PynputKeyboardAdapter` sınıfını ekle:
  ```python
  class PynputKeyboardAdapter:
      def __init__(self, controller=None):
          if controller is None:
              from pynput.keyboard import Controller
              controller = Controller()
          self.controller = controller

      def send(self, hotkey: str) -> None:
          if hotkey.lower() in {"ctrl+v", "^v"}:
              from pynput.keyboard import Key
              self.controller.press(Key.ctrl)
              self.controller.press('v')
              self.controller.release('v')
              self.controller.release(Key.ctrl)
  ```
- [ ] (2–5 dk) `requirements.txt` dosyasını düzenle: `keyboard>=0.13.5,<1` satırını sil, yerine `pynput>=1.7.7,<2` satırını ekle.
- [ ] (2–5 dk) `TextInjector.paste()` içine logger çağrılarını ekle: panoya kopyalanan karakter sayısı, tuş gönderimi ve pano geri yükleme adımlarını debug logla.
- [ ] Test komutu: `python -m pytest tests/test_text_injector.py -q`

---

### Task 5 — Pipeline Bileşenlerine Debug Loglama Entegrasyonu

**Done when:** `audio_recorder.py`, `transcriber.py`, `llm_cleaner.py` ve `controller.py` bileşenleri tüm kritik operasyonları `app_logger` üzerinden yapılandırılmış biçimde loglar; API anahtarları asla loga yazılmaz; pipeline testleri yeşil geçer.

- [ ] (2–5 dk) `audio_recorder.py` içine loglama ekle:
  - Kayıt başlarken: `sample_rate`, `channels`, `max_seconds`.
  - Kayıt dururken: toplam alınan frame sayısı, toplam byte ve hesaplanan süre (`saniye`).
  - İptal durumunda: iptal kaydı.
- [ ] (2–5 dk) `transcriber.py` içine loglama ekle:
  - Transkripsiyon başlarken: model adı, hedef dil, gelen WAV byte boyutu.
  - Transkripsiyon bittiğinde: geçen süre (`ms`), üretilen metin uzunluğu ve ilk 50 karakterlik önizleme.
- [ ] (2–5 dk) `llm_cleaner.py` içine loglama ekle:
  - İstek atılırken: hedef endpoint URL, model adı, giriş metni uzunluğu (API ANAHTARI ASLA LOGLANMAZ).
  - Yanıt alındığında: HTTP yanıt süresi (`ms`), dönen temiz metin uzunluğu ve önizleme.
  - Hata durumunda: sanitize hata mesajı.
- [ ] (2–5 dk) `controller.py` içine loglama ve durum metni güncellemesi ekle:
  - `STATUS_TEXT[AppState.LISTENING] = "Dinleniyor..."` olarak güncelle.
  - `_emit()` ve `_pipeline()` içinde state geçişlerini, süreleri ve olası istisnalarda stack trace'i `logger.exception()` ile logla.
- [ ] Test komutu: `python -m pytest tests/test_controller.py tests/test_pipeline.py -q`

---

### Task 6 — GUI Geliştirmeleri (Combobox, API Key Kalıcılığı, Test/Durdur Butonu, Logları Aç)

**Done when:** GUI'de kısayol seçimi readonly `ttk.Combobox` ile `ALLOWED_HOTKEYS` listesinden yapılır; açılışta CredentialStore'daki API anahtarı maskeli dolu gelir; kaydetme sonrasında anahtar kutusu silinmez; "Göster/Gizle" butonu anahtarı koruyarak görünürlüğü değiştirir; "Test Et" butonu basıldığında veya hotkey tetiklendiğinde dinamik olarak "Durdur" ve "Dinleniyor..." geri bildirimi verir; "Logları Aç" butonu `app.log` dosyasını sistemde açar.

- [ ] (2–5 dk) `tests/test_gui.py` dosyasını güncelle (failing tests):
  - `FIELD_SPECS` içinde `hotkey` alanının choices tuple'ının `ALLOWED_HOTKEYS` olduğunu doğrula.
  - Açılışta kayıtlı anahtar varsa Entry widget'ının dolu ve `show="*"` olduğunu test et.
  - `save()` eyleminin `llm_key` değerini silmediğini, CredentialStore'a doğru yazdığını doğrula.
  - "Logları Aç" butonunun varlığını ve tıklandığında `open_log_file()` çağrısını test et.
  - "Test Et" butonunun `LISTENING` durumunda metninin `"Durdur"`, `TRANSCRIBING` durumunda `"İşleniyor..."` (disabled), `READY` durumunda `"Test Et"` olduğunu test et.
- [ ] (2–5 dk) `gui.py` içinde `FIELD_SPECS` tanımını güncelle:
  ```python
  ("Global kısayol", "hotkey", ALLOWED_HOTKEYS),
  ```
- [ ] (2–5 dk) `gui.py::_build` içinde başlangıç API anahtarı ve butonları kur:
  - `saved_key = self.credentials.get("llm_api_key") or ""`
  - `defaults["llm_key"] = saved_key`
  - Butonlar satırında üç buton yerleştir:
    1. `ttk.Button(buttons, text="Logları Aç", style="Secondary.TButton", command=self.open_logs)`
    2. `self.test_btn = ttk.Button(buttons, text="Test Et", style="Secondary.TButton", command=self.test_action)`
    3. `ttk.Button(buttons, text="Kaydet", style="Primary.TButton", command=self.save)`
- [ ] (2–5 dk) `gui.py::save` metodunu düzelt:
  - `self.vars["llm_key"].set("")` satırını KALDIR; anahtar metin kutusunda kalsın.
  - Kullanıcı kutuyu tamamen boşalttıysa `credentials.delete("llm_api_key")` çağır; doluysa `credentials.set("llm_api_key", key_val)` çağır.
- [ ] (2–5 dk) `gui.py::poll_events` ve `test_action` metodlarını reaktif hale getir:
  - State `LISTENING` olduğunda: `self.test_btn.configure(text="Durdur", state="normal")`.
  - State `TRANSCRIBING`, `CLEANING`, `INJECTING` olduğunda: `self.test_btn.configure(text="İşleniyor...", state="disabled")`.
  - State `READY`, `WRITTEN`, `ERROR` olduğunda: `self.test_btn.configure(text="Test Et", state="normal")`.
  - `open_logs()` metodunu bağla: `app_logger.open_log_file()`.
- [ ] Test komutu: `python -m pytest tests/test_gui.py -q`

---

### Task 7 — `main.py` Entegrasyonu, `README.md` ve Uçtan Uca Doğrulama

**Done when:** `main.py` içinden `keyboard` import'u tamamen kaldırılır; `app_logger.setup_logging()` çağrısı eklenir; `TextInjector`'a `PynputKeyboardAdapter` verilir; `README.md` ve `test_readme.py` güncellenir; tüm test suite eksiksiz YEŞİL geçer.

- [ ] (2–5 dk) `main.py` dosyasını güncelle:
  - `import keyboard` satırını sil.
  - `from app_logger import get_logger, setup_logging` ve `from text_injector import PynputKeyboardAdapter, TextInjector` ekle.
  - `create_app()` başlangıcında `setup_logging()` çağır; `HotkeyService()` ve `TextInjector(pyperclip, PynputKeyboardAdapter())` kurulumunu yap.
- [ ] (2–5 dk) `tests/test_main.py` dosyasını güncelle: `keyboard` referansı kalmadığını ve `pynput` tabanlı bileşenlerin doğru bağlandığını doğrula.
- [ ] (2–5 dk) `README.md` ve `tests/test_readme.py` dosyalarını güncelle:
  - V3 pynput mimarisi, tanımlı kısayol seçenekleri (`F8`, `F9`, `F10`, `F12`, `Ctrl+Alt+Space`, `Ctrl+Shift+D`), debug loglama (`app.log`), "Logları Aç" butonu ve dinamik "Test Et / Durdur" butonunu dokümante et.
  - Kaldırılan `keyboard` kütüphanesini yasaklı sözcükler listesine ekle.
- [ ] (2–5 dk) Tam regresyon koşumu yap ve doğrula.
- [ ] Test komutu: `python -m pytest`

---

## 6. Yargu beklentisi (Review Gates)

### Testler
- Yeni `tests/test_logger.py` ile dosya yazımı, rotasyon, redaction ve open log çağrısı %100 kapsanmalıdır.
- `tests/test_hotkeys.py` içinde pynput tabanlı listener için hem tek tuş hem kombinasyonlar, hem `toggle` autorepeat filtrelemesi hem de `push_to_talk` release davranışı doğrulanmalıdır.
- `tests/test_gui.py` içinde Combobox readonly state'i, maskeli anahtar başlangıcı, silinmeyen anahtar kutusu, log açma eylemi ve dinamik buton metin/state geçişleri test edilmelidir.
- `python -m pytest` komutunun tüm testleri (en az 65+ test) sıfır hata ile geçmelidir.

### Security Hotspots
- **Secret Redaction:** 9Router API anahtarı hiçbir koşulda `app.log` veya `error.log` dosyasına yazılmamalıdır. `llm_cleaner.py` ve `app_logger.py` bu izolasyonu garanti etmelidir.
- **Maskeli UI Girişi:** API anahtarı arayüzde varsayılan olarak `show="*"` ile açılmalı; sadece kullanıcının bilinçli "Göster" tıklamasıyla açık metne geçmelidir.
- **Git Temizliği:** `.gitignore` dosyası `app.log`, `error.log` ve `*.log` desenlerini barındırmalı; çalışma esnasında oluşan loglar repoya commit edilmemelidir.

### UI Checklist (Surface / Token / a11y)
- **Surface:** `rasyon_web_ui` koyu tema native Tk adaptasyonu.
- **Tokens:** Renkler sadece `ui_tokens.py` içinden (`COLORS`, `SPACING`) gelmelidir; `gui.py` içine `#hex` literal'i yazılamaz.
- **Erişilebilirlik:** Combobox `state="readonly"` olmalı, fare ve klavye ok tuşlarıyla dolaşılabilmeli; "Göster/Gizle", "Logları Aç", "Test Et" ve "Kaydet" butonları `takefocus=True` ile Tab sıralamasında yer almalıdır.

---

## 7. Yapma listesi (Out of Scope & Forbidden Actions)

1. **`keyboard` kütüphanesini projede tutma:** `requirements.txt`, `hotkeys.py`, `text_injector.py` ve `main.py` içinden `keyboard` tamamen çıkarılmalı, yerine `pynput` kullanılmalıdır.
2. **API anahtarını log dosyasına yazma:** `app.log` dosyasına debug log atarken `api_key`, `Authorization: Bearer ...` veya anahtar gövdesi asla yazılmamalıdır.
3. **Kaydet butonunda anahtar kutusunu temizleme:** `self.vars["llm_key"].set("")` çağrısı yapılmamalı; kullanıcının kaydettiği anahtar kutuda maskeli biçimde kalmalıdır.
4. **Serbest metin kısayol girişi bırakma:** `hotkey` alanı için serbest Entry bırakılmamalı; yalnızca `ALLOWED_HOTKEYS` içeren readonly Combobox kullanılmalıdır.
5. **Hardcoded renk literali yazma:** `gui.py` veya diğer modüllere `#1e1e2e`, `#22c55e` gibi hex kodları doğrudan yazılmamalı, `ui_tokens.py` kullanılmalıdır.
6. **Büyük kod uygulama (Asena'nın görevi):** Tonyukuk olarak kod dosyalarını doğrudan değiştirmekten kaçınılmalı, plan kilitlenerek Asena'ya teslim edilmelidir.
7. **Deploy / VPS işlemi yapma:** Bu masaüstü Python projesinde VPS/deploy adımı yoktur; release veya git push çalıştırılmamalıdır.
