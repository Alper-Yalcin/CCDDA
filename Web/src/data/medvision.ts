import {
  Activity,
  BadgeCheck,
  BrainCircuit,
  CheckCircle2,
  FileChartColumn,
  FileText,
  FlaskConical,
  Gauge,
  Layers3,
  Microscope,
  ServerCog,
  ShieldCheck,
  Sparkles,
  Target,
  UploadCloud,
  Users,
  Zap,
  type LucideIcon,
} from 'lucide-react';

// Bilingual string helper.
export type LS = { en: string; tr: string };

export const emotionClasses = ['Happy', 'Sad', 'Angry', 'Fear'];
export const emotionClassesTr = ['Mutlu', 'Üzgün', 'Öfkeli', 'Korku'];
export const emotionColors = ['#5BAE7B', '#2F80ED', '#E76F3C', '#9B5DE5'];

export const sampleImages = [
  '/samples/happy_1.jpg',
  '/samples/happy_2.jpg',
  '/samples/happy_3.jpg',
  '/samples/sad_1.jpg',
  '/samples/sad_2.jpg',
  '/samples/sad_3.jpg',
  '/samples/angry_1.jpg',
  '/samples/angry_2.jpg',
  '/samples/angry_3.jpg',
  '/samples/fear_1.jpg',
  '/samples/fear_2.jpg',
  '/samples/fear_3.jpg',
];

export const heroFeatures: { title: LS; icon: LucideIcon }[] = [
  { title: { en: 'Concept Bottleneck (CBM)', tr: 'Kavram Darboğazı (CBM)' }, icon: BrainCircuit },
  { title: { en: 'Grad-CAM explanation', tr: 'Grad-CAM Açıklama' }, icon: Activity },
  { title: { en: 'Calibrated confidence', tr: 'Kalibre Güven Skoru' }, icon: ShieldCheck },
  { title: { en: 'LLM clinical narrative', tr: 'LLM Klinik Açıklama' }, icon: Sparkles },
];

export const homeStats: { value: LS; label: LS; icon: LucideIcon }[] = [
  { value: { en: '5,177', tr: '5.177' }, label: { en: 'KIDO drawings (hand-labeled)', tr: 'KIDO Çizimi (elle etiket)' }, icon: FileChartColumn },
  { value: { en: '0.834', tr: '0,834' }, label: { en: 'Macro F1 (clean test, n=775)', tr: 'Makro F1 (temiz test, n=775)' }, icon: Target },
  { value: { en: '82.1%', tr: '%82,1' }, label: { en: 'Test accuracy', tr: 'Test Doğruluğu' }, icon: BadgeCheck },
  { value: { en: '4', tr: '4' }, label: { en: 'Emotion classes', tr: 'Duygu Sınıfı' }, icon: Layers3 },
  { value: { en: 'r=0.79', tr: 'r=0,79' }, label: { en: 'Concept fidelity', tr: 'Gösterge Sadakati' }, icon: FlaskConical },
  { value: { en: '0.019', tr: '0,019' }, label: { en: 'ECE (calibration ↓)', tr: 'ECE (kalibrasyon ↓)' }, icon: Gauge },
];

export const howItWorks: { title: LS; body: LS; icon: LucideIcon }[] = [
  {
    title: { en: 'Upload the drawing', tr: 'Çizimi Yükle' },
    body: { en: "Upload an image of the child's hand drawing to the system.", tr: 'Çocuğun el çizimi görüntüsünü sisteme yükleyin.' },
    icon: UploadCloud,
  },
  {
    title: { en: 'Concept Bottleneck analysis', tr: 'Kavram Darboğazı Analizi' },
    body: {
      en: 'A ResNet-50 backbone predicts 16 figure-aware clinical indicators from the image; the emotion is derived only from those indicators.',
      tr: 'ResNet-50 omurgası görüntüden 16 figür-farkında klinik gösterge tahmin eder; duygu yalnızca bu göstergelerden belirlenir.',
    },
    icon: BrainCircuit,
  },
  {
    title: { en: 'Explainable report', tr: 'Açıklanabilir Rapor' },
    body: {
      en: 'A Grad-CAM heatmap and an LLM-assisted clinical narrative grounded in the most salient clinical indicators are produced.',
      tr: 'Grad-CAM ısı haritası ve öne çıkan klinik göstergelere dayalı LLM destekli klinik açıklama üretilir.',
    },
    icon: FileChartColumn,
  },
];

