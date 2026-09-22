# Boş Ses ve Hata Toparlanması — Implementation Plan

PLAN_ARTIFACT

scope_id: `ses-yazici-bos-ses-toparlanma-2026-09-22`
iteration: `2`
status: `READY_FOR_ASENA`

## Parent transfer block

- `parent_artifact`: `USER_REQUEST/2026-09-22/ses-yazici-bos-ses-ve-hata-toparlanmasi`
- `scope_id`: `ses-yazici-bos-ses-toparlanma-2026-09-22`
- `acceptance_inventory`: Bu belgedeki “Locked acceptance inventory”; A1–A8 ve A10 zorunlu, A9 isteğe bağlıdır ve uygulama/review süresince anlamı değiştirilemez.
- `evidence_required`: Her kabul maddesi için tabloda kilitlenen kanıt zinciri, ardından taze hedefli pytest, tam pytest, script statik/izole smoke kanıtı ve scoped diff. Worker öz bildirimi veya yalnız exit code doğrulama sayılmaz; parent belirtilen dosya ve komutları bağımsız kontrol eder.
- `out_of_scope`: Whisper model/sağlayıcı değişikliği, VAD/ses seviyesi analizi, yeni ayar veya GUI kontrolü, bildirim/toast tasarımı, hotkey servisinin yeniden yazılması, yeni dependency, tam paketleme/installer, generated build, VPS/deploy/sync/rollback, commit/push, secret veya `.env` okuma/yazma. Hafif Windows başlangıç/kısayol scriptleri (`baslat_arkaplan.vbs`, `otomatik_baslat_kur.bat`, `otomatik_baslat_kaldir.bat`) ve README kullanımı açıkça kapsam içidir.
- `iteration`: `2`
- `blockers`: `Yok.` Eşik kullanıcı bildirimindeki sözleşmeye göre sabit `0.3` saniyedir; tam `0.3` saniye kısa sayılmaz.

---

## 1. Goal · Architecture · Tech/repo

**Goal:** Kazara oluşturulan 0.3 saniyeden kısa veya konuşma içermeyen kayıtları geri kazanılabilir biçimde sonlandırmak ve uygulamayı görünür CMD penceresi olmadan elle ya da Windows başlangıcında çalıştıran hafif kısayol scriptlerini sağlamak.

**Architecture:** `AppController` kayıt durduktan hemen sonra PCM metadata üzerinden süreyi hesaplayarak kısa klibi WAV encode/Whisper çağrısından önce keser; Whisper’ın geçerli fakat segmentsiz sonucu `LocalWhisperTranscriber` katmanından boş string olarak döner ve controller tarafından temizleme/yapıştırma yapılmadan `READY` durumuna çevrilir. Beklenmeyen gerçek pipeline hataları mevcut `ERROR` görünürlüğünü korurken yeniden kayıt kabul edilir; repo-köküne eklenecek VBScript `pythonw` ile `main.py`yi görünür CMD penceresi olmadan başlatır, iki batch script ise kullanıcının `shell:startup` klasöründeki kısayolu idempotent biçimde kurar/kaldırır.

**Tech / repo:** Python 3.11+, Tkinter durum kuyruğu, `sounddevice`, `faster-whisper`, `pytest`; kaynak repo `C:/Users/esahi/OneDrive/Masaüstü/git_r/ses-yazici`.

**Global constraints:** TDD (failing test → minimum implementation → pass), DRY ve YAGNI uygulanır. Yeni dependency, ayar alanı veya servis katmanı eklenmez; loglar ham ses, transkript, secret veya traceback ayrıntısını kullanıcı durum mesajına taşımaz. Windows host komutları repo kökünde `python -m pytest ...` biçiminde çalıştırılır.

### Repo/source-build ayrımı

- **A) Kaynak feature + test:** `controller.py`, `transcriber.py`, ilgili pytest dosyaları, `baslat_arkaplan.vbs`, `otomatik_baslat_kur.bat`, `otomatik_baslat_kaldir.bat` ve `README.md` bu planın uygulama yüzeyidir.
- **B) Generated/release output:** Repo yerel Python kaynak uygulamasıdır; ayrı `dist/`, production build, sync veya deploy hedefi saptanmamıştır. Bu iş için build/deploy aşaması yoktur ve yeni bir sync/rollback aracı oluşturulmaz.
- Kaynak testlerinin geçmesi release/deploy iddiası değildir; bu plan yalnız local source artifact üretimini kapsar.

