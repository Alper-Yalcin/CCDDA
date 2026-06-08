import {
  Activity,
  ArrowRight,
  Brain,
  BrainCircuit,
  CheckCircle2,
  FileText,
  Gauge,
  GraduationCap,
  Image as ImageIcon,
  Landmark,
  Layers3,
  MessageSquareText,
  Network,
  Smile,
  Sparkles,
  ThumbsUp,
} from 'lucide-react';
import { motion } from 'motion/react';
import { heroFeatures, pipeline, sampleImages } from '../data/medvision';

const EMOTION_BADGES = [
  { label: 'Mutlu',  pct: '94%', color: '#5BAE7B', img: sampleImages[0]  },
  { label: 'Öfkeli', pct: '87%', color: '#E76F3C', img: sampleImages[6]  },
  { label: 'Korku',  pct: '91%', color: '#9B5DE5', img: sampleImages[10] },
  { label: 'Üzgün',  pct: '78%', color: '#2F80ED', img: sampleImages[5]  },
];

const VISUAL_MARKERS = [
  { label: 'Grad-CAM', icon: Activity },
  { label: 'Klinik Göstergeler', icon: Gauge },
  { label: 'LLM Açıklama', icon: MessageSquareText },
];

export function DrawingAnalysisHero() {
  return (
    <div className="relative mx-auto min-h-[460px] w-full max-w-[700px] sm:min-h-[540px] lg:min-h-[610px]">
      <div
        className="absolute inset-0 opacity-60"
        style={{
          backgroundImage:
            'linear-gradient(#E9E1D7 1px, transparent 1px), linear-gradient(90deg, #E9E1D7 1px, transparent 1px)',
          backgroundSize: '38px 38px',
          maskImage: 'radial-gradient(circle at 55% 45%, black, transparent 72%)',
        }}
      />
      <div className="absolute -right-6 top-14 hidden h-[430px] w-[430px] rounded-full border border-[#E76F3C]/15 lg:block" />
      <div className="absolute right-8 top-24 hidden h-[340px] w-[340px] rounded-full border border-[#0F4C81]/10 lg:block" />

      <motion.div
        animate={{ y: [0, -8, 0] }}
        transition={{ duration: 7, repeat: Infinity, ease: 'easeInOut' }}
        className="absolute left-1/2 top-10 w-[86%] max-w-[560px] -translate-x-1/2 -rotate-3 rounded-md bg-surface p-3 shadow-[0_34px_80px_-44px_rgba(52,31,17,0.68)] sm:top-12 lg:left-[46%] lg:w-[78%]"
      >
        <div className="relative aspect-[4/3] overflow-hidden rounded-sm border border-line bg-surface">
          <img src="/home-preview.jpg" alt="Çocuk çizimi analizi" className="h-full w-full object-cover" />
          <div className="absolute inset-y-0 right-0 w-[48%] overflow-hidden border-l border-white/70">
            <div className="absolute inset-0 bg-[#0F4C81]/25 mix-blend-multiply" />
            <div
              className="absolute inset-0 opacity-90 mix-blend-screen"
              style={{
                background:
                  'radial-gradient(circle at 28% 32%, rgba(255,235,91,0.95) 0 9%, rgba(231,111,60,0.84) 14%, transparent 28%), radial-gradient(circle at 70% 68%, rgba(255,207,97,0.92) 0 10%, rgba(231,111,60,0.78) 17%, transparent 30%), radial-gradient(circle at 58% 22%, rgba(91,174,123,0.7) 0 11%, transparent 25%), linear-gradient(120deg, rgba(15,76,129,0.42), rgba(47,128,237,0.28))',
              }}
            />
          </div>
          <div
            className="absolute inset-y-0 left-[52%] w-5 -translate-x-1/2 bg-surface/90 shadow-[0_0_18px_rgba(255,253,249,0.85)]"
            style={{
              clipPath:
                'polygon(35% 0, 100% 0, 70% 12%, 100% 24%, 62% 37%, 96% 50%, 56% 67%, 95% 82%, 58% 100%, 0 100%, 22% 84%, 0 70%, 30% 55%, 4% 39%, 35% 22%, 0 8%)',
            }}
          />
        </div>
      </motion.div>

      <div className="absolute right-0 top-8 hidden w-[132px] rounded-2xl border border-line bg-surface/90 p-2 shadow-[0_22px_55px_-40px_rgba(52,31,17,0.55)] backdrop-blur md:block">
        {VISUAL_MARKERS.map((marker) => {
          const Icon = marker.icon;
          return (
            <div key={marker.label} className="flex flex-col items-center gap-2 border-b border-line px-2 py-4 text-center last:border-b-0">
              <span className="grid h-9 w-9 place-items-center rounded-full bg-tint text-[#E76F3C]">
                <Icon size={17} strokeWidth={1.8} />
              </span>
              <span className="text-[11px] font-semibold leading-snug text-ink">{marker.label}</span>
            </div>
          );
        })}
      </div>

      <motion.div
        initial={{ opacity: 0, y: 18 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.55, delay: 0.45 }}
        className="absolute bottom-[108px] right-2 w-[245px] rounded-2xl bg-[#25231F]/95 p-5 text-white shadow-[0_28px_60px_-32px_rgba(0,0,0,0.9)] sm:bottom-[118px] sm:right-10 sm:w-[280px]"
      >
        <div className="text-xs font-semibold text-white/80">Açıklanabilir Tahmin</div>
        <div className="mt-2 font-serif text-5xl font-semibold leading-none text-[#FFD18A]">%83.4</div>
        <div className="mt-2 flex items-center justify-between gap-3 text-sm text-white/85">
          <span>Makro F1 Skoru</span>
          <span className="h-px flex-1 bg-[#E76F3C]/45" />
          <span className="h-2 w-2 rounded-full bg-[#E76F3C]" />
        </div>
      </motion.div>

      <div className="absolute bottom-0 left-1/2 grid w-[96%] -translate-x-1/2 gap-2 sm:grid-cols-2 lg:w-[90%]">
        {heroFeatures.map((feature, index) => {
          const Icon = feature.icon;
          return (
            <motion.div
              key={feature.title}
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.42, delay: 0.35 + index * 0.06 }}
              className="flex items-center gap-2 rounded-full border border-line bg-surface/90 px-3 py-2 text-xs font-semibold text-ink shadow-[0_14px_34px_-28px_rgba(52,31,17,0.6)] backdrop-blur"
            >
              <Icon size={15} className="shrink-0 text-[#E76F3C]" strokeWidth={1.8} />
              <span className="truncate">{feature.title}</span>
            </motion.div>
          );
        })}
      </div>
    </div>
  );
}

