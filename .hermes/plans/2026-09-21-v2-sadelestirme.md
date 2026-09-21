# Ses Yazıcı v2 Sadeleştirme — Implementation Plan

PLAN_ARTIFACT

scope_id: `ses-yazici-v2-sadelestirme-2026-09-21`
iteration: `1`
status: `READY_FOR_ASENA`

## Parent transfer block

- `parent_artifact`: `USER_REQUEST/2026-09-21/ses-yazici-v2-sadelestirme`
- `scope_id`: `ses-yazici-v2-sadelestirme-2026-09-21`
- `acceptance_inventory`: Bu belgedeki “Locked acceptance inventory”; A1–A12 sınıfları ve anlamları uygulama/review boyunca değiştirilemez.
- `evidence_required`: Her zorunlu kabul maddesi için tabloda belirtilen kanıt zinciri; ardından taze hedefli pytest, tam pytest ve statik diff kanıtı. Bir worker exit code’u veya öz bildirimi doğrulama değildir.
- `out_of_scope`: Yeni STT/LLM sağlayıcısı, STT API veya fallback, model seçeneğini tiny/base dışına genişletme, Whisper modelini paketleme, installer/exe/auto-update, yeni framework/dependency, tray yeniden tasarımı, deploy/VPS/sync/rollback, commit/push, mevcut LLM API’sini kaldırma.
- `iteration`: `1`
- `blockers`: `Yok.` “API key göster/gizle” talebi, STT key kaldırıldıktan sonra kalan `9Router API anahtarı` alanına uygulanacaktır.

## 1. Goal · Architecture · Tech/repo

**Goal:** Ses Yazıcı’yı yalnız yerel Whisper (`tiny`/`base`) kullanan iki akışa sadeleştirmek; yüksek kontrastlı Tk arayüzü, göster/gizle kontrollü 9Router anahtar alanı, güvenilir F8 kenar tetiklemesi ve `pythonw.exe` ile terminalsiz başlatma sağlamak.

**Architecture:** `AppSettings.flow_mode` yalnız `combined | local_only` değerlerini kabul eder ve STT ayarı sadece yerel model/dil taşır; composition root her iki modda da `LocalWhisperTranscriber` kurar, yalnız `combined` için mevcut LLM cleaner’ı ekler. Eski config içindeki `api_only`, `provider`, `api_base_url` ve `api_model` kontrollü bir legacy sınırında ele alınır: kullanılmayan STT alanları okunmadan atılır, artık desteklenmeyen `api_only` açık ve sanitize bir ayar hatası verir; gizli biçimde başka moda çevrilmez. Hotkey servisi tuş basma/bırakma kenarlarını ve auto-repeat guard’ını tek yerde yönetir; UI renkleri yalnız `ui_tokens.py` üzerinden gelir.

**Tech / repo:** Python 3.11+, Tkinter/ttk, `keyboard`, `faster-whisper`, httpx (yalnız LLM), keyring (yalnız LLM anahtarı), pytest; kaynak repo `C:/Users/esahi/OneDrive/Masaüstü/git_r/ses-yazici`.

**TDD / DRY / YAGNI:** Her davranış için önce failing test, sonra minimum implementation, sonra hedefli pass uygulanır. Mod kümeleri ve UI renkleri tek kaynaktan gelir; yeni strategy katmanı, tema motoru, launcher üreticisi veya ileride gerekebilir diye API abstraction’ı eklenmez.

### Repo/source-build ayrımı

- **A) Kaynak feature + test:** Bu plan Python kaynaklarını, Tk tokenlarını, Windows launcher’ı, config örneğini, README’yi ve pytest testlerini kapsar.
- **B) Generated/release output:** Repoda ayrı generated production build, paket veya deploy dizini yoktur. `baslat.bat` kaynak launcher’dır; build/deploy değildir. Yeni exe/installer üretimi ve yayın kapsam dışıdır.
- Test veya launcher statik doğrulamasından release/deploy başarısı çıkarılamaz.

### Davranış sınıflandırması

| İddia | Sınıf | Mevcut repo/DOM eşdeğeri kanıtı | Hedef davranış |
|---|---|---|---|
| Entry/Combobox metni okunaksız | `render/state` | `gui.py::_style` input `fieldbackground`ını kart rengine bırakıyor; readonly Combobox state renk map’i ve listbox rengi tanımlı değil. | Entry ve Combobox normal/focus/readonly durumlarında `#2d2d3f` zemin ve `#ffffff` metin; görünür focus/border. |
| API key maskesi açılıp kapanamıyor | `form/action` | `gui.py::_build` key alanlarını da genel döngüde `show="*"` ile kuruyor; widget referansı/toggle action yok. | Kalan 9Router key alanının yanındaki klavye erişilebilir kontrol `show="*" ↔ ""` değiştirir; değeri değiştirmez veya açılışta ifşa etmez. |
| F8 güvenilir değil | `form/action` | `hotkeys.py` toggle için `add_hotkey(... trigger_on_release=False)` kullanıyor ve `_active` değerini callback tamamlanmadan değiştiriyor; key auto-repeat/istisna davranışı açıkça kilitli değil. | Bir fiziksel basış yalnız bir start/stop üretir, basılı tutma repeat’i ikinci eylem üretmez, release bir sonraki basışı hazırlar; callback/yeniden kayıt hatası eski sağlam binding’i bozmaz. |
| Başlatmada terminal görünüyor | `navigation/link` (launcher) | `baslat.bat` doğrudan `...Scripts\python.exe main.py` çağırıyor. | Launcher aynı yorumlayıcının `pythonw.exe` executable’ını kullanır; çalışma dizini/script yolu boşluklara dayanır ve hata `error.log` + GUI iletişim kanalında kalır. |

