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
  type LS,
} from '../data/medvision';
import { useTranslation, type Lang } from '../i18n';
import type { Page } from '../types';

type IconType = ComponentType<{ size?: number; className?: string; strokeWidth?: number }>;

// Clean test set (n=775) — eight backbone configurations + the final Concept Bottleneck model.
const EXPERIMENTS: {
  id: string;
  label: LS;
  sub: LS;
  f1: number;
  acc: number;
  valF1: number;
  trainTimeS: number;
  params: string;
  best: boolean;
  note: LS;
  classF1: Record<string, number>;
  precision: Record<string, number>;
  recall: Record<string, number>;
}[] = [
  {
    id: 'CB',
    label: { en: 'Concept Bottleneck', tr: 'Kavram Darboğazı' },
    sub: { en: 'ResNet-50 + 16 indicators', tr: 'ResNet-50 + 16 gösterge' },
    f1: 0.8341,
    acc: 0.8206,
    valF1: 0.8241,
    trainTimeS: 1670.3,
    params: '~25M',
    best: true,
    note: {
      en: 'The deployed final model. The emotion decision is produced from 16 figure-aware clinical indicators predicted from the image.',
      tr: 'Dağıtılan nihai modeldir. Duygu kararı, görüntüden tahmin edilen 16 figür-farkında klinik göstergeden üretilir.',
    },
    classF1: { Happy: 0.862, Sad: 0.6631, Angry: 0.932, Fear: 0.8794 },
    precision: { Happy: 0.8224, Sad: 0.8039, Angry: 0.8889, Fear: 0.7949 },
    recall: { Happy: 0.9056, Sad: 0.5642, Angry: 0.9796, Fear: 0.9841 },
  },
  {
    id: 'B6',
    label: { en: 'ResNet-50', tr: 'ResNet-50' },
    sub: { en: 'Visual', tr: 'Görsel' },
    f1: 0.8257,
    acc: 0.8258,
    valF1: 0.8276,
    trainTimeS: 1499.9,
    params: '~25M',
    best: false,
    note: {
      en: 'The strongest image-only reference in the backbone comparison; it reaches high overall accuracy without any clinical features.',
      tr: 'Omurga karşılaştırmasında en güçlü görüntü-yalnızca referanstır; klinik özellik eklenmeden yüksek genel başarı verir.',
    },
    classF1: { Happy: 0.8693, Sad: 0.6893, Angry: 0.8393, Fear: 0.9051 },
    precision: { Happy: 0.8436, Sad: 0.8, Angry: 0.746, Fear: 0.8378 },
    recall: { Happy: 0.8966, Sad: 0.6055, Angry: 0.9592, Fear: 0.9841 },
  },
  {
    id: 'B3',
    label: { en: 'ResNet-50', tr: 'ResNet-50' },
    sub: { en: '+Clinical', tr: '+Klinik' },
    f1: 0.8206,
    acc: 0.8181,
    valF1: 0.8364,
    trainTimeS: 1203.1,
    params: '~25M',
    best: false,
    note: {
      en: 'The standard clinical-fusion reference. It helps on critical classes, but its overall Macro F1 remains limited compared with the image-only model.',
      tr: 'Standart klinik füzyon referansıdır. Kritik sınıflarda katkı sağlar ancak genel Makro F1 görüntü-yalnızca modele göre sınırlı kalır.',
    },
    classF1: { Happy: 0.8602, Sad: 0.6755, Angry: 0.8364, Fear: 0.9104 },
    precision: { Happy: 0.8247, Sad: 0.8038, Angry: 0.7541, Fear: 0.8592 },
    recall: { Happy: 0.8989, Sad: 0.5826, Angry: 0.9388, Fear: 0.9683 },
  },
  {
    id: 'A3',
    label: { en: 'EffNet-B3', tr: 'EffNet-B3' },
    sub: { en: 'Visual', tr: 'Görsel' },
    f1: 0.7981,
    acc: 0.7948,
    valF1: 0.8201,
    trainTimeS: 1737.8,
    params: '~12M',
    best: false,
    note: {
      en: 'A strong image-only variant of the EfficientNet family; it could not match the balanced per-class performance of ResNet-50.',
      tr: 'EfficientNet ailesinin güçlü görsel-only varyantıdır; ResNet-50 kadar dengeli sınıf başarımı sağlayamamıştır.',
    },
    classF1: { Happy: 0.8415, Sad: 0.6442, Angry: 0.8333, Fear: 0.8732 },
    precision: { Happy: 0.8191, Sad: 0.7425, Angry: 0.7627, Fear: 0.7848 },
    recall: { Happy: 0.8652, Sad: 0.5688, Angry: 0.9184, Fear: 0.9841 },
  },
  {
    id: 'B5',
    label: { en: 'ViT-B/16', tr: 'ViT-B/16' },
    sub: { en: '+Clinical', tr: '+Klinik' },
    f1: 0.7891,
    acc: 0.7948,
    valF1: 0.7787,
    trainTimeS: 4234.1,
    params: '~86M',
    best: false,
    note: {
      en: 'The largest model; because the dataset is limited, it could not transfer its pre-training advantage to the drawing domain well enough.',
      tr: 'En büyük modeldir; veri boyutu sınırlı olduğu için pre-training avantajını çizim alanına yeterince aktaramamıştır.',
    },
    classF1: { Happy: 0.8453, Sad: 0.6457, Angry: 0.7895, Fear: 0.8759 },
    precision: { Happy: 0.8203, Sad: 0.7546, Angry: 0.6923, Fear: 0.8108 },
    recall: { Happy: 0.8719, Sad: 0.5642, Angry: 0.9184, Fear: 0.9524 },
  },
  {
    id: 'B4',
    label: { en: 'MobileNetV3', tr: 'MobileNetV3' },
    sub: { en: '+Clinical', tr: '+Klinik' },
    f1: 0.7866,
    acc: 0.7845,
    valF1: 0.7686,
    trainTimeS: 956.1,
    params: '~5.5M',
    best: false,
    note: {
      en: 'One of the fastest, lightest options; meaningful for low-resource settings, but its final performance is lower.',
      tr: 'En hızlı ve hafif seçeneklerden biridir; düşük kaynaklı kullanım için anlamlıdır ancak nihai başarı daha düşüktür.',
    },
    classF1: { Happy: 0.8354, Sad: 0.6348, Angry: 0.8319, Fear: 0.8444 },
    precision: { Happy: 0.8217, Sad: 0.7039, Angry: 0.7344, Fear: 0.7917 },
    recall: { Happy: 0.8494, Sad: 0.578, Angry: 0.9592, Fear: 0.9048 },
  },
  {
    id: 'A1',
    label: { en: 'EffNet-B0', tr: 'EffNet-B0' },
    sub: { en: 'Visual', tr: 'Görsel' },
    f1: 0.7831,
    acc: 0.791,
    valF1: 0.7932,
    trainTimeS: 1241.6,
    params: '~5.3M',
    best: false,
    note: {
      en: 'A lightweight EfficientNet reference; reasonable on Happy and Fear, more limited at distinguishing Sad and Angry.',
      tr: 'Hafif EfficientNet referansıdır; Happy ve Fear sınıflarında makul, Sad ve Angry ayrımında daha sınırlı performans verir.',
    },
    classF1: { Happy: 0.843, Sad: 0.6423, Angry: 0.7692, Fear: 0.8777 },
    precision: { Happy: 0.824, Sad: 0.7455, Angry: 0.6618, Fear: 0.8026 },
    recall: { Happy: 0.8629, Sad: 0.5642, Angry: 0.9184, Fear: 0.9683 },
  },
  {
    id: 'A4',
    label: { en: 'EffNet-B3', tr: 'EffNet-B3' },
    sub: { en: '+Clinical', tr: '+Klinik' },
    f1: 0.7776,
    acc: 0.7755,
    valF1: 0.7953,
    trainTimeS: 1428.9,
    params: '~12M',
    best: false,
    note: {
      en: 'Despite adding clinical fusion, it stayed behind the image-only EfficientNet-B3 variant.',
      tr: 'Klinik füzyon eklenmesine rağmen EfficientNet-B3 görsel-only varyantının gerisinde kalmıştır.',
    },
    classF1: { Happy: 0.8249, Sad: 0.6263, Angry: 0.8039, Fear: 0.8551 },
    precision: { Happy: 0.8038, Sad: 0.6966, Angry: 0.7736, Fear: 0.7867 },
    recall: { Happy: 0.8472, Sad: 0.5688, Angry: 0.8367, Fear: 0.9365 },
  },
  {
    id: 'A2',
    label: { en: 'EffNet-B0', tr: 'EffNet-B0' },
    sub: { en: '+Clinical', tr: '+Klinik' },
    f1: 0.7724,
    acc: 0.7639,
    valF1: 0.7891,
    trainTimeS: 979.7,
    params: '~5.3M',
    best: false,
    note: {
      en: 'One of the weakest overall results in the comparison. A small backbone and naive clinical fusion together cannot produce enough discriminative power.',
      tr: 'Karşılaştırmadaki en zayıf genel sonuçlardan biri. Küçük omurga ve naive klinik füzyon birlikte yeterli ayrıştırma gücü üretemiyor.',
    },
    classF1: { Happy: 0.8135, Sad: 0.6131, Angry: 0.7759, Fear: 0.8872 },
    precision: { Happy: 0.8135, Sad: 0.6528, Angry: 0.6716, Fear: 0.8429 },
    recall: { Happy: 0.8135, Sad: 0.578, Angry: 0.9184, Fear: 0.9365 },
  },
];