### Davranış sınıflandırması

| İddia | Sınıf | Mevcut kod/DOM-runtime kanıtı | Hedef davranış |
|---|---|---|---|
| Kazara kısa basış Whisper’ı gereksiz çalıştırıyor | `form/action` | `controller.py:99-106`, `recorder.stop()` sonrasında süre kontrolü olmadan `encode_wav()` ve `transcriber.transcribe()` çağırıyor; bildirilen runtime izi 0.21 sn kaydın yaklaşık 5.8 sn transkripsiyona gittiğini gösteriyor. | PCM süre `< 0.3` ise transcriber/cleaner/injector çağrılmaz, bilgi logu üretilir ve durum `READY` olur. |
| Sessizlik boş transkripsiyonla fatal hataya dönüşüyor | `render/state` | `transcriber.py:65-66` boş sonucu `TranscriptionError` yapıyor; `controller.py:105-106` boş/whitespace sonucu ayrıca `RuntimeError` yapıyor; `controller.py:120-122` tümünü `ERROR`a çeviriyor. | Segmentsiz Whisper sonucu `""` döner; boş/whitespace transkripsiyon ve geriye dönük boş-transkripsiyon sinyali “konuşma algılanmadı” olarak yapıştırmasız `READY` ile kapanır. |
| Hata sonrası hotkey/Test tekrar başlayamıyor | `form/action` + `render/state` | `controller.py:75-78` yalnız `READY` durumunda başlangıca izin verdiği için `ERROR` kalıcı engel oluyor; GUI/hotkey aynı `start_recording()` girişini kullanıyor. | `start_recording()` yalnız `READY` veya `ERROR` durumunda kabul edilir; `ERROR`dan başarılı başlangıç `LISTENING`e geçer. Aktif pipeline durumları yine re-entry kabul etmez. |

Bu iş görsel UI değişikliği içermez; browser/DOM yüzeyi yoktur. Durum olayları mevcut GUI tarafından tüketilen runtime kontratıdır.

---

## 2. Design surface

**Design surface:** N/A — widget, layout, renk, tipografi veya token değişikliği yok; yalnız mevcut `AppState` olay akışının semantiği düzeltilir.

**Token source path:** Değişmeyecek: `ui_tokens.py`; kanon `C:/Users/esahi/OneDrive/Belgeler/Notlar/91 - AI Context/DESIGN_SYSTEM.md`.

**Design read:** Mevcut native masaüstü durum yüzeyi korunur; kısa/sessiz kayıt hata yüzeyi göstermeden tekrar “Hazır” durumuna döner.

---

## 3. Locked acceptance inventory