## 2. Design surface

**Design surface:** `rasyon_web_ui` koyu yeşil masaüstü uygulama dilinin native Tk/ttk uyarlaması.

**Token source path:** Repo içi `ui_tokens.py`; kanonik tasarım kaynağı `C:/Users/esahi/OneDrive/Belgeler/Notlar/91 - AI Context/DESIGN_SYSTEM.md`, surface referansı `rasyon_web_ui/src/index.css`.

**Design read:** Sıkı ve işlevsel Türkçe masaüstü ayar kartı; kullanıcının kilitlediği koyu kart `#1e1e2e`, input `#2d2d3f`, beyaz yazı `#ffffff` ile erişilebilir kontrast, güven için belirgin yeşil primary ve yardımcı eylem için mavi secondary kullanılır; superseded toprak/serif tarla dili kullanılmaz.

**Token kararı:** Yukarıdaki üç hex kullanıcı tarafından açıkça kilitlenmiştir ve `ui_tokens.py` içinde adlandırılmış token olur; `gui.py` içine renk literal’i yazılmaz. Yeşil primary mevcut house `#22c55e` ile korunur; mavi secondary mevcut house dual-accent dilinden seçilip token dosyasında tek kez tanımlanır. Asena, mavi değer için repo/kanon referansındaki uygun değeri kullanmalı ve kanıtlamalıdır; rastgele ek palet üretmemelidir.

## Locked acceptance inventory

| ID | Sınıf | Kilitli kabul maddesi | Kanıt şekli |
|---|---|---|---|
| A1 | zorunlu | Desteklenen tek akış değerleri `combined` ve `local_only` olur; default `combined`, yerel model default `base`, geçerli modeller yalnız `tiny`/`base` kalır. | type/allowed set → defaults → validation matrix → save/load equality |
| A2 | zorunlu | STT API çalışma kodundan kaldırılır: `ApiWhisperTranscriber`, STT HTTP isteği, STT credential okuma/yazma ve runtime provider seçimi bulunmaz; iki mod da `LocalWhisperTranscriber` kurar. | source symbol scan → per-mode factory spy → credential call log → HTTP request log `0` for STT |
| A3 | zorunlu | GUI’de `stt_url`, `stt_model`, `stt_key` ve `api_only` seçeneği bulunmaz; çalışma modu readonly olarak yalnız anlaşılır iki Türkçe etiketi gösterir; `local_model` tiny/base seçimi kalır. | `FIELD_SPECS` inventory → readonly choices → ViewModel canonical payload |
| A4 | zorunlu | `combined`: yerel Whisper ham metni üretir, mevcut 9Router cleaner bir kez temizler, temiz metin bir kez yapıştırılır; yalnız LLM key/HTTPS endpoint gerekir. | F8/controller start → local STT → raw → one cleaner call → paste(cleaned) → WRITTEN |
| A5 | zorunlu | `local_only`: yerel Whisper ham metni karakterlerini değiştirmeden bir kez yapıştırır; cleaner, LLM key ve ağ isteği yoktur. | local STT → exact raw payload → no cleaner/key/HTTP → paste(raw) → WRITTEN |
| A6 | zorunlu | Eski config’teki tanınan STT API alanları (`provider`, `api_base_url`, `api_model`) veri kaybı/hata yaratmadan yok sayılır ve bir sonraki save’de yazılmaz; eski `api_only` sessizce çevrilmeyip sanitize `SettingsError` verir. | legacy raw JSON → load result/error by case → save raw payload → obsolete-key absence |
| A7 | zorunlu | `CredentialStore` ve GUI yalnız `llm_api_key` kabul eder; uygulama `stt_api_key` okumaz/yazmaz/silmez. Mevcut orphan Windows Credential Manager kaydını otomatik temizlemek bu scope’a dahil değildir. | allowed-name assertion → fake keyring call log → GUI save action → only `llm_api_key` |
| A8 | zorunlu | Tk kart/input/metin tokenları sırasıyla `#1e1e2e`, `#2d2d3f`, `#ffffff` olur; Entry ve Combobox normal/focus/readonly/listbox durumlarında okunur, primary Kaydet yeşil ve secondary eylemler mavi/kontrastlıdır; renk literal’leri `gui.py`ye dağılmaz. | token assertions → ttk configure/map/listbox options → widget state inspection → manual visual checklist |
| A9 | zorunlu | 9Router API anahtarı başlangıçta maskelidir; göster/gizle kontrolü yalnız widget `show` özelliğini `*` ve boş arasında değiştirir, anahtar değerini/store’u değiştirmez; Tab ve Space/Enter ile kullanılabilir, erişilebilir Türkçe metni vardır. | initial masked widget → toggle action → visible → same raw value/no keyring call → toggle → masked |
| A10 | zorunlu | F8 toggle ve push-to-talk bir fiziksel basışta yalnız bir start üretir; auto-repeat yutulur, release guard’ı sıfırlar, toggle’ın sonraki basışı yalnız bir stop üretir; callback veya yeniden kayıt hatasında internal state/eski binding tutarlı kalır. | down → repeated down → release → next down event trace; injected callback failure; failed re-register → old handler trace |
| A11 | zorunlu | `baslat.bat` `python.exe` yerine aynı sabit interpreter dizinindeki `pythonw.exe`yi kullanır, `%~dp0`/quoted script path’i korur ve terminale bağlı hata/pause akışına güvenmez; başlangıç hataları mevcut `error.log` + Tk messagebox yolunda kalır. | launcher raw text/static test → quoted pythonw/script assertions → `main.main` failure test → log/dialog contract |
| A12 | zorunlu | README/config örneği yalnız iki modu, yerel Whisper tiny/base gereksinimini, combined/local_only veri-ağ sınırını, F8 kullanımını ve pythonw launcher’ını doğru anlatır; STT API talimatı içermez. | docs keyword/forbidden-term checklist → config JSON schema assertions |

