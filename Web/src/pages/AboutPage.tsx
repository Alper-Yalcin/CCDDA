import { useState, type ComponentType, type ReactNode } from 'react';
import {
  Activity,
  ArrowRight,
  BarChart3,
  BrainCircuit,
  CheckCircle2,
  ChevronDown,
  Database,
  FlaskConical,
  Gauge,
  GraduationCap,
  Layers3,
  MessageSquareText,
  ScanSearch,
  ShieldAlert,
  Smile,
  Sparkles,
  SlidersHorizontal,
  TriangleAlert,
} from 'lucide-react';
import { AnimatePresence, motion } from 'motion/react';
import { PipelineDiagram, ResearchHeroVisual } from '../components/MedicalVisuals';
import { Button, IconBubble, PageMotion, SectionTitle } from '../components/UI';
import {
  aboutStats,
  futureWork,
  limitations,
  methodology,
  performance,
  sampleImages,
  techStack,
} from '../data/medvision';
import type { Page } from '../types';

// Temiz test seti (n=775) — sekiz omurga konfigürasyonu + nihai Kavram Darboğazı modeli.
const EXPERIMENTS = [
  {
    id: 'CB',
    label: 'Kavram Darboğazı',
    sub: 'ResNet-50 + 16 gösterge',
    f1: 0.8341,
    acc: 0.8206,
    valF1: 0.8241,
    trainTimeS: 1670.3,
    params: '~25M',
    best: true,
    note: 'Dağıtılan nihai modeldir. Duygu kararı, görüntüden tahmin edilen 16 figür-farkında klinik göstergeden üretilir.',
    classF1: { Happy: 0.862, Sad: 0.6631, Angry: 0.932, Fear: 0.8794 },
    precision: { Happy: 0.8224, Sad: 0.8039, Angry: 0.8889, Fear: 0.7949 },
    recall: { Happy: 0.9056, Sad: 0.5642, Angry: 0.9796, Fear: 0.9841 },
  },
  {
    id: 'B6',
    label: 'ResNet-50',
    sub: 'Görsel',
    f1: 0.8257,
    acc: 0.8258,
    valF1: 0.8276,
    trainTimeS: 1499.9,
    params: '~25M',
    best: false,
    note: 'Omurga karşılaştırmasında en güçlü görüntü-yalnızca referanstır; klinik özellik eklenmeden yüksek genel başarı verir.',
    classF1: { Happy: 0.8693, Sad: 0.6893, Angry: 0.8393, Fear: 0.9051 },
    precision: { Happy: 0.8436, Sad: 0.8, Angry: 0.746, Fear: 0.8378 },
    recall: { Happy: 0.8966, Sad: 0.6055, Angry: 0.9592, Fear: 0.9841 },
  },
  {
    id: 'B3',
    label: 'ResNet-50',
    sub: '+Klinik',
    f1: 0.8206,
    acc: 0.8181,
    valF1: 0.8364,
    trainTimeS: 1203.1,
    params: '~25M',
    best: false,
    note: 'Standart klinik füzyon referansıdır. Kritik sınıflarda katkı sağlar ancak genel Makro F1 görüntü-yalnızca modele göre sınırlı kalır.',
    classF1: { Happy: 0.8602, Sad: 0.6755, Angry: 0.8364, Fear: 0.9104 },
    precision: { Happy: 0.8247, Sad: 0.8038, Angry: 0.7541, Fear: 0.8592 },
    recall: { Happy: 0.8989, Sad: 0.5826, Angry: 0.9388, Fear: 0.9683 },
  },
  {
    id: 'A3',
    label: 'EffNet-B3',
    sub: 'Görsel',
    f1: 0.7981,
    acc: 0.7948,
    valF1: 0.8201,
    trainTimeS: 1737.8,
    params: '~12M',
    best: false,
    note: 'EfficientNet ailesinin güçlü görsel-only varyantıdır; ResNet-50 kadar dengeli sınıf başarımı sağlayamamıştır.',
    classF1: { Happy: 0.8415, Sad: 0.6442, Angry: 0.8333, Fear: 0.8732 },
    precision: { Happy: 0.8191, Sad: 0.7425, Angry: 0.7627, Fear: 0.7848 },
    recall: { Happy: 0.8652, Sad: 0.5688, Angry: 0.9184, Fear: 0.9841 },
  },
  {
    id: 'B5',
    label: 'ViT-B/16',
    sub: '+Klinik',
    f1: 0.7891,
    acc: 0.7948,
    valF1: 0.7787,
    trainTimeS: 4234.1,
    params: '~86M',
    best: false,
    note: 'En büyük modeldir; veri boyutu sınırlı olduğu için pre-training avantajını çizim alanına yeterince aktaramamıştır.',
    classF1: { Happy: 0.8453, Sad: 0.6457, Angry: 0.7895, Fear: 0.8759 },
    precision: { Happy: 0.8203, Sad: 0.7546, Angry: 0.6923, Fear: 0.8108 },
    recall: { Happy: 0.8719, Sad: 0.5642, Angry: 0.9184, Fear: 0.9524 },
  },
  {
    id: 'B4',
    label: 'MobileNetV3',
    sub: '+Klinik',
    f1: 0.7866,
    acc: 0.7845,
    valF1: 0.7686,
    trainTimeS: 956.1,
    params: '~5.5M',
    best: false,
    note: 'En hızlı ve hafif seçeneklerden biridir; düşük kaynak ortamları için anlamlıdır ancak nihai başarı daha düşüktür.',
    classF1: { Happy: 0.8354, Sad: 0.6348, Angry: 0.8319, Fear: 0.8444 },
    precision: { Happy: 0.8217, Sad: 0.7039, Angry: 0.7344, Fear: 0.7917 },
    recall: { Happy: 0.8494, Sad: 0.578, Angry: 0.9592, Fear: 0.9048 },
  },
  {
    id: 'A1',
    label: 'EffNet-B0',
    sub: 'Görsel',
    f1: 0.7831,
    acc: 0.791,
    valF1: 0.7932,
    trainTimeS: 1241.6,
    params: '~5.3M',
    best: false,
    note: 'Hafif EfficientNet referansıdır; Happy ve Fear sınıflarında makul, Sad ve Angry ayrımında daha sınırlı performans verir.',
    classF1: { Happy: 0.843, Sad: 0.6423, Angry: 0.7692, Fear: 0.8777 },
    precision: { Happy: 0.824, Sad: 0.7455, Angry: 0.6618, Fear: 0.8026 },
    recall: { Happy: 0.8629, Sad: 0.5642, Angry: 0.9184, Fear: 0.9683 },
  },
  {
    id: 'A4',
    label: 'EffNet-B3',
    sub: '+Klinik',
    f1: 0.7776,
    acc: 0.7755,
    valF1: 0.7953,
    trainTimeS: 1428.9,
    params: '~12M',
    best: false,
    note: 'Klinik füzyon eklenmesine rağmen EfficientNet-B3 görsel-only varyantının gerisinde kalmıştır.',
    classF1: { Happy: 0.8249, Sad: 0.6263, Angry: 0.8039, Fear: 0.8551 },
    precision: { Happy: 0.8038, Sad: 0.6966, Angry: 0.7736, Fear: 0.7867 },
    recall: { Happy: 0.8472, Sad: 0.5688, Angry: 0.8367, Fear: 0.9365 },
  },
  {
    id: 'A2',
    label: 'EffNet-B0',
    sub: '+Klinik',
    f1: 0.7724,
    acc: 0.7639,
    valF1: 0.7891,
    trainTimeS: 979.7,
    params: '~5.3M',
    best: false,
    note: 'EfficientNet-B0 üzerinde standart klinik füzyon genel başarıyı artırmamış, yalnızca sınıf bazında sınırlı değişimler üretmiştir.',
    classF1: { Happy: 0.8135, Sad: 0.6131, Angry: 0.7759, Fear: 0.8872 },
    precision: { Happy: 0.8135, Sad: 0.6528, Angry: 0.6716, Fear: 0.8429 },
    recall: { Happy: 0.8135, Sad: 0.578, Angry: 0.9184, Fear: 0.9365 },
  },
];