| ID | Sınıf | Kilitli kabul maddesi | Kanıt şekli |
|---|---|---|---|
| A1 | zorunlu | PCM süresi `len(clip.pcm_s16le) / (clip.sample_rate * clip.channels * 2)` ile belirlenir; süre `< 0.3` saniyeyse controller kaydı normal biçimde abort eder. Tam `0.3` saniye ve üzeri mevcut pipeline’a devam eder. | kısa `AudioClip` → recorder stop → transcriber çağrı sayısı `0` → final `READY`; sınır klibi `0.3` → transcriber çağrı sayısı `1` |
| A2 | zorunlu | Kısa kayıt WAV encode/Whisper, cleaner ve injector’a gitmez; kullanıcı içeriği içermeyen INFO seviyesinde kısa-kayıt logu bırakır ve `ERROR`/`WRITTEN` olayı üretmez. | kısa clip → event trace `LISTENING → TRANSCRIBING → READY` → downstream spy’lar boş → caplog INFO var / ERROR yok |
| A3 | zorunlu | `LocalWhisperTranscriber.transcribe()` geçerli WAV için hiç metin segmenti oluşmadığında `TranscriptionError` fırlatmak yerine `""` döner; geçici WAV dosyasını yine siler. Boş byte girdisinin mevcut `Ses verisi boş.` hatası değişmez. | fake Whisper empty segments → return `""` → temp path yok; empty bytes → mevcut `TranscriptionError` |
| A4 | zorunlu | Controller transcriber’dan `""` veya yalnız whitespace aldığında cleaner/injector çağırmaz, `WRITTEN`/`ERROR` üretmez ve `READY`ye döner. | normal süre → blank STT → cleaner `0` + paste `0` → event trace sonu `READY` |
| A5 | zorunlu | Mevcut/legacy transcriber `TranscriptionError("Transkripsiyon boş döndü.")` üretirse yalnız bu bilinen no-speech vakası normal abort edilir; farklı `TranscriptionError` ve diğer beklenmeyen hatalar `ERROR` olmaya devam eder. | known empty error → no paste + `READY`; different STT error → no paste + `ERROR` |
| A6 | zorunlu | `start_recording()` `ERROR` durumundan yeni kayıt kabul eder ve başarılı recorder başlangıcında `LISTENING` olur; `_shutdown` veya `LISTENING/TRANSCRIBING/CLEANING/INJECTING/WRITTEN` durumlarında mevcut re-entry engeli korunur. | forced `ERROR` → start → recorder call + `LISTENING`; busy/shutdown matrix → recorder çağrısı artmaz |
| A7 | zorunlu | Gerçek hata görünürlüğü ve güvenli kullanıcı mesajı regresyona uğramaz: mikrofon, cleaner, injector ve no-speech olmayan transcriber hataları `ERROR` üretir; event mesajları exception içeriği/transkript/secret sızdırmaz. | parametrik failure spies → `ERROR`, no `WRITTEN` → event-message sensitive-string absence |
| A8 | zorunlu | Hedefli controller/transcriber/pipeline testleri ve tam test paketi geçer. | taze `python -m pytest tests/test_transcriber.py tests/test_controller.py tests/test_pipeline.py -q` → pass; taze `python -m pytest -q` → pass |
| A9 | isteğe bağlı | Kısa kayıt eşiği controller içinde açıklayıcı tek bir modül sabitinden (`MIN_RECORDING_SECONDS = 0.3`) okunur; testler aynı literal’i kopyalamak yerine sınırın altı/eşiti örnekleriyle davranışı kilitler. | source inspection → tek eşik tanımı → boundary tests |
| A10 | zorunlu | Otomatik başlatma ve kısayol scriptleri (`baslat_arkaplan.vbs`, `otomatik_baslat_kur.bat`, `otomatik_baslat_kaldir.bat`) doğru dizin ve komutları hedefler; `README.md` kullanım talimatını içerir. | repo başka dizine kopyalanmış varsayımı → script-relative repo/`main.py` çözümü → `pythonw` ile gizli başlatma → `shell:startup` kısayol hedefi/çalışma dizini doğrulaması → kaldırma → README komut eşleşmesi |

**Acceptance freeze:** A1–A8 ve A10 bloklayıcıdır; A9 uygulanmazsa KIRMIZI nedeni değildir. Yargu yeni bir blocking maddeyi yalnız gerçek güvenlik açığı, veri kaybı veya açık ürün ihlali için `dosya:satır + somut etki` kanıtıyla ekleyebilir; diğer gözlemler SARI/sonraki iş olur. İlk KIRMIZI sonrası tüm blockerlar tek listede toplanır; ikinci düzeltme turundan sonra liste dışı kapsam açılmaz (kanıtlı güvenlik istisnası hariç).

---

## 4. Files