export function HistologyBlob({ variant = 'hero' }: { variant?: 'hero' | 'compact' }) {
  const isHero = variant === 'hero';

  return (
    <div className={`relative mx-auto ${isHero ? 'h-[460px] w-full max-w-[500px]' : 'h-[340px] max-w-[440px]'}`}>
      {/* Background blobs */}
      <div className="absolute left-8 top-6 h-64 w-72 rounded-[45%_55%_50%_50%] bg-[#F4D8C2]/60" />
      <div className="absolute right-4 top-2 h-72 w-72 rounded-full border border-[#E9CDBA]" />

      {/* 2×2 drawing grid — fixed height, no aspect-square overflow */}
      <div className="absolute inset-x-6 top-8 overflow-hidden rounded-[28px] border-[6px] border-white bg-surface shadow-[0_30px_80px_-40px_rgba(52,31,17,0.7)]">
        <div className="grid grid-cols-2">
          {EMOTION_BADGES.map((b) => (
            <div key={b.label} className="relative h-[160px] overflow-hidden">
              <img src={b.img} alt={b.label} className="h-full w-full object-cover" />
              <div
                className="absolute bottom-0 inset-x-0 py-1.5 text-center text-[10px] font-bold text-white"
                style={{ background: `${b.color}cc` }}
              >
                {b.label} {b.pct}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Floating icon — top left */}
      <div className="absolute left-0 top-12 grid h-14 w-14 place-items-center rounded-full border border-line bg-surface text-[#E76F3C] shadow-[0_16px_40px_-24px_rgba(52,31,17,0.7)]">
        <Sparkles size={22} strokeWidth={1.6} />
      </div>

      {/* Floating icon — bottom right */}
      <div className="absolute bottom-4 right-2 grid h-16 w-16 place-items-center rounded-full border border-line bg-surface text-[#E76F3C] shadow-[0_16px_40px_-24px_rgba(52,31,17,0.7)]">
        <BrainCircuit size={28} strokeWidth={1.5} />
      </div>

      {/* Floating badge — Grad-CAM */}
      <div className="absolute bottom-2 left-4 flex items-center gap-2 rounded-full border border-line bg-surface px-3 py-1.5 shadow-[0_12px_30px_-16px_rgba(52,31,17,0.5)]">
        <ThumbsUp size={12} className="text-[#E76F3C]" />
        <span className="text-xs font-semibold text-ink">Grad-CAM aktif</span>
      </div>

      <span className="absolute right-2 top-16 h-2 w-2 rounded-full bg-[#E76F3C]" />
      <span className="absolute left-24 bottom-24 h-2 w-2 rounded-full bg-[#E76F3C]" />
    </div>
  );
}

export function MicroscopeComposition() {
  return (
    <div className="relative mx-auto min-h-[320px] max-w-[620px]">
      <div className="absolute inset-x-8 bottom-8 h-64 rounded-[46%_54%_52%_48%] bg-surface2" />
      <div className="absolute right-6 top-20 h-56 w-56 overflow-hidden rounded-full border-[8px] border-white shadow-[0_24px_70px_-48px_rgba(52,31,17,0.75)]">
        <img src={sampleImages[2]} alt="Örnek çizim" className="h-full w-full object-cover" />
      </div>
      <div className="absolute left-12 top-10 grid h-56 w-56 place-items-center rounded-[40%_60%_55%_45%] bg-tint text-[#E76F3C]">
        <Brain size={120} strokeWidth={1.1} />
      </div>
      <span className="absolute left-8 top-24 h-2 w-2 rounded-full bg-[#F08A5D]" />
      <span className="absolute right-2 top-12 h-2 w-2 rounded-full bg-[#F08A5D]" />
      <span className="absolute bottom-12 right-12 h-2 w-2 rounded-full bg-[#F08A5D]" />
    </div>
  );
}

export function PipelineDiagram({ withImage = false }: { withImage?: boolean }) {
  return (
    <div className="grid gap-4 md:grid-cols-4">
      {pipeline.map((item, index) => {
        const Icon = item.icon;
        return (
          <div key={item.title} className="relative">
            <div className="flex h-full flex-col items-center justify-center rounded-2xl border border-line bg-surface p-5 text-center">
              {withImage && index === 0 ? (
                <img src={sampleImages[2]} alt="" className="mb-4 h-20 w-20 rounded-xl object-cover" />
              ) : (
                <Icon className="mb-4 text-ink" size={38} strokeWidth={1.4} />
              )}
              <div className="font-semibold text-ink">{item.title}</div>
              <div className="mt-2 text-sm leading-relaxed text-muted">{item.body}</div>
            </div>
            {index < pipeline.length - 1 && (
              <div className="absolute -right-3 top-1/2 z-10 hidden -translate-y-1/2 text-[#E76F3C] md:block">→</div>
            )}
          </div>
        );
      })}
    </div>
  );
}

export function EditorialPipelineDiagram() {
  return (
    <div className="relative">
      <div className="absolute left-8 right-8 top-10 hidden h-px bg-line lg:block" />
      <div className="grid gap-5 md:grid-cols-2 lg:grid-cols-4">
        {pipeline.map((item, index) => {
          const Icon = item.icon;
          return (
            <div key={item.title} className="relative border-t border-line pt-5 lg:border-t-0 lg:pt-0">
              <div className="relative z-10 flex items-start gap-4 lg:block">
                <div className="grid h-20 w-20 shrink-0 place-items-center rounded-full border border-line bg-surface text-[#E76F3C] shadow-[0_16px_38px_-30px_rgba(52,31,17,0.5)]">
                  <Icon size={31} strokeWidth={1.45} />
                </div>
                <div className="lg:mt-6">
                  <div className="text-xs font-bold uppercase tracking-[0.22em] text-[#E76F3C]">0{index + 1}</div>
                  <h3 className="mt-2 font-serif text-2xl font-semibold leading-tight text-ink">{item.title}</h3>
                  <p className="mt-2 text-sm leading-6 text-muted">{item.body}</p>
                </div>
              </div>
              {index < pipeline.length - 1 && (
                <ArrowRight className="absolute right-4 top-8 hidden text-[#E76F3C] lg:block" size={20} strokeWidth={1.7} />
              )}
            </div>
          );
        })}
      </div>
      <div className="mt-8 flex items-start gap-3 border-t border-line pt-5 text-sm leading-6 text-muted">
        <FileText className="mt-0.5 shrink-0 text-[#E76F3C]" size={18} strokeWidth={1.8} />
        <span>
          ResNet-50 omurga (~25M parametre); duyguya 16 figür-farkında klinik göstergeden ulaşan kavram darboğazı. Tüm deney konfigürasyonları yeniden üretilebilir.
        </span>
      </div>
    </div>
  );
}

// — About hero için "tez masası / kâğıt kolaj" kompozisyonu —
const COLLAGE_FLOW = [
  { icon: ImageIcon, label: 'Çizim Girdisi' },
  { icon: Network, label: 'ResNet-50' },
  { icon: Gauge, label: 'Klinik Göstergeler' },
  { icon: Layers3, label: 'Concept Bottleneck' },
  { icon: MessageSquareText, label: 'LLM Açıklama' },
  { icon: Smile, label: 'Duygu Çıktısı' },
];

function ChildDrawing() {
  return (
    <svg viewBox="0 0 240 150" className="block h-full w-full" role="img" aria-label="Çocuk çizimi illüstrasyonu">
      <rect width="240" height="150" fill="#FCFBF7" />
      {/* güneş */}
      <g stroke="#F2C94C" strokeWidth="3" strokeLinecap="round">
        <line x1="206" y1="14" x2="206" y2="5" />
        <line x1="206" y1="57" x2="206" y2="66" />
        <line x1="183" y1="35" x2="174" y2="35" />
        <line x1="229" y1="35" x2="238" y2="35" />
        <line x1="190" y1="19" x2="184" y2="13" />
        <line x1="222" y1="51" x2="228" y2="57" />
        <line x1="222" y1="19" x2="228" y2="13" />
        <line x1="190" y1="51" x2="184" y2="57" />
      </g>
      <circle cx="206" cy="35" r="14" fill="#F2C94C" />
      {/* bulut */}
      <g fill="#FFFFFF" stroke="#C9DCEE" strokeWidth="2">
        <ellipse cx="44" cy="26" rx="19" ry="10" />
        <ellipse cx="62" cy="23" rx="13" ry="8" />
      </g>
      {/* ağaç */}
      <rect x="40" y="94" width="9" height="36" rx="2" fill="#B07A45" />
      <circle cx="30" cy="96" r="13" fill="#69BE88" />
      <circle cx="58" cy="96" r="13" fill="#69BE88" />
      <circle cx="44" cy="86" r="22" fill="#5BAE7B" />
      {/* ev */}
      <rect x="150" y="98" width="62" height="44" rx="2" fill="#FCE6D6" stroke="#E0B79B" strokeWidth="2" />
      <path d="M144 99 L181 70 L218 99 Z" fill="#E76F3C" />
      <rect x="173" y="118" width="15" height="24" rx="1" fill="#B07A45" />
      <rect x="156" y="106" width="13" height="12" rx="1" fill="#DCEAF7" stroke="#9CC0E0" strokeWidth="1.5" />
      {/* çocuklar — el ele */}
      <line x1="106" y1="134" x2="116" y2="134" stroke="#F7CBA6" strokeWidth="3" strokeLinecap="round" />
      <g>
        <circle cx="96" cy="116" r="9" fill="#F7CBA6" stroke="#E0A982" strokeWidth="1.5" />
        <path d="M96 125 L84 146 L108 146 Z" fill="#2F80ED" />
        <line x1="91" y1="131" x2="81" y2="137" stroke="#F7CBA6" strokeWidth="3" strokeLinecap="round" />
        <line x1="101" y1="131" x2="110" y2="134" stroke="#F7CBA6" strokeWidth="3" strokeLinecap="round" />
      </g>
      <g>
        <circle cx="124" cy="116" r="9" fill="#F7CBA6" stroke="#E0A982" strokeWidth="1.5" />
        <path d="M124 125 L113 146 L135 146 Z" fill="#9B5DE5" />
        <line x1="119" y1="131" x2="110" y2="134" stroke="#F7CBA6" strokeWidth="3" strokeLinecap="round" />
        <line x1="129" y1="131" x2="139" y2="137" stroke="#F7CBA6" strokeWidth="3" strokeLinecap="round" />
      </g>
      {/* zemin */}
      <path d="M0 142 H240 V150 H0 Z" fill="#A8D5A2" />
    </svg>
  );
}

export function ThesisCollage() {
  return (
    <div className="relative mx-auto min-h-[430px] w-full max-w-[620px] lg:min-h-[500px]">
      <motion.div
        initial={{ opacity: 0, x: 32, scale: 0.96 }}
        animate={{ opacity: 1, x: 0, scale: 1 }}
        transition={{ duration: 0.6 }}
        className="absolute inset-0 overflow-hidden rounded-[32px] border border-line bg-surface/78 shadow-[0_24px_80px_-40px_rgba(52,31,17,0.08)] backdrop-blur"
      >
        {/* Grid paper texture */}
        <div
          className="absolute inset-0 opacity-[0.3]"
          style={{
            backgroundImage:
              'linear-gradient(#E9E1D7 1px, transparent 1px), linear-gradient(90deg, #E9E1D7 1px, transparent 1px)',
            backgroundSize: '24px 24px',
          }}
        />

        {/* Tez kapağı (Sol üst) */}
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.1 }}
          className="absolute left-5 top-6 z-30 w-[210px] rounded-[18px] border border-line bg-surface2 p-6 text-center shadow-[0_32px_64px_-40px_rgba(52,31,17,0.4)] sm:left-8 sm:top-8 sm:w-[230px]"
          style={{ transform: 'rotate(-3deg)' }}
        >
          <div className="text-[9px] font-bold uppercase tracking-[0.25em] text-[#E76F3C]">Lisans Tezi</div>
          <div className="mt-3 font-serif text-base font-semibold leading-snug text-ink sm:text-[17px]">
            ÇOCUK ÇİZİMLERİNDE AÇIKLANABİLİR DUYGU SINIFLANDIRMASI
          </div>
          <div className="mx-auto my-4 h-px w-12 bg-line" />
          <div className="text-[9px] font-semibold leading-relaxed tracking-wide text-ink">
            NİĞDE ÖMER HALİSDEMİR ÜNİVERSİTESİ
          </div>
          <div className="mt-1 text-[9px] text-muted">Bilgisayar Mühendisliği</div>
          <div className="mt-4 inline-flex rounded-md border border-[#F2C8B2] bg-tint px-2 py-0.5 text-[9px] font-bold text-[#E76F3C]">
            2024 - 2025
          </div>
        </motion.div>

        {/* Sistem akışı (Sağ üst) */}
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.16 }}
          className="absolute right-5 top-6 z-10 w-[240px] rounded-2xl border border-line bg-surface p-5 shadow-[0_20px_50px_-30px_rgba(52,31,17,0.2)] sm:right-8 sm:w-[280px] lg:right-10 lg:top-8 lg:w-[300px]"
          style={{ transform: 'rotate(1deg)' }}
        >
          <div className="mb-3 text-[10px] font-bold uppercase tracking-[0.25em] text-muted">Sistem Akışı</div>
          <div className="relative flex flex-col gap-2">
            <div className="absolute bottom-4 left-[13px] top-4 w-px bg-line" />
            {COLLAGE_FLOW.map((step, idx) => {
              const Icon = step.icon;
              return (
                <div key={idx} className="group relative z-10 flex flex-row items-center gap-3 bg-surface">
                  <span className="grid h-[28px] w-[28px] shrink-0 place-items-center rounded-full border border-[#F2C8B2] bg-tint text-[#E76F3C]">
                    <Icon size={14} />
                  </span>
                  <span className="text-[11px] font-semibold text-muted">{step.label}</span>
                </div>
              );
            })}
          </div>
        </motion.div>

        {/* Çocuk çizimi (Sol alt) */}
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.22 }}
          className="absolute bottom-6 left-5 z-20 w-[240px] rounded-2xl border border-line bg-surface p-3 pb-4 shadow-[0_28px_60px_-32px_rgba(52,31,17,0.3)] sm:bottom-8 sm:left-8 sm:w-[320px] lg:bottom-10 lg:w-[340px]"
          style={{ transform: 'rotate(2deg)' }}
        >
          <div className="overflow-hidden rounded-xl border border-line bg-surface2">
            <img
              src={sampleImages[0] || '/samples/happy_1.jpg'}
              alt="Çocuk Çizimi"
              className="h-[140px] w-full object-contain sm:h-[160px] lg:h-[190px]"
            />
          </div>
        </motion.div>

        {/* Metrik Pill'leri (Orta / Dağınık) */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.3 }}
          className="absolute bottom-36 right-6 z-20 flex hidden flex-col items-end gap-2.5 sm:flex sm:right-10 lg:right-14"
        >
          <div className="rounded-full border border-line bg-surface px-3.5 py-1.5 text-[10px] font-semibold text-ink shadow-sm">
            5.177 Çizim
          </div>
          <div className="relative right-4 rounded-full border border-line bg-surface px-3.5 py-1.5 text-[10px] font-semibold text-ink shadow-sm">
            0.834 Makro F1
          </div>
          <div className="rounded-full border border-line bg-surface px-3.5 py-1.5 text-[10px] font-semibold text-ink shadow-sm">
            16 Klinik Gösterge
          </div>
          <div className="rounded-full border border-[#F2C8B2] bg-tint px-3.5 py-1.5 text-[10px] font-bold text-[#E76F3C] shadow-sm">
            Grad-CAM + LLM
          </div>
        </motion.div>

        {/* TÜBİTAK notu (Sağ alt) */}
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.4, delay: 0.35 }}
          className="absolute bottom-6 right-5 z-40 w-[140px] rounded-lg border border-[#F2C8B2] bg-tint p-3.5 shadow-[0_16px_40px_-20px_rgba(231,111,60,0.3)] sm:bottom-8 sm:right-8"
          style={{ transform: 'rotate(4deg)' }}
        >
          <div className="text-[9px] font-bold uppercase tracking-[0.2em] text-[#E76F3C]/80">Destek</div>
          <div className="mt-1.5 flex items-center gap-2">
            <span className="grid h-6 w-6 place-items-center rounded-sm bg-[#0F4C81] text-white">
              <Landmark size={13} strokeWidth={2} />
            </span>
            <span className="font-serif text-[13px] font-bold leading-tight text-ink">TÜBİTAK 2209-A</span>
          </div>
        </motion.div>
      </motion.div>
    </div>
  );
}

