# Ses Yazıcı Üçlü Çalışma/Akış Modu — Implementation Plan

PLAN_ARTIFACT

scope_id: `ses-yazici-flow-modes-2026-09-21-v1`
iteration: `1`

## Parent transfer block

- `parent_artifact`: `USER_REQUEST/2026-09-21/ses-yazici-uc-mod`
- `scope_id`: `ses-yazici-flow-modes-2026-09-21-v1`
- `acceptance_inventory`: Bu plandaki “Locked acceptance inventory” bölümü; uygulama boyunca adlar ve zorunlu/isteğe bağlı sınıfları değiştirilemez.
- `evidence_required`: Her acceptance satırı için aşağıdaki kanıt biçimi + taze hedefli pytest + taze tam suite çıktısı.
- `out_of_scope`: Deploy, installer/packaging, yeni sync/rollback aracı, yeni STT/LLM sağlayıcısı, streaming/VAD, yeni framework veya dependency, secret taşıma/migrasyon.
- `iteration`: `1`
- `blockers`: `Yok.` API-only, mevcut yapıdaki yapılandırılabilir STT API endpoint’i ile 9Router LLM endpoint’ini kullanır; STT’nin de aynı 9Router origin’inde bulunacağı varsayılmaz.

## 1. Goal · Architecture · Tech/repo

**Goal:** Ses Yazıcı’ya kalıcı ve anlaşılır `combined`, `local_only`, `api_only` akış seçimi eklemek; varsayılanı yerel Whisper `base` + 9Router temizliği yapmak ve `local_only` yolunda ham metni hiçbir API/LLM çağrısı olmadan aynen yapıştırmak.

**Architecture:** JSON’a uygun tek kanonik seçim `AppSettings.flow_mode: FlowMode` olur; controller bu değere göre yalnız temizleme/paste dalını seçer, composition root (`main.py`) ise moda uygun yerel/API transcriber ve opsiyonel cleaner kurar. Mevcut `SttSettings.provider` geriye dönük config uyumluluğu için veri yapısında kalabilir fakat GUI ve çalışma zamanı için otorite değildir; servis fabrikası provider’ı moddan türetir, böylece çelişkili iki kullanıcı seçimi oluşmaz. TDD sırası failing mode-contract testleri → minimum routing/config/UI kodu → tam regresyondur; DRY için mod sabitleri/etiket eşlemesi tek kaynaktan kullanılır, YAGNI gereği yeni strategy sınıf hiyerarşisi kurulmaz.

**Tech / repo:** Python 3.11+, frozen dataclass + `Literal`, Tkinter/ttk, httpx, faster-whisper (opsiyonel local requirements), pytest; kaynak repo `C:/Users/esahi/OneDrive/Masaüstü/git_r/ses-yazici`.

**Repo/source-build ayrımı:**
- **A) Kaynak feature + test:** Bu planın tamamı editable Python kaynakları, testler ve README üzerindedir.
- **B) Generated/release output:** Repoda ayrı generated production build veya deploy hedefi saptanmadı; bu aşama `N/A` ve kapsam dışıdır. Test başarısı release/deploy iddiası değildir.

**Başlangıç kanıtı:** Planlama sırasında `python -m pytest -q` çalıştı ve `39 passed in 0.24s` döndü. Bu, uygulama sonrası kanıt yerine geçmez.

## 2. Design

**Design surface:** `rasyon_web_ui` dark green app dilinin native Tk uyarlaması.

**Token source path:** Repo içi `ui_tokens.py`; kanon `C:/Users/esahi/OneDrive/Belgeler/Notlar/91 - AI Context/DESIGN_SYSTEM.md` ve kaynak referansı `rasyon_web_ui/src/index.css`.

**Design read:** Masaüstü ayar formu · Türkçe dikte kullanıcısı · koyu zinc/yeşil uygulama yüzeyi · mevcut sıkı, işlevsel ttk formuna tek açıklayıcı readonly akış Combobox’ı ekle; yeni renk veya görsel motif üretme.

**UI davranışı:** Combobox görünür Türkçe etiket gösterir, fakat ViewModel etiketi kanonik `FlowMode` değerine çevirir. `STT sağlayıcısı` alanı kaldırılır; aksi halde akış modu ile provider arasında çelişkili iki kontrol oluşur. STT API adres/model/key ve LLM alanları gelişmiş ayar olarak görünür kalır; bu kapsam dinamik alan gizleme/disable etme içermez.