| Path | Create/Edit | Sorumluluk |
|---|---|---|
| `controller.py` | Edit | Kısa klip süresi kontrolü, no-speech normal bitişi, bilinen legacy boş-transkripsiyon hatasının ayrımı ve `ERROR`dan yeniden kayıt kabulü. |
| `transcriber.py` | Edit | Geçerli fakat segmentsiz Whisper sonucunu boş string olarak döndürme; gerçek STT hatalarını koruma. |
| `tests/test_controller.py` | Edit | Kısa/sınır kayıt, blank/whitespace/legacy no-speech, gerçek hata ve ERROR recovery birim testleri; test doubles’a çağrı sayacı/özelleştirilebilir clip ekleme. |
| `tests/test_transcriber.py` | Edit | Empty-segment sonucu, temp dosya temizliği ve empty-byte hata regresyonu. |
| `tests/test_pipeline.py` | Edit | Uçtan uca kısa/sessiz işlem izinde downstream çağrıların atlanması ve bir sonraki kaydın kabulü. |
| `baslat_arkaplan.vbs` | Create | Kendi dosya konumundan repo kökünü çözüp `main.py`yi `pythonw` ile pencere göstermeden ve doğru working directory ile başlatma. |
| `otomatik_baslat_kur.bat` | Create | Kullanıcının Windows Startup klasöründe uygulamaya ait kısayolu doğru VBScript hedefi ve repo çalışma diziniyle oluşturma/güncelleme. |
| `otomatik_baslat_kaldir.bat` | Create | Yalnız bu uygulamaya ait başlangıç kısayolunu güvenli ve idempotent biçimde kaldırma. |
| `README.md` | Edit | Arka planda elle başlatma, otomatik başlangıç kurma/kaldırma ve dosyaların birlikte tutulması gereğini belgeleme. |
| Generated production output | N/A | Ayrı generated build yok; hiçbir `dist/` veya binary düzenlenmeyecek. |
| VPS/deploy directory | N/A | Yerel masaüstü uygulaması; VPS/release/deploy kapsam dışı. |

---

## 5. Tasks

### Task 1 — Transcriber no-speech kontratını TDD ile düzelt

**Done when:** Geçerli ses girdisinde Whisper boş segment döndürürse `LocalWhisperTranscriber` `""` döndürür, temp dosyayı temizler; boş byte ve gerçek model hataları hata olmaya devam eder.

- [ ] (2–5 dk) `tests/test_transcriber.py` içine fake modelin `([], {})` döndürdüğü failing testi yaz; dönüşün `""` ve yakalanan temp path’in silinmiş olduğunu doğrula.
- [ ] (2–5 dk) Aynı dosyada `b""` girdisinin `TranscriptionError("Ses verisi boş.")` üretmeye devam ettiğini kilitleyen regresyon testini ekle.
- [ ] (2–5 dk) Testi kırmızı çalıştır: `python -m pytest tests/test_transcriber.py -q`; beklenen ilk kırmızı, boş sonuçta `Transkripsiyon boş döndü.` istisnasıdır.
- [ ] (2–5 dk) `transcriber.py` içindeki final `if not text: raise ...` dalını kaldır; başarıyla tamamlanan çıkarımı, metin boş olsa da `return text` ile sonuçlandır. `_load()`/model/inference ve empty-byte hata yollarına dokunma.
- [ ] Test komutu: `python -m pytest tests/test_transcriber.py -q`

### Task 2 — Kısa kayıt fast-abort yolunu TDD ile ekle

**Done when:** `< 0.3` saniyelik PCM klip transcribe edilmeden INFO loguyla `READY` olur; `0.3` saniyelik sınır klibi normal pipeline’a girer.

- [ ] (2–5 dk) `tests/test_controller.py` test double’larını istenen `AudioClip`i döndürebilecek ve STT çağrı sayısını kaydedecek minimum biçimde genişlet.
- [ ] (2–5 dk) `< 0.3` saniye testini yaz: final state `READY`, olaylarda `ERROR/WRITTEN` yok, transcriber/cleaner/injector çağrıları yok ve sanitize kısa-kayıt INFO logu var.
- [ ] (2–5 dk) Tam `0.3` saniyelik PCM için transcriber’ın bir kez çağrıldığını doğrulayan sınır testini yaz.
- [ ] (2–5 dk) Testleri kırmızı çalıştır: `python -m pytest tests/test_controller.py -q`; beklenen kırmızı, kısa klipte STT çağrısının yapılmasıdır.
- [ ] (2–5 dk) `controller.py::_pipeline()` içinde `recorder.stop()` sonrasında, `encode_wav()` öncesinde PCM süresini hesapla; `< MIN_RECORDING_SECONDS` dalında içerik taşımayan INFO logu yaz, `_emit(AppState.READY)` çağır ve `return` et. Bölme için geçersiz metadata oluşursa bunu no-speech sayma; mevcut gerçek hata yoluna bırak.
- [ ] Test komutu: `python -m pytest tests/test_controller.py -q`

