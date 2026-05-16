# 00 — Proje Genel Özet

## Projenin Adı

**CCDDA** — *Children's Drawing-Based Duygu/Emotion Analizi*

Proje dizin adı `CCDDA`'dır. Commit geçmişi ve dosya yapısından çıkarıldığı kadarıyla bu kısaltma, "Children's Chart/Drawing Duygu Analizi" ya da benzer bir Türkçe-İngilizce karışık isimlendirmeye karşılık gelmektedir. Kesin açılımı commit ya da README'de belirtilmemiştir.

---

## Projenin Amacı

Bu proje, çocuklara ait el çizmesi resimleri kullanarak yapay zeka ile duygu sınıflandırması yapmayı hedeflemektedir. Klinik psikolojide yaygın olarak kullanılan projektif çizim testlerinden (ör. İnsan Çizme Testi, Ev-Ağaç-İnsan) esinlenerek, çocukların çizdikleri resimlerin bilgisayarlı görü yöntemleriyle analiz edilip analiz edilemeyeceği araştırılmaktadır.

Proje iki farklı sınıflandırma hedefi ile başlamıştır:

1. **Duygu sınıflandırması**: Resmi çizen çocuğun duygusal durumunun tespit edilmesi
2. **Cinsiyet sınıflandırması**: Çizim sahibinin cinsiyetinin çizimden tahmin edilmesi

Proje ilerledikçe cinsiyet sınıflandırması bırakılmış, duygu sınıflandırması daha fazla sınıf içerecek biçimde genişletilmiştir.

---

## Çözülmeye Çalışılan Problem

Çocukların duygusal durumları genellikle sözel ifadelerle tam olarak ortaya konulamaz. Projektif çizim testleri bu boşluğu doldurmak amacıyla psikoloji pratiğinde kullanılmaktadır; ancak bu testlerin yorumlanması uzman gerektirmekte, zaman almakta ve öznellik içermektedir.

Bu proje, söz konusu değerlendirme sürecini bir dereceye kadar otomatikleştirmeyi ve nesnel bir referans araç sunmayı amaçlamaktadır. Yapay zekanın bir klinisyenin yerini almak için değil, ona destek olmak için kullanılması hedeflenmektedir.

---

## Kullanılan Teknolojiler

### Derin Öğrenme & Görüntü İşleme
| Teknoloji | Kullanım Amacı |
|---|---|
| PyTorch | Ana derin öğrenme çerçevesi |
| EfficientNet-B0 / B2 / B3 | Görüntü özellik çıkarımı için CNN |
| Torchvision | Veri dönüşümleri, model ağırlıkları |
| Grad-CAM | Açıklanabilirlik (hangi bölgeye bakıldığının görselleştirilmesi) |

### Doğal Dil İşleme (Erken Dönem — Sonradan Kaldırıldı)
| Teknoloji | Kullanım Amacı |
|---|---|
| `dbmdz/bert-base-turkish-cased` | Türkçe metin kodlaması |
| HuggingFace Transformers | BERT entegrasyonu |

### Pseudo-Etiketleme & Veri Genişletme (Son Dönem)
| Teknoloji | Kullanım Amacı |
|---|---|
| Qwen2.5-VL (3B / 7B) | Çok modlu büyük dil modeli ile görsel etiketleme |
| HuggingFace Inference API | Uzak model çağrıları |
| Ollama | Yerel LLM çalıştırma |

### Backend & API
| Teknoloji | Kullanım Amacı |
|---|---|
| FastAPI | REST API sunucusu |
| Uvicorn | ASGI sunucu |
| Pydantic | Veri doğrulama |

### Frontend
| Teknoloji | Kullanım Amacı |
|---|---|
| React + Vite | Web arayüzü |
| TypeScript | Tip güvenli frontend kodu |
| Tailwind CSS | Stil |
| i18next | Türkçe/İngilizce çoklu dil desteği |

### Masaüstü Uygulama
| Teknoloji | Kullanım Amacı |
|---|---|
| PyInstaller | Python uygulamasını `.exe` formatına dönüştürme |
| pywebview | Masaüstünde web içeriği gösterme |
| Inno Setup | Windows kurulum paketi oluşturma |
| Tkinter | Erken dönem yerel GUI |