Acceptance freeze: Yargu yalnız gerçek güvenlik açığı, veri kaybı veya yukarıdaki açık ürün sözleşmesi ihlalinde `file:line + somut etki` ile yeni blocker ekleyebilir. Diğer gözlemler SARI/sonraki iş olur. İlk KIRMIZI’dan sonra bütün açık blockerlar tek listede toplanır; ikinci turdan sonra bu liste dışında kapsam açılmaz, güvenlik istisnası yine dosya:satır kanıtı ister.

## 3. Files

| Path | Create/Edit | Sorumluluk |
|---|---|---|
| `settings.py` | Edit | İki modlu `FlowMode`; local-only `SttSettings`; obsolete config alanlarını filtreleyen legacy load sınırı; yalnız LLM credential allowlist’i. |
| `transcriber.py` | Edit | API transcriber ve STT credential/http bağımlılığını kaldırma; yalnız `LocalWhisperTranscriber` ve sade yerel factory/constructor kontratı. |
| `main.py` | Edit | Her modda yerel transcriber composition; yalnız combined için LLM cleaner/key; gereksiz `replace`/STT provider akışını kaldırma. |
| `gui.py` | Edit | İki mod, üç STT API alanının kaldırılması, yüksek kontrast ttk state stilleri, widget referansları ve LLM key göster/gizle eylemi. |
| `ui_tokens.py` | Edit | Kullanıcı-kilitli card/input/foreground tokenları ile house yeşil primary ve mavi secondary/focus tokenlarının tek kaynağı. |
| `hotkeys.py` | Edit | F8 press/release edge guard, repeat engeli, exception-safe state ve atomik re-registration. |
| `baslat.bat` | Edit | Quoted `pythonw.exe` ile terminalsiz launcher; console `pause`/echo hata bağımlılığını kaldırma. |
| `config.example.json` | Edit | Yalnız combined/local config şekli; STT nesnesinde sadece local model/language; obsolete API alanlarının kaldırılması. |
| `README.md` | Edit | İki mod, local Whisper, LLM-only credential/ağ, F8 güvenilir kullanım, pythonw launcher ve hata logu. |
| `tests/test_settings.py` | Edit | İki mod/default/round-trip, legacy obsolete alan filtresi, api_only reject ve LLM-only credential kontratı. |
| `tests/test_transcriber.py` | Edit | API testlerini kaldırıp yerel-only factory, lazy model, tiny/base ve temp WAV temizliği testleriyle değiştirme. |
| `tests/test_main.py` | Edit | İki modun her ikisinde local STT; yalnız combined cleaner/key; STT credential/request yokluğu. |
| `tests/test_gui.py` | Edit | Alan inventory’si, iki label, input token/state stilleri ve key visibility saf davranışı. |
| `tests/test_hotkeys.py` | Edit | Down-repeat-release trace, toggle/PTT, callback failure ve failed re-register regresyonu. |
| `tests/test_controller.py` | Edit | `api_only` parametrizasyonunu kaldırıp combined/local_only durum ve payload kontratlarını koruma. |
| `tests/test_pipeline.py` | Edit | Yalnız iki yerel-STT trace; combined temiz, local_only exact raw ve sıfır LLM. |
| `tests/test_readme.py` | Edit | Dokümanda iki mod/pythonw/local setup; STT API/api_only yasak terim ve config örneği kontrolleri. |
| `tests/test_launcher.py` | Create | `baslat.bat` için pythonw, quoted path, python.exe/pause yokluğu statik kontratı. |
| `requirements.txt` | No change expected | httpx LLM için kalır; yeni dependency eklenmez. |
| `requirements-local.txt` | No change expected | `faster-whisper` local extra olarak kalır. |
| Generated production output | N/A | Ayrı build/deploy hedefi yoktur; oluşturulmayacak. |
| VPS/deploy directory | N/A | Bu masaüstü kaynak repo işi deploy içermez. |