### Task 3 — Boş transkripsiyonu normal READY sonucu yap

**Done when:** Boş/whitespace dönüş ve yalnız bilinen legacy `Transkripsiyon boş döndü.` hatası paste/clean yapmadan `READY` olur; diğer hatalar `ERROR` kalır.

- [ ] (2–5 dk) `tests/test_controller.py` içindeki blank beklentilerini `ERROR`dan `READY`ye çevir; hem combined hem `local_only` modunda cleaner ve injector’ın çağrılmadığını, `WRITTEN/ERROR` olayı çıkmadığını ayrı assertionlarla doğrula.
- [ ] (2–5 dk) `TranscriptionError("Transkripsiyon boş döndü.")` atan test double için `READY`; farklı `TranscriptionError` için `ERROR` bekleyen failing regresyon testlerini ekle.
- [ ] (2–5 dk) Testleri kırmızı çalıştır: `python -m pytest tests/test_controller.py -q`.
- [ ] (2–5 dk) `controller.py::_pipeline()` içinde blank/whitespace `raw` dalını exception yerine INFO log + `_emit(AppState.READY)` + erken `return` yap; clean ve paste kesinlikle bu dalın altında çalışmasın.
- [ ] (2–5 dk) Bilinen legacy empty-transcription istisnasını dar bir `TranscriptionError` ayrımıyla aynı no-speech bitişine yönlendir; exception mesajı kullanıcı event’ine/log detayına taşınmasın ve diğer exception’lar genel `ERROR` handler’a ulaşsın.
- [ ] Test komutu: `python -m pytest tests/test_controller.py -q`

### Task 4 — ERROR durumunu yeniden başlatılabilir yap

**Done when:** `ERROR`dan çağrılan `start_recording()` recorder’ı başlatıp `LISTENING`e geçer; shutdown ve busy state guard’ları değişmez.

- [ ] (2–5 dk) `tests/test_controller.py` içinde controller’ı `ERROR`a geçirip `start_recording()` çağıran failing testi yaz; recorder `starts` artışı, state `LISTENING` ve event doğrula.
- [ ] (2–5 dk) Parametrik guard testiyle `LISTENING`, `TRANSCRIBING`, `CLEANING`, `INJECTING`, `WRITTEN` ve shutdown durumlarında yeni recorder çağrısı yapılmadığını kilitle.
- [ ] (2–5 dk) Testleri kırmızı çalıştır: `python -m pytest tests/test_controller.py -q`.
- [ ] (2–5 dk) `controller.py::start_recording()` guard’ını `_state not in {AppState.READY, AppState.ERROR}` biçiminde daralt; state’i recorder çağrısı öncesi mevcut atomik lock akışında `LISTENING`e al ve mikrofon başlatma hatasının yine `ERROR`a dönmesini koru.
- [ ] Test komutu: `python -m pytest tests/test_controller.py -q`

### Task 5 — Pipeline entegrasyonu ve tam regresyon

**Done when:** Kısa/sessiz işlem gerçek sıra ile yapıştırmasız `READY` olur, ardından yeni kayıt kabul edilir; hedefli ve tüm testler taze çalıştırıldığında geçer.

- [ ] (2–5 dk) `tests/test_pipeline.py` içine kısa clip → no STT/LLM/clipboard → `READY` → ikinci `start_recording()` kabul edilir izini doğrulayan entegrasyon testi ekle.
- [ ] (2–5 dk) Normal combined ve `local_only` trace testlerinin aynı kaldığını; gerçek STT/cleaner/injector hatalarının `ERROR` üretmeye devam ettiğini kontrol et ve yalnız yeni sözleşmeyle çelişen eski blank beklentisini güncelle.
- [ ] (2–5 dk) Hedefli paketi çalıştır: `python -m pytest tests/test_transcriber.py tests/test_controller.py tests/test_pipeline.py -q`.
- [ ] (2–5 dk) Tam regresyonu çalıştır: `python -m pytest -q`.

### Task 6 — Otomatik başlatma ve kısayol scriptleri

**Done when:** `baslat_arkaplan.vbs`, `otomatik_baslat_kur.bat` ve `otomatik_baslat_kaldir.bat` dosyaları oluşturulur, `README.md` güncellenir.