// About hero görseli: tez/araştırma temalı kod-tabanlı kompozisyon (Grad-CAM ve metrik yok).
const ABOUT_CONCEPTS = [
  { icon: Gauge, label: 'Klinik Göstergeler' },
  { icon: Layers3, label: 'Kavram Darboğazı' },
  { icon: MessageSquareText, label: 'LLM Açıklama' },
];

export function ResearchHeroVisual() {
  return (
    <div className="relative mx-auto min-h-[440px] w-full max-w-[740px] sm:min-h-[490px] lg:min-h-[520px]">
      {/* kareli kâğıt zemin */}
      <div
        className="absolute inset-0 opacity-60"
        style={{
          backgroundImage:
            'linear-gradient(#E9E1D7 1px, transparent 1px), linear-gradient(90deg, #E9E1D7 1px, transparent 1px)',
          backgroundSize: '38px 38px',
          maskImage: 'radial-gradient(circle at 52% 46%, black, transparent 72%)',
          WebkitMaskImage: 'radial-gradient(circle at 52% 46%, black, transparent 72%)',
        }}
      />
      {/* dekoratif halkalar */}
      <div className="absolute -right-4 top-12 hidden h-[400px] w-[400px] rounded-full border border-[#E76F3C]/12 lg:block" />
      <div className="absolute right-10 top-24 hidden h-[300px] w-[300px] rounded-full border border-[#0F4C81]/10 lg:block" />
      {/* yumuşak sıcak ışık */}
      <div className="absolute left-1/2 top-1/2 h-52 w-[74%] -translate-x-1/2 -translate-y-1/2 rounded-full bg-[#F4D8C2]/35 blur-3xl" />

      {/* Akademik / tez rozeti */}
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, delay: 0.45 }}
        className="absolute left-0 top-10 z-20 hidden items-center gap-2.5 rounded-2xl border border-line bg-surface/95 px-3.5 py-2.5 shadow-[0_18px_44px_-30px_rgba(52,31,17,0.55)] backdrop-blur sm:flex"
      >
        <span className="grid h-9 w-9 shrink-0 place-items-center rounded-full bg-tint text-[#E76F3C] ring-1 ring-[#F2C8B2]">
          <GraduationCap size={17} strokeWidth={1.7} />
        </span>
        <div>
          <div className="text-[9px] font-bold uppercase tracking-[0.18em] text-[#E76F3C]">Lisans Tezi</div>
          <div className="text-sm font-semibold leading-tight text-ink">NÖHÜ · Bilgisayar Müh.</div>
        </div>
      </motion.div>

      {/* Ana kâğıt kart: çocuk çizimi (gerçek) */}
      <motion.div
        animate={{ y: [0, -8, 0] }}
        transition={{ duration: 7, repeat: Infinity, ease: 'easeInOut' }}
        className="absolute left-1/2 top-12 w-[86%] max-w-[520px] -translate-x-1/2 -rotate-3 rounded-2xl border border-line bg-surface p-3 shadow-[0_36px_84px_-46px_rgba(52,31,17,0.62)] lg:left-[49%]"
      >
        <div className="overflow-hidden rounded-xl border border-line bg-surface">
          <img src={sampleImages[0]} alt="Çocuk çizimi örneği" className="aspect-[1.45] w-full object-cover" />
          <div className="flex items-center gap-2 border-t border-line px-3 py-2 text-[11px] font-semibold text-muted">
            <Sparkles size={13} className="text-[#E76F3C]" strokeWidth={1.9} />
            Çocuk Çizimi · KIDO Veri Seti
          </div>
        </div>
      </motion.div>

      {/* TÜBİTAK destek rozeti */}
      <motion.div
        initial={{ opacity: 0, y: 14 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.55, delay: 0.5 }}
        className="absolute bottom-[88px] right-1 z-20 hidden items-center gap-2.5 rounded-2xl border border-[#F0E3B8] bg-gradient-to-br from-[#FFFBEC] to-[#FFF4D4] px-4 py-3 shadow-[0_22px_50px_-32px_rgba(52,31,17,0.6)] sm:flex"
      >
        <span className="grid h-9 w-9 shrink-0 place-items-center rounded-full bg-[#0F4C81] text-white">
          <Landmark size={16} strokeWidth={1.8} />
        </span>
        <div>
          <div className="text-[9px] font-bold uppercase tracking-[0.18em] text-[#9A7B1F] dark:text-[#D8B968]">Destek</div>
          <div className="font-serif text-[15px] font-semibold leading-tight text-ink">TÜBİTAK 2209-A</div>
        </div>
      </motion.div>

      {/* Kavram pill'leri (yüzde yok) */}
      <div className="absolute bottom-0 left-1/2 flex w-[94%] -translate-x-1/2 flex-wrap justify-center gap-2">
        {ABOUT_CONCEPTS.map((step, index) => {
          const Icon = step.icon;
          return (
            <motion.div
              key={step.label}
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.42, delay: 0.55 + index * 0.07 }}
              className="flex items-center gap-2 rounded-full border border-line bg-surface/90 px-3 py-2 text-xs font-semibold text-ink shadow-[0_14px_34px_-28px_rgba(52,31,17,0.6)] backdrop-blur"
            >
              <Icon size={14} className="shrink-0 text-[#E76F3C]" strokeWidth={1.8} />
              <span className="truncate">{step.label}</span>
            </motion.div>
          );
        })}
      </div>
    </div>
  );
}

export function ResultBadge() {
  return (
    <div className="inline-flex items-center gap-2 rounded-full bg-[#EAF6EF] px-4 py-2 text-sm font-semibold text-[#5BAE7B]">
      Tamamlandı
      <CheckCircle2 size={15} />
    </div>
  );
}