const EXPERIMENT_ANALYSIS: Record<string, Array<[LS, LS]>> = {
  CB: [
    [
      { en: 'Quality assessment', tr: 'Kalite değerlendirmesi' },
      {
        en: 'The most balanced result is this model: highest Macro F1, strong on Angry and Fear, and the decision path is readable through 16 clinical indicators.',
        tr: 'En dengeli sonuç bu modelde: Makro F1 en yüksek, Angry ve Fear sınıflarında güçlü, karar yolu ise 16 klinik gösterge üzerinden okunabilir durumda.',
      },
    ],
    [
      { en: 'Why this result?', tr: 'Neden bu sonuç çıktı?' },
      {
        en: 'While the ResNet-50 backbone extracts strong visual representations from the drawing, the concept bottleneck ties the decision directly to clinical indicators such as figure size, line pressure, shading and composition. This structure is especially advantageous for classes that carry clear line-based cues, like anger.',
        tr: 'ResNet-50 omurgası çizimden güçlü görsel temsiller çıkarırken, kavram darboğazı kararı doğrudan figür boyutu, çizgi baskısı, gölgeleme ve kompozisyon gibi klinik göstergelere bağlıyor. Bu yapı özellikle öfke gibi belirgin çizgisel ipuçları taşıyan sınıflarda avantaj sağlıyor.',
      },
    ],
    [
      { en: 'Limitation / takeaway', tr: 'Sınırlılık / çıkarım' },
      {
        en: 'Because recall remains low on the Sad class, the model is more cautious about catching sadness patterns. Even so, it was chosen as the final model not just for the small F1 gain, but for its clinical explainability and more consistent decisions on critical classes.',
        tr: 'Sad sınıfında recall düşük kaldığı için model üzüntü örüntülerini daha temkinli yakalıyor. Buna rağmen nihai model olarak seçilmesinin nedeni yalnızca küçük F1 artışı değil, klinik açıklanabilirlik ve kritik sınıflarda daha tutarlı karar üretmesi.',
      },
    ],
  ],
  B6: [
    [
      { en: 'Quality assessment', tr: 'Kalite değerlendirmesi' },
      {
        en: 'The strongest image-only reference. Very good in overall accuracy, balanced on Happy and Fear; however, not tying the decision to a clinical intermediate indicator limits interpretability.',
        tr: 'En güçlü görüntü-yalnızca referans. Genel doğrulukta çok iyi, Happy ve Fear sınıflarında dengeli; ancak kararın klinik ara göstergeye bağlanmaması yorumlanabilirliği sınırlar.',
      },
    ],
    [
      { en: 'Why this result?', tr: 'Neden bu sonuç çıktı?' },
      {
        en: 'ResNet-50 can directly learn low- and mid-level visual cues such as line density, color distribution, empty space and form dominance. It therefore scores high even without clinical features.',
        tr: 'ResNet-50 çizgi yoğunluğu, renk dağılımı, boş alan ve form baskınlığı gibi düşük ve orta seviye görsel ipuçlarını doğrudan öğrenebiliyor. Bu nedenle klinik özellik eklenmeden de yüksek skor veriyor.',
      },
    ],
    [
      { en: 'Limitation / takeaway', tr: 'Sınırlılık / çıkarım' },
      {
        en: 'Although recall is high on Angry, precision is weaker; the model may over-flag some tense drawing patterns as anger. Strong for clinical reporting, but its explanation is less direct than the CB model.',
        tr: 'Angry sınıfında recall yüksek olsa da precision daha zayıf; model bazı gergin çizim örüntülerini öfke lehine fazla işaretleyebiliyor. Klinik raporlama için güçlü ama açıklaması CB kadar doğrudan değil.',
      },
    ],
  ],
  B3: [
    [
      { en: 'Quality assessment', tr: 'Kalite değerlendirmesi' },
      {
        en: 'A strong reference for standard clinical fusion. Macro F1 is close to image-only ResNet-50 but does not surpass it; the clinical information adds a limited, selective contribution.',
        tr: 'Standart klinik füzyon için güçlü bir referans. Makro F1, görüntü-yalnızca ResNet-50’ye yakın ama onu geçemiyor; klinik ek bilgi sınırlı ve seçici katkı veriyor.',
      },
    ],
    [
      { en: 'Why this result?', tr: 'Neden bu sonuç çıktı?' },
      {
        en: 'The clinical vector is appended to the CNN representation at the final stage. This supports the decision on some classes, but because it repeats visual signals the CNN already learned, the overall gain stays limited.',
        tr: 'Klinik vektör son aşamada CNN temsiline ekleniyor. Bu yöntem bazı sınıflarda kararı destekliyor fakat CNN’in zaten öğrendiği görsel sinyalleri tekrarladığı için genel kazanım sınırlı kalıyor.',
      },
    ],
    [
      { en: 'Limitation / takeaway', tr: 'Sınırlılık / çıkarım' },
      {
        en: 'Because naive fusion does not make the clinical information a mandatory decision path, interpretability is partial. More meaningful as a comparison baseline than as the final model.',
        tr: 'Naive füzyon klinik bilgiyi zorunlu karar yolu haline getirmediği için yorumlanabilirlik kısmi. Nihai model yerine karşılaştırma tabanı olarak daha anlamlı.',
      },
    ],
  ],
  A3: [
    [
      { en: 'Quality assessment', tr: 'Kalite değerlendirmesi' },
      {
        en: 'An upper-mid-level image model. Parameter efficiency is good, but on the clean test it cannot match the balanced per-class performance of ResNet-50.',
        tr: 'Orta-üst düzey bir görüntü modeli. Parametre verimliliği iyi fakat temiz testte ResNet-50 kadar dengeli sınıf başarımı sağlayamıyor.',
      },
    ],
    [
      { en: 'Why this result?', tr: 'Neden bu sonuç çıktı?' },
      {
        en: 'EfficientNet-B3 extracts features efficiently; however, in a domain like children’s drawings with high line, space and form variance, ResNet-50’s broader representation appears to generalize more stably.',
        tr: 'EfficientNet-B3 verimli özellik çıkarıyor; ancak çocuk çizimi gibi çizgi, boşluk ve form varyansı yüksek bir alanda ResNet-50’nin daha geniş temsili daha stabil genelleme yapmış görünüyor.',
      },
    ],
    [
      { en: 'Limitation / takeaway', tr: 'Sınırlılık / çıkarım' },
      {
        en: 'Scores stay mid-level on Sad and Angry. A good backbone candidate, but not sufficient on its own for the clinical-explanation goal.',
        tr: 'Sad ve Angry sınıflarında skorlar orta düzeyde kalıyor. Bu model iyi bir omurga adayı olsa da nihai klinik açıklama hedefi için tek başına yeterli değil.',
      },
    ],
  ],
  B5: [
    [
      { en: 'Quality assessment', tr: 'Kalite değerlendirmesi' },
      {
        en: 'Despite being the largest model, it does not produce the expected quality gain. Macro F1 and validation F1 suggest the model capacity is excessive relative to the data scale.',
        tr: 'En büyük model olmasına rağmen beklenen kalite artışını üretmiyor. Makro F1 ve validasyon F1, model kapasitesinin veri ölçeğine göre fazla olduğunu düşündürüyor.',
      },
    ],
    [
      { en: 'Why this result?', tr: 'Neden bu sonuç çıktı?' },
      {
        en: 'ViT-B/16 demands more data and good pre-training alignment. Because KIDO drawings are a small and clinically heterogeneous domain, the transformer representation could not transfer to the drawing domain as efficiently as ResNet.',
        tr: 'ViT-B/16 daha fazla veri ve güçlü ön eğitim uyumu ister. KIDO çizimleri küçük ve klinik açıdan heterojen bir alan olduğu için transformer temsili çizim domainine ResNet kadar verimli aktarılamamış.',
      },
    ],
    [
      { en: 'Limitation / takeaway', tr: 'Sınırlılık / çıkarım' },
      {
        en: 'High training time, low gain. This result points to the fact that a larger model is not always better and that data–architecture fit is critical.',
        tr: 'Eğitim süresi yüksek, kazanım düşük. Bu sonuç daha büyük modelin her zaman daha iyi olmadığına ve veri-mimari uyumunun kritik olduğuna işaret ediyor.',
      },
    ],
  ],
  B4: [
    [
      { en: 'Quality assessment', tr: 'Kalite değerlendirmesi' },
      {
        en: 'A light, fast option; meaningful for low-resource use. In return, Macro F1 is clearly below the final model.',
        tr: 'Hafif ve hızlı bir seçenek; düşük kaynaklı kullanım için anlamlı. Buna karşılık Makro F1 nihai modelin belirgin biçimde altında.',
      },
    ],
    [
      { en: 'Why this result?', tr: 'Neden bu sonuç çıktı?' },
      {
        en: 'MobileNetV3 trades representation capacity for efficiency. Because class separation in children’s drawings sometimes rests on subtle line pressure, shading and composition differences, this capacity limit shows up in the score.',
        tr: 'MobileNetV3 verimlilik için temsil kapasitesinden ödün verir. Çocuk çizimlerinde sınıf ayrımı bazen ince çizgi baskısı, gölgeleme ve kompozisyon farklarına dayandığı için bu kapasite sınırı skora yansıyor.',
      },
    ],
    [
      { en: 'Limitation / takeaway', tr: 'Sınırlılık / çıkarım' },
      {
        en: 'It has a speed advantage but is not suitable as the main model for clinical confidence and class separation. It should be read as an alternative for mobile/edge scenarios.',
        tr: 'Hız avantajı var fakat klinik güven ve sınıf ayrımı için ana model olmaya uygun değil. Daha çok mobil/kenar cihaz senaryosu için alternatif olarak okunmalı.',
      },
    ],
  ],
  A1: [
    [
      { en: 'Quality assessment', tr: 'Kalite değerlendirmesi' },
      {
        en: 'Reasonable performance as a lightweight baseline. Happy and Fear classes are better; Sad and Angry separation is more limited.',
        tr: 'Hafif baseline olarak makul performans veriyor. Happy ve Fear sınıfları daha iyi, Sad ve Angry ayrımı daha sınırlı.',
      },
    ],
    [
      { en: 'Why this result?', tr: 'Neden bu sonuç çıktı?' },
      {
        en: 'EfficientNet-B0 captures basic visual patterns but has lower capacity. So while clear positive/negative distinctions work, errors increase on close emotional patterns.',
        tr: 'EfficientNet-B0 temel görsel örüntüleri yakalıyor fakat kapasitesi daha düşük. Bu nedenle belirgin pozitif/negatif ayrımlar çalışırken, yakın duygusal örüntülerde hata artıyor.',
      },
    ],
    [
      { en: 'Limitation / takeaway', tr: 'Sınırlılık / çıkarım' },
      {
        en: 'Despite few parameters and reasonable time, it cannot capture enough detail for clinical decision support. Valuable for ablation and lightweight-model comparison.',
        tr: 'Az parametre ve makul süre avantajına rağmen klinik karar desteği için yeterli ayrıntı yakalayamıyor. Ablasyon ve hafif model karşılaştırması için değerli.',
      },
    ],
  ],
  A4: [
    [
      { en: 'Quality assessment', tr: 'Kalite değerlendirmesi' },
      {
        en: 'The clinical-augmented EfficientNet-B3 variant falls behind the image-only A3. This shows that extra features do not automatically bring gains in every architecture.',
        tr: 'Klinik eklenmiş EfficientNet-B3 varyantı, görsel-only A3’ün gerisinde kalıyor. Bu, ek özelliklerin her mimaride otomatik kazanım sağlamadığını gösteriyor.',
      },
    ],
    [
      { en: 'Why this result?', tr: 'Neden bu sonuç çıktı?' },
      {
        en: 'Appending the clinical vector afterwards may not align well with the scale of the EfficientNet representation. The extra signal appears to have produced noise or decision instability instead of benefit on some classes.',
        tr: 'Klinik vektörün sonradan eklenmesi, EfficientNet temsilinin ölçeğiyle tam uyumlu çalışmamış olabilir. Ek sinyal bazı sınıflarda fayda yerine gürültü veya karar kararsızlığı üretmiş görünüyor.',
      },
    ],
    [
      { en: 'Limitation / takeaway', tr: 'Sınırlılık / çıkarım' },
      {
        en: 'An important negative example showing that naive fusion must be designed carefully. When clinical information is not better structured, performance can drop.',
        tr: 'Naive füzyonun dikkatli tasarlanması gerektiğini gösteren önemli bir negatif örnek. Klinik bilgi daha iyi yapılandırılmadığında performans düşebilir.',
      },
    ],
  ],
  A2: [
    [
      { en: 'Quality assessment', tr: 'Kalite değerlendirmesi' },
      {
        en: 'One of the weakest overall results in the comparison. A small backbone and naive clinical fusion together cannot produce enough discrimination.',
        tr: 'Karşılaştırmadaki en zayıf genel sonuçlardan biri. Küçük omurga ve naive klinik füzyon birlikte yeterli ayrıştırma gücü üretemiyor.',
      },
    ],
    [
      { en: 'Why this result?', tr: 'Neden bu sonuç çıktı?' },
      {
        en: 'A clinical vector is appended afterwards to EfficientNet-B0’s limited representation capacity; because this extra information does not actually structure the decision path, no clear gain appears.',
        tr: 'EfficientNet-B0’un sınırlı temsil kapasitesine klinik vektör sonradan ekleniyor; bu ek bilgi karar yolunu gerçekten düzenlemediği için net kazanım oluşmuyor.',
      },
    ],
    [
      { en: 'Limitation / takeaway', tr: 'Sınırlılık / çıkarım' },
      {
        en: 'Should be treated as a control experiment rather than a final candidate. The result supports that what is decisive is not merely adding clinical indicators, but how they are used in the architecture.',
        tr: 'Nihai adaydan çok kontrol deneyi olarak değerlendirilmeli. Sonuç, klinik göstergelerin yalnızca eklenmesinin değil, mimaride nasıl kullanıldığının belirleyici olduğunu destekliyor.',
      },
    ],
  ],
};