const EXPERIMENT_ANALYSIS: Record<string, Array<[string, string]>> = {
  CB: [
    ['Kalite değerlendirmesi', 'En dengeli sonuç bu modelde: Makro F1 en yüksek, Angry ve Fear sınıflarında güçlü, karar yolu ise 16 klinik gösterge üzerinden okunabilir durumda.'],
    ['Neden bu sonuç çıktı?', 'ResNet-50 omurgası çizimden güçlü görsel temsiller çıkarırken, kavram darboğazı kararı doğrudan figür boyutu, çizgi baskısı, gölgeleme ve kompozisyon gibi klinik göstergelere bağlıyor. Bu yapı özellikle öfke gibi belirgin çizgisel ipuçları taşıyan sınıflarda avantaj sağlıyor.'],
    ['Sınırlılık / çıkarım', 'Sad sınıfında recall düşük kaldığı için model üzüntü örüntülerini daha temkinli yakalıyor. Buna rağmen nihai model olarak seçilmesinin nedeni yalnızca küçük F1 artışı değil, klinik açıklanabilirlik ve kritik sınıflarda daha tutarlı karar üretmesi.'],
  ],
  B6: [
    ['Kalite değerlendirmesi', 'En güçlü görüntü-yalnızca referans. Genel doğrulukta çok iyi, Happy ve Fear sınıflarında dengeli; ancak kararın klinik ara göstergeye bağlanmaması yorumlanabilirliği sınırlar.'],
    ['Neden bu sonuç çıktı?', 'ResNet-50 çizgi yoğunluğu, renk dağılımı, boş alan ve form baskınlığı gibi düşük ve orta seviye görsel ipuçlarını doğrudan öğrenebiliyor. Bu nedenle klinik özellik eklenmeden de yüksek skor veriyor.'],
    ['Sınırlılık / çıkarım', 'Angry sınıfında recall yüksek olsa da precision daha zayıf; model bazı gergin çizim örüntülerini öfke lehine fazla işaretleyebiliyor. Klinik raporlama için güçlü ama açıklaması CB kadar doğrudan değil.'],
  ],
  B3: [
    ['Kalite değerlendirmesi', 'Standart klinik füzyon için güçlü bir referans. Makro F1, görüntü-yalnızca ResNet-50’ye yakın ama onu geçemiyor; klinik ek bilgi sınırlı ve seçici katkı veriyor.'],
    ['Neden bu sonuç çıktı?', 'Klinik vektör son aşamada CNN temsiline ekleniyor. Bu yöntem bazı sınıflarda kararı destekliyor fakat CNN’in zaten öğrendiği görsel sinyalleri tekrarladığı için genel kazanım sınırlı kalıyor.'],
    ['Sınırlılık / çıkarım', 'Naive füzyon klinik bilgiyi zorunlu karar yolu haline getirmediği için yorumlanabilirlik kısmi. Nihai model yerine karşılaştırma tabanı olarak daha anlamlı.'],
  ],
  A3: [
    ['Kalite değerlendirmesi', 'Orta-üst düzey bir görüntü modeli. Parametre verimliliği iyi fakat temiz testte ResNet-50 kadar dengeli sınıf başarımı sağlayamıyor.'],
    ['Neden bu sonuç çıktı?', 'EfficientNet-B3 verimli özellik çıkarıyor; ancak çocuk çizimi gibi çizgi, boşluk ve form varyansı yüksek bir alanda ResNet-50’nin daha geniş temsili daha stabil genelleme yapmış görünüyor.'],
    ['Sınırlılık / çıkarım', 'Sad ve Angry sınıflarında skorlar orta düzeyde kalıyor. Bu model iyi bir omurga adayı olsa da nihai klinik açıklama hedefi için tek başına yeterli değil.'],
  ],
  B5: [
    ['Kalite değerlendirmesi', 'En büyük model olmasına rağmen beklenen kalite artışını üretmiyor. Makro F1 ve validasyon F1, model kapasitesinin veri ölçeğine göre fazla olduğunu düşündürüyor.'],
    ['Neden bu sonuç çıktı?', 'ViT-B/16 daha fazla veri ve güçlü ön eğitim uyumu ister. KIDO çizimleri küçük ve klinik açıdan heterojen bir alan olduğu için transformer temsili çizim domainine ResNet kadar verimli aktarılamamış.'],
    ['Sınırlılık / çıkarım', 'Eğitim süresi yüksek, kazanım düşük. Bu sonuç daha büyük modelin her zaman daha iyi olmadığına ve veri-mimari uyumunun kritik olduğuna işaret ediyor.'],
  ],
  B4: [
    ['Kalite değerlendirmesi', 'Hafif ve hızlı bir seçenek; düşük kaynaklı kullanım için anlamlı. Buna karşılık Makro F1 nihai modelin belirgin biçimde altında.'],
    ['Neden bu sonuç çıktı?', 'MobileNetV3 verimlilik için temsil kapasitesinden ödün verir. Çocuk çizimlerinde sınıf ayrımı bazen ince çizgi baskısı, gölgeleme ve kompozisyon farklarına dayandığı için bu kapasite sınırı skora yansıyor.'],
    ['Sınırlılık / çıkarım', 'Hız avantajı var fakat klinik güven ve sınıf ayrımı için ana model olmaya uygun değil. Daha çok mobil/kenar cihaz senaryosu için alternatif olarak okunmalı.'],
  ],
  A1: [
    ['Kalite değerlendirmesi', 'Hafif baseline olarak makul performans veriyor. Happy ve Fear sınıfları daha iyi, Sad ve Angry ayrımı daha sınırlı.'],
    ['Neden bu sonuç çıktı?', 'EfficientNet-B0 temel görsel örüntüleri yakalıyor fakat kapasitesi daha düşük. Bu nedenle belirgin pozitif/negatif ayrımlar çalışırken, yakın duygusal örüntülerde hata artıyor.'],
    ['Sınırlılık / çıkarım', 'Az parametre ve makul süre avantajına rağmen klinik karar desteği için yeterli ayrıntı yakalayamıyor. Ablasyon ve hafif model karşılaştırması için değerli.'],
  ],
  A4: [
    ['Kalite değerlendirmesi', 'Klinik eklenmiş EfficientNet-B3 varyantı, görsel-only A3’ün gerisinde kalıyor. Bu, ek özelliklerin her mimaride otomatik kazanım sağlamadığını gösteriyor.'],
    ['Neden bu sonuç çıktı?', 'Klinik vektörün sonradan eklenmesi, EfficientNet temsilinin ölçeğiyle tam uyumlu çalışmamış olabilir. Ek sinyal bazı sınıflarda fayda yerine gürültü veya karar kararsızlığı üretmiş görünüyor.'],
    ['Sınırlılık / çıkarım', 'Naive füzyonun dikkatli tasarlanması gerektiğini gösteren önemli bir negatif örnek. Klinik bilgi daha iyi yapılandırılmadığında performans düşebilir.'],
  ],
  A2: [
    ['Kalite değerlendirmesi', 'Karşılaştırmadaki en zayıf genel sonuçlardan biri. Küçük omurga ve naive klinik füzyon birlikte yeterli ayrıştırma gücü üretemiyor.'],
    ['Neden bu sonuç çıktı?', 'EfficientNet-B0’un sınırlı temsil kapasitesine klinik vektör sonradan ekleniyor; bu ek bilgi karar yolunu gerçekten düzenlemediği için net kazanım oluşmuyor.'],
    ['Sınırlılık / çıkarım', 'Nihai adaydan çok kontrol deneyi olarak değerlendirilmeli. Sonuç, klinik göstergelerin yalnızca eklenmesinin değil, mimaride nasıl kullanıldığının belirleyici olduğunu destekliyor.'],
  ],
};