- [ ] (2–5 dk) `baslat_arkaplan.vbs` oluştur: script kendi klasörünü referans alarak `pythonw.exe main.py` komutunu penceresiz (0) ve arka planda çalıştırsın.
- [ ] (2–5 dk) `otomatik_baslat_kur.bat` oluştur: Windows Başlangıç klasörüne (`%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\Ses Yazıcı.lnk`) `baslat_arkaplan.vbs` hedefiyle kısayol oluştursun.
- [ ] (2–5 dk) `otomatik_baslat_kaldir.bat` oluştur: Başlangıç klasöründeki kısayolu silsin.
- [ ] (2–5 dk) `README.md` dosyasını güncelle: otomatik başlatma ve kısayol scriptlerinin kullanımını belgele.
- [ ] (2–5 dk) `git diff` ile tüm değişikliklerin plana uygun olduğunu incele.

---

## 6. Asena handoff checklist

Asena yalnız `IMPLEMENTATION_ARTIFACT` üretmelidir; YEŞİL/Yargu hükmü yazmamalıdır.

- [ ] Parent transfer block’u aynen referansla; çelişki veya eksik scope görürse `BLOCKED_CONTEXT` ile dur.
- [ ] A1–A8 ve A10 için ayrı evidence satırı ver; A9’un uygulanıp uygulanmadığını açıkça belirt.
- [ ] Changed files listesini ve her kabul maddesi → test/assertion eşlemesini yaz.
- [ ] Gerçekte çalıştırılan komutları, pass/fail sayılarını ve kısa çıktı özetini yaz; çalıştırılmayan komutu çalışmış gibi bildirme.
- [ ] Kanıt şekillerini değiştirme: kısa clip → downstream spies → state/event; empty Whisper → return/temp cleanup; ERROR → restart; startup scripts → path/target validation.
- [ ] İlk KIRMIZI gelirse Yargu’nun tüm blockerlarını tek listede ele al; ikinci turda liste dışı kapsam açma.
- [ ] Blocker varsa dosya/satır ve etkisiyle bildir; commit, push, release veya deploy yapma.

### Asena parent transfer block

- `parent_artifact`: `C:/Users/esahi/OneDrive/Masaüstü/git_r/ses-yazici/.hermes/plans/2026-09-22-bos-ses-ve-hata-toparlanmasi.md`
- `scope_id`: `ses-yazici-bos-ses-toparlanma-2026-09-22`
- `acceptance_inventory`: `A1–A8 ve A10 zorunlu; A9 isteğe bağlı.`
- `evidence_required`: `Locked acceptance inventory` tablosundaki kanıt zincirleri + hedefli pytest + tam pytest + startup script doğrulaması + scoped diff.
- `out_of_scope`: Parent bloktaki kapsam dışı liste.
- `iteration`: `2`
- `blockers`: `Yok.`

---

## 7. Yargu beklentisi

Yargu yalnız `REVIEW_ARTIFACT` üretmeli; locked inventory’yi taze ve bağımsız kanıtla satır satır `PASS/FAIL` hükümlemeli ve sonuçta `YEŞİL | SARI | KIRMIZI` vermelidir.

### Testler ve taze kanıt

- `python -m pytest tests/test_transcriber.py tests/test_controller.py tests/test_pipeline.py -q`
- `python -m pytest -q`
- Scoped diff kontrolü: yalnız `controller.py`, `transcriber.py`, `tests/test_controller.py`, `tests/test_transcriber.py`, `tests/test_pipeline.py` beklenir.
- A1 boundary kanıtı: `< 0.3` STT’ye gitmez; `== 0.3` gider.
- A4/A5 ayrım kanıtı: blank dönüş ve bilinen no-speech istisnası `READY`; başka STT hatası `ERROR`.
- A6 recovery kanıtı: `ERROR → start_recording → LISTENING`; busy/shutdown re-entry hâlâ reddedilir.
- Bir worker exit code’u veya Asena öz bildirimi yerine test dosyalarını ve uygulama yollarını bağımsız incele.

### Security hotspots