const EMOTION_LABELS: { key: string; label: LS }[] = [
  { key: 'Happy', label: { en: 'Happy', tr: 'Mutlu' } },
  { key: 'Sad', label: { en: 'Sad', tr: 'Üzgün' } },
  { key: 'Angry', label: { en: 'Angry', tr: 'Kızgın' } },
  { key: 'Fear', label: { en: 'Fear', tr: 'Korku' } },
];

function f3(value: number) {
  return value.toFixed(3);
}

function pct(value: number) {
  return `${(value * 100).toFixed(1)}%`;
}

function minutes(seconds: number, lang: Lang) {
  return `${(seconds / 60).toFixed(1)} ${lang === 'tr' ? 'dk' : 'min'}`;
}

function scoreWidth(value: number, min = 0.76, max = 0.84) {
  return `${Math.max(6, Math.min(100, ((value - min) / (max - min)) * 100))}%`;
}

// Final model comparison — clean test set (Table 4.2)
const FINAL_MODELS: { name: LS; f1: number; best: boolean }[] = [
  { name: { en: 'ResNet-50 image-only', tr: 'ResNet-50 görüntü-yalnızca' }, f1: 0.826, best: false },
  { name: { en: 'ResNet-50 + Clinical (naive fusion)', tr: 'ResNet-50 + Klinik (naive füzyon)' }, f1: 0.821, best: false },
  { name: { en: 'Concept Bottleneck (16 indicators) ★', tr: 'Kavram Darboğazı (16 gösterge) ★' }, f1: 0.834, best: true },
];

// Final Concept Bottleneck model — per-class F1 of the deployed V2_CB1 model.
const FINAL_CLASS_F1: { name: LS; f1: number }[] = [
  { name: { en: 'Happy', tr: 'Mutlu / Happy' }, f1: 0.862 },
  { name: { en: 'Sad', tr: 'Üzgün / Sad' }, f1: 0.663 },
  { name: { en: 'Angry', tr: 'Kızgın / Angry' }, f1: 0.932 },
  { name: { en: 'Fear', tr: 'Korku / Fear' }, f1: 0.879 },
];

const ABOUT_CARD = 'border-line bg-surface2 shadow-none';
const ABOUT_ICON_BUBBLE = 'border border-[#F2C8B2] bg-tint text-[#E76F3C]';
const ABOUT_PROGRESS_TRACK = '#DED5CB';
const ABOUT_PROGRESS_FILL = '#B8ADA0';
const ABOUT_PROGRESS_SELECTED_TRACK = '#F2D8CA';
const ABOUT_ORANGE = '#E76F3C';