## Locked acceptance inventory

| ID | Sınıf | Kilitli kabul maddesi | Kanıt şekli |
|---|---|---|---|
| A1 | zorunlu | `FlowMode = Literal["combined", "local_only", "api_only"]`; `AppSettings.flow_mode` varsayılanı `combined`, `SttSettings.local_model` varsayılanı `base`; save/load round-trip bu değerleri korur. | default object → atomic save raw payload (secret yok) → load equality |
| A2 | zorunlu | GUI readonly seçiminde üç anlaşılır Türkçe etiket vardır ve seçim kanonik moda çevrilir; bağımsız `STT sağlayıcısı` kullanıcı alanı kaldırılır. | visible label/value set → ViewModel build → canonical `flow_mode` |
| A3 | zorunlu | `combined`, yerel Whisper’ı seçer; raw transcript’i bir kez `cleaner.clean` ile temizler ve temiz metni bir kez yapıştırır. | mode → local transcriber factory → raw → cleaner call → paste(cleaned) → WRITTEN |
| A4 | zorunlu | `local_only`, yerel Whisper’ı seçer; cleaner/LLM’yi kurmaz veya çağırmaz; nonblank `raw` değerini karakterlerini değiştirmeden `injector.paste(raw)` ile yapıştırır ve WRITTEN olayı üretir. | mode → local transcriber → exact raw payload → no cleaner/no API credential read → paste(raw) → WRITTEN |
| A5 | zorunlu | `api_only`, API Whisper transcriber’ı ve LLM cleaner’ı seçer; transcript temizlendikten sonra temiz metni yapıştırır. | mode → API transcriber factory + cleaner factory → raw → cleaned → paste(cleaned) → WRITTEN |
| A6 | zorunlu | `local_only` başlangıç/kayıt akışı STT veya LLM API anahtarı gerektirmez ve hiçbir HTTP isteği üretmez; `combined` yalnız LLM key, `api_only` STT + LLM key ister. | fake credential call log + mock transport request log per mode |
| A7 | zorunlu | Controller durum izi `local_only` için CLEANING içermez; diğer iki mod CLEANING içerir. Tüm başarılı yollar INJECTING → WRITTEN → READY ile biter; boş transcript ve kullanılan servis hataları paste etmez ve ERROR verir. | per-mode state event list + spy call order + error table |
| A8 | zorunlu | URL doğrulaması yalnız modda kullanılan uzak servisler için zorunludur: local_only hiçbir uzak URL’ye, combined yalnız LLM URL’ye, api_only STT + LLM URL’ye bağlıdır. | mode × invalid URL validation matrix |
| A9 | zorunlu | Mevcut 39 test silinmeden/skip-xfail ile etkisizleştirilmeden geçer; yeni mod/config/UI/composition testleri de tam suite’te geçer. | git diff test inventory → targeted tests → `python -m pytest -q` fresh output |
| A10 | zorunlu | README üç modun veri sınırlarını, `base` defaultunu, local ekstra kurulumunu ve her modun credential/ağ gereksinimini doğru açıklar. | README checklist test + metin incelemesi |
| A11 | zorunlu | Config/key güvenliği korunur: API anahtarları JSON’a girmez, kullanıcıya gösterilen hata transcript/secret ayrıntısı sızdırmaz, uzak kullanılan endpoint’lerde mevcut HTTPS kuralı sürer. | config raw scan + sanitized controller error assertion + URL policy tests |
| A12 | isteğe bağlı | Moda göre ilgisiz API alanlarını GUI’de disable/hide etmek. Bu iş olmadan özellik tamamlanmış sayılır; uygulanırsa a11y/focus testleri ayrıca gerekir. | widget state/focus test; yalnız ayrıca uygulanırsa |

Acceptance freeze: Yargu yeni blocking maddeyi yalnız gerçek güvenlik açığı, veri kaybı veya bu kilitli ürün sözleşmesinin açık ihlali için `file:line + somut etki` ile ekleyebilir. Diğer gözlemler SARI/sonraki iş olur.

## 3. Files