## 4. Tasks

### Task 1 — İki modlu settings ve legacy config sınırını kilitle

**Done when:** Settings yalnız `combined/local_only` kabul eder, local STT şekli round-trip olur, tanınan eski STT API alanları güvenle atılır ve eski `api_only` açıkça reddedilir.

- [ ] (2–5 dk) `tests/test_settings.py` içinde iki mod, combined/base defaults, tiny/base validasyonu ve `api_only` rejection için failing testleri yaz.
- [ ] (2–5 dk) Legacy JSON’da `provider/api_base_url/api_model` varken load’ın yerel alanları koruduğunu; save sonrası obsolete alanların raw payload’da olmadığını failing testle yaz.
- [ ] (2–5 dk) `settings.py` içinde `FlowMode`, `FLOW_MODES`, `SttSettings` ve mode validation’ı minimum iki-mod sözleşmesine indir.
- [ ] (2–5 dk) `SettingsStore.load` içinde yalnız bilinen local STT alanlarını explicit seç; bozuk JSON/bilinmeyen mode için mevcut sanitize domain error zincirini koru.
- [ ] Test: `python -m pytest tests/test_settings.py -q`

### Task 2 — STT API runtime ve credential yüzeyini kaldır

**Done when:** Transcriber modülü yalnız local Whisper taşır ve CredentialStore yalnız LLM anahtarını kabul eder.

- [ ] (2–5 dk) `tests/test_transcriber.py` içinde API multipart/error testlerini kaldırılacak davranış olarak değil, local-only public symbol/factory kontratıyla değiştiren failing testleri yaz; local lazy-load testlerini koru.
- [ ] (2–5 dk) `transcriber.py`den `ApiWhisperTranscriber`, STT `httpx`, `api_url`, CredentialStore ve provider branch’ini kaldır; local constructor/factory’i tiny/base ile sınırla.
- [ ] (2–5 dk) `tests/test_settings.py` içinde `CredentialStore.ALLOWED == {"llm_api_key"}` ve `stt_api_key` get/set’in reddedildiği testi ekle.
- [ ] (2–5 dk) `settings.py::CredentialStore` type hint/allowlist’ini yalnız `llm_api_key` yap; eski STT secret’ını otomatik okuma/silme.
- [ ] Test: `python -m pytest tests/test_transcriber.py tests/test_settings.py -q`

### Task 3 — Composition root’u her zaman yerel Whisper’a bağla

**Done when:** Combined ve local_only aynı local transcriber yolunu kullanır; yalnız combined LLM key/cleaner kurar ve hiçbir STT credential/HTTP yolu kalmaz.

- [ ] (2–5 dk) `tests/test_main.py` parametrizasyonunu iki moda indir; local transcriber modelinin her iki modda da `base/tiny` ayarından geldiğini failing spy ile doğrula.
- [ ] (2–5 dk) Combined için yalnız `llm_api_key` read + cleaner, local_only için sıfır credential read/cleaner/request testlerini yaz.
- [ ] (2–5 dk) `main.py::build_services` içindeki provider türetme ve `replace` kullanımını kaldır; local transcriber’ı doğrudan kur ve mevcut `require_keys` startup davranışını yalnız LLM için koru.
- [ ] (2–5 dk) `create_app/rebuild` aynı helper’ı kullansın; local model lazy-load kalsın ve eksik LLM anahtarı yalnız combined’ı etkilesin.
- [ ] Test: `python -m pytest tests/test_main.py tests/test_transcriber.py tests/test_llm_cleaner.py -q`

### Task 4 — GUI alanlarını sadeleştir ve ViewModel’i düzelt

**Done when:** Kullanıcı yalnız iki akış, local model ve LLM ayarlarını görür; STT URL/model/key hiçbir UI/value/save yolunda yoktur.

- [ ] (2–5 dk) `tests/test_gui.py` içinde exact `FIELD_SPECS`/mode label inventory’sini iki moda ve STT API alanlarının yokluğuna göre failing hale getir.
- [ ] (2–5 dk) ViewModel test datasından `stt_url/stt_model/stt_key`i çıkar; build sonucunda sadece seçilen `local_model/language` oluştuğunu doğrula.
- [ ] (2–5 dk) `gui.py` label map/defaults/build/save akışından API-only ve üç STT API alanını kaldır; key save loop’unu yalnız LLM key’e indir.
- [ ] (2–5 dk) Row hesaplarını `len(FIELD_SPECS)` tabanlı tut; iki mod Combobox’ı readonly ve local model tiny/base olarak kalsın.
- [ ] Test: `python -m pytest tests/test_gui.py tests/test_settings.py -q`