const CLINICAL_INDICATOR_GROUPS: { group: LS; basis: LS; items: [LS, LS][] }[] = [
  {
    group: { en: 'Figure size & placement', tr: 'Figür Boyutu & Yerleşimi' },
    basis: { en: 'Koppitz / Di Leo', tr: 'Koppitz / Di Leo' },
    items: [
      [
        { en: 'Figure size', tr: 'Figür boyutu' },
        { en: 'A small figure is read as withdrawal and insecurity; a large figure as a cue of impulsivity or aggression.', tr: 'Küçük figür çekilme ve güvensizlik; büyük figür dürtüsellik ya da saldırganlık ipucu olarak yorumlanır.' },
      ],
      [
        { en: 'Distance from center', tr: 'Merkezden uzaklık' },
        { en: 'The figure moving away from the page center (edge/corner placement) signals isolation and withdrawal.', tr: 'Figürün sayfa merkezinden uzaklaşması kenar/köşe yerleşimi, izolasyon ve geri çekilme sinyali verir.' },
      ],
      [
        { en: 'Vertical position', tr: 'Dikey konum' },
        { en: 'Lower placement is associated with insecurity and depression; upper placement with escape or detachment from reality.', tr: 'Alt yerleşim güvensizlik ve çökkünlük; üst yerleşim kaçış ya da gerçeklikten uzaklaşma eğilimiyle ilişkilendirilir.' },
      ],
      [
        { en: 'Figure tilt', tr: 'Figür eğikliği' },
        { en: 'A tilted or unstable figure is treated as an indicator of instability, indecision and anxiety.', tr: 'Eğik veya dengesiz figür çizimi instabilite, kararsızlık ve kaygı göstergesi olarak ele alınır.' },
      ],
    ],
  },
  {
    group: { en: 'Line quality & pressure', tr: 'Çizgi Kalitesi & Baskı' },
    basis: { en: 'Pressure / anxiety indicators', tr: 'Basınç / kaygı göstergeleri' },
    items: [
      [
        { en: 'Line darkness', tr: 'Çizgi koyuluğu' },
        { en: 'High line pressure is associated with anger, tension and intense emotional load.', tr: 'Yüksek çizgi baskısı öfke, gerginlik ve yoğun duygusal yük ile ilişkilendirilir.' },
      ],
      [
        { en: 'Line tremor', tr: 'Çizgi titrekliği' },
        { en: 'A rough or shaky line can signal anxiety, indecision and motor-control difficulty.', tr: 'Pürüzlü ya da titrek çizgi kaygı, kararsızlık ve motor kontrol zorluğu sinyali olabilir.' },
      ],
      [
        { en: 'Pressure variability', tr: 'Baskı değişkenliği' },
        { en: 'Fluctuating line pressure within the drawing cues impulsivity and difficulty with emotion regulation.', tr: 'Çizgi baskısının çizim içinde dalgalanması dürtüsellik ve duygusal regülasyon zorluğu ipucu verir.' },
      ],
      [
        { en: 'Sharp-angle ratio', tr: 'Keskin açı oranı' },
        { en: 'Hard corners and angular form structure are matched with aggression, tension or anger patterns.', tr: 'Sert köşeler ve açısal form yapısı saldırganlık, gerginlik veya öfke örüntüleriyle eşleştirilir.' },
      ],
    ],
  },
  {
    group: { en: 'Shading & integrity', tr: 'Gölgeleme & Bütünlük' },
    basis: { en: 'Koppitz emotional indicators', tr: 'Koppitz duygusal göstergeleri' },
    items: [
      [
        { en: 'Shading on figure', tr: 'Figür içi gölgeleme' },
        { en: 'Heavy darkening over the figure is evaluated as an indicator of anxiety and inner tension.', tr: 'Figür üzerinde yoğun koyulaştırma kaygı ve içsel gerilim göstergesi olarak değerlendirilir.' },
      ],
      [
        { en: 'Part fragmentation', tr: 'Parça kopukluğu' },
        { en: 'Poorly integrated, fragmented drawing can indicate impulsivity, immaturity and organization difficulty.', tr: 'Zayıf bütünleşmiş, kopuk parçalı çizim dürtüsellik, immatürite ve organizasyon zorluğuna işaret edebilir.' },
      ],
      [
        { en: 'Component count', tr: 'Bileşen sayısı' },
        { en: 'The number of separate parts in the drawing quantifies compositional scatter and fragmented line structure.', tr: 'Çizimdeki ayrı parça sayısı kompozisyonun dağınıklığını ve parçalı çizgi yapısını nicelleştirir.' },
      ],
    ],
  },
  {
    group: { en: 'Composition', tr: 'Kompozisyon' },
    basis: { en: 'Page usage', tr: 'Sayfa kullanımı' },
    items: [
      [
        { en: 'Foreground fill', tr: 'Ön plan doluluğu' },
        { en: 'The area the drawing occupies on the page measures the figure’s overall dominance and page-usage density.', tr: 'Çizimin sayfada kapladığı alan figürün genel baskınlığını ve sayfa kullanım yoğunluğunu ölçer.' },
      ],
      [
        { en: 'Empty-space ratio', tr: 'Boş alan oranı' },
        { en: 'High use of empty space can be associated with isolation, withdrawal and sadness patterns.', tr: 'Yüksek boşluk kullanımı izolasyon, geri çekilme ve üzüntü örüntüleriyle ilişkilendirilebilir.' },
      ],
      [
        { en: 'Dark-tone ratio', tr: 'Koyu ton oranı' },
        { en: 'A high ratio of dark color and low brightness is observed in fear/anxiety or negative-emotion patterns.', tr: 'Koyu renk ve düşük parlaklık oranı korku/kaygı ya da olumsuz duygu örüntülerinde izlenir.' },
      ],
    ],
  },
  {
    group: { en: 'Color & composite', tr: 'Renk & Kompozit' },
    basis: { en: 'Supporting indicators', tr: 'Destekleyici göstergeler' },
    items: [
      [
        { en: 'Warm-color ratio', tr: 'Sıcak renk oranı' },
        { en: 'Use of warm, vivid tones is a weak but useful signal supporting positive-emotion patterns.', tr: 'Sıcak ve canlı ton kullanımı pozitif duygu örüntülerini destekleyen zayıf ama yararlı bir sinyaldir.' },
      ],
      [
        { en: 'Form integrity', tr: 'Biçim bütünlüğü' },
        { en: 'A composite score derived from figure area and part count summarizes the form integrity of the drawing.', tr: 'Figür alanı ve parça sayısından türetilen kompozit skor, çizimin form bütünlüğünü özetler.' },
      ],
    ],
  },
];

const GRADCAM_DETAILS: [LS, LS][] = [
  [
    { en: 'Purpose', tr: 'Amaç' },
    { en: 'Grad-CAM makes visible, as a heatmap, which regions of the image were more influential while the model produced its class decision.', tr: 'Grad-CAM, modelin sınıf kararını üretirken görüntüde hangi bölgelerin daha etkili olduğunu ısı haritası olarak görünür kılar.' },
  ],
  [
    { en: 'Role in the thesis', tr: 'Tezdeki rol' },
    { en: 'While clinical indicators explain the numerical decision path, Grad-CAM shows the visual focus area. Thus “which features” and “which region of the drawing” can be interpreted together.', tr: 'Klinik göstergeler sayısal karar yolunu açıklarken, Grad-CAM görsel odak alanını gösterir. Böylece “hangi özellikler” ve “çizimin hangi bölgesi” birlikte yorumlanabilir.' },
  ],
  [
    { en: 'Clinical reading', tr: 'Klinik okuma' },
    { en: 'The heatmap is not diagnostic evidence on its own; it must be evaluated together with the class probability, the 16 clinical indicators and expert interpretation.', tr: 'Isı haritası tek başına tanı kanıtı değildir; sınıf olasılığı, 16 klinik gösterge ve uzman yorumu ile birlikte değerlendirilmelidir.' },
  ],
  [
    { en: 'Limitation', tr: 'Sınırlılık' },
    { en: 'Grad-CAM does not give causal explanation; it approximately shows attention intensity in the model’s last convolutional layer. It should therefore be used as an explainability aid.', tr: 'Grad-CAM nedensel açıklama vermez, modelin son evrişim katmanındaki dikkat yoğunluğunu yaklaşık gösterir. Bu nedenle açıklanabilirlik desteği olarak kullanılmalıdır.' },
  ],
];

// Horizontal project-identity strip below the hero
const IDENTITY_STRIP: { icon: IconType; label: LS; value: LS }[] = [
  { icon: GraduationCap, label: { en: 'University', tr: 'Üniversite' }, value: { en: 'NÖHÜ', tr: 'NÖHÜ' } },
  { icon: Layers3, label: { en: 'Department', tr: 'Bölüm' }, value: { en: 'Computer Engineering', tr: 'Bilgisayar Mühendisliği' } },
  { icon: Database, label: { en: 'Project type', tr: 'Proje Türü' }, value: { en: 'B.Sc. Thesis', tr: 'Lisans Tezi' } },
  { icon: ShieldAlert, label: { en: 'Funding', tr: 'Destek' }, value: { en: 'TÜBİTAK 2209-A', tr: 'TÜBİTAK 2209-A' } },
  { icon: ScanSearch, label: { en: 'Dataset', tr: 'Veri Seti' }, value: { en: 'KIDO', tr: 'KIDO' } },
  { icon: Sparkles, label: { en: 'Goal', tr: 'Amaç' }, value: { en: 'Explainable Emotion Analysis', tr: 'Açıklanabilir Duygu Analizi' } },
];

// Detailed project identity (lower section)
const IDENTITY_DETAILS: [LS, LS][] = [
  [
    { en: 'Project title', tr: 'Proje Adı' },
    {
      en: "Development of a Deep Learning System with Clinical Feature Fusion for Explainable Emotion Classification from Children's Drawings",
      tr: 'Çocuk Çizimlerinde Açıklanabilir Duygu Sınıflandırması için Klinik Özellik Füzyonlu Derin Öğrenme Sistemi Geliştirilmesi',
    },
  ],
  [{ en: 'Principal investigator', tr: 'Yürütücü' }, { en: 'Alper YALÇIN', tr: 'Alper YALÇIN' }],
  [{ en: 'Advisor', tr: 'Danışman' }, { en: 'Assoc. Prof. Dr. Erkan ÇALIŞKAN', tr: 'Doç. Dr. Erkan ÇALIŞKAN' }],
  [
    { en: 'Institution', tr: 'Kurum' },
    { en: 'Niğde Ömer Halisdemir University, Computer Engineering', tr: 'Niğde Ömer Halisdemir Üniversitesi, Bilgisayar Mühendisliği' },
  ],
  [
    { en: 'Institutional status', tr: 'Kurumsal Durum' },
    { en: 'TÜBİTAK-approved undergraduate research project', tr: 'TÜBİTAK onaylı lisans araştırma projesi' },
  ],
  [
    { en: 'Dataset', tr: 'Veri Seti' },
    { en: 'KIDO (hand-labeled, 5,177 drawings · clean test n=775)', tr: 'KIDO (elle etiketlenmiş, 5.177 çizim · temiz test n=775)' },
  ],
  [
    { en: 'Final model', tr: 'Nihai Model' },
    { en: 'Concept Bottleneck — ResNet-50 + 16 figure-aware clinical indicators', tr: 'Kavram Darboğazı — ResNet-50 + 16 figür-farkında klinik gösterge' },
  ],
];

const CONTRIBUTIONS: { icon: IconType; title: LS; body: LS }[] = [
  {
    icon: Layers3,
    title: { en: 'Concept Bottleneck', tr: 'Concept Bottleneck' },
    body: { en: 'Makes model decisions explainable through clinically meaningful concepts.', tr: 'Model kararlarını klinik anlamlı kavramlar üzerinden açıklanabilir kılar.' },
  },
  {
    icon: Activity,
    title: { en: 'Grad-CAM', tr: 'Grad-CAM' },
    body: { en: 'Visualizes decision regions, showing which areas of the drawing were influential.', tr: 'Karar bölgelerini görselleştirerek çizimde hangi alanların etkili olduğunu gösterir.' },
  },
  {
    icon: MessageSquareText,
    title: { en: 'LLM explanation', tr: 'LLM Açıklama' },
    body: { en: 'Provides experts with clear, textual explanations via a generative language model.', tr: 'Üretken dil modeli ile uzmanlara anlaşılır, metinsel açıklamalar sunar.' },
  },
  {
    icon: Gauge,
    title: { en: '16 clinical indicators', tr: '16 Klinik Gösterge' },
    body: { en: 'Produces meaningful inferences through 16 indicators grounded in the psychology/psychopathology literature.', tr: 'Psikoloji/psikopatoloji literatürüne dayalı 16 gösterge üzerinden anlamlı çıkarımlar üretir.' },
  },
];