export const technologyHighlights: { title: LS; body: LS; icon: LucideIcon }[] = [
  {
    title: { en: 'Concept Bottleneck', tr: 'Kavram Darboğazı (Concept Bottleneck)' },
    body: {
      en: 'The model reaches the emotion not directly from pixels but through 16 figure-aware clinical indicators (Koppitz 1968, Di Leo 1973) it predicts from the image — interpretable by design.',
      tr: 'Model duyguya doğrudan pikselden değil, görüntüden tahmin ettiği 16 figür-farkında klinik göstergeden (Koppitz 1968, Di Leo 1973) ulaşır — yorumlanabilir-tasarımca.',
    },
    icon: Layers3,
  },
  {
    title: { en: 'Five-backbone comparison', tr: 'Beş Omurga Karşılaştırması' },
    body: {
      en: 'EfficientNet-B0/B3, ResNet-50, MobileNetV3 and ViT-B/16 were compared systematically; ResNet-50 was selected as the best backbone.',
      tr: 'EfficientNet-B0/B3, ResNet-50, MobileNetV3 ve ViT-B/16 sistematik olarak karşılaştırıldı; en iyi omurga olarak ResNet-50 seçildi.',
    },
    icon: BrainCircuit,
  },
  {
    title: { en: 'Calibrated by design', tr: 'Yapısı Gereği Kalibre' },
    body: {
      en: 'The Concept Bottleneck model is well calibrated by design (ECE=0.019); confidence scores are consistent with real accuracy.',
      tr: 'Kavram Darboğazı modeli yapısı gereği iyi kalibre olmuştur (ECE=0,019); güven skorları gerçek doğrulukla tutarlıdır.',
    },
    icon: FlaskConical,
  },
  {
    title: { en: 'Concept fidelity', tr: 'Gösterge Sadakati (Concept Fidelity)' },
    body: {
      en: 'The indicators the model predicts correlate with the real values measured by OpenCV at an average of r=0.79 (16/16 indicators r>0.5).',
      tr: 'Modelin tahmin ettiği göstergeler, OpenCV ile ölçülen gerçek değerlerle ortalama r=0,79 korelasyon gösterir (16/16 gösterge r>0,5).',
    },
    icon: Target,
  },
  {
    title: { en: 'Grad-CAM visualization', tr: 'Grad-CAM Görselleştirme' },
    body: {
      en: 'A class-specific heatmap is produced from the gradients of the last convolutional layer.',
      tr: 'Son evrişim katmanı gradyanlarından sınıfa özgü ısı haritası üretilir.',
    },
    icon: Activity,
  },
  {
    title: { en: 'LLM clinical narrative', tr: 'LLM Klinik Açıklama' },
    body: {
      en: 'An explanation that links the salient clinical indicators to the literature, with a rule-based fallback mechanism.',
      tr: 'Öne çıkan klinik göstergeleri literatürle ilişkilendiren açıklama; kural tabanlı yedek mekanizma ile.',
    },
    icon: Sparkles,
  },
];

export const pipeline: { title: LS; body: LS; icon: LucideIcon }[] = [
  { title: { en: 'Drawing input', tr: 'Çizim Girdisi' }, body: { en: '224×224 normalized', tr: '224×224 normalize' }, icon: Microscope },
  { title: { en: 'Clinical indicators', tr: 'Klinik Göstergeler' }, body: { en: '16 figure-aware indicators', tr: '16 figür-farkında gösterge' }, icon: Gauge },
  { title: { en: 'Concept Bottleneck', tr: 'Kavram Darboğazı' }, body: { en: 'ResNet-50 → indicators → emotion', tr: 'ResNet-50 → göstergeler → duygu' }, icon: BrainCircuit },
  { title: { en: 'Report', tr: 'Rapor' }, body: { en: 'Emotion + Grad-CAM', tr: 'Duygu + Grad-CAM' }, icon: FileText },
];