| Path | Create/Edit | Sorumluluk |
|---|---|---|
| `settings.py` | Edit | `FlowMode` tipi/sabitleri, `flow_mode` default ve doğrulaması, yerel `base` defaultu, moda bağlı URL doğrulama politikası, persistence uyumluluğu. |
| `gui.py` | Edit | Türkçe mod etiketi ↔ kanonik değer eşlemesi, readonly Combobox, provider kontrolünün kaldırılması, dinamik satır indeksleri ve ViewModel dönüşümü. |
| `controller.py` | Edit | `_pipeline` içinde local_only temizleme bypass’ı; exact raw paste ve durum olayları; cleaner’ın opsiyonel oluşuna güvenli guard. |
| `main.py` | Edit | Moddan provider türeten test edilebilir servis composition helper’ı; moda göre credential erişimi/cleaner kurulumu; create/rebuild reuse. |
| `tests/test_settings.py` | Edit | Varsayılan, round-trip, invalid mode ve mode × URL validation matrisi. |
| `tests/test_gui.py` | Edit | Üç kullanıcı etiketi, canonical mapping, provider alanının yokluğu, token/readonly sözleşmesi. |
| `tests/test_controller.py` | Edit | Üç modun paste/cleaner/state/error unit kontratları; raw metnin birebir korunması. |
| `tests/test_pipeline.py` | Edit | Üç uçtan uca mocked call trace; local_only içinde LLM çağrısının yokluğu. |
| `tests/test_main.py` | Create | Composition root: yerel/API seçimleri, cleaner optionality, mode bazlı credential reads ve sıfır request kanıtı. |
| `tests/test_readme.py` | Edit | Üç mod, base default, offline/credential veri sınırı dokümantasyon checklist’i. |
| `README.md` | Edit | Kurulum/kullanım/güvenlik metnini üç moda göre güncelleme. |
| `transcriber.py` | No change expected | Mevcut `build_transcriber` local/API fabrikası reuse edilir; yalnız testin zorunlu kıldığı küçük tip uyumu çıkarsa editlenebilir, yeni provider eklenmez. |
| `ui_tokens.py` | No change | Kanonik mevcut Tk token kaynağı; yeni token üretilmez. |
| Generated output / deploy target | N/A | Ayrı build/deploy yüzeyi yok; üretim/release bu planın dışındadır. |

## Veri tipleri ve sınırlar

- `FlowMode = Literal["combined", "local_only", "api_only"]` (`settings.py`).
- `FLOW_MODES: frozenset[str]` veya eşdeğer immutable doğrulama kümesi; runtime doğrulama tek kaynaktan yapılır.
- `AppSettings.flow_mode: FlowMode = "combined"`.
- `SttSettings.local_model: Literal["tiny", "base"] = "base"`.
- `AppController.cleaner`: `Cleaner | None` davranışında; yeni runtime Protocol ancak mevcut typing stiline doğal biçimde gerekiyorsa eklenir. `None` yalnız local_only composition’ında geçerlidir.
- GUI eşlemesi: kullanıcı metni → `FlowMode`; ters eşleme mevcut ayarı gösterir. Localize label hiçbir zaman config’e yazılmaz.
- `SttSettings.provider`, eski config/factory uyumu için kalırsa deprecated internal inputtur; controller ve GUI karar vermez, `main.py` modu `local`/`api` provider’a türetir.

## 4. Tasks

### Task 1 — Settings kontratını TDD ile kilitle

**Done when:** Üç mod tipi/defaultu, `base` defaultu, round-trip ve moda bağlı URL doğrulama matrisi hedefli testte geçer.

- [ ] (2–5 dk) `tests/test_settings.py` içinde önce combined/base default, üç geçerli mod ve geçersiz mod için failing testleri yaz.
- [ ] (2–5 dk) Aynı dosyada `local_only`/`combined`/`api_only` için kullanılan-kullanılmayan URL validation matrisini failing test olarak ekle.
- [ ] (2–5 dk) `settings.py` içine `FlowMode`, immutable allowed set, `AppSettings.flow_mode` ve `local_model="base"` minimum değişikliklerini yap.
- [ ] (2–5 dk) `validate_settings`i moda göre yalnız kullanılan uzak URL’leri doğrulayacak şekilde daralt; `SettingsStore` round-trip’in eksik eski `flow_mode` alanında yeni defaulta düştüğünü koru.
- [ ] Test: `python -m pytest tests/test_settings.py -q`

### Task 2 — GUI mod seçimini kanonik değere bağla

**Done when:** Kullanıcı üç açıklayıcı Türkçe seçeneği readonly Combobox’ta görür; ViewModel canonical mode üretir ve STT provider için ikinci bir kontrol yoktur.