const JOURNEY: { icon: IconType; title: LS; body: LS }[] = [
  { icon: Database, title: { en: 'Data collection', tr: 'Veri Toplama' }, body: { en: 'Collecting children’s drawings from the KIDO dataset', tr: 'KIDO veri setinden çocuk çizimlerinin toplanması' } },
  { icon: SlidersHorizontal, title: { en: 'Pre-processing', tr: 'Ön İşleme' }, body: { en: 'Resizing, normalization and data augmentation', tr: 'Boyutlandırma, normalizasyon ve veri artırma' } },
  { icon: BrainCircuit, title: { en: 'ResNet-50', tr: 'ResNet-50' }, body: { en: 'Extracting image features with deep learning', tr: 'Görüntü özelliklerinin derin öğrenme ile çıkarımı' } },
  { icon: Gauge, title: { en: 'Clinical indicators', tr: 'Klinik Göstergeler' }, body: { en: 'Predicting probabilities for 16 clinical indicators', tr: '16 klinik gösterge için olasılıkların tahmin edilmesi' } },
  { icon: Layers3, title: { en: 'Concept Bottleneck', tr: 'Kavram Darboğazı' }, body: { en: 'An explainable decision mechanism via Concept Bottleneck', tr: 'Concept Bottleneck ile açıklanabilir karar mekanizması' } },
  { icon: MessageSquareText, title: { en: 'Explainable output', tr: 'Açıklanabilir Çıktı' }, body: { en: 'Emotion prediction + textual explanation via LLM', tr: 'Duygu tahmini + LLM ile metinsel açıklama' } },
];

const PERF_HIGHLIGHTS: { icon: IconType; value: string; label: LS; sub: LS }[] = [
  { icon: Smile, value: '4', label: { en: 'Emotion classes', tr: 'Duygu Sınıfı' }, sub: { en: 'Happy · Sad · Angry · Fear', tr: 'Mutlu · Üzgün · Kızgın · Korku' } },
  { icon: Gauge, value: '16', label: { en: 'Clinical indicators', tr: 'Klinik Gösterge' }, sub: { en: 'Indicators derived from the psychology literature', tr: 'Psikoloji literatüründen türetilmiş göstergeler' } },
  { icon: FlaskConical, value: '0.834', label: { en: 'Macro F1 score', tr: 'Makro F1 Skoru' }, sub: { en: 'Best overall performance with Concept Bottleneck', tr: 'Concept Bottleneck ile en iyi genel performans' } },
];

const DATASET_POINTS: [LS, LS][] = [
  [
    { en: 'Original total', tr: 'Orijinal toplam' },
    { en: '5,177 drawings', tr: '5.177 çizim' },
  ],
  [
    { en: 'Classes', tr: 'Sınıflar' },
    { en: 'Happy: 2,963 · Sad: 1,456 · Angry: 359 · Fear: 399', tr: 'Mutlu: 2.963 · Üzgün: 1.456 · Kızgın: 359 · Korku: 399' },
  ],
  [
    { en: 'Augmented training set', tr: 'Artırılmış eğitim seti' },
    { en: '6,619 samples (minority + Sad class balanced)', tr: '6.619 örnek (azınlık + Üzgün sınıfı dengelendi)' },
  ],
  [
    { en: 'Clean test set', tr: 'Temiz test seti' },
    { en: '775 samples — data leakage removed, original images only', tr: '775 örnek — veri sızıntısı giderildi, yalnızca orijinal görüntüler' },
  ],
  [
    { en: 'Training augmentation', tr: 'Eğitim artırımı' },
    { en: '±15° rotation, brightness/contrast jitter, light blur', tr: '±15° döndürme, parlaklık/kontrast değişimi, hafif bulanıklaştırma' },
  ],
];