### Task 5 — Yüksek kontrast token ve ttk state stillerini uygula

**Done when:** Kullanıcı-kilitli kart/input/metin renkleri ile yeşil/mavi eylemler tüm ilgili ttk durumlarında okunur ve GUI source içinde hex literal yoktur.

- [ ] (2–5 dk) `tests/test_gui.py` içinde `card=#1e1e2e`, `input=#2d2d3f`, `foreground=#ffffff`, yeşil primary ve tokenized mavi secondary/focus için failing token assertions ekle.
- [ ] (2–5 dk) `ui_tokens.py` token adlarını `input`, `input_foreground`, `secondary`, `focus` gibi semantik anahtarlarla güncelle; yalnız istenen/house renklerini tek yerde tut.
- [ ] (2–5 dk) `gui.py::_style` içinde `TEntry` ve `TCombobox` configure/map değerlerini normal, focus, disabled ve readonly durumları için açıkça ayarla; selection ve insert renklerini kontrastlı yap.
- [ ] (2–5 dk) Combobox açılır Listbox için `option_add` foreground/background/select renklerini tokenlardan ayarla; Kaydet `Primary.TButton`, Test Et ve key toggle `Secondary.TButton` kullansın.
- [ ] Test: `python -m pytest tests/test_gui.py -q`

### Task 6 — LLM anahtarına göster/gizle kontrolü ekle

**Done when:** Anahtar maskeli başlar, kontrol aynı değeri bozmadan görünürlüğü iki yönde değiştirir ve klavyeyle erişilebilir.

- [ ] (2–5 dk) Görünürlük kararını test edilebilir saf helper/metot olarak failing testle tanımla: `* → "" → *`; raw StringVar değeri değişmez.
- [ ] (2–5 dk) `AppGui` içinde `self.widgets` veya yalnız key widget referansı tut; LLM key Entry ve toggle button’ı aynı grid hücresindeki küçük frame’e yerleştir.
- [ ] (2–5 dk) Türkçe buton metnini duruma göre `Göster/Gizle` yap, command yalnız Entry `show` ayarını değiştirip keyring/store/controller çağırmasın.
- [ ] (2–5 dk) Toggle’ın Tab almasını, Space/Enter varsayılan ttk Button davranışını ve label→input sırasını source/widget testinde doğrula; başlangıç maskesini koru.
- [ ] Test: `python -m pytest tests/test_gui.py -q`

### Task 7 — F8 kenar ve repeat davranışını güvenilir hale getir

**Done when:** Toggle ve push-to-talk repeat üretmez; callback/re-register hataları internal state’i ve eski binding’i bozmaz.

- [ ] (2–5 dk) `tests/test_hotkeys.py` fake backend’ini press/release handler’larını saklayacak şekilde genişlet; `down, down(repeat), release` izinde tek start failing testi yaz.
- [ ] (2–5 dk) Toggle için iki ayrı fiziksel basışın `start, stop`; PTT için press/repeat/release’in `start, stop` ürettiğini ve fazladan release’in no-op olduğunu test et.
- [ ] (2–5 dk) `on_start/on_stop` exception’ında `_pressed/_active` tutarlılığı ve sonraki F8’in kurtulması için failing test ekle; exception’ın keyboard callback thread’ini gereksiz ayrıntıyla sızdırmamasını hedefle.
- [ ] (2–5 dk) `hotkeys.py` içinde her mod için press/release edge hook’ları, ortak repeat guard ve callback başarılı olduktan sonra state commit uygula; atomik re-register rollback’ini koru.
- [ ] (2–5 dk) İkinci hook registration başarısızsa yeni handle’ların temizlenip eski iki handle’ın çalıştığını test et.
- [ ] Test: `python -m pytest tests/test_hotkeys.py tests/test_controller.py -q`

### Task 8 — Pipeline testlerini iki moda daralt

**Done when:** Controller ve mocked integration suite yalnız combined/local_only yollarını ve doğru payload/state sırasını kanıtlar.

- [ ] (2–5 dk) `tests/test_controller.py` içindeki `api_only` parametrizasyonunu kaldır; combined’ın CLEANING, local_only’ın no-CLEANING izini koru.
- [ ] (2–5 dk) Local_only testinde baş/son boşluk ve noktalama içeren raw string’in birebir paste edildiğini, combined’da cleaned string’in paste edildiğini doğrula.
- [ ] (2–5 dk) `tests/test_pipeline.py` API-STT trace’ini kaldır; kalan iki trace’i `local-stt` ve opsiyonel `llm:clean` ile açıkça kilitle.
- [ ] (2–5 dk) Boş transcript, STT/cleaner/paste hatalarında paste/WRITTEN olmadığını ve kullanıcı mesajında transcript/secret sızmadığını regresyon olarak çalıştır.
- [ ] Test: `python -m pytest tests/test_controller.py tests/test_pipeline.py -q`