const EMOTION_LABELS = [
  { key: 'Happy', label: 'Mutlu' },
  { key: 'Sad', label: 'Üzgün' },
  { key: 'Angry', label: 'Kızgın' },
  { key: 'Fear', label: 'Korku' },
] as const;

function f3(value: number) {
  return value.toFixed(3);
}

function pct(value: number) {
  return `%${(value * 100).toFixed(1)}`;
}

function minutes(seconds: number) {
  return `${(seconds / 60).toFixed(1)} dk`;
}

function scoreWidth(value: number, min = 0.76, max = 0.84) {
  return `${Math.max(6, Math.min(100, ((value - min) / (max - min)) * 100))}%`;
}

// Nihai model karşılaştırması — temiz test seti (Çizelge 4.2)
const FINAL_MODELS = [
  { name: 'ResNet-50 görüntü-yalnızca',     f1: 0.826, best: false },
  { name: 'ResNet-50 + Klinik (naive füzyon)', f1: 0.821, best: false },
  { name: 'Kavram Darboğazı (16 gösterge) ★',  f1: 0.834, best: true  },
];

// Nihai Kavram Darboğazı modeli — dağıtılan V2_CB1 modelinin sınıf bazlı F1 değerleri.
const FINAL_CLASS_F1 = [
  { name: 'Mutlu / Happy',  f1: 0.862 },
  { name: 'Üzgün / Sad',    f1: 0.663 },
  { name: 'Kızgın / Angry', f1: 0.932 },
  { name: 'Korku / Fear',   f1: 0.879 },
];

const ABOUT_CARD = 'border-line bg-surface2 shadow-none';
const ABOUT_ICON_BUBBLE = 'border border-[#F2C8B2] bg-tint text-[#E76F3C]';
const ABOUT_PROGRESS_TRACK = '#DED5CB';
const ABOUT_PROGRESS_FILL = '#B8ADA0';
const ABOUT_PROGRESS_SELECTED_TRACK = '#F2D8CA';
const ABOUT_ORANGE = '#E76F3C';

const CLINICAL_INDICATOR_GROUPS = [
  {
    group: 'Figür Boyutu & Yerleşimi',
    basis: 'Koppitz / Di Leo',
    items: [
      ['Figür boyutu', 'Küçük figür çekilme ve güvensizlik; büyük figür dürtüsellik ya da saldırganlık ipucu olarak yorumlanır.'],
      ['Merkezden uzaklık', 'Figürün sayfa merkezinden uzaklaşması kenar/köşe yerleşimi, izolasyon ve geri çekilme sinyali verir.'],
      ['Dikey konum', 'Alt yerleşim güvensizlik ve çökkünlük; üst yerleşim kaçış ya da gerçeklikten uzaklaşma eğilimiyle ilişkilendirilir.'],
      ['Figür eğikliği', 'Eğik veya dengesiz figür çizimi instabilite, kararsızlık ve kaygı göstergesi olarak ele alınır.'],
    ],
  },
  {
    group: 'Çizgi Kalitesi & Baskı',
    basis: 'Basınç / kaygı göstergeleri',
    items: [
      ['Çizgi koyuluğu', 'Yüksek çizgi baskısı öfke, gerginlik ve yoğun duygusal yük ile ilişkilendirilir.'],
      ['Çizgi titrekliği', 'Pürüzlü ya da titrek çizgi kaygı, kararsızlık ve motor kontrol zorluğu sinyali olabilir.'],
      ['Baskı değişkenliği', 'Çizgi baskısının çizim içinde dalgalanması dürtüsellik ve duygusal regülasyon zorluğu ipucu verir.'],
      ['Keskin açı oranı', 'Sert köşeler ve açısal form yapısı saldırganlık, gerginlik veya öfke örüntüleriyle eşleştirilir.'],
    ],
  },
  {
    group: 'Gölgeleme & Bütünlük',
    basis: 'Koppitz duygusal göstergeleri',
    items: [
      ['Figür içi gölgeleme', 'Figür üzerinde yoğun koyulaştırma kaygı ve içsel gerilim göstergesi olarak değerlendirilir.'],
      ['Parça kopukluğu', 'Zayıf bütünleşmiş, kopuk parçalı çizim dürtüsellik, immatürite ve organizasyon zorluğuna işaret edebilir.'],
      ['Bileşen sayısı', 'Çizimdeki ayrı parça sayısı kompozisyonun dağınıklığını ve parçalı çizgi yapısını nicelleştirir.'],
    ],
  },
  {
    group: 'Kompozisyon',
    basis: 'Sayfa kullanımı',
    items: [
      ['Ön plan doluluğu', 'Çizimin sayfada kapladığı alan figürün genel baskınlığını ve sayfa kullanım yoğunluğunu ölçer.'],
      ['Boş alan oranı', 'Yüksek boşluk kullanımı izolasyon, geri çekilme ve üzüntü örüntüleriyle ilişkilendirilebilir.'],
      ['Koyu ton oranı', 'Koyu renk ve düşük parlaklık oranı korku/kaygı ya da olumsuz duygu örüntülerinde izlenir.'],
    ],
  },
  {
    group: 'Renk & Kompozit',
    basis: 'Destekleyici göstergeler',
    items: [
      ['Sıcak renk oranı', 'Sıcak ve canlı ton kullanımı pozitif duygu örüntülerini destekleyen zayıf ama yararlı bir sinyaldir.'],
      ['Biçim bütünlüğü', 'Figür alanı ve parça sayısından türetilen kompozit skor, çizimin form bütünlüğünü özetler.'],
    ],
  },
];

const GRADCAM_DETAILS = [
  ['Amaç', 'Grad-CAM, modelin sınıf kararını üretirken görüntüde hangi bölgelerin daha etkili olduğunu ısı haritası olarak görünür kılar.'],
  ['Tezdeki rol', 'Klinik göstergeler sayısal karar yolunu açıklarken, Grad-CAM görsel odak alanını gösterir. Böylece “hangi özellikler” ve “çizimin hangi bölgesi” birlikte yorumlanabilir.'],
  ['Klinik okuma', 'Isı haritası tek başına tanı kanıtı değildir; sınıf olasılığı, 16 klinik gösterge ve uzman yorumu ile birlikte değerlendirilmelidir.'],
  ['Sınırlılık', 'Grad-CAM nedensel açıklama vermez, modelin son evrişim katmanındaki dikkat yoğunluğunu yaklaşık gösterir. Bu nedenle açıklanabilirlik desteği olarak kullanılmalıdır.'],
];

// Hero altı yatay proje kimliği şeridi
const IDENTITY_STRIP: { icon: ComponentType<{ size?: number; className?: string; strokeWidth?: number }>; label: string; value: string }[] = [
  { icon: GraduationCap, label: 'Üniversite', value: 'NÖHÜ' },
  { icon: Layers3, label: 'Bölüm', value: 'Bilgisayar Mühendisliği' },
  { icon: Database, label: 'Proje Türü', value: 'Lisans Tezi' },
  { icon: ShieldAlert, label: 'Destek', value: 'TÜBİTAK 2209-A' },
  { icon: ScanSearch, label: 'Veri Seti', value: 'KIDO' },
  { icon: Sparkles, label: 'Amaç', value: 'Açıklanabilir Duygu Analizi' },
];

// Detaylı proje kimliği (alt bölüm)
const IDENTITY_DETAILS: [string, string][] = [
  ['Proje Adı', 'Çocuk Çizimlerinde Açıklanabilir Duygu Sınıflandırması için Klinik Özellik Füzyonlu Derin Öğrenme Sistemi Geliştirilmesi'],
  ['Yürütücü', 'Alper YALÇIN'],
  ['Danışman', 'Doç. Dr. Erkan ÇALIŞKAN'],
  ['Kurum', 'Niğde Ömer Halisdemir Üniversitesi, Bilgisayar Mühendisliği'],
  ['Kurumsal Durum', 'TÜBİTAK onaylı lisans araştırma projesi'],
  ['Veri Seti', 'KIDO (elle etiketlenmiş, 5.177 çizim · temiz test n=775)'],
  ['Nihai Model', 'Kavram Darboğazı — ResNet-50 + 16 figür-farkında klinik gösterge'],
];