export const analysisProcess: { title: LS; body: LS; icon: LucideIcon }[] = [
  { title: { en: 'Upload', tr: 'Yükleme' }, body: { en: 'The drawing image is received.', tr: 'Çizim görüntüsü alınır.' }, icon: UploadCloud },
  { title: { en: 'Pre-processing', tr: 'Ön İşleme' }, body: { en: '224×224, ImageNet norm.', tr: '224×224, ImageNet norm.' }, icon: ServerCog },
  { title: { en: 'Concept Bottleneck', tr: 'Kavram Darboğazı' }, body: { en: 'ResNet-50 → 16 clinical indicators → emotion.', tr: 'ResNet-50 → 16 klinik gösterge → duygu.' }, icon: BrainCircuit },
  { title: { en: 'Report', tr: 'Rapor' }, body: { en: 'Grad-CAM + LLM explanation.', tr: 'Grad-CAM + LLM açıklaması.' }, icon: FileChartColumn },
];

export const aboutStats: { value: LS; label: LS; icon: LucideIcon }[] = [
  { value: { en: '5,177', tr: '5.177' }, label: { en: 'Original drawings (KIDO)', tr: 'Orijinal Çizim (KIDO)' }, icon: Users },
  { value: { en: '0.834', tr: '0,834' }, label: { en: 'Macro F1 (n=775)', tr: 'Makro F1 (n=775)' }, icon: CheckCircle2 },
  { value: { en: '4', tr: '4' }, label: { en: 'Emotion classes', tr: 'Duygu Sınıfı' }, icon: Layers3 },
  { value: { en: '8', tr: '8' }, label: { en: 'Experiment configs', tr: 'Deney Konfigürasyonu' }, icon: FileChartColumn },
];

export const performance: { value: LS; label: LS; icon: LucideIcon }[] = [
  { value: { en: '0.834', tr: '0,834' }, label: { en: 'Macro F1', tr: 'Makro F1' }, icon: Activity },
  { value: { en: '82.1%', tr: '%82,1' }, label: { en: 'Test accuracy', tr: 'Test Doğruluğu' }, icon: Target },
  { value: { en: 'r=0.79', tr: 'r=0,79' }, label: { en: 'Concept fidelity', tr: 'Gösterge Sadakati' }, icon: Zap },
  { value: { en: '0.019', tr: '0,019' }, label: { en: 'ECE (calibration)', tr: 'ECE (kalibrasyon)' }, icon: CheckCircle2 },
];

export const methodology: { title: LS; body: LS }[] = [
  {
    title: { en: 'Data preparation', tr: 'Veri Hazırlama' },
    body: {
      en: 'KIDO was hand-labeled; a clean test set (n=775, original images only) was built by removing data leakage; minority and the Sad class were balanced via offline augmentation.',
      tr: 'KIDO elle etiketlendi; veri sızıntısı giderilerek temiz test seti (n=775, yalnızca orijinal görüntüler) oluşturuldu; azınlık ve Üzgün sınıfı çevrimdışı artırma ile dengelendi.',
    },
  },
  {
    title: { en: 'Backbone selection', tr: 'Omurga Seçimi' },
    body: {
      en: 'Five backbones (EfficientNet-B0/B3, ResNet-50, MobileNetV3, ViT-B/16) were compared under the same protocol; ResNet-50, giving the best performance–cost trade-off, was chosen as the final backbone.',
      tr: 'Beş omurga (EfficientNet-B0/B3, ResNet-50, MobileNetV3, ViT-B/16) aynı protokolle karşılaştırıldı; performans–maliyet dengesinde en iyi sonucu veren ResNet-50 nihai omurga olarak seçildi.',
    },
  },
  {
    title: { en: 'Concept Bottleneck architecture', tr: 'Kavram Darboğazı Mimarisi' },
    body: {
      en: 'The ResNet-50 backbone predicts 16 figure-aware clinical indicators (Koppitz/Di Leo) from the image; the emotion is determined only from those indicators.',
      tr: 'ResNet-50 omurgası görüntüden 16 figür-farkında klinik gösterge (Koppitz/Di Leo) tahmin eder; duygu yalnızca bu göstergelerden belirlenir.',
    },
  },
  {
    title: { en: 'Calibration', tr: 'Kalibrasyon' },
    body: {
      en: 'The Concept Bottleneck model is well calibrated by design (ECE=0.019); confidence scores are consistent with real accuracy.',
      tr: 'Kavram Darboğazı modeli yapısı gereği iyi kalibre olmuştur (ECE=0,019); güven skorları gerçek doğrulukla tutarlıdır.',
    },
  },
  {
    title: { en: 'Explainability', tr: 'Açıklanabilirlik' },
    body: {
      en: 'A Grad-CAM heatmap and an LLM-assisted clinical narrative based on the salient clinical indicators were produced (concept fidelity r=0.79).',
      tr: 'Grad-CAM ısı haritası ve öne çıkan klinik göstergelere dayalı LLM destekli klinik açıklama üretildi (gösterge sadakati r=0,79).',
    },
  },
];