### Task 9 — `pythonw.exe` launcher’ını TDD ile değiştir

**Done when:** Batch launcher quoted `pythonw.exe` ve script path’i ile terminalsiz başlatır; console pause/error metnine dayanmaz.

- [ ] (2–5 dk) `tests/test_launcher.py` oluştur; `baslat.bat` içinde case-insensitive `pythonw.exe` varlığı, exact `python.exe` çağrısının ve `pause`ın yokluğu, `%~dp0`/quoted `main.py` path’i için failing statik test yaz.
- [ ] (2–5 dk) `baslat.bat`te mevcut sabit interpreter dizinini değiştirmeden executable’ı `pythonw.exe` yap; script ve çalışma dizinini boşluk güvenli tut, gerekiyorsa `start ""` ile terminali bekletmeden çık.
- [ ] (2–5 dk) Console’a echo/pause hata yolunu kaldır; `main.py`deki `error.log` + messagebox yolunun pythonw altında tek hata yüzeyi olduğunu test/incelemeyle doğrula.
- [ ] (2–5 dk) Yeni launcher/installer/fallback interpreter discovery ekleme; bulunmayan pythonw için uydurma başarı verme.
- [ ] Test: `python -m pytest tests/test_launcher.py tests/test_main.py -q`

### Task 10 — Config örneği ve README’yi yeni sözleşmeye getir

**Done when:** Doküman ve örnek config yalnız iki local-STT modu anlatır; STT API veya api_only talimatı kalmaz.

- [ ] (2–5 dk) `tests/test_readme.py` içinde `combined`, `local_only`, `tiny`, `base`, `pythonw.exe`, F8 ve LLM-only key/ağ anlatımı için failing checklist ekle.
- [ ] (2–5 dk) Aynı testte README/config örneğinde `api_only`, `stt_api_key`, `api_base_url`, `api_model`, `whisper-1` bulunmadığını doğrula; genel “API” kelimesini yasaklama çünkü 9Router LLM API kalır.
- [ ] (2–5 dk) `config.example.json`u geçerli iki-mod/local STT şekline güncelle ve JSON parse/schema testini ekle.
- [ ] (2–5 dk) `README.md` mod tablosu, kurulum, kullanım, güvenlik ve troubleshooting bölümlerini güncelle; ilk Whisper model indirmesi ile sonraki offline kullanım ayrımını koru.
- [ ] Test: `python -m pytest tests/test_readme.py tests/test_settings.py tests/test_launcher.py -q`

### Task 11 — Regresyon, kaynak taraması ve IMPLEMENTATION_ARTIFACT

**Done when:** Eski API yüzeyi kaynak/test/docs içinde kapsam dışı kalıntı bırakmadan kaldırılmış, tüm suite geçmiştir ve Asena gerçek kanıt artifact’ını üretmiştir.

- [ ] (2–5 dk) `git diff -- tests` ile eski testlerin sırf yeşil için skip/xfail edilmediğini; API testlerinin yeni local-only sözleşmeyle bilinçli değiştirildiğini incele.
- [ ] (2–5 dk) `ApiWhisperTranscriber|api_only|stt_api_key|stt_url|stt_model|api_base_url|api_model` source taraması yap; yalnız plan/history/cache değil, aktif kod/test/docs sonuçlarını değerlendir ve beklenmeyen kalıntıyı düzelt.
- [ ] (2–5 dk) Hedefli suite’i çalıştır: `python -m pytest tests/test_settings.py tests/test_transcriber.py tests/test_main.py tests/test_gui.py tests/test_hotkeys.py tests/test_controller.py tests/test_pipeline.py tests/test_launcher.py tests/test_readme.py -q`.
- [ ] (2–5 dk) `python -m pytest -q` ve `git diff --check` çalıştır; gerçek exit/özetleri kaydet, pass sayısı uydurma.
- [ ] (2–5 dk) `IMPLEMENTATION_ARTIFACT` üret: changed files; A1–A12 → dosya/test/çıktı kanıtı; gerçekten koşan komutlar + özet; blockerlar. YEŞİL/Yargu veya release/deploy iddiası yazma.
- [ ] Test: `python -m pytest -q`

## Asena handoff checklist