const CONTRIBUTIONS: { icon: ComponentType<{ size?: number; className?: string; strokeWidth?: number }>; title: string; body: string }[] = [
  { icon: Layers3, title: 'Concept Bottleneck', body: 'Model kararlarını klinik anlamlı kavramlar üzerinden açıklanabilir kılar.' },
  { icon: Activity, title: 'Grad-CAM', body: 'Karar bölgelerini görselleştirerek çizimde hangi alanların etkili olduğunu gösterir.' },
  { icon: MessageSquareText, title: 'LLM Açıklama', body: 'Üretken dil modeli ile uzmanlara anlaşılır, metinsel açıklamalar sunar.' },
  { icon: Gauge, title: '16 Klinik Gösterge', body: 'Psikoloji/psikopatoloji literatürüne dayalı 16 gösterge üzerinden anlamlı çıkarımlar üretir.' },
];

const JOURNEY: { icon: ComponentType<{ size?: number; className?: string; strokeWidth?: number }>; title: string; body: string }[] = [
  { icon: Database, title: 'Veri Toplama', body: 'KIDO veri setinden çocuk çizimlerinin toplanması' },
  { icon: SlidersHorizontal, title: 'Ön İşleme', body: 'Boyutlandırma, normalizasyon ve veri artırma' },
  { icon: BrainCircuit, title: 'ResNet-50', body: 'Görüntü özelliklerinin derin öğrenme ile çıkarımı' },
  { icon: Gauge, title: 'Klinik Göstergeler', body: '16 klinik gösterge için olasılıkların tahmin edilmesi' },
  { icon: Layers3, title: 'Kavram Darboğazı', body: 'Concept Bottleneck ile açıklanabilir karar mekanizması' },
  { icon: MessageSquareText, title: 'Açıklanabilir Çıktı', body: 'Duygu tahmini + LLM ile metinsel açıklama' },
];

const PERF_HIGHLIGHTS: { icon: ComponentType<{ size?: number; className?: string; strokeWidth?: number }>; value: string; label: string; sub: string }[] = [
  { icon: Smile, value: '4', label: 'Duygu Sınıfı', sub: 'Mutlu · Üzgün · Kızgın · Korku' },
  { icon: Gauge, value: '16', label: 'Klinik Gösterge', sub: 'Psikoloji literatüründen türetilmiş göstergeler' },
  { icon: FlaskConical, value: '0,834', label: 'Makro F1 Skoru', sub: 'Concept Bottleneck ile en iyi genel performans' },
];

function Eyebrow({ children }: { children: ReactNode }) {
  return <div className="text-xs font-bold uppercase tracking-[0.26em] text-[#E76F3C]">{children}</div>;
}

function SectionHead({ title, desc, className = '' }: { title: string; desc?: string; className?: string }) {
  return (
    <div className={className}>
      <h2 className="font-serif text-3xl font-semibold tracking-[-0.02em] text-ink md:text-4xl">{title}</h2>
      <div className="mt-3 h-[3px] w-12 rounded-full bg-[#E76F3C]" />
      {desc && <p className="mt-5 max-w-2xl text-[15px] leading-7 text-muted">{desc}</p>}
    </div>
  );
}

function AboutPanel({ children, className = '' }: { children: ReactNode; className?: string }) {
  return (
    <section className={`rounded-2xl border ${ABOUT_CARD} ${className}`}>
      {children}
    </section>
  );
}

const fadeUp = {
  initial: { opacity: 0, y: 16 },
  whileInView: { opacity: 1, y: 0 },
  viewport: { once: true, margin: '-80px' },
  transition: { duration: 0.45 },
};