- [ ] (2–5 dk) `tests/test_gui.py` içine üç label, label→mode dönüşümü ve `STT sağlayıcısı` alanının kaldırılması için failing test ekle/güncelle.
- [ ] (2–5 dk) `gui.py` içinde tek mod label map’i tanımla; `SettingsViewModel.build` ile defaults tarafında çift yönlü dönüşümü uygula.
- [ ] (2–5 dk) `FIELD_SPECS`e “Çalışma modu” readonly Combobox’ını ekle ve `stt_provider` satırını kaldır; tokenları değiştirme.
- [ ] (2–5 dk) Durum ve button satırlarını sabit `11/12` yerine `len(FIELD_SPECS)` tabanlı hesapla; eklenen alanın yerleşimi çakışmasın ve Tab sırası doğal kalsın.
- [ ] Test: `python -m pytest tests/test_gui.py -q`

### Task 3 — Mode-aware servis composition’ını TDD ile ayır

**Done when:** Composition helper her mod için doğru transcriber/cleaner’ı üretir; local_only hiçbir key okumaz, combined yalnız LLM key okur, api_only iki keyi okur.

- [ ] (2–5 dk) `tests/test_main.py` oluştur; fake credential store ve monkeypatched factories ile üç modun provider/cleaner/key-call kontratlarını failing test olarak yaz.
- [ ] (2–5 dk) Local_only için boş credential store ile başarı ve mock HTTP transport request listesinin boş kalması kanıtını ekle.
- [ ] (2–5 dk) `main.py` içinde moda göre `SttSettings.provider` türeten, transcriber ve `cleaner | None` döndüren küçük `build_services` helper’ı çıkar.
- [ ] (2–5 dk) `create_app` ve `rebuild` fonksiyonlarını aynı helper’ı kullanacak biçimde bağla; local_only yolunda `llm_api_key` dâhil hiçbir key isteme, combined/api_only’da eksik gerekli key için mevcut sanitize hata stilini koru.
- [ ] Test: `python -m pytest tests/test_main.py tests/test_transcriber.py tests/test_llm_cleaner.py -q`

### Task 4 — Controller pipeline dallarını TDD ile uygula

**Done when:** local_only raw metni aynen paste eder ve CLEANING üretmez; combined/api_only cleaned metni paste eder; tüm state/error sözleşmeleri korunur.

- [ ] (2–5 dk) `tests/test_controller.py` fake cleaner’a call log ekle; üç mod için failing call/state assertions yaz.
- [ ] (2–5 dk) Local_only test datasını baş/son boşluk, noktalama ve konuşma dolgusuyla kur; nonblank kontrolünden sonra `paste(raw)` değerinin byte-for-byte/eşit string olduğunu doğrula.
- [ ] (2–5 dk) `controller.py::_pipeline` içinde yalnız local_only dalında CLEANING ve `cleaner.clean`i atla; diğer modlarda cleaner yoksa kontrollü hata ver, ortak INJECTING/WRITTEN/READY kuyruğunu DRY tut.
- [ ] (2–5 dk) Boş raw, STT hatası, cleaner hatası ve paste hatasında hiçbir yanlış başarı/paste olmadığını; kullanıcı mesajında özel exception/transcript bulunmadığını test et.
- [ ] Test: `python -m pytest tests/test_controller.py -q`

### Task 5 — Entegrasyon call trace’lerini üç moda genişlet

**Done when:** Mocked kayıt→STT→opsiyonel LLM→clipboard zinciri her mod için sıralı ve beklenen payload ile kanıtlanır.

- [ ] (2–5 dk) `tests/test_pipeline.py` mevcut combined trace’i açıkça `flow_mode="combined"` yapacak failing beklentiye güncelle.
- [ ] (2–5 dk) Local_only trace’e `audio:start → audio:wav → local-stt → clipboard:raw → keyboard` ekle ve `llm:clean` yokluğunu assert et.
- [ ] (2–5 dk) Api_only trace’e API-STT ve LLM-clean adımlarını ayrı spy isimleriyle ekle; cleaned payload’ın clipboard’a gittiğini doğrula.
- [ ] (2–5 dk) Test helper tekrarlarını parametrization veya küçük factory ile azalt; modlar arası davranışı gizleyen aşırı abstraction kurma.
- [ ] Test: `python -m pytest tests/test_pipeline.py tests/test_controller.py tests/test_main.py -q`