- [ ] Parent transfer blocku taşı; scope/acceptance eksik veya çelişkiliyse kod yazmadan `BLOCKED_CONTEXT` dön.
- [ ] Her davranışta failing test → minimum implementation → hedefli pass → tam suite sırasını izle.
- [ ] A1–A12 kanıtlarını aynı biçimde kullan; yeni test standardı icat etme.
- [ ] STT API sınıfını, endpoint alanlarını, api_only modunu ve STT key erişimini aktif koddan tamamen kaldır; fallback bırakma.
- [ ] Legacy STT config alanlarını yalnız explicit allowlist ile at; `SttSettings(**legacy_dict)` kullanıp bilinmeyen alanla crash etme.
- [ ] Eski `api_only`yi sessizce combined/local_only’a çevirme; sanitize ayar hatası üret.
- [ ] Orphan STT key’i keyring’den otomatik silme; secret okuma/migration bu scope dışında.
- [ ] Kullanıcı-kilitli renkleri yalnız `ui_tokens.py`de tut; ttk state map ve Combobox listbox yüzeyini unutma.
- [ ] Key toggle değer/store çağrısı yapmasın; başlangıçta maskeyi ve klavye erişimini korusun.
- [ ] Hotkey callback state’ini callback başarılı olmadan kalıcı flip etme; auto-repeat ve partial re-register failure testlerini koş.
- [ ] `baslat.bat`te mevcut interpreter konumunu farklı kurulum discovery projesine dönüştürme; yalnız pythonw sözleşmesini uygula.
- [ ] Secret, token, transcript veya gerçek credential’ı config/log/test çıktısına yazma; opaque fake kullan.
- [ ] `IMPLEMENTATION_ARTIFACT`: changed files, A1–A12 evidence, gerçekten koşan commands/output summary, blockers. Yargu hükmü yok.

## 5. Yargu beklentisi

### Locked inventory review

Yargu A1–A12’nin her birine `PASS | FAIL | N/A` (N/A yalnız gerçekten uygulanamazsa somut gerekçeyle) ve taze evidence yazar. Asena öz bildirimi veya geçmiş komut çıktısı kabul edilmez. İlk KIRMIZI tüm blockerları tek listede toplar; yeni blocker yalnız acceptance ihlali ya da `file:line + somut security/data-loss/product impact` ile eklenir.

### Fresh test gates

1. `python -m pytest tests/test_settings.py tests/test_transcriber.py tests/test_main.py tests/test_gui.py tests/test_hotkeys.py tests/test_controller.py tests/test_pipeline.py tests/test_launcher.py tests/test_readme.py -q`
2. `python -m pytest -q`
3. `git diff --check`
4. Aktif yüzey taraması: `ApiWhisperTranscriber|api_only|stt_api_key|stt_url|stt_model|api_base_url|api_model`
5. `git diff -- settings.py transcriber.py main.py gui.py ui_tokens.py hotkeys.py baslat.bat config.example.json README.md tests`
6. Windows manuel smoke (otomasyonda gerçek global hook/GUI yüzeyi doğrulanamıyorsa açıkça manual evidence): launcher’dan aç → terminal kalmıyor → odaklı bir metin alanında F8 bas/bırak ile bir kayıt başlıyor → basılı tutma duplicate üretmiyor → ikinci fiziksel basış bitiriyor → metin yapıştırılıyor.

### Security hotspots

- `settings.py`: Legacy JSON dict doğrudan dataclass’a unpack edilmemeli; yalnız beklenen alanlar alınmalı. Config raw payload’da credential olmamalı.
- `settings.py/gui.py/main.py/transcriber.py`: `stt_api_key` hiçbir şekilde get/set/delete edilmemeli; orphan secret’ı temizleme bahanesiyle okunmamalı.
- `main.py`: local_only LLM key/HTTP istememeli; combined yalnız LLM credential kullanmalı; local Whisper hatasında raw fallback veya uzak STT fallback olmamalı.
- `controller.py`: Transcript/secret exception, status veya log metnine girmemeli; hata halinde paste ve WRITTEN olmamalı.
- `gui.py`: Göster/gizle yalnız kullanıcının açık eylemiyle olmalı; re-render/save/error sonrası key istemeden açık kalmamalı; gerçek key hiçbir test snapshotına yazılmamalı.
- `hotkeys.py`: Hook callback exception’ı state’i kilitlememeli; eski handle’lar yeni kayıt tamamen başarılı olmadan kaldırılmamalı.
- `baslat.bat/main.py`: pythonw console stderr sağlamaz; startup exception’ı secret/transcript içermeyen `error.log` ve messagebox ile görünür kalmalı. Launcher secret argüman taşımamalı.
- Offline iddiası: model ilk kullanımda indirilebilir; model hazır olduktan sonra local_only dikte pipeline’ında LLM/STT HTTP request count `0` olmalı.

### UI checklist

