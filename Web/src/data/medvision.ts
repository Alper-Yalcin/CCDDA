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
  Network,
  ServerCog,
  ShieldCheck,
  Sparkles,
  Target,
  UploadCloud,
  Users,
  Zap,
  type LucideIcon,
} from 'lucide-react';

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

export const heroFeatures: { title: string; icon: LucideIcon }[] = [
  { title: 'Kavram Darboğazı (CBM)', icon: BrainCircuit },
  { title: 'Grad-CAM Açıklama', icon: Activity },
  { title: 'Kalibre Güven Skoru', icon: ShieldCheck },
  { title: 'LLM Klinik Açıklama', icon: Sparkles },
];

export const homeStats: { value: string; label: string; icon: LucideIcon }[] = [
  { value: '5.177', label: 'KIDO Çizimi (elle etiket)', icon: FileChartColumn },
  { value: '0,834', label: 'Makro F1 (temiz test, n=775)', icon: Target },
  { value: '%82,1', label: 'Test Doğruluğu', icon: BadgeCheck },
  { value: '4', label: 'Duygu Sınıfı', icon: Layers3 },
  { value: 'r=0,79', label: 'Gösterge Sadakati', icon: FlaskConical },
  { value: '0,019', label: 'ECE (kalibrasyon ↓)', icon: Gauge },
];

export const howItWorks = [
  {
    title: 'Çizimi Yükle',
    body: 'Çocuğun el çizimi görüntüsünü sisteme yükleyin.',
    icon: UploadCloud,
  },
  {
    title: 'Kavram Darboğazı Analizi',
    body: 'ResNet-50 omurgası görüntüden 16 figür-farkında klinik gösterge tahmin eder; duygu yalnızca bu göstergelerden belirlenir.',
    icon: BrainCircuit,
  },
  {
    title: 'Açıklanabilir Rapor',
    body: 'Grad-CAM ısı haritası ve öne çıkan klinik göstergelere dayalı LLM destekli klinik açıklama üretilir.',
    icon: FileChartColumn,
  },
];

export const technologyHighlights = [
  {
    title: 'Kavram Darboğazı (Concept Bottleneck)',
    body: 'Model duyguya doğrudan pikselden değil, görüntüden tahmin ettiği 16 figür-farkında klinik göstergeden (Koppitz 1968, Di Leo 1973) ulaşır — yorumlanabilir-tasarımca.',
    icon: Layers3,
  },
  {
    title: 'Beş Omurga Karşılaştırması',
    body: 'EfficientNet-B0/B3, ResNet-50, MobileNetV3 ve ViT-B/16 sistematik olarak karşılaştırıldı; en iyi omurga olarak ResNet-50 seçildi.',
    icon: BrainCircuit,
  },
  {
    title: 'Yapısı Gereği Kalibre',
    body: 'Kavram Darboğazı modeli yapısı gereği iyi kalibre olmuştur (ECE=0,019); güven skorları gerçek doğrulukla tutarlıdır.',
    icon: FlaskConical,
  },
  {
    title: 'Gösterge Sadakati (Concept Fidelity)',
    body: 'Modelin tahmin ettiği göstergeler, OpenCV ile ölçülen gerçek değerlerle ortalama r=0,79 korelasyon gösterir (16/16 gösterge r>0,5).',
    icon: Target,
  },
  {
    title: 'Grad-CAM Görselleştirme',
    body: 'Son evrişim katmanı gradyanlarından sınıfa özgü ısı haritası üretilir.',
    icon: Activity,
  },
  {
    title: 'LLM Klinik Açıklama',
    body: 'Öne çıkan klinik göstergeleri literatürle ilişkilendiren açıklama; kural tabanlı yedek mekanizma ile.',
    icon: Sparkles,
  },
];

export const pipeline = [
  { title: 'Çizim Girdisi', body: '224×224 normalize', icon: Microscope },
  { title: 'Klinik Göstergeler', body: '16 figür-farkında gösterge', icon: Gauge },
  { title: 'Kavram Darboğazı', body: 'ResNet-50 → göstergeler → duygu', icon: BrainCircuit },
  { title: 'Rapor', body: 'Duygu + Grad-CAM', icon: FileText },
];

export const analysisProcess = [
  { title: 'Yükleme', body: 'Çizim görüntüsü alınır.', icon: UploadCloud },
  { title: 'Ön İşleme', body: '224×224, ImageNet norm.', icon: ServerCog },
  { title: 'Kavram Darboğazı', body: 'ResNet-50 → 16 klinik gösterge → duygu.', icon: BrainCircuit },
  { title: 'Rapor', body: 'Grad-CAM + LLM açıklaması.', icon: FileChartColumn },
];

export const resultMetrics = [
  ['Makro F1 (temiz test)', '0,834'],
  ['Test Doğruluğu', '%82,1'],
  ['Gösterge Sadakati', 'r=0,79'],
  ['ECE (kalibrasyon)', '0,019'],
  ['Model', 'Kavram Darboğazı (CBM)'],
];