- Kullanıcı event mesajlarına exception metni, transkript, ses içeriği, path, API key/token veya Authorization değeri sızmamalı.
- No-speech ayrımı geniş `except TranscriptionError` ile gerçek model/kurulum/inference hatalarını yutmamalı; yalnız blank dönüş ve tanımlı legacy boş-transkripsiyon sinyali normalleştirilmeli.
- `ERROR`dan restart izni shutdown veya aktif pipeline durumlarında paralel/çifte recorder başlatmaya yol açmamalı; lock/state guard korunmalı.
- Süre hesabında sıfır/geçersiz `sample_rate` veya `channels` sessizce başarılı sayılmamalı; güvenli gerçek hata yoluna düşmeli.
- Kısa kayıt optimizasyonu recorder’ın `stop()`/stream kapatma adımından önce dönmemeli.

### UI checklist

- **Surface/token:** Görsel diff beklenmez; `gui.py` ve `ui_tokens.py` değişmemeli. Surface N/A, token kaynağı `ui_tokens.py` korunur.
- **State:** Kısa/sessiz sonuçta son görünür durum `Hazır`; `Hata` ve `Yazıldı` olayı çıkmamalı. Gerçek hatada `Hata` görünürlüğü korunmalı, yeni basış toparlanabilmeli.
- **A11y/theme:** Widget, focus, contrast, motion ve tema değişikliği yok; regresyon yaratacak GUI değişikliği kapsam dışıdır.
- Indigo/emoji/lorem/sahte metrik veya superseded agritech/tarla paleti eklenmemeli.

### Yargu parent transfer block

- `parent_artifact`: Asena’nın doğrulanmış `IMPLEMENTATION_ARTIFACT` yolu/kimliği; yoksa `BLOCKED_CONTEXT`.
- `scope_id`: `ses-yazici-bos-ses-toparlanma-2026-09-22`
- `acceptance_inventory`: `A1–A8 zorunlu; A9 isteğe bağlı.`
- `evidence_required`: Kilitli kanıt zincirleri ve Yargu’nun taze hedefli/tam pytest çıktısı.
- `out_of_scope`: Yeni VAD, UI, config, dependency, packaging, deploy ve parent bloktaki diğer maddeler.
- `iteration`: Asena artifact’ındaki iteration ile aynı olmalı.
- `blockers`: Asena artifact’ındaki açık blockerlar; çelişirse `BLOCKED_CONTEXT`.

---

## 8. Riskler

- PCM byte uzunluğundan süre hesabı 16-bit signed PCM varsayımına dayanır; `AudioClip` ve `encode_wav()` mevcut sözleşmesi zaten sample width `2` kullanır. Yeni format soyutlaması bu işte YAGNI’dır.
- 0.3 saniyeden kısa gerçek bir sözcük de atlanabilir; eşik Eren’in açık ürün talebidir ve ayara taşınmayacaktır.
- Legacy hata mesajına dayalı uyumluluk dar ve bilinçli tutulmalıdır; tüm `TranscriptionError` örneklerini no-speech saymak gerçek arızaları gizler.
- `TRANSCRIBING` olayı klip süresi ancak recorder durduktan sonra bilindiği için kısa süre görünür olabilir; yeni state/UI eklemek kapsam dışıdır.

---

## 9. Yapma listesi

- VAD, RMS/sessizlik eşiği, debounce veya yeni ses kütüphanesi ekleme.
- `0.3` eşiğini yeni GUI/config alanına dönüştürme.
- Tüm `TranscriptionError` hatalarını `READY` yaparak gerçek STT arızalarını gizleme.
- Cleaner’ın boş çıktısını no-speech ile karıştırma; mevcut “Düzenlenmiş metin boş” gerçek pipeline hatası semantiğini değiştirme.
- `ERROR` durumunu tamamen kaldırma veya her exception’ı sessizce yutma.
- Recorder durdurulmadan/stream kapanmadan erken return etme.
- Ham ses, transkript, secret, `.env`, token, hash/prefix/suffix okuma veya loglama.
- GUI/theme/token dosyalarını, hotkey servisini veya dependency listesini değiştirme.
- Generated build, installer, VPS, deploy, sync/rollback, commit veya push yapma.
- Test standardını review turlarında değiştirme; acceptance inventory dışında yeni blocker açma (kanıtlı security/data-loss/product ihlali hariç).