- [ ] Surface `rasyon_web_ui` native Tk adaptation; token source `ui_tokens.py`; kanon DESIGN_SYSTEM okundu mu?
- [ ] Kart `#1e1e2e`, input `#2d2d3f`, metin `#ffffff` gerçekten widget normal/focus/readonly/listbox durumlarına uygulanıyor mu?
- [ ] Yeşil primary ve mavi secondary butonlarda foreground/active/focus kontrastı yeterli ve metin okunur mu?
- [ ] Entry caret/selection ve readonly Combobox seçili metni görünür mü; Windows ttk theme state map rengi geri ezmiyor mu?
- [ ] Yalnız iki akış etiketi var mı; STT URL/model/key ve API-only görünmüyor mu?
- [ ] 9Router key başlangıçta maskeli mi; Göster/Gizle Türkçe, Tab ile erişilebilir ve Space/Enter ile çalışır mı; değer değişmiyor mu?
- [ ] Focus göstergesi yalnız renge dayalı belirsiz hale gelmemiş mi; form label’ları ve doğal Tab sırası korunmuş mu?
- [ ] Hardcoded renk `gui.py`ye sızmamış mı; superseded `#2F3A2E`/serif/tarla dili, indigo/violet brand, emoji, lorem veya sahte metrik yok mu?
- [ ] Yeni framework/dependency ve gereksiz motion yok mu?

### REVIEW_ARTIFACT biçimi

- `parent_artifact`: Asena’nın gerçek `IMPLEMENTATION_ARTIFACT` yolu/kimliği
- `scope_id`: `ses-yazici-v2-sadelestirme-2026-09-21`
- `acceptance_inventory`: A1–A12 locked liste
- `evidence_required`: Bu plandaki kanıt şekilleri + Yargu’nun taze komutları/manual smoke durumu
- `out_of_scope`: Parent block ile aynı
- `iteration`: review turu
- `blockers`: Tek toplu liste; her yeni istisna için `file:line + somut etki`
- A1–A12 verdict tablosu, fresh command outputs, security/UI findings
- Son hüküm yalnız `YEŞİL | SARI | KIRMIZI`

## Riskler ve kararlar

- **Legacy config:** Eski `api_only`yi otomatik combined’a çevirmek ağ/veri davranışını sessizce değiştirir; bu nedenle açık sanitize hata zorunludur. Eski local/combined config’teki artık kullanılmayan STT API alanları ise güvenle yok sayılıp sonraki save’de temizlenir.
- **Orphan credential:** Kod allowlist’inden STT key kaldırılınca eski Windows Credential Manager girdisi diskte kalabilir. Otomatik silme secret’a erişim ve geri dönüşsüz yan etki yaratır; cleanup bu scope dışındadır.
- **Tk/ttk platform farkı:** `clam` kullanılsa bile readonly Combobox ve popdown Listbox renkleri ayrı state/option katmanlarından gelir. Sadece token testi yeterli değildir; Windows visual smoke Yargu kapısıdır.
- **Hotkey thread/state:** `keyboard` callback’leri Tk ana thread’i dışında çalışabilir. Bu plan UI çağrısını hotkey modülüne taşımaz; yalnız deterministik edge/repeat/state kontratını düzeltir. Controller’ın mevcut thread-safe/event yaklaşımı korunur.
- **pythonw hata görünürlüğü:** Terminal kalkınca stdout/stderr görünmez. Mevcut `main.py` error.log + messagebox yolu korunmalı; batch `pause` artık anlamlı değildir.
- **Hardcoded interpreter:** Launcher mevcut makineye özgü interpreter path’i zaten kullanıyor. Eren yalnız pythonw istedi; portable environment discovery/installer YAGNI ve kapsam dışıdır.
- **Model indirme:** Local-only ilk model yüklemesinde faster-whisper ağ kullanabilir. “STT API yok” ile “model artifact indirmesi yok” aynı şey değildir; README bu nüansı açık tutar.

## 6. Yapma listesi

- STT API sınıfı, endpoint alanı, API-only modu veya uzak STT fallback’i bırakma.
- Eski `api_only` ayarını sessizce başka moda çevirme.
- Orphan STT credential’ı otomatik okuma, loglama, taşıma veya silme.
- LLM/9Router API’sini kaldırma; `combined` için mevcut cleaner davranışı kalır.
- Local-only raw payloadı trim/normalize/temizleme veya LLM’ye gönderme.
- API/LLM hatasında sessiz raw paste fallback yapma.
- Gerçek secret, `.env`, key prefix/suffix, transcript veya credential değerini plan/test/log/config içine koyma.
- Renkleri `gui.py` içine hardcode etme; kullanıcı-kilitli üç rengi değiştirme veya yeni palet yağmuru ekleme.
- Sadece default ttk style’a güvenip readonly/listbox/focus durumlarını doğrulamadan “kontrast düzeldi” deme.
- Key alanını varsayılan görünür yapma ya da toggle sırasında StringVar/keyring değerini değiştirme.
- F8 için sleep/debounce timer, admin escalation veya yeni hotkey dependency’si ekleme; edge guard yeterli.
- `python.exe` fallback’i ile terminali yeniden açma; launcher’dan secret argüman geçirme.
- Yeni framework/dependency, installer, exe packaging, auto-update, sync/rollback aracı ekleme.
- Mevcut testleri skip/xfail ederek veya assertions’ı gevşeterek yeşil üretme.
- Commit/push, deploy, VPS değişikliği veya release iddiası yapma.
- Test/build çıktısını Yargu YEŞİL ya da yayın başarısı olarak sunma.