### Veri & Raporlama
| Teknoloji | Kullanım Amacı |
|---|---|
| Pandas, pyarrow | Veri manipülasyonu |
| scikit-learn | Metrik hesaplama |
| python-docx | DOCX raporu üretimi |
| Matplotlib | Görselleştirme |

---

## Genel Sistem Yapısı

Proje tarihin farklı dönemlerinde farklı mimarilere sahip olmuştur:

### İlk Mimari (Kasım 2025)
Çok modlu sinir ağı: görüntü (EfficientNet-B0) + metin (Türkçe BERT) → ortak gömmeler → iki ayrı sınıflandırma kafası (duygu + cinsiyet)

### Arayüz Dönemi (Kasım 2025 – Mart 2026)
Tkinter tabanlı masaüstü GUI → React web arayüzü → FastAPI arka ucu → PyInstaller ile paketlenmiş masaüstü uygulama

### Yeniden Yapılanma (Nisan 2026)
Eski çok modlu yapı (BERT dahil) tamamen kaldırıldı. Yeni hedef: **yalnızca görüntü tabanlı 4 sınıflı duygu tanıma** (Anger / Fear / Happiness / Sadness)

### Yeni Veri Hattı (Mayıs 2026)
Pseudo-etiketleme yaklaşımıyla büyük ölçekli veri üretimi. Öğretmen modeller (EfficientNet-B2/B3) çizim resimlerini etiketliyor; yüksek güvenilirlikli tahminler yeni eğitim veri kümesini oluşturuyor.

---

## Veri Kaynakları

Commit geçmişi ve dosya yapısından anlaşılan veri kaynakları:

- **KIDO Veri Kümesi**: Türk okul çocuklarına ait el çizmesi resimler; dosya adları `[okul_id]-[sınıf]-[öğrenci_id]-[cinsiyet]-[duygu]` formatında kodlanmış (örn. `101-1A-369-F-H.jpg`)
- **HuggingFace Parquet Dosyaları**: `Dataset/huggingface/` dizininde saklanan büyük ölçekli ek veri
- **Roboflow — Drawing Facial Emotions**: `Dataset/Images/Emotion_Roboflow_DrawingFacialEmotions/`
- **SigLIP 4-class**: `Dataset/Images/Emotion_SigLIP_4Class/` — SigLIP modeli kullanılarak 4 sınıfa göre önceden sınıflandırılmış veri
- **Türetilmiş Veri Kümeleri**: Pseudo-etiketleme ile üretilmiş veri manifestleri (`out/highconf_pipeline/`, `out/consensus_pipeline/`)

---

## Tez Bağlamında Projenin Önemi

Bu proje aşağıdaki araştırma sorularını karşılamayı amaçlamaktadır:

1. Çocuk çizimleri yalnızca görsel özelliklerinden hareketle duygu sınıflandırmasına uygun mudur?
2. Çok modlu yaklaşımlar (görüntü + metin) görüntü-only yaklaşımdan daha iyi performans gösterir mi?
3. Pseudo-etiketleme ile veri artırımı sınıflandırma başarısını iyileştirilebilir mi?
4. Bu sistem klinisyenlere pratik destek sağlayabilecek bir kullanılabilirlik düzeyine ulaşabilir mi?

---

## Mevcut Durumun Özeti (Kod Yapısından Çıkarılan)

- **Eski AI katmanı** Nisan 2026'da bilinçli olarak kaldırılmıştır.
- `api_server.py` içinde `/predict` endpoint'i hâlâ vardır ancak `503 reset_in_progress` döndürmektedir.
- Yeni 4-sınıflı sistem için `run_highconf_pipeline.py` ve `run_consensus_pipeline.py` aktif olarak geliştirilmektedir.
- Frontend (React) ve masaüstü uygulama kabuğu korunmuştur; yeni model tamamlandığında bu kabuğa bağlanacaktır.
- `artifacts/` klasörü eğitim kontrol noktaları için yer tutucu olarak kullanılmaktadır.