### Task 6 — README ve UI/a11y sözleşmesini güncelle

**Done when:** Doküman üç modu ve veri sınırlarını yanlış vaat olmadan açıklar; GUI mevcut token/focus yaklaşımını korur.

- [ ] (2–5 dk) `tests/test_readme.py` checklist’ine Kombine, Yalnızca Yerel/Ham, Yalnızca 9Router/API, base ve “local_only API anahtarı/ağ gerektirmez” maddelerini failing test olarak ekle.
- [ ] (2–5 dk) `README.md` giriş/kurulum/kullanım/güvenlik bölümlerini üç mod tablosu ile güncelle; ilk local model kullanımının model indirmek için ağ gerektirebileceğini, hazır model sonrası diktenin offline olduğunu açıkça ayır.
- [ ] (2–5 dk) GUI source testinde renklerin yalnız `ui_tokens.py`den geldiğini, mod widget’ının readonly olduğunu ve label’ın mevcut olduğunu koru.
- [ ] Test: `python -m pytest tests/test_readme.py tests/test_gui.py -q`

### Task 7 — Tam regresyon ve IMPLEMENTATION_ARTIFACT kanıtı

**Done when:** Mevcut testler kaldırılmadan tüm suite geçer ve Asena her acceptance maddesini gerçek dosya/komut kanıtına bağlayan artifact üretir.

- [ ] (2–5 dk) `git diff -- tests` ile eski testlerin silinmediğini, skip/xfail ile etkisizleştirilmediğini kontrol et.
- [ ] (2–5 dk) `python -m pytest tests/test_settings.py tests/test_gui.py tests/test_main.py tests/test_controller.py tests/test_pipeline.py -q` çalıştır ve gerçek özeti kaydet.
- [ ] (2–5 dk) `python -m pytest -q` çalıştır; sıfır exit ve 39’dan fazla toplam passing case bekle, fakat uydurma sabit toplam yazma.
- [ ] (2–5 dk) Değişen dosyaları acceptance A1–A11’e eşleyen `IMPLEMENTATION_ARTIFACT` hazırla; yalnız gerçekten koşan komutları/özetlerini ve blockerları bildir, YEŞİL/Yargu hükmü yazma.
- [ ] Test: `python -m pytest -q`

## Asena handoff checklist

- [ ] Parent transfer blocku aynen taşı; scope/acceptance çelişirse kod yazmadan `BLOCKED_CONTEXT` dön.
- [ ] Önce failing test, sonra minimum implementation, sonra hedefli pass; en son full suite.
- [ ] `flow_mode` tek kanonik kullanıcı tercihi olsun; provider ikinci kullanıcı seçimine dönüşmesin.
- [ ] Local_only sırasında `cleaner.clean`, LLM factory, API key lookup ve HTTP request gerçekleşmediğini spy ile kanıtla.
- [ ] Raw metni yalnız boşluk kontrolü için `strip()` ile incele; paste payloadını strip/normalize etme.
- [ ] Secret, token veya transcript’i test çıktısı/error içine yazma; opaque fake değer kullan.
- [ ] Yeni dependency/framework/token ekleme; `ui_tokens.py`yi reuse et.
- [ ] `IMPLEMENTATION_ARTIFACT` alanları: changed files; A1–A11 → evidence; gerçekten koşan commands + output summary; blockers. Yargu hükmü veya release/deploy iddiası yok.

## 5. Yargu beklentisi

### Fresh test gates

1. `python -m pytest tests/test_settings.py tests/test_gui.py tests/test_main.py tests/test_controller.py tests/test_pipeline.py -q`
2. `python -m pytest -q`
3. `git diff --check`
4. `git diff -- settings.py gui.py controller.py main.py README.md tests`

Yargu, Asena’nın exit code/self-report’unu doğrulama saymaz; dosyaları ve komutları bağımsız kontrol eder. A1–A11’i satır satır `pass/fail + evidence` ile hükmeder. İlk KIRMIZI’da tüm blockerlar tek listede toplanır; ikinci turdan sonra liste dışı kapsam açılamaz (yalnız `file:line + somut security/data-loss/product impact` istisnası).

### Security hotspots