export const techStack: { name: string; desc: LS; color: string }[] = [
  { name: 'Python', desc: { en: '3.11+', tr: '3.11+' }, color: 'text-[#3776AB]' },
  { name: 'PyTorch', desc: { en: 'Deep learning', tr: 'Derin Öğrenme' }, color: 'text-[#E76F3C]' },
  { name: 'ResNet-50', desc: { en: 'Visual backbone', tr: 'Görsel Omurga' }, color: 'text-[#5BAE7B]' },
  { name: 'OpenCV', desc: { en: 'Clinical features', tr: 'Klinik Özellikler' }, color: 'text-[#0FA37F]' },
  { name: 'FastAPI', desc: { en: 'API service', tr: 'API Servisi' }, color: 'text-[#0FA37F]' },
  { name: 'React + Vite', desc: { en: 'Interface', tr: 'Arayüz' }, color: 'text-[#2F80ED]' },
];

export const limitations: LS[] = [
  {
    en: "Labeling was performed by a single researcher; Cohen's κ was not measured.",
    tr: "Etiketleme tek bir araştırmacı tarafından yapıldı; Cohen's κ ölçülmedi.",
  },
  {
    en: "The Sad class F1 (~0.66) remained low due to visual similarity with the Happy class.",
    tr: "Üzgün sınıfı F1'i (~0,66) Mutlu sınıfıyla görsel benzerlik nedeniyle düşük kaldı.",
  },
  {
    en: 'Macro F1 differences did not reach statistical significance in the McNemar test; the contribution should be framed as a measured improvement in clinically critical classes and as interpretability.',
    tr: 'Makro F1 farkları McNemar testinde istatistiksel anlamlılığa ulaşmadı; katkı, klinik açıdan kritik sınıflarda ölçülü iyileşme ve yorumlanabilirlik olarak çerçevelenmelidir.',
  },
  {
    en: 'The system has not yet been evaluated with psychologists in a real clinical setting.',
    tr: 'Sistem gerçek klinik ortamda henüz psikologlarla değerlendirilmedi.',
  },
  {
    en: 'LLM explanation requires external API access; a privacy assessment may be needed for clinical use.',
    tr: 'LLM açıklaması harici API erişimi gerektiriyor; klinik kullanımda gizlilik değerlendirmesi gerekebilir.',
  },
];

export const futureWork: LS[] = [
  {
    en: "Improving reliability with multi-rater labeling and Cohen's κ measurement",
    tr: "Çok araştırmacılı etiketleme ve Cohen's κ ölçümü ile güvenilirlik artırımı",
  },
  {
    en: 'Targeted augmentation and decision-boundary refinement for the Sad class',
    tr: 'Üzgün sınıfı için hedefli artırma ve karar sınırı iyileştirme',
  },
  {
    en: 'Deep-learning-based clinical feature extraction (segmentation models)',
    tr: 'Derin öğrenme tabanlı klinik özellik çıkarımı (segmentasyon modelleri)',
  },
  {
    en: "Multi-task learning architectures that account for the child's developmental context",
    tr: 'Gelişimsel bağlamı hesaba katan çok görevli öğrenme mimarisi',
  },
  {
    en: 'A psychologist user study for clinical utility and safety evaluation',
    tr: 'Psikolog kullanıcı çalışması ile klinik etkinlik ve güvenlik değerlendirmesi',
  },
  {
    en: 'Privacy-focused small language models (SLM) for offline explanation generation',
    tr: 'Gizlilik odaklı küçük dil modelleri (SLM) ile çevrimdışı açıklama üretimi',
  },
];

export const API_URL = '/api/predict';

// Backward-compat alias (AnalysisPage still imports cancerClasses)
export const cancerClasses = emotionClasses;