export function AboutPage({ setPage }: { setPage: (page: Page) => void }) {
  const [selectedExperimentId, setSelectedExperimentId] = useState(EXPERIMENTS[0].id);
  const [openGroup, setOpenGroup] = useState<string | null>(CLINICAL_INDICATOR_GROUPS[0].group);
  const selectedExperiment = EXPERIMENTS.find((exp) => exp.id === selectedExperimentId) ?? EXPERIMENTS[0];
  const selectedExperimentAnalysis = EXPERIMENT_ANALYSIS[selectedExperiment.id] ?? [];

  return (
    <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -12 }}>
      <PageMotion>
        {/* ── Hero ── */}
        <section className="grid items-center gap-10 lg:grid-cols-[0.92fr_1.08fr]">
          <motion.div initial={{ opacity: 0, x: -24 }} animate={{ opacity: 1, x: 0 }} transition={{ duration: 0.5, delay: 0.05 }}>
            <Eyebrow>LİSANS TEZİ · ARAŞTIRMA PROJESİ</Eyebrow>
            <h1 className="mt-5 font-serif text-5xl font-semibold leading-[1.02] tracking-[-0.035em] text-ink md:text-6xl lg:text-7xl">
              Proje <span className="text-[#E76F3C]">Hakkında</span>
            </h1>
            <p className="mt-6 max-w-xl text-lg leading-8 text-muted">
              Bu çalışma, çocuk çizimlerinden duygusal ifadeleri açıklanabilir şekilde analiz etmeyi amaçlayan, TÜBİTAK 2209-A kapsamında desteklenen bir lisans tezidir. Derin öğrenme, klinik gösterge çıkarımı, kavram darboğazı (Concept Bottleneck) ve üretken dil modeli açıklamalarını birleştirerek uzmanlara anlamlı ve şeffaf çıktılar sunar.
            </p>
            <p className="mt-4 max-w-xl text-[15px] leading-7 text-muted">
              Beş omurga karşılaştırılmış (en iyi: ResNet-50); klinik bilgiyi yapısal bir Kavram Darboğazına dönüştüren mimari nihai model olarak seçilmiştir.
            </p>
          </motion.div>
          <motion.div
            initial={{ opacity: 0, x: 32, scale: 0.97 }}
            animate={{ opacity: 1, x: 0, scale: 1 }}
            transition={{ duration: 0.65, delay: 0.08 }}
            className="relative min-w-0"
          >
            <ResearchHeroVisual />
          </motion.div>
        </section>

        {/* ── Proje kimliği şeridi ── */}
        <div className="mt-12 grid grid-cols-2 divide-x divide-y divide-line overflow-hidden rounded-2xl border border-line bg-surface sm:grid-cols-3 lg:grid-cols-6 lg:divide-y-0">
          {IDENTITY_STRIP.map((item, i) => {
            const Icon = item.icon;
            return (
              <motion.div
                key={item.label}
                initial={{ opacity: 0, y: 10 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.4, delay: i * 0.05 }}
                className="flex items-center gap-3 p-4"
              >
                <Icon size={20} className="shrink-0 text-[#E76F3C]" strokeWidth={1.7} />
                <div className="min-w-0">
                  <div className="text-[11px] font-semibold uppercase tracking-wide text-muted">{item.label}</div>
                  <div className="truncate text-sm font-semibold text-ink">{item.value}</div>
                </div>
              </motion.div>
            );
          })}
        </div>

        {/* ── Araştırma Özeti + Temel Katkılar ── */}
        <section className="mt-16 grid gap-12 lg:grid-cols-[0.92fr_1.08fr]">
          <motion.div {...fadeUp}>
            <SectionHead title="Araştırma Özeti" />
            <p className="mt-6 text-[15px] leading-7 text-muted">
              Çocuk çizimleri, duygusal ve psikolojik durumların anlaşılmasında değerli ipuçları içerir. Bu projede, ResNet-50 tabanlı derin öğrenme modeli ile çizimler analiz edilmekte; klinik literatüre dayalı 16 gösterge kavramı aracılığıyla duygular açıklanabilir hale getirilmektedir. Concept Bottleneck yaklaşımı ile modelin karar mekanizması şeffaflaşır ve üretken dil modeli (LLM) ile uzman dostu açıklamalar üretilir.
            </p>
            <div className="mt-8 rounded-2xl border border-line bg-surface2 p-5">
              <div className="text-xs font-bold uppercase tracking-[0.2em] text-[#E76F3C]">Proje Kimliği</div>
              <dl className="mt-4 space-y-2.5">
                {IDENTITY_DETAILS.map(([label, value]) => (
                  <div key={label} className="flex gap-3 text-sm">
                    <dt className="w-28 shrink-0 font-semibold text-ink">{label}</dt>
                    <dd className="text-muted">{value}</dd>
                  </div>
                ))}
              </dl>
            </div>
          </motion.div>

          <motion.div {...fadeUp}>
            <SectionHead title="Temel Katkılar" />
            <div className="mt-7 grid gap-x-8 gap-y-7 sm:grid-cols-2">
              {CONTRIBUTIONS.map((c) => {
                const Icon = c.icon;
                return (
                  <div key={c.title} className="border-t border-line pt-5">
                    <Icon size={24} className="text-[#E76F3C]" strokeWidth={1.6} />
                    <h3 className="mt-3 font-semibold text-ink">{c.title}</h3>
                    <p className="mt-1.5 text-sm leading-6 text-muted">{c.body}</p>
                  </div>
                );
              })}
            </div>
          </motion.div>
        </section>

        {/* ── Sistemin Yolculuğu ── */}
        <section className="mt-16">
          <SectionHead title="Sistemin Yolculuğu" desc="Çizim girdisinden açıklanabilir çıktıya: sistemin uçtan uca işleyiş adımları." />
          <div className="relative mt-10">
            <div className="absolute inset-x-0 top-7 hidden h-px bg-line lg:block" />
            <div className="grid gap-y-9 sm:grid-cols-2 lg:grid-cols-6 lg:gap-x-4">
              {JOURNEY.map((step, i) => {
                const Icon = step.icon;
                return (
                  <motion.div
                    key={step.title}
                    initial={{ opacity: 0, y: 14 }}
                    whileInView={{ opacity: 1, y: 0 }}
                    viewport={{ once: true }}
                    transition={{ duration: 0.4, delay: i * 0.07 }}
                    className="relative"
                  >
                    <div className="relative inline-block">
                      <div className="grid h-14 w-14 place-items-center rounded-full border border-[#F2C8B2] bg-tint text-[#E76F3C] shadow-none">
                        <Icon size={22} strokeWidth={1.6} />
                      </div>
                      <span className="absolute -right-1 -top-1 grid h-5 w-5 place-items-center rounded-full bg-[#E76F3C] text-[10px] font-bold text-white">
                        {i + 1}
                      </span>
                    </div>
                    <h3 className="mt-4 font-semibold text-ink">{step.title}</h3>
                    <p className="mt-1 text-sm leading-6 text-muted lg:pr-3">{step.body}</p>
                  </motion.div>
                );
              })}
            </div>
          </div>
        </section>

        {/* ── Model Performansı ── */}
        <section className="mt-16">
          <SectionHead
            title="Model Performansı"
            desc="Farklı yaklaşımların 4 duygu sınıfı üzerindeki makro F1 skorları aşağıda karşılaştırılmıştır. Concept Bottleneck yaklaşımı, en yüksek genel performansı ve yorumlanabilir karar yolunu sağlamıştır."
          />
          <div className="mt-8 grid items-stretch gap-10 lg:grid-cols-[1.1fr_0.9fr]">
            <div className="lg:flex lg:flex-col">
              <p className="mb-4 text-xs font-bold uppercase tracking-[0.18em] text-muted">Makro F1 Skoru ↑</p>
              <div className="space-y-4">
                {FINAL_MODELS.map((m) => (
                  <div key={m.name}>
                    <div className="mb-1.5 flex items-center justify-between text-sm">
                      <span className={m.best ? 'font-semibold text-ink' : 'text-muted'}>{m.name}</span>
                      <span className={`font-mono font-bold ${m.best ? 'text-[#E76F3C]' : 'text-muted'}`}>{f3(m.f1)}</span>
                    </div>
                    <div className="h-3 overflow-hidden rounded-full" style={{ backgroundColor: m.best ? ABOUT_PROGRESS_SELECTED_TRACK : ABOUT_PROGRESS_TRACK }}>
                      <motion.div
                        initial={{ width: 0 }}
                        whileInView={{ width: scoreWidth(m.f1, 0.78, 0.84) }}
                        viewport={{ once: true }}
                        transition={{ duration: 0.7, ease: 'easeOut' }}
                        className="h-full rounded-full"
                        style={{ background: m.best ? ABOUT_ORANGE : ABOUT_PROGRESS_FILL }}
                      />
                    </div>
                  </div>
                ))}
              </div>
              <div className="mt-6 grid grid-cols-2 gap-3 sm:grid-cols-4 lg:mt-auto">
                {performance.map((metric) => {
                  const Icon = metric.icon;
                  return (
                    <div key={metric.label} className="rounded-xl border border-line bg-surface p-3 text-center">
                      <Icon className="mx-auto text-[#E76F3C]" size={20} strokeWidth={1.6} />
                      <div className="mt-2 font-serif text-xl font-semibold text-ink">{metric.value}</div>
                      <div className="mt-0.5 text-[11px] font-medium text-muted">{metric.label}</div>
                    </div>
                  );
                })}
              </div>
            </div>

            <div className="grid gap-3 sm:grid-cols-3 lg:auto-rows-fr lg:grid-cols-1">
              {PERF_HIGHLIGHTS.map((h) => {
                const Icon = h.icon;
                return (
                  <div key={h.label} className="flex items-center gap-4 rounded-2xl border border-line bg-surface p-4">
                    <Icon size={24} className="shrink-0 text-[#E76F3C]" strokeWidth={1.5} />
                    <div className="min-w-0">
                      <div className="font-serif text-2xl font-semibold text-ink">{h.value}</div>
                      <div className="text-sm font-semibold text-ink">{h.label}</div>
                      <div className="mt-0.5 text-xs leading-5 text-muted">{h.sub}</div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          <div className="mt-8 grid grid-cols-2 divide-x divide-y divide-line overflow-hidden rounded-2xl border border-line bg-surface sm:grid-cols-4 sm:divide-y-0">
            {aboutStats.map((stat) => {
              const Icon = stat.icon;
              return (
                <div key={stat.label} className="flex items-center gap-3 p-5">
                  <Icon size={24} className="shrink-0 text-[#E76F3C]" strokeWidth={1.6} />
                  <div className="min-w-0">
                    <div className="font-serif text-2xl font-semibold text-ink">{stat.value}</div>
                    <div className="text-xs font-medium text-muted">{stat.label}</div>
                  </div>
                </div>
              );
            })}
          </div>
        </section>

        {/* ── Detaylı Araştırma Alanları ── */}
        <section className="mt-20 border-t border-line pt-12">
          <Eyebrow>Detaylı Araştırma Alanları</Eyebrow>
          <h2 className="mt-3 font-serif text-3xl font-semibold tracking-[-0.02em] text-ink md:text-4xl">
            Yöntem, Sonuçlar ve Klinik Temeller
          </h2>
        </section>

        {/* ── Model comparison ── */}
        <motion.section {...fadeUp} className="mt-12">
          {/* Editorial başlık */}
          <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
            <div>
              <Eyebrow>Model Karşılaştırma Laboratuvarı</Eyebrow>
              <h2 className="mt-3 font-serif text-3xl font-semibold tracking-[-0.02em] text-ink md:text-4xl">
                Temiz Test Setinde Model Performansı
              </h2>
              <div className="mt-3 h-[3px] w-12 rounded-full bg-[#E76F3C]" />
              <p className="mt-4 max-w-2xl text-[15px] leading-7 text-muted">
                Dokuz deney konfigürasyonu, veri sızıntısı giderilmiş temiz test seti üzerinde Makro F1, doğruluk, sınıf bazlı başarı ve açıklanabilirlik açısından karşılaştırılmıştır.
              </p>
            </div>
            <span className="inline-flex shrink-0 items-center gap-2 self-start rounded-full border border-line bg-surface px-4 py-2 text-xs font-semibold text-muted sm:self-auto">
              <span className="h-1.5 w-1.5 rounded-full bg-[#E76F3C]" />
              Sıralama: Makro F1 · n=775
            </span>
          </div>

          {/* Üst: Leaderboard | Seçili model özeti */}
          <div className="mt-8 grid items-stretch gap-6 xl:grid-cols-[minmax(0,1.1fr)_420px]">
            {/* Leaderboard */}
            <div className="space-y-2">
              {EXPERIMENTS.map((exp, i) => {
                const isSelected = selectedExperiment.id === exp.id;
                return (
                  <motion.button
                    key={exp.id}
                    type="button"
                    initial={{ opacity: 0, y: 6 }}
                    whileInView={{ opacity: 1, y: 0 }}
                    viewport={{ once: true }}
                    transition={{ duration: 0.35, delay: i * 0.04 }}
                    onClick={() => setSelectedExperimentId(exp.id)}
                    className={`flex w-full items-center gap-3 rounded-xl border px-4 py-3 text-left transition ${
                      isSelected
                        ? 'border-[#E76F3C] bg-surface2'
                        : 'border-line bg-surface hover:bg-surface2'
                    }`}
                  >
                    <span className={`w-6 shrink-0 text-center font-mono text-xs font-bold ${isSelected ? 'text-[#E76F3C]' : 'text-muted'}`}>
                      {String(i + 1).padStart(2, '0')}
                    </span>
                    <span
                      className={`w-9 shrink-0 rounded-md py-0.5 text-center font-mono text-[11px] font-bold ${
                        isSelected ? 'bg-[#E76F3C] text-white' : 'bg-surface2 text-muted'
                      }`}
                    >
                      {exp.id}
                    </span>
                    <div className="w-[7.5rem] shrink-0">
                      <p className="truncate text-sm font-semibold leading-none text-ink">{exp.label}</p>
                      <p className={`mt-1 truncate text-xs ${isSelected ? 'text-[#E76F3C]' : 'text-muted'}`}>{exp.sub}</p>
                    </div>
                    <div className="flex min-w-0 flex-1 items-center gap-3">
                      <div className="h-1.5 flex-1 overflow-hidden rounded-full" style={{ backgroundColor: isSelected ? ABOUT_PROGRESS_SELECTED_TRACK : ABOUT_PROGRESS_TRACK }}>
                        <motion.div
                          initial={{ width: 0 }}
                          whileInView={{ width: scoreWidth(exp.f1, 0.76, 0.834) }}
                          viewport={{ once: true }}
                          transition={{ duration: 0.7, ease: 'easeOut', delay: i * 0.04 }}
                          className="h-full rounded-full"
                          style={{ background: isSelected ? ABOUT_ORANGE : ABOUT_PROGRESS_FILL }}
                        />
                      </div>
                      <span className={`w-12 shrink-0 text-right font-mono text-sm font-bold ${isSelected ? 'text-[#E76F3C]' : 'text-muted'}`}>
                        {f3(exp.f1)}
                      </span>
                    </div>
                    {exp.best ? (
                      <span className="shrink-0 rounded-full bg-[#E76F3C] px-2 py-0.5 text-[10px] font-bold text-white">Nihai</span>
                    ) : (
                      <span className="w-[44px] shrink-0" />
                    )}
                  </motion.button>
                );
              })}
            </div>

            {/* Seçili model özeti */}
            <motion.div
              key={selectedExperiment.id}
              initial={{ opacity: 0, x: 12 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.35 }}
              className="rounded-2xl border border-line bg-surface2 p-6"
            >
              <div className="flex items-start justify-between gap-3">
                <div>
                  <span className="inline-block rounded-md bg-[#E76F3C] px-2 py-0.5 font-mono text-[11px] font-bold text-white">{selectedExperiment.id}</span>
                  <h3 className="mt-3 font-serif text-2xl font-semibold text-ink">{selectedExperiment.label}</h3>
                  <p className="mt-1 text-sm text-muted">{selectedExperiment.sub} · {selectedExperiment.params}</p>
                </div>
                {selectedExperiment.best && (
                  <span className="shrink-0 rounded-full bg-[#E76F3C] px-3 py-1 text-xs font-bold text-white">Nihai Model</span>
                )}
              </div>

              <div className="mt-6 flex items-end gap-3">
                <div className="font-serif text-6xl font-semibold leading-none text-[#E76F3C]">{f3(selectedExperiment.f1)}</div>
                <div className="pb-1.5 text-sm font-semibold text-muted">Makro F1</div>
              </div>

              <dl className="mt-6 border-t border-line2">
                {[
                  ['Doğruluk', pct(selectedExperiment.acc)],
                  ['Val F1', f3(selectedExperiment.valF1)],
                  ['Süre', minutes(selectedExperiment.trainTimeS)],
                  ['Parametre', selectedExperiment.params],
                ].map(([label, value]) => (
                  <div key={label} className="flex items-center justify-between border-b border-line2 py-2.5 text-sm">
                    <dt className="text-muted">{label}</dt>
                    <dd className="font-mono font-semibold text-ink">{value}</dd>
                  </div>
                ))}
              </dl>
            </motion.div>
          </div>

          {/* Alt: Sınıf bazlı başarım | Akademik değerlendirme */}
          <div className="mt-6 grid items-stretch gap-6 lg:grid-cols-2">
            <div className="rounded-2xl border border-line bg-surface2 p-6">
              <h3 className="font-serif text-xl font-semibold text-ink">Sınıf Bazlı Başarım</h3>
              <p className="mt-1 text-sm leading-6 text-muted">Seçili modelin dört duygu sınıfındaki F1, precision ve recall değerleri.</p>
              <div className="mt-5 space-y-4">
                {EMOTION_LABELS.map((emotion) => (
                  <div key={emotion.key}>
                    <div className="mb-1.5 flex items-center justify-between text-sm">
                      <span className="font-medium text-ink">{emotion.label}</span>
                      <span className="font-mono font-bold text-ink">{f3(selectedExperiment.classF1[emotion.key])}</span>
                    </div>
                    <div className="h-2.5 overflow-hidden rounded-full" style={{ backgroundColor: ABOUT_PROGRESS_TRACK }}>
                      <motion.div
                        key={`${selectedExperiment.id}-${emotion.key}`}
                        initial={{ width: 0 }}
                        animate={{ width: `${selectedExperiment.classF1[emotion.key] * 100}%` }}
                        transition={{ duration: 0.6, ease: 'easeOut' }}
                        className="h-full rounded-full"
                        style={{ backgroundColor: ABOUT_PROGRESS_FILL }}
                      />
                    </div>
                    <div className="mt-1 flex justify-between text-[11px] font-medium text-muted">
                      <span>Precision {f3(selectedExperiment.precision[emotion.key])}</span>
                      <span>Recall {f3(selectedExperiment.recall[emotion.key])}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <motion.div
              key={selectedExperiment.id}
              initial={{ opacity: 0, x: 12 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.35 }}
              className="rounded-2xl border border-line bg-surface2 p-6"
            >
              <h3 className="font-serif text-xl font-semibold text-ink">Akademik Değerlendirme</h3>
              <div className="mt-4 divide-y divide-line2">
                {selectedExperimentAnalysis.map(([title, body], i) => (
                  <div key={title} className="py-4 first:pt-0">
                    <div className="flex items-baseline gap-2">
                      <span className="font-mono text-xs font-bold text-[#E76F3C]">{String(i + 1).padStart(2, '0')}</span>
                      <span className="text-sm font-semibold text-ink">{title}</span>
                    </div>
                    <p className="mt-1.5 text-sm leading-6 text-muted">{body}</p>
                  </div>
                ))}
              </div>
              <p className="mt-2 rounded-xl bg-surface2 p-4 text-sm leading-6 text-muted">{selectedExperiment.note}</p>
            </motion.div>
          </div>
        </motion.section>

        {/* ── Methodology + Final model ── */}
        <section className="mt-6 grid items-stretch gap-6 lg:grid-cols-2">
          <AboutPanel className="h-full p-7">
            <div className="flex items-center gap-3">
              <IconBubble icon={Layers3} className={`h-10 w-10 ${ABOUT_ICON_BUBBLE}`} />
              <SectionTitle className="text-2xl">Metodoloji & Mimari</SectionTitle>
            </div>
            <p className="mt-5 text-sm leading-6 text-muted">
              Kavram Darboğazı (Concept Bottleneck) mimarisi: ResNet-50 omurgası görüntüden 16 figür-farkında klinik gösterge tahmin eder; 4-sınıf duygu kararı yalnızca bu göstergelerden verilir.
            </p>
            <div className="mt-6 space-y-4">
              {methodology.map(([title, body]) => (
                <div key={title} className="flex gap-4">
                  <div className="grid h-10 w-10 shrink-0 place-items-center rounded-xl border border-[#F2C8B2] bg-tint text-[#E76F3C]">
                    <CheckCircle2 size={18} />
                  </div>
                  <div>
                    <div className="font-semibold text-ink">{title}</div>
                    <div className="mt-1 text-sm leading-6 text-muted">{body}</div>
                  </div>
                </div>
              ))}
            </div>
            <div className="mt-6">
              <PipelineDiagram withImage />
            </div>
          </AboutPanel>

          <AboutPanel className="h-full p-7">
            <div className="flex items-center gap-3 mb-5">
              <IconBubble icon={Layers3} className={`h-10 w-10 ${ABOUT_ICON_BUBBLE}`} />
              <SectionTitle className="text-2xl">Nihai Model & Sınıf Başına F1</SectionTitle>
            </div>

            <p className="mb-3 text-sm font-semibold text-ink">Nihai Model — Temiz Test (n=775)</p>
            <div className="mb-6 space-y-2.5">
              {FINAL_MODELS.map((m) => (
                <div
                  key={m.name}
                  className={`flex items-center gap-3 rounded-xl px-4 py-2.5 ${
                    m.best ? 'border border-[#E76F3C] bg-surface2' : 'border border-line bg-surface'
                  }`}
                >
                  <span className={`flex-1 text-sm font-medium ${m.best ? 'text-ink' : 'text-[#555]'}`}>{m.name}</span>
                  <div className="h-2 w-24 overflow-hidden rounded-full" style={{ backgroundColor: m.best ? ABOUT_PROGRESS_SELECTED_TRACK : ABOUT_PROGRESS_TRACK }}>
                    <div className="h-full rounded-full" style={{ width: scoreWidth(m.f1, 0.78, 0.84), background: m.best ? ABOUT_ORANGE : ABOUT_PROGRESS_FILL }} />
                  </div>
                  <span className={`w-12 shrink-0 text-right font-mono text-sm font-bold ${m.best ? 'text-[#E76F3C]' : 'text-[#555]'}`}>{f3(m.f1)}</span>
                </div>
              ))}
            </div>

            <p className="mb-3 text-sm font-semibold text-ink">Sınıf Başına F1 — Nihai Kavram Darboğazı</p>
            <div className="space-y-5">
              {FINAL_CLASS_F1.map((c) => (
                <div key={c.name}>
                  <div className="flex justify-between text-sm mb-1.5">
                    <span className="font-medium text-ink">{c.name}</span>
                    <span className="font-mono font-bold text-ink">{f3(c.f1)}</span>
                  </div>
                  <div className="h-3 rounded-full overflow-hidden" style={{ backgroundColor: ABOUT_PROGRESS_TRACK }}>
                    <div className="h-full rounded-full" style={{ width: `${c.f1 * 100}%`, backgroundColor: ABOUT_PROGRESS_FILL }} />
                  </div>
                </div>
              ))}
            </div>
            <p className="mt-4 text-xs leading-5 text-muted">
              Tezdeki Çizelge 4.2, nihai modelin özellikle Kızgın sınıfında belirgin iyileşme sağladığını; katkının genel doğruluk artışından çok yorumlanabilirlik ve kritik sınıflardaki ölçülü kazanım olarak çerçevelenmesi gerektiğini belirtir.
            </p>
            <div className="mt-6 grid grid-cols-2 gap-3">
              {performance.map((metric) => {
                const Icon = metric.icon;
                return (
                  <div key={metric.label} className="rounded-xl border border-line bg-surface p-4 text-center">
                    <Icon className="mx-auto text-[#E76F3C]" size={22} strokeWidth={1.6} />
                    <div className="mt-3 font-serif text-2xl font-semibold text-ink">{metric.value}</div>
                    <div className="mt-1 text-xs font-medium text-muted">{metric.label}</div>
                  </div>
                );
              })}
            </div>
          </AboutPanel>
        </section>

        <section className="mt-6">
          <AboutPanel className="p-7">
            <div className="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
              <div className="flex items-center gap-3">
                <IconBubble icon={Database} className={`h-10 w-10 ${ABOUT_ICON_BUBBLE}`} />
                <SectionTitle className="text-2xl">16 Klinik Gösterge</SectionTitle>
              </div>
              <div className="max-w-2xl rounded-xl bg-surface2 px-4 py-3 text-sm leading-6 text-muted">
                Göstergeler OpenCV ile figür izole edildikten sonra hesaplanır ve Kavram Darboğazı modelinde kararın geçtiği yorumlanabilir ara katmanı oluşturur.
              </div>
            </div>

            <div className="mt-7 divide-y divide-line border-y border-line">
              {CLINICAL_INDICATOR_GROUPS.map((group) => {
                const isOpen = openGroup === group.group;
                return (
                  <div key={group.group}>
                    <button
                      type="button"
                      onClick={() => setOpenGroup(isOpen ? null : group.group)}
                      className="flex w-full items-center justify-between gap-3 py-4 text-left transition hover:text-[#E76F3C]"
                    >
                      <span className="flex flex-wrap items-center gap-3">
                        <span className="font-semibold text-ink">{group.group}</span>
                        <span className="rounded-full border border-line2 bg-surface2 px-2.5 py-1 text-[11px] font-semibold text-muted">
                          {group.basis}
                        </span>
                        <span className="text-xs font-medium text-muted">{group.items.length} gösterge</span>
                      </span>
                      <ChevronDown size={18} className={`shrink-0 text-[#E76F3C] transition-transform ${isOpen ? 'rotate-180' : ''}`} />
                    </button>
                    <AnimatePresence initial={false}>
                      {isOpen && (
                        <motion.div
                          initial={{ height: 0, opacity: 0 }}
                          animate={{ height: 'auto', opacity: 1 }}
                          exit={{ height: 0, opacity: 0 }}
                          transition={{ duration: 0.3, ease: 'easeInOut' }}
                          className="overflow-hidden"
                        >
                          <div className="grid gap-x-8 gap-y-4 pb-5 sm:grid-cols-2">
                            {group.items.map(([name, body]) => (
                              <div key={name}>
                                <div className="text-sm font-semibold text-ink">{name}</div>
                                <p className="mt-1 text-sm leading-6 text-muted">{body}</p>
                              </div>
                            ))}
                          </div>
                        </motion.div>
                      )}
                    </AnimatePresence>
                  </div>
                );
              })}
            </div>
          </AboutPanel>
        </section>

        <section className="mt-6">
          <AboutPanel className="p-7">
            <div className="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
              <div className="flex items-center gap-3">
                <IconBubble icon={Activity} className={`h-10 w-10 ${ABOUT_ICON_BUBBLE}`} />
                <SectionTitle className="text-2xl">Grad-CAM Açıklanabilirlik</SectionTitle>
              </div>
              <div className="max-w-2xl rounded-xl bg-surface2 px-4 py-3 text-sm leading-6 text-muted">
                Grad-CAM, modelin görsel kararını denetlenebilir hale getiren destekleyici açıklama katmanıdır; klinik göstergelerin yerine geçmez, onları tamamlar.
              </div>
            </div>

            <div className="mt-7 grid gap-6 lg:grid-cols-[0.9fr_1.1fr]">
              <div className="relative min-h-[320px] overflow-hidden rounded-xl border border-line bg-[#1F1F1F]">
                <img src={sampleImages[2]} alt="Grad-CAM odak örneği" className="h-full min-h-[320px] w-full object-cover opacity-90" />
                <div
                  className="absolute inset-0 mix-blend-screen"
                  style={{
                    background:
                      'radial-gradient(circle at 44% 36%, rgba(231, 111, 60, 0.64), transparent 30%), radial-gradient(circle at 60% 55%, rgba(242, 200, 178, 0.46), transparent 28%), radial-gradient(circle at 35% 68%, rgba(184, 173, 160, 0.36), transparent 24%)',
                  }}
                />
                <div className="absolute bottom-4 left-4 right-4 rounded-xl bg-surface/92 p-4 shadow-[0_18px_40px_-30px_rgba(31,31,31,0.7)] backdrop-blur">
                  <div className="text-sm font-semibold text-ink">Isı Haritası Mantığı</div>
                  <p className="mt-1 text-sm leading-6 text-muted">
                    Sıcak alanlar, modelin seçili sınıf kararında daha yoğun kullandığı çizim bölgelerini temsil eder.
                  </p>
                </div>
              </div>

              <div className="grid gap-3 sm:grid-cols-2">
                {GRADCAM_DETAILS.map(([title, body]) => (
                  <div key={title} className="rounded-xl border border-line bg-surface p-5">
                    <div className="text-sm font-semibold text-ink">{title}</div>
                    <p className="mt-2 text-sm leading-6 text-muted">{body}</p>
                  </div>
                ))}
              </div>
            </div>
          </AboutPanel>
        </section>

        {/* ── Dataset + Technologies ── */}
        <section className="mt-6 grid items-stretch gap-6 lg:grid-cols-2">
          <AboutPanel className="grid h-full gap-7 p-7 md:grid-cols-[1fr_200px]">
            <div>
              <div className="flex items-center gap-3">
                <IconBubble icon={Database} className={`h-10 w-10 ${ABOUT_ICON_BUBBLE}`} />
                <SectionTitle className="text-2xl">Veri Seti — KIDO</SectionTitle>
              </div>
              <p className="mt-5 leading-7 text-muted">
                KIDO (Kinetic Family Drawing) veri seti kullanılmıştır. Tüm etiketler tek bir araştırmacı tarafından elle atandı; pseudo-etiket veya model güdümlü etiket kullanılmadı.
              </p>
              <div className="mt-5 space-y-3">
                {[
                  ['Orijinal toplam', '5.177 çizim'],
                  ['Sınıflar', 'Mutlu: 2.963 · Üzgün: 1.456 · Kızgın: 359 · Korku: 399'],
                  ['Artırılmış eğitim seti', '6.619 örnek (azınlık + Üzgün sınıfı dengelendi)'],
                  ['Temiz test seti', '775 örnek — veri sızıntısı giderildi, yalnızca orijinal görüntüler'],
                  ['Eğitim artırımı', '±15° döndürme, parlaklık/kontrast değişimi, hafif bulanıklaştırma'],
                ].map(([label, value]) => (
                  <div key={label} className="flex gap-3 text-sm">
                    <CheckCircle2 className="mt-0.5 shrink-0 text-[#E76F3C]" size={16} />
                    <span><span className="font-semibold text-ink">{label}: </span><span className="text-muted">{value}</span></span>
                  </div>
                ))}
              </div>
            </div>
            <div>
              <img src={sampleImages[0]} alt="Örnek çizim" className="h-52 w-full rounded-2xl object-cover" />
              <div className="mt-4 rounded-xl bg-surface2 px-4 py-3 text-center text-sm text-muted">
                KIDO veri seti örneği
              </div>
            </div>
          </AboutPanel>

          <AboutPanel className="h-full p-7">
            <SectionTitle className="text-2xl">Kullanılan Teknolojiler</SectionTitle>
            <div className="mt-7 grid gap-3 sm:grid-cols-2">
              {techStack.map(([name, desc]) => (
                <div key={name} className="rounded-xl border border-line2 bg-surface2 p-4">
                  <div className="text-lg font-bold text-ink">{name}</div>
                  <div className="mt-1 text-xs font-medium text-muted">{desc}</div>
                </div>
              ))}
            </div>
          </AboutPanel>
        </section>

        {/* ── Limitations + Future ── */}
        <section className="mt-6 grid items-stretch gap-6 lg:grid-cols-2">
          <AboutPanel className="h-full p-7">
            <div className="flex items-center gap-3">
              <TriangleAlert className="text-[#E76F3C]" size={28} />
              <SectionTitle className="text-2xl">Sınırlılıklar</SectionTitle>
            </div>
            <ul className="mt-7 space-y-4">
              {limitations.map((item) => (
                <li key={item} className="flex gap-3 text-sm leading-6 text-muted">
                  <span className="mt-2 h-2 w-2 shrink-0 rounded-full bg-[#E76F3C]" />
                  {item}
                </li>
              ))}
            </ul>
          </AboutPanel>

          <AboutPanel className="h-full p-7">
            <div className="flex items-center gap-3">
              <IconBubble icon={BarChart3} className={`h-10 w-10 ${ABOUT_ICON_BUBBLE}`} />
              <SectionTitle className="text-2xl">Gelecek Çalışmalar</SectionTitle>
            </div>
            <ul className="mt-7 space-y-4">
              {futureWork.map((item) => (
                <li key={item} className="flex gap-3 text-sm leading-6 text-muted">
                  <CheckCircle2 className="mt-0.5 shrink-0 text-[#E76F3C]" size={18} />
                  {item}
                </li>
              ))}
            </ul>
          </AboutPanel>
        </section>

        {/* ── Etik Sınırlar ve Kullanım ── */}
        <section className="mt-16 flex flex-col gap-6 rounded-2xl border border-[#F2C8B2] bg-tint p-8 md:flex-row md:items-center md:justify-between">
          <div className="flex items-start gap-5">
            <div className="grid h-16 w-16 shrink-0 place-items-center rounded-full border border-[#F2C8B2] bg-surface text-[#E76F3C]">
              <ShieldAlert size={30} strokeWidth={1.6} />
            </div>
            <div>
              <h2 className="font-serif text-2xl font-semibold text-ink">Etik Sınırlar ve Kullanım</h2>
              <p className="mt-2 max-w-3xl text-sm leading-7 text-muted">
                Bu sistem klinik tanı aracı değildir; uzman değerlendirmesini desteklemek için tasarlanmış açıklanabilir bir karar destek prototipidir. Çıktılar yalnızca uzman değerlendirmesine destek amacı taşır; tüm sonuçlar olasılıksaldır ve nihai yorum ile karar yetkisi nitelikli bir psikolog veya klinisyene aittir.
              </p>
            </div>
          </div>
          <div className="shrink-0">
            <Button onClick={() => setPage('analysis')}>
              Analizi Başlat
              <ArrowRight size={17} />
            </Button>
            <p className="mt-2 text-center text-xs text-muted">Sistemi deneyin, çiziminizi yükleyip analizi inceleyin.</p>
          </div>
        </section>
      </PageMotion>
    </motion.div>
  );
}