const C = {
  en: {
    heroEyebrow: 'B.SC. THESIS · RESEARCH PROJECT',
    heroTitleA: 'About the ',
    heroTitleB: 'Project',
    heroLead:
      'This work is a B.Sc. thesis, supported under TÜBİTAK 2209-A, that aims to analyze emotional expressions in children’s drawings in an explainable way. By combining deep learning, clinical indicator extraction, a concept bottleneck and generative language-model explanations, it provides experts with meaningful and transparent outputs.',
    heroLead2:
      'Five backbones were compared (best: ResNet-50); the architecture that turns clinical information into a structural Concept Bottleneck was selected as the final model.',
    identityTitle: 'Project Identity',
    summaryTitle: 'Research Summary',
    summaryBody:
      'Children’s drawings carry valuable cues for understanding emotional and psychological states. In this project, drawings are analyzed with a ResNet-50-based deep learning model; emotions are made explainable through 16 indicator concepts grounded in the clinical literature. With the Concept Bottleneck approach, the model’s decision mechanism becomes transparent, and expert-friendly explanations are produced with a generative language model (LLM).',
    contributionsTitle: 'Key Contributions',
    journeyTitle: 'The System’s Journey',
    journeyDesc: 'From drawing input to explainable output: the end-to-end operation steps of the system.',
    perfTitle: 'Model Performance',
    perfDesc:
      'The macro F1 scores of different approaches over the 4 emotion classes are compared below. The Concept Bottleneck approach delivered the highest overall performance and an interpretable decision path.',
    macroF1Up: 'Macro F1 score ↑',
    detailedEyebrow: 'Detailed Research Areas',
    detailedTitle: 'Method, Results and Clinical Foundations',
    labEyebrow: 'Model Comparison Lab',
    labTitle: 'Model Performance on the Clean Test Set',
    labDesc:
      'Nine experiment configurations were compared on a leakage-removed clean test set in terms of Macro F1, accuracy, per-class success and explainability.',
    sortBadge: 'Sort: Macro F1 · n=775',
    finalTag: 'Final',
    finalModelTag: 'Final Model',
    macroF1: 'Macro F1',
    accuracy: 'Accuracy',
    valF1: 'Val F1',
    time: 'Time',
    params: 'Parameters',
    classPerfTitle: 'Per-Class Performance',
    classPerfDesc: 'F1, precision and recall of the selected model across the four emotion classes.',
    precision: 'Precision',
    recall: 'Recall',
    academicTitle: 'Academic Assessment',
    methodologyTitle: 'Methodology & Architecture',
    methodologyBody:
      'Concept Bottleneck architecture: the ResNet-50 backbone predicts 16 figure-aware clinical indicators from the image; the 4-class emotion decision is made only from those indicators.',
    finalModelTitle: 'Final Model & Per-Class F1',
    finalCleanTest: 'Final Model — Clean Test (n=775)',
    perClassFinal: 'Per-Class F1 — Final Concept Bottleneck',
    finalNote:
      'Table 4.2 in the thesis notes that the final model brings clear improvement especially on the Angry class; the contribution should be framed as interpretability and a measured gain on critical classes rather than an overall accuracy increase.',
    indicatorsTitle: '16 Clinical Indicators',
    indicatorsIntro:
      'The indicators are computed after the figure is isolated with OpenCV and form the interpretable intermediate layer through which the decision passes in the Concept Bottleneck model.',
    indicatorsCount: 'indicators',
    gradcamTitle: 'Grad-CAM Explainability',
    gradcamIntro:
      'Grad-CAM is a supporting explanation layer that makes the model’s visual decision auditable; it does not replace the clinical indicators, it complements them.',
    heatmapLogic: 'Heatmap Logic',
    heatmapLogicBody: 'Warm areas represent the drawing regions the model used more intensively for the selected class decision.',
    gradcamFocusAlt: 'Grad-CAM focus example',
    datasetTitle: 'Dataset — KIDO',
    datasetBody:
      'The KIDO (Kinetic Family Drawing) dataset was used. All labels were assigned manually by a single researcher; no pseudo-labels or model-guided labels were used.',
    datasetSampleAlt: 'Sample drawing',
    datasetSampleCaption: 'KIDO dataset sample',
    techTitle: 'Technologies Used',
    limitationsTitle: 'Limitations',
    futureTitle: 'Future Work',
    ethicsTitle: 'Ethical Boundaries and Use',
    ethicsBody:
      'This system is not a clinical diagnosis tool; it is an explainable decision-support prototype designed to assist expert evaluation. Outputs are intended only to support expert assessment; all results are probabilistic and the final interpretation and decision authority belong to a qualified psychologist or clinician.',
    startAnalysis: 'Start Analysis',
    startAnalysisNote: 'Try the system, upload your drawing and review the analysis.',
  },
  tr: {
    heroEyebrow: 'LİSANS TEZİ · ARAŞTIRMA PROJESİ',
    heroTitleA: 'Proje ',
    heroTitleB: 'Hakkında',
    heroLead:
      'Bu çalışma, çocuk çizimlerinden duygusal ifadeleri açıklanabilir şekilde analiz etmeyi amaçlayan, TÜBİTAK 2209-A kapsamında desteklenen bir lisans tezidir. Derin öğrenme, klinik gösterge çıkarımı, kavram darboğazı (Concept Bottleneck) ve üretken dil modeli açıklamalarını birleştirerek uzmanlara anlamlı ve şeffaf çıktılar sunar.',
    heroLead2:
      'Beş omurga karşılaştırılmış (en iyi: ResNet-50); klinik bilgiyi yapısal bir Kavram Darboğazına dönüştüren mimari nihai model olarak seçilmiştir.',
    identityTitle: 'Proje Kimliği',
    summaryTitle: 'Araştırma Özeti',
    summaryBody:
      'Çocuk çizimleri, duygusal ve psikolojik durumların anlaşılmasında değerli ipuçları içerir. Bu projede, ResNet-50 tabanlı derin öğrenme modeli ile çizimler analiz edilmekte; klinik literatüre dayalı 16 gösterge kavramı aracılığıyla duygular açıklanabilir hale getirilmektedir. Concept Bottleneck yaklaşımı ile modelin karar mekanizması şeffaflaşır ve üretken dil modeli (LLM) ile uzman dostu açıklamalar üretilir.',
    contributionsTitle: 'Temel Katkılar',
    journeyTitle: 'Sistemin Yolculuğu',
    journeyDesc: 'Çizim girdisinden açıklanabilir çıktıya: sistemin uçtan uca işleyiş adımları.',
    perfTitle: 'Model Performansı',
    perfDesc:
      'Farklı yaklaşımların 4 duygu sınıfı üzerindeki makro F1 skorları aşağıda karşılaştırılmıştır. Concept Bottleneck yaklaşımı, en yüksek genel performansı ve yorumlanabilir karar yolunu sağlamıştır.',
    macroF1Up: 'Makro F1 Skoru ↑',
    detailedEyebrow: 'Detaylı Araştırma Alanları',
    detailedTitle: 'Yöntem, Sonuçlar ve Klinik Temeller',
    labEyebrow: 'Model Karşılaştırma Laboratuvarı',
    labTitle: 'Temiz Test Setinde Model Performansı',
    labDesc:
      'Dokuz deney konfigürasyonu, veri sızıntısı giderilmiş temiz test seti üzerinde Makro F1, doğruluk, sınıf bazlı başarı ve açıklanabilirlik açısından karşılaştırılmıştır.',
    sortBadge: 'Sıralama: Makro F1 · n=775',
    finalTag: 'Nihai',
    finalModelTag: 'Nihai Model',
    macroF1: 'Makro F1',
    accuracy: 'Doğruluk',
    valF1: 'Val F1',
    time: 'Süre',
    params: 'Parametre',
    classPerfTitle: 'Sınıf Bazlı Başarım',
    classPerfDesc: 'Seçili modelin dört duygu sınıfındaki F1, precision ve recall değerleri.',
    precision: 'Precision',
    recall: 'Recall',
    academicTitle: 'Akademik Değerlendirme',
    methodologyTitle: 'Metodoloji & Mimari',
    methodologyBody:
      'Kavram Darboğazı (Concept Bottleneck) mimarisi: ResNet-50 omurgası görüntüden 16 figür-farkında klinik gösterge tahmin eder; 4-sınıf duygu kararı yalnızca bu göstergelerden verilir.',
    finalModelTitle: 'Nihai Model & Sınıf Başına F1',
    finalCleanTest: 'Nihai Model — Temiz Test (n=775)',
    perClassFinal: 'Sınıf Başına F1 — Nihai Kavram Darboğazı',
    finalNote:
      'Tezdeki Çizelge 4.2, nihai modelin özellikle Kızgın sınıfında belirgin iyileşme sağladığını; katkının genel doğruluk artışından çok yorumlanabilirlik ve kritik sınıflardaki ölçülü kazanım olarak çerçevelenmesi gerektiğini belirtir.',
    indicatorsTitle: '16 Klinik Gösterge',
    indicatorsIntro:
      'Göstergeler OpenCV ile figür izole edildikten sonra hesaplanır ve Kavram Darboğazı modelinde kararın geçtiği yorumlanabilir ara katmanı oluşturur.',
    indicatorsCount: 'gösterge',
    gradcamTitle: 'Grad-CAM Açıklanabilirlik',
    gradcamIntro:
      'Grad-CAM, modelin görsel kararını denetlenebilir hale getiren destekleyici açıklama katmanıdır; klinik göstergelerin yerine geçmez, onları tamamlar.',
    heatmapLogic: 'Isı Haritası Mantığı',
    heatmapLogicBody: 'Sıcak alanlar, modelin seçili sınıf kararında daha yoğun kullandığı çizim bölgelerini temsil eder.',
    gradcamFocusAlt: 'Grad-CAM odak örneği',
    datasetTitle: 'Veri Seti — KIDO',
    datasetBody:
      'KIDO (Kinetic Family Drawing) veri seti kullanılmıştır. Tüm etiketler tek bir araştırmacı tarafından elle atandı; pseudo-etiket veya model güdümlü etiket kullanılmadı.',
    datasetSampleAlt: 'Örnek çizim',
    datasetSampleCaption: 'KIDO veri seti örneği',
    techTitle: 'Kullanılan Teknolojiler',
    limitationsTitle: 'Sınırlılıklar',
    futureTitle: 'Gelecek Çalışmalar',
    ethicsTitle: 'Etik Sınırlar ve Kullanım',
    ethicsBody:
      'Bu sistem klinik tanı aracı değildir; uzman değerlendirmesini desteklemek için tasarlanmış açıklanabilir bir karar destek prototipidir. Çıktılar yalnızca uzman değerlendirmesine destek amacı taşır; tüm sonuçlar olasılıksaldır ve nihai yorum ile karar yetkisi nitelikli bir psikolog veya klinisyene aittir.',
    startAnalysis: 'Analizi Başlat',
    startAnalysisNote: 'Sistemi deneyin, çiziminizi yükleyip analizi inceleyin.',
  },
};

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
  const { lang } = useTranslation();
  const c = C[lang];
  const [selectedExperimentId, setSelectedExperimentId] = useState(EXPERIMENTS[0].id);
  const [openGroup, setOpenGroup] = useState<string | null>(CLINICAL_INDICATOR_GROUPS[0].group.en);
  const selectedExperiment = EXPERIMENTS.find((exp) => exp.id === selectedExperimentId) ?? EXPERIMENTS[0];
  const selectedExperimentAnalysis = EXPERIMENT_ANALYSIS[selectedExperiment.id] ?? [];

  return (
    <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -12 }}>
      <PageMotion>
        {/* ── Hero ── */}
        <section className="grid items-center gap-10 lg:grid-cols-[0.92fr_1.08fr]">
          <motion.div initial={{ opacity: 0, x: -24 }} animate={{ opacity: 1, x: 0 }} transition={{ duration: 0.5, delay: 0.05 }}>
            <Eyebrow>{c.heroEyebrow}</Eyebrow>
            <h1 className="mt-5 font-serif text-5xl font-semibold leading-[1.02] tracking-[-0.035em] text-ink md:text-6xl lg:text-7xl">
              {c.heroTitleA}<span className="text-[#E76F3C]">{c.heroTitleB}</span>
            </h1>
            <p className="mt-6 max-w-xl text-lg leading-8 text-muted">
              {c.heroLead}
            </p>
            <p className="mt-4 max-w-xl text-[15px] leading-7 text-muted">
              {c.heroLead2}
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

        {/* ── Project identity strip ── */}
        <div className="mt-12 grid grid-cols-2 divide-x divide-y divide-line overflow-hidden rounded-2xl border border-line bg-surface sm:grid-cols-3 lg:grid-cols-6 lg:divide-y-0">
          {IDENTITY_STRIP.map((item, i) => {
            const Icon = item.icon;
            return (
              <motion.div
                key={item.label.en}
                initial={{ opacity: 0, y: 10 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.4, delay: i * 0.05 }}
                className="flex items-center gap-3 p-4"
              >
                <Icon size={20} className="shrink-0 text-[#E76F3C]" strokeWidth={1.7} />
                <div className="min-w-0">
                  <div className="text-[11px] font-semibold uppercase tracking-wide text-muted">{item.label[lang]}</div>
                  <div className="truncate text-sm font-semibold text-ink">{item.value[lang]}</div>
                </div>
              </motion.div>
            );
          })}
        </div>

        {/* ── Research summary + Key contributions ── */}
        <section className="mt-16 grid gap-12 lg:grid-cols-[0.92fr_1.08fr]">
          <motion.div {...fadeUp}>
            <SectionHead title={c.summaryTitle} />
            <p className="mt-6 text-[15px] leading-7 text-muted">
              {c.summaryBody}
            </p>
            <div className="mt-8 rounded-2xl border border-line bg-surface2 p-5">
              <div className="text-xs font-bold uppercase tracking-[0.2em] text-[#E76F3C]">{c.identityTitle}</div>
              <dl className="mt-4 space-y-2.5">
                {IDENTITY_DETAILS.map(([label, value]) => (
                  <div key={label.en} className="flex gap-3 text-sm">
                    <dt className="w-28 shrink-0 font-semibold text-ink">{label[lang]}</dt>
                    <dd className="text-muted">{value[lang]}</dd>
                  </div>
                ))}
              </dl>
            </div>
          </motion.div>

          <motion.div {...fadeUp}>
            <SectionHead title={c.contributionsTitle} />
            <div className="mt-7 grid gap-x-8 gap-y-7 sm:grid-cols-2">
              {CONTRIBUTIONS.map((item) => {
                const Icon = item.icon;
                return (
                  <div key={item.title.en} className="border-t border-line pt-5">
                    <Icon size={24} className="text-[#E76F3C]" strokeWidth={1.6} />
                    <h3 className="mt-3 font-semibold text-ink">{item.title[lang]}</h3>
                    <p className="mt-1.5 text-sm leading-6 text-muted">{item.body[lang]}</p>
                  </div>
                );
              })}
            </div>
          </motion.div>
        </section>

        {/* ── The system's journey ── */}
        <section className="mt-16">
          <SectionHead title={c.journeyTitle} desc={c.journeyDesc} />
          <div className="relative mt-10">
            <div className="absolute inset-x-0 top-7 hidden h-px bg-line lg:block" />
            <div className="grid gap-y-9 sm:grid-cols-2 lg:grid-cols-6 lg:gap-x-4">
              {JOURNEY.map((step, i) => {
                const Icon = step.icon;
                return (
                  <motion.div
                    key={step.title.en}
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
                    <h3 className="mt-4 font-semibold text-ink">{step.title[lang]}</h3>
                    <p className="mt-1 text-sm leading-6 text-muted lg:pr-3">{step.body[lang]}</p>
                  </motion.div>
                );
              })}
            </div>
          </div>
        </section>

        {/* ── Model performance ── */}
        <section className="mt-16">
          <SectionHead title={c.perfTitle} desc={c.perfDesc} />
          <div className="mt-8 grid items-stretch gap-10 lg:grid-cols-[1.1fr_0.9fr]">
            <div className="lg:flex lg:flex-col">
              <p className="mb-4 text-xs font-bold uppercase tracking-[0.18em] text-muted">{c.macroF1Up}</p>
              <div className="space-y-4">
                {FINAL_MODELS.map((m) => (
                  <div key={m.name.en}>
                    <div className="mb-1.5 flex items-center justify-between text-sm">
                      <span className={m.best ? 'font-semibold text-ink' : 'text-muted'}>{m.name[lang]}</span>
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
                    <div key={metric.label.en} className="rounded-xl border border-line bg-surface p-3 text-center">
                      <Icon className="mx-auto text-[#E76F3C]" size={20} strokeWidth={1.6} />
                      <div className="mt-2 font-serif text-xl font-semibold text-ink">{metric.value[lang]}</div>
                      <div className="mt-0.5 text-[11px] font-medium text-muted">{metric.label[lang]}</div>
                    </div>
                  );
                })}
              </div>
            </div>

            <div className="grid gap-3 sm:grid-cols-3 lg:auto-rows-fr lg:grid-cols-1">
              {PERF_HIGHLIGHTS.map((h) => {
                const Icon = h.icon;
                return (
                  <div key={h.label.en} className="flex items-center gap-4 rounded-2xl border border-line bg-surface p-4">
                    <Icon size={24} className="shrink-0 text-[#E76F3C]" strokeWidth={1.5} />
                    <div className="min-w-0">
                      <div className="font-serif text-2xl font-semibold text-ink">{h.value}</div>
                      <div className="text-sm font-semibold text-ink">{h.label[lang]}</div>
                      <div className="mt-0.5 text-xs leading-5 text-muted">{h.sub[lang]}</div>
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
                <div key={stat.label.en} className="flex items-center gap-3 p-5">
                  <Icon size={24} className="shrink-0 text-[#E76F3C]" strokeWidth={1.6} />
                  <div className="min-w-0">
                    <div className="font-serif text-2xl font-semibold text-ink">{stat.value[lang]}</div>
                    <div className="text-xs font-medium text-muted">{stat.label[lang]}</div>
                  </div>
                </div>
              );
            })}
          </div>
        </section>

        {/* ── Detailed research areas ── */}
        <section className="mt-20 border-t border-line pt-12">
          <Eyebrow>{c.detailedEyebrow}</Eyebrow>
          <h2 className="mt-3 font-serif text-3xl font-semibold tracking-[-0.02em] text-ink md:text-4xl">
            {c.detailedTitle}
          </h2>
        </section>

        {/* ── Model comparison ── */}
        <motion.section {...fadeUp} className="mt-12">
          {/* Editorial header */}
          <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
            <div>
              <Eyebrow>{c.labEyebrow}</Eyebrow>
              <h2 className="mt-3 font-serif text-3xl font-semibold tracking-[-0.02em] text-ink md:text-4xl">
                {c.labTitle}
              </h2>
              <div className="mt-3 h-[3px] w-12 rounded-full bg-[#E76F3C]" />
              <p className="mt-4 max-w-2xl text-[15px] leading-7 text-muted">
                {c.labDesc}
              </p>
            </div>
            <span className="inline-flex shrink-0 items-center gap-2 self-start rounded-full border border-line bg-surface px-4 py-2 text-xs font-semibold text-muted sm:self-auto">
              <span className="h-1.5 w-1.5 rounded-full bg-[#E76F3C]" />
              {c.sortBadge}
            </span>
          </div>

          {/* Top: leaderboard | selected model summary */}
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
                      <p className="truncate text-sm font-semibold leading-none text-ink">{exp.label[lang]}</p>
                      <p className={`mt-1 truncate text-xs ${isSelected ? 'text-[#E76F3C]' : 'text-muted'}`}>{exp.sub[lang]}</p>
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
                      <span className="shrink-0 rounded-full bg-[#E76F3C] px-2 py-0.5 text-[10px] font-bold text-white">{c.finalTag}</span>
                    ) : (
                      <span className="w-[44px] shrink-0" />
                    )}
                  </motion.button>
                );
              })}
            </div>

            {/* Selected model summary */}
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
                  <h3 className="mt-3 font-serif text-2xl font-semibold text-ink">{selectedExperiment.label[lang]}</h3>
                  <p className="mt-1 text-sm text-muted">{selectedExperiment.sub[lang]} · {selectedExperiment.params}</p>
                </div>
                {selectedExperiment.best && (
                  <span className="shrink-0 rounded-full bg-[#E76F3C] px-3 py-1 text-xs font-bold text-white">{c.finalModelTag}</span>
                )}
              </div>

              <div className="mt-6 flex items-end gap-3">
                <div className="font-serif text-6xl font-semibold leading-none text-[#E76F3C]">{f3(selectedExperiment.f1)}</div>
                <div className="pb-1.5 text-sm font-semibold text-muted">{c.macroF1}</div>
              </div>

              <dl className="mt-6 border-t border-line2">
                {([
                  [c.accuracy, pct(selectedExperiment.acc)],
                  [c.valF1, f3(selectedExperiment.valF1)],
                  [c.time, minutes(selectedExperiment.trainTimeS, lang)],
                  [c.params, selectedExperiment.params],
                ] as [string, string][]).map(([label, value]) => (
                  <div key={label} className="flex items-center justify-between border-b border-line2 py-2.5 text-sm">
                    <dt className="text-muted">{label}</dt>
                    <dd className="font-mono font-semibold text-ink">{value}</dd>
                  </div>
                ))}
              </dl>
            </motion.div>
          </div>

          {/* Bottom: per-class performance | academic assessment */}
          <div className="mt-6 grid items-stretch gap-6 lg:grid-cols-2">
            <div className="rounded-2xl border border-line bg-surface2 p-6">
              <h3 className="font-serif text-xl font-semibold text-ink">{c.classPerfTitle}</h3>
              <p className="mt-1 text-sm leading-6 text-muted">{c.classPerfDesc}</p>
              <div className="mt-5 space-y-4">
                {EMOTION_LABELS.map((emotion) => (
                  <div key={emotion.key}>
                    <div className="mb-1.5 flex items-center justify-between text-sm">
                      <span className="font-medium text-ink">{emotion.label[lang]}</span>
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
                      <span>{c.precision} {f3(selectedExperiment.precision[emotion.key])}</span>
                      <span>{c.recall} {f3(selectedExperiment.recall[emotion.key])}</span>
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
              <h3 className="font-serif text-xl font-semibold text-ink">{c.academicTitle}</h3>
              <div className="mt-4 divide-y divide-line2">
                {selectedExperimentAnalysis.map(([title, body], i) => (
                  <div key={title.en} className="py-4 first:pt-0">
                    <div className="flex items-baseline gap-2">
                      <span className="font-mono text-xs font-bold text-[#E76F3C]">{String(i + 1).padStart(2, '0')}</span>
                      <span className="text-sm font-semibold text-ink">{title[lang]}</span>
                    </div>
                    <p className="mt-1.5 text-sm leading-6 text-muted">{body[lang]}</p>
                  </div>
                ))}
              </div>
              <p className="mt-2 rounded-xl bg-surface2 p-4 text-sm leading-6 text-muted">{selectedExperiment.note[lang]}</p>
            </motion.div>
          </div>
        </motion.section>

        {/* ── Methodology + Final model ── */}
        <section className="mt-6 grid items-stretch gap-6 lg:grid-cols-2">
          <AboutPanel className="h-full p-7">
            <div className="flex items-center gap-3">
              <IconBubble icon={Layers3} className={`h-10 w-10 ${ABOUT_ICON_BUBBLE}`} />
              <SectionTitle className="text-2xl">{c.methodologyTitle}</SectionTitle>
            </div>
            <p className="mt-5 text-sm leading-6 text-muted">
              {c.methodologyBody}
            </p>
            <div className="mt-6 space-y-4">
              {methodology.map((item) => (
                <div key={item.title.en} className="flex gap-4">
                  <div className="grid h-10 w-10 shrink-0 place-items-center rounded-xl border border-[#F2C8B2] bg-tint text-[#E76F3C]">
                    <CheckCircle2 size={18} />
                  </div>
                  <div>
                    <div className="font-semibold text-ink">{item.title[lang]}</div>
                    <div className="mt-1 text-sm leading-6 text-muted">{item.body[lang]}</div>
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
              <SectionTitle className="text-2xl">{c.finalModelTitle}</SectionTitle>
            </div>

            <p className="mb-3 text-sm font-semibold text-ink">{c.finalCleanTest}</p>
            <div className="mb-6 space-y-2.5">
              {FINAL_MODELS.map((m) => (
                <div
                  key={m.name.en}
                  className={`flex items-center gap-3 rounded-xl px-4 py-2.5 ${
                    m.best ? 'border border-[#E76F3C] bg-surface2' : 'border border-line bg-surface'
                  }`}
                >
                  <span className={`flex-1 text-sm font-medium ${m.best ? 'text-ink' : 'text-[#555]'}`}>{m.name[lang]}</span>
                  <div className="h-2 w-24 overflow-hidden rounded-full" style={{ backgroundColor: m.best ? ABOUT_PROGRESS_SELECTED_TRACK : ABOUT_PROGRESS_TRACK }}>
                    <div className="h-full rounded-full" style={{ width: scoreWidth(m.f1, 0.78, 0.84), background: m.best ? ABOUT_ORANGE : ABOUT_PROGRESS_FILL }} />
                  </div>
                  <span className={`w-12 shrink-0 text-right font-mono text-sm font-bold ${m.best ? 'text-[#E76F3C]' : 'text-[#555]'}`}>{f3(m.f1)}</span>
                </div>
              ))}
            </div>

            <p className="mb-3 text-sm font-semibold text-ink">{c.perClassFinal}</p>
            <div className="space-y-5">
              {FINAL_CLASS_F1.map((cl) => (
                <div key={cl.name.en}>
                  <div className="flex justify-between text-sm mb-1.5">
                    <span className="font-medium text-ink">{cl.name[lang]}</span>
                    <span className="font-mono font-bold text-ink">{f3(cl.f1)}</span>
                  </div>
                  <div className="h-3 rounded-full overflow-hidden" style={{ backgroundColor: ABOUT_PROGRESS_TRACK }}>
                    <div className="h-full rounded-full" style={{ width: `${cl.f1 * 100}%`, backgroundColor: ABOUT_PROGRESS_FILL }} />
                  </div>
                </div>
              ))}
            </div>
            <p className="mt-4 text-xs leading-5 text-muted">
              {c.finalNote}
            </p>
            <div className="mt-6 grid grid-cols-2 gap-3">
              {performance.map((metric) => {
                const Icon = metric.icon;
                return (
                  <div key={metric.label.en} className="rounded-xl border border-line bg-surface p-4 text-center">
                    <Icon className="mx-auto text-[#E76F3C]" size={22} strokeWidth={1.6} />
                    <div className="mt-3 font-serif text-2xl font-semibold text-ink">{metric.value[lang]}</div>
                    <div className="mt-1 text-xs font-medium text-muted">{metric.label[lang]}</div>
                  </div>
                );
              })}
            </div>
          </AboutPanel>
        </section>

        {/* ── 16 clinical indicators ── */}
        <section className="mt-6">
          <AboutPanel className="p-7">
            <div className="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
              <div className="flex items-center gap-3">
                <IconBubble icon={Database} className={`h-10 w-10 ${ABOUT_ICON_BUBBLE}`} />
                <SectionTitle className="text-2xl">{c.indicatorsTitle}</SectionTitle>
              </div>
              <div className="max-w-2xl rounded-xl bg-surface2 px-4 py-3 text-sm leading-6 text-muted">
                {c.indicatorsIntro}
              </div>
            </div>

            <div className="mt-7 divide-y divide-line border-y border-line">
              {CLINICAL_INDICATOR_GROUPS.map((group) => {
                const isOpen = openGroup === group.group.en;
                return (
                  <div key={group.group.en}>
                    <button
                      type="button"
                      onClick={() => setOpenGroup(isOpen ? null : group.group.en)}
                      className="flex w-full items-center justify-between gap-3 py-4 text-left transition hover:text-[#E76F3C]"
                    >
                      <span className="flex flex-wrap items-center gap-3">
                        <span className="font-semibold text-ink">{group.group[lang]}</span>
                        <span className="rounded-full border border-line2 bg-surface2 px-2.5 py-1 text-[11px] font-semibold text-muted">
                          {group.basis[lang]}
                        </span>
                        <span className="text-xs font-medium text-muted">{group.items.length} {c.indicatorsCount}</span>
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
                              <div key={name.en}>
                                <div className="text-sm font-semibold text-ink">{name[lang]}</div>
                                <p className="mt-1 text-sm leading-6 text-muted">{body[lang]}</p>
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

        {/* ── Grad-CAM ── */}
        <section className="mt-6">
          <AboutPanel className="p-7">
            <div className="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
              <div className="flex items-center gap-3">
                <IconBubble icon={Activity} className={`h-10 w-10 ${ABOUT_ICON_BUBBLE}`} />
                <SectionTitle className="text-2xl">{c.gradcamTitle}</SectionTitle>
              </div>
              <div className="max-w-2xl rounded-xl bg-surface2 px-4 py-3 text-sm leading-6 text-muted">
                {c.gradcamIntro}
              </div>
            </div>

            <div className="mt-7 grid gap-6 lg:grid-cols-[0.9fr_1.1fr]">
              <div className="relative min-h-[320px] overflow-hidden rounded-xl border border-line bg-[#1F1F1F]">
                <img src={sampleImages[2]} alt={c.gradcamFocusAlt} className="h-full min-h-[320px] w-full object-cover opacity-90" />
                <div
                  className="absolute inset-0 mix-blend-screen"
                  style={{
                    background:
                      'radial-gradient(circle at 44% 36%, rgba(231, 111, 60, 0.64), transparent 30%), radial-gradient(circle at 60% 55%, rgba(242, 200, 178, 0.46), transparent 28%), radial-gradient(circle at 35% 68%, rgba(184, 173, 160, 0.36), transparent 24%)',
                  }}
                />
                <div className="absolute bottom-4 left-4 right-4 rounded-xl bg-surface/92 p-4 shadow-[0_18px_40px_-30px_rgba(31,31,31,0.7)] backdrop-blur">
                  <div className="text-sm font-semibold text-ink">{c.heatmapLogic}</div>
                  <p className="mt-1 text-sm leading-6 text-muted">
                    {c.heatmapLogicBody}
                  </p>
                </div>
              </div>

              <div className="grid gap-3 sm:grid-cols-2">
                {GRADCAM_DETAILS.map(([title, body]) => (
                  <div key={title.en} className="rounded-xl border border-line bg-surface p-5">
                    <div className="text-sm font-semibold text-ink">{title[lang]}</div>
                    <p className="mt-2 text-sm leading-6 text-muted">{body[lang]}</p>
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
                <SectionTitle className="text-2xl">{c.datasetTitle}</SectionTitle>
              </div>
              <p className="mt-5 leading-7 text-muted">
                {c.datasetBody}
              </p>
              <div className="mt-5 space-y-3">
                {DATASET_POINTS.map(([label, value]) => (
                  <div key={label.en} className="flex gap-3 text-sm">
                    <CheckCircle2 className="mt-0.5 shrink-0 text-[#E76F3C]" size={16} />
                    <span><span className="font-semibold text-ink">{label[lang]}: </span><span className="text-muted">{value[lang]}</span></span>
                  </div>
                ))}
              </div>
            </div>
            <div>
              <img src={sampleImages[0]} alt={c.datasetSampleAlt} className="h-52 w-full rounded-2xl object-cover" />
              <div className="mt-4 rounded-xl bg-surface2 px-4 py-3 text-center text-sm text-muted">
                {c.datasetSampleCaption}
              </div>
            </div>
          </AboutPanel>

          <AboutPanel className="h-full p-7">
            <SectionTitle className="text-2xl">{c.techTitle}</SectionTitle>
            <div className="mt-7 grid gap-3 sm:grid-cols-2">
              {techStack.map((tech) => (
                <div key={tech.name} className="rounded-xl border border-line2 bg-surface2 p-4">
                  <div className="text-lg font-bold text-ink">{tech.name}</div>
                  <div className="mt-1 text-xs font-medium text-muted">{tech.desc[lang]}</div>
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
              <SectionTitle className="text-2xl">{c.limitationsTitle}</SectionTitle>
            </div>
            <ul className="mt-7 space-y-4">
              {limitations.map((item) => (
                <li key={item.en} className="flex gap-3 text-sm leading-6 text-muted">
                  <span className="mt-2 h-2 w-2 shrink-0 rounded-full bg-[#E76F3C]" />
                  {item[lang]}
                </li>
              ))}
            </ul>
          </AboutPanel>

          <AboutPanel className="h-full p-7">
            <div className="flex items-center gap-3">
              <IconBubble icon={BarChart3} className={`h-10 w-10 ${ABOUT_ICON_BUBBLE}`} />
              <SectionTitle className="text-2xl">{c.futureTitle}</SectionTitle>
            </div>
            <ul className="mt-7 space-y-4">
              {futureWork.map((item) => (
                <li key={item.en} className="flex gap-3 text-sm leading-6 text-muted">
                  <CheckCircle2 className="mt-0.5 shrink-0 text-[#E76F3C]" size={18} />
                  {item[lang]}
                </li>
              ))}
            </ul>
          </AboutPanel>
        </section>

        {/* ── Ethical boundaries and use ── */}
        <section className="mt-16 flex flex-col gap-6 rounded-2xl border border-[#F2C8B2] bg-tint p-8 md:flex-row md:items-center md:justify-between">
          <div className="flex items-start gap-5">
            <div className="grid h-16 w-16 shrink-0 place-items-center rounded-full border border-[#F2C8B2] bg-surface text-[#E76F3C]">
              <ShieldAlert size={30} strokeWidth={1.6} />
            </div>
            <div>
              <h2 className="font-serif text-2xl font-semibold text-ink">{c.ethicsTitle}</h2>
              <p className="mt-2 max-w-3xl text-sm leading-7 text-muted">
                {c.ethicsBody}
              </p>
            </div>
          </div>
          <div className="shrink-0">
            <Button onClick={() => setPage('analysis')}>
              {c.startAnalysis}
              <ArrowRight size={17} />
            </Button>
            <p className="mt-2 text-center text-xs text-muted">{c.startAnalysisNote}</p>
          </div>
        </section>
      </PageMotion>
    </motion.div>
  );
}