- `main.py`: local_only yolunda keyring get veya LlmCleaner construction olmamalı; combined STT key istememeli; api_only gerekli iki anahtarı kullanmalı.
- `controller.py`: ham/temiz transcript exception message’e veya loga eklenmemeli; servis hatasında paste/WRITTEN olmamalı.
- `settings.py`: config JSON’da key/secret bulunmamalı; moda göre kullanılan uzak URL’lerde HTTPS/loopback politikası gevşememeli.
- `gui.py`: key alanları maskeli kalmalı; flow label config’e yazılmamalı; credential davranışı moda göre yanlış “gerekli” hale gelmemeli.
- `transcriber.py`/`llm_cleaner.py`: Authorization/header içeriği test veya hata metninde açığa çıkmamalı.
- Offline iddiası: local_only için mock transport request count kesin `0`; hazır yerel model varsayımının README’de belirtilmesi gerekir.

### UI checklist

- [ ] Surface `rasyon_web_ui` native Tk adaptation ve token source `ui_tokens.py` doğru mu?
- [ ] Üç mod Türkçe ve anlaşılır mı; Combobox readonly ve klavye/Tab ile erişilebilir mi?
- [ ] Seçili label kaydet/yükle sonrası doğru kanonik moda dönüyor mu?
- [ ] Bağımsız STT provider kontrolü kaldırılarak çelişki önlendi mi?
- [ ] Yeni hardcoded renk, indigo/violet brand, emoji, lorem, sahte metrik veya superseded tarla/serif paleti yok mu?
- [ ] Mevcut dark zinc/green tokenlar, contrast ve focus davranışı bozulmamış mı?
- [ ] Yeni motion yok; reduced-motion kapsamı doğmuyor. Stack sapması/dependency yok mu?

### REVIEW_ARTIFACT biçimi

- `parent_artifact`: Asena’nın gerçek `IMPLEMENTATION_ARTIFACT` yolu/kimliği
- `scope_id`, kilitli `acceptance_inventory`, `evidence_required`, `out_of_scope`, `iteration`, `blockers`
- A1–A11 verdict tablosu ve taze komut çıktıları
- Security/UI findings
- Son hüküm yalnız `YEŞİL | SARI | KIRMIZI`
- Yeni blocker yalnız `file:line + somut güvenlik/veri kaybı/ürün etkisi`

## Riskler ve kararlar

- **Legacy `stt.provider` çelişkisi:** Alanı bir anda silmek mevcut JSON’u bozabilir. Minimum riskli çözüm alanı geriye dönük olarak tutup runtime provider’ını `flow_mode`dan türetmektir; GUI’de gösterilmez.
- **Default combined + local dependency:** Local model lazy load olduğundan GUI açılışı model yüklememeli; ilk dikte local extra/model eksikse sanitize hata verir. README kurulum gereksinimini görünür kılar.
- **“Tam offline” nüansı:** faster-whisper modeli ilk kullanımda indirebilir. Kabul, model önceden hazır olduktan sonra local_only dikte pipeline’ının sıfır API/HTTP kullanmasıdır; README bunu açık yazar.
- **Opsiyonel cleaner:** `None` yalnız local_only için geçerlidir; yanlış composition combined/api_only’da sessiz raw fallback yapmamalı, ERROR olmalıdır.
- **UI yüksekliği:** Bir alan eklenip biri kaldırıldığı için toplam satır sayısı değişmeyebilir; yine de hardcoded row indeksleri kaldırılarak gelecekte overlap riski azaltılır.

## 6. Yapma listesi

- Yeni framework, package veya strategy/plugin mimarisi ekleme.
- `combined` veya `api_only` hata verdiğinde sessizce raw paste fallback yapma.
- Local_only raw payloadını trim, whitespace-collapse, punctuation-fix veya LLM’den geçirme.
- Mode yanında bağımsız ve otoriter ikinci STT provider seçimi bırakma.
- API keyleri config/README/test snapshot/log/traceback içine yazma ya da secret okumaya çalışma.
- Kullanılmayan API URL’sini local_only için zorunlu doğrulayıp offline başlangıcı bloke etme.
- Mevcut 39 testi silme, gevşetme, skip/xfail etme veya sadece yeni testleri çalıştırıp “bitti” deme.
- Token uydurma, `#2F3A2E` serif/tarla paleti, hardcoded GUI rengi veya yeni UI dependency’si ekleme.
- Installer/build/deploy, commit/push, VPS, sync/rollback veya release işlemi yapma.
- Build/test çıktısından deploy/release başarısı iddia etme.