export const aboutStats = [
  { value: '5.177', label: 'Orijinal Çizim (KIDO)', icon: Users },
  { value: '0,834', label: 'Makro F1 (n=775)', icon: CheckCircle2 },
  { value: '4', label: 'Duygu Sınıfı', icon: Layers3 },
  { value: '8', label: 'Deney Konfigürasyonu', icon: FileChartColumn },
];

export const performance = [
  { value: '0,834', label: 'Makro F1', icon: Activity },
  { value: '%82,1', label: 'Test Doğruluğu', icon: Target },
  { value: 'r=0,79', label: 'Gösterge Sadakati', icon: Zap },
  { value: '0,019', label: 'ECE (kalibrasyon)', icon: CheckCircle2 },
];

export const methodology: [string, string][] = [
  ['Veri Hazırlama', 'KIDO elle etiketlendi; veri sızıntısı giderilerek temiz test seti (n=775, yalnızca orijinal görüntüler) oluşturuldu; azınlık ve Üzgün sınıfı çevrimdışı artırma ile dengelendi.'],
  ['Omurga Seçimi', 'Beş omurga (EfficientNet-B0/B3, ResNet-50, MobileNetV3, ViT-B/16) aynı protokolle karşılaştırıldı; performans–maliyet dengesinde en iyi sonucu veren ResNet-50 nihai omurga olarak seçildi.'],
  ['Kavram Darboğazı Mimarisi', 'ResNet-50 omurgası görüntüden 16 figür-farkında klinik gösterge (Koppitz/Di Leo) tahmin eder; duygu yalnızca bu göstergelerden belirlenir.'],
  ['Kalibrasyon', 'Kavram Darboğazı modeli yapısı gereği iyi kalibre olmuştur (ECE=0,019); güven skorları gerçek doğrulukla tutarlıdır.'],
  ['Açıklanabilirlik', 'Grad-CAM ısı haritası ve öne çıkan klinik göstergelere dayalı LLM destekli klinik açıklama üretildi (gösterge sadakati r=0,79).'],
];

export const techStack: [string, string, string][] = [
  ['Python', '3.11+', 'text-[#3776AB]'],
  ['PyTorch', 'Derin Öğrenme', 'text-[#E76F3C]'],
  ['ResNet-50', 'Görsel Omurga', 'text-[#5BAE7B]'],
  ['OpenCV', 'Klinik Özellikler', 'text-[#0FA37F]'],
  ['FastAPI', 'API Servisi', 'text-[#0FA37F]'],
  ['React + Vite', 'Arayüz', 'text-[#2F80ED]'],
];

export const limitations = [
  'Etiketleme tek bir araştırmacı tarafından yapıldı; Cohen\'s κ ölçülmedi.',
  'Üzgün sınıfı F1\'i (~0,66) Mutlu sınıfıyla görsel benzerlik nedeniyle düşük kaldı.',
  'Makro F1 farkları McNemar testinde istatistiksel anlamlılığa ulaşmadı; katkı, klinik açıdan kritik sınıflarda ölçülü iyileşme ve yorumlanabilirlik olarak çerçevelenmelidir.',
  'Sistem gerçek klinik ortamda henüz psikologlarla değerlendirilmedi.',
  'LLM açıklaması harici API erişimi gerektiriyor; klinik kullanımda gizlilik değerlendirmesi gerekebilir.',
];

export const futureWork = [
  'Çok araştırmacılı etiketleme ve Cohen\'s κ ölçümü ile güvenilirlik artırımı',
  'Üzgün sınıfı için hedefli artırma ve karar sınırı iyileştirme',
  'Derin öğrenme tabanlı klinik özellik çıkarımı (segmentasyon modelleri)',
  'Gelişimsel bağlamı hesaba katan çok görevli öğrenme mimarisi',
  'Psikolog kullanıcı çalışması ile klinik etkinlik ve güvenlik değerlendirmesi',
  'Gizlilik odaklı küçük dil modelleri (SLM) ile çevrimdışı açıklama üretimi',
];

export const bottomFeatures = [
  {
    title: 'Açıklanabilir Çıktı',
    body: 'Grad-CAM ısı haritası ve LLM klinik raporu ile her karar şeffaf ve yorumlanabilir.',
    icon: ShieldCheck,
  },
  {
    title: 'Kalibre Güven Skoru',
    body: 'Sıcaklık Ölçekleme ile güven skorları gerçek doğrulukla hizalandı; belirsiz durumlar işaretlenir.',
    icon: Zap,
  },
  {
    title: 'Uzman Destek Aracı',
    body: 'Bu sistem klinik tanı aracı değildir; uzman değerlendirmesini desteklemek için tasarlanmıştır.',
    icon: Target,
  },
];

export const API_URL = '/api/predict';

// Backward-compat alias (AnalysisPage still imports cancerClasses)
export const cancerClasses = emotionClasses;
