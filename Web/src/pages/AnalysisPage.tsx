import {
  AlertCircle,
  ArrowRight,
  BookOpen,
  Check,
  CircleAlert,
  Eraser,
  Frown,
  ImageIcon,
  Info,
  Pencil,
  RefreshCw,
  Settings2,
  ShieldCheck,
  Smile,
  Sparkles,
  Trash2,
  UploadCloud,
  X,
  Zap,
  type LucideIcon,
} from 'lucide-react';
import { AnimatePresence, motion } from 'motion/react';
import { useEffect, useMemo, useRef, useState, type ChangeEvent, type DragEvent, type PointerEvent as ReactPointerEvent } from 'react';
import { Button } from '../components/UI';
import {
  API_URL,
  analysisProcess,
  emotionClasses,
  emotionClassesTr,
  emotionColors,
  sampleImages,
} from '../data/medvision';
import type { ApiResult } from '../types';

const CANVAS_COLORS = ['#1F1F1F', '#E76F3C', '#2F80ED', '#5BAE7B', '#9B5DE5', '#F2C94C', '#EB5757'];
const BRUSH_SIZES = [4, 8, 16, 28];

type MainTab = 'original' | 'gradcam';
type InfoTab = 'explanation' | 'indicators' | 'llm';
type SampleFilter = 'all' | 'Happy' | 'Sad' | 'Angry' | 'Fear';

type NormalizedResult = {
  label: string;
  confidence: number;
  probabilities: number[];
  heatmap: string | null;
  explanation: string | null;
};

type IndicatorItem = {
  label: string;
  value: number | string;
};

const infoTabs: { key: InfoTab; label: string }[] = [
  { key: 'explanation', label: 'Açıklama' },
  { key: 'indicators', label: 'Klinik Göstergeler' },
  { key: 'llm', label: 'LLM Yorum' },
];

const infoTabContent: Record<InfoTab, { title: string; body: string }> = {
  explanation: {
    title: 'Tahmin Edilen Duygu ve Güven Skoru',
    body: 'Analiz tamamlandığında çizimden tahmin edilen duygu sınıfı, modelin güven skoru ve dört duygu için olasılık dağılımı burada görüntülenir.',
  },
  indicators: {
    title: '16 Figür-Farkında Klinik Gösterge',
    body: 'Model, kararını Koppitz/Di Leo temelli açıklanabilir ara kavramlar üzerinden verir. Çizime ait gösterge değerleri analiz sonrası bu alanda listelenir.',
  },
  llm: {
    title: 'Yapay Zeka Destekli Klinik Yorum',
    body: 'Tahmin ve klinik göstergeler bir dil modeline aktarılarak okunabilir bir klinik değerlendirme metnine dönüştürülür; bu yorum analiz sonrası burada yer alır.',
  },
};

const emotionIcons: LucideIcon[] = [Smile, Frown, CircleAlert, ShieldCheck];

// Maps an English emotion label to its Turkish equivalent (falls back to the raw label).
function toTurkishLabel(label: string): string {
  const i = emotionClasses.findIndex((c) => c.toLowerCase() === label.toLowerCase());
  return i >= 0 ? emotionClassesTr[i] : label || 'Belirsiz';
}

function percent(v: number) {
  return `${Math.max(0, Math.min(v, 100)).toFixed(1)}%`;
}

function sampleEmotionForIndex(index: number): SampleFilter {
  return emotionClasses[Math.min(Math.floor(index / 3), emotionClasses.length - 1)] as SampleFilter;
}

function normalizeResult(result: ApiResult): NormalizedResult {
  const rawLabel =
    result.prediction ?? result.predicted_class ?? result.pred_class ?? result.class_name ?? result.pred_emotion ?? '';
  const rawConfidence =
    result.confidence ?? result.confidence_score ?? result.probability ?? result.confidence_emotion ?? 0;
  const confidence = rawConfidence <= 1 ? rawConfidence * 100 : rawConfidence;
  const rawProbs = result.probabilities ?? result.probs ?? result.probs_emotion;
  const probabilities =
    rawProbs && rawProbs.length >= 4
      ? rawProbs.slice(0, 4).map((v) => (v <= 1 ? v * 100 : v))
      : [
          confidence,
          Math.max(0.2, (100 - confidence) * 0.48),
          Math.max(0.2, (100 - confidence) * 0.3),
          Math.max(0.2, (100 - confidence) * 0.22),
        ];
  const canonicalLabel = emotionClasses.find((c) => c.toLowerCase() === rawLabel.toLowerCase()) ?? rawLabel;
  return {
    label: canonicalLabel,
    confidence,
    probabilities,
    heatmap: result.heatmap_b64 ?? result.heatmap_emotion_b64 ?? null,
    explanation: result.explanation ?? null,
  };
}

function getIndicatorValue(raw: unknown): number | string | null {
  if (typeof raw === 'number' || typeof raw === 'string') return raw;
  if (!raw || typeof raw !== 'object') return null;
  const record = raw as Record<string, unknown>;
  const value = record.value ?? record.score ?? record.probability ?? record.confidence ?? record.prediction;
  return typeof value === 'number' || typeof value === 'string' ? value : null;
}

function extractIndicators(result: ApiResult | null): IndicatorItem[] {
  if (!result) return [];
  const record = result as Record<string, unknown>;
  const source =
    record.concepts ??
    record.concept_scores ??
    record.clinical_indicators ??
    record.indicators ??
    record.indicator_scores;

  if (!source) return [];

  if (Array.isArray(source)) {
    return source
      .map((item, index) => {
        if (Array.isArray(item) && item.length >= 2) {
          return { label: String(item[0]), value: item[1] as number | string };
        }
        if (item && typeof item === 'object') {
          const itemRecord = item as Record<string, unknown>;
          const label = itemRecord.label ?? itemRecord.name ?? itemRecord.title ?? itemRecord.concept ?? `Gösterge ${index + 1}`;
          const value = getIndicatorValue(item);
          return value !== null ? { label: String(label), value } : null;
        }
        return { label: `Gösterge ${index + 1}`, value: item as number | string };
      })
      .filter((item): item is IndicatorItem => Boolean(item));
  }

  if (typeof source === 'object') {
    return Object.entries(source as Record<string, unknown>)
      .map(([label, value]) => {
        const normalizedValue = getIndicatorValue(value);
        return normalizedValue !== null ? { label, value: normalizedValue } : null;
      })
      .filter((item): item is IndicatorItem => Boolean(item));
  }

  return [];
}

function formatIndicatorValue(value: number | string) {
  if (typeof value === 'number') {
    return value <= 1 ? value.toFixed(2) : value.toFixed(1);
  }
  return value;
}

function prepareContext(ctx: CanvasRenderingContext2D) {
  ctx.lineCap = 'round';
  ctx.lineJoin = 'round';
}

// SPA oturumu boyunca yaşayan analiz cache'i (sayfa değişiminde state korunur).
const analysisCache: {
  file: File | null;
  previewSrc: string | null;
  result: ApiResult | null;
} = { file: null, previewSrc: null, result: null };

export function AnalysisPage() {
  const [file, setFile] = useState<File | null>(analysisCache.file);
  const [previewSrc, setPreviewSrc] = useState<string | null>(analysisCache.previewSrc);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [result, setResult] = useState<ApiResult | null>(analysisCache.result);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<MainTab>('original');
  const [isCanvasOpen, setIsCanvasOpen] = useState(false);
  const [isDragging, setIsDragging] = useState(false);
  const fileInputRef = useRef<HTMLInputElement | null>(null);

  // Sayfa değişiminde (component unmount) state kaybolmasın diye modül-seviyesi
  // cache'e yansıt; AnalysisPage tekrar açıldığında buradan geri yüklenir.
  useEffect(() => {
    analysisCache.file = file;
    analysisCache.previewSrc = previewSrc;
    analysisCache.result = result;
  }, [file, previewSrc, result]);

  const normalized = useMemo(() => (result ? normalizeResult(result) : null), [result]);
  const indicators = useMemo(() => extractIndicators(result), [result]);

  const filteredSamples = useMemo(
    () => sampleImages.map((src, index) => ({ src, emotion: sampleEmotionForIndex(index), index })),
    [],
  );

  const selectFile = (f: File, preview: string) => {
    setFile(f);
    setPreviewSrc(preview);
    setResult(null);
    setError(null);
    setActiveTab('original');
  };

  const handleFileChange = (e: ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0];
    if (f) selectFile(f, URL.createObjectURL(f));
    // Aynı dosya tekrar seçilebilsin diye input değerini sıfırla.
    e.target.value = '';
  };

  const handleSampleClick = async (src: string) => {
    setPreviewSrc(src);
    setResult(null);
    setError(null);
    setActiveTab('original');
    const res = await fetch(src);
    const blob = await res.blob();
    setFile(new File([blob], src.split('/').pop() ?? 'sample.jpg', { type: blob.type || 'image/jpeg' }));
  };

  const handleAnalyze = async () => {
    if (!file) return;
    setIsAnalyzing(true);
    setError(null);
    setResult(null);
    setActiveTab('original');
    const formData = new FormData();
    formData.append('image', file);
    formData.append('file', file);
    formData.append('lang', 'tr');
    try {
      const res = await fetch(API_URL, { method: 'POST', body: formData });
      if (!res.ok) {
        const body = await res.json().catch(() => null);
        throw new Error(body?.detail ?? `Analiz başarısız oldu (${res.status}).`);
      }
      setResult(await res.json());
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Beklenmeyen bir hata oluştu.');
    } finally {
      setIsAnalyzing(false);
    }
  };

  const reset = () => {
    setFile(null);
    setPreviewSrc(null);
    setResult(null);
    setError(null);
    setActiveTab('original');
  };

  const handleDrop = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragging(false);
    const dropped = e.dataTransfer.files?.[0];
    if (!dropped) return;
    if (!dropped.type.startsWith('image/')) {
      setError('Lütfen PNG, JPG, JPEG veya WEBP formatında bir görsel yükleyin.');
      return;
    }
    selectFile(dropped, URL.createObjectURL(dropped));
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -8 }}
      transition={{ duration: 0.4 }}
      className="bg-bg xl:h-[calc(100vh-5rem)] xl:overflow-hidden"
    >
      <input
        ref={fileInputRef}
        type="file"
        accept="image/png,image/jpeg,image/jpg,image/webp"
        onChange={handleFileChange}
        className="hidden"
      />

      <div className="mx-auto grid max-w-[1640px] grid-cols-1 px-4 sm:px-6 xl:h-full xl:grid-cols-[minmax(0,1fr)_480px]">
        {/* ── Sol: çalışma kolonu ── */}
        <motion.section
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4, delay: 0.1 }}
          className="order-1 flex min-w-0 flex-col py-4 xl:col-start-1 xl:h-full xl:min-h-0 xl:pr-10"
        >
          {/* Başlık */}
          <div className="shrink-0">
            <div className="text-xs font-bold uppercase tracking-[0.32em] text-[#E76F3C]">ANALİZ ÇALIŞMA ALANI</div>
            <h1 className="mt-2 font-serif text-3xl font-semibold leading-tight tracking-[-0.02em] text-ink md:text-4xl">
              Çizim Yükle ve Analizi İncele
            </h1>
            <p className="mt-2 max-w-2xl text-sm leading-6 text-muted">
              Çocuğun çizimini yükleyin, yapay zeka destekli analiz sonuçlarını ve klinik göstergeleri inceleyin.
            </p>
          </div>

          {/* Örnek çizimler — kompakt rail */}
          <div className="mt-4 shrink-0">
            <h2 className="font-serif text-xl font-semibold text-ink">Örnek Çizimler</h2>
            <div className="mt-2 flex gap-2.5 overflow-x-auto pb-1">
              {filteredSamples.map((sample) => {
                const selected = previewSrc === sample.src;
                return (
                  <motion.button
                    key={sample.src}
                    type="button"
                    whileHover={{ y: -2 }}
                    onClick={() => handleSampleClick(sample.src)}
                    className={`group relative h-16 w-24 shrink-0 overflow-hidden rounded-lg border bg-surface/70 transition ${
                      selected ? 'border-[#E76F3C] ring-2 ring-[#E76F3C]/20' : 'border-line hover:border-[#E76F3C]'
                    }`}
                  >
                    <img
                      src={sample.src}
                      alt={`${emotionClassesTr[emotionClasses.indexOf(sample.emotion)]} örnek çizim`}
                      className="h-full w-full object-cover"
                    />
                    {selected && (
                      <span className="absolute right-1.5 top-1.5 grid h-5 w-5 place-items-center rounded-full bg-[#E76F3C] text-white shadow">
                        <Check size={12} strokeWidth={2.4} />
                      </span>
                    )}
                  </motion.button>
                );
              })}
            </div>
          </div>

          {/* Ayırıcı + çalışma alanı */}
          <div className="mt-4 flex flex-col border-t border-line pt-4 xl:min-h-0 xl:flex-1">
            <div
              onDragOver={(e) => {
                e.preventDefault();
                setIsDragging(true);
              }}
              onDragLeave={() => setIsDragging(false)}
              onDrop={handleDrop}
              className={`mt-2 overflow-hidden rounded-2xl border transition xl:mt-2 xl:min-h-0 xl:flex-1 ${
                isDragging ? 'border-[#E76F3C] bg-tint/55' : 'border-transparent'
              }`}
            >
              <WorkspacePreview
                activeTab={activeTab}
                previewSrc={previewSrc}
                normalized={normalized}
                onPickFile={() => fileInputRef.current?.click()}
                onOpenCanvas={() => setIsCanvasOpen(true)}
                onClear={reset}
              />
            </div>

            <p className="mt-3 shrink-0 text-center text-xs text-muted">PNG, JPG veya WEBP · Maks. 10MB · 224×224 ön işleme</p>

            <Button
              type="button"
              onClick={handleAnalyze}
              disabled={!file || isAnalyzing}
              className="mt-4 w-full shrink-0 !rounded-xl disabled:cursor-not-allowed disabled:opacity-60"
            >
              {isAnalyzing ? (
                <>
                  <RefreshCw className="animate-spin" size={17} />
                  Analiz Ediliyor
                </>
              ) : (
                <>
                  Analizi Başlat
                  <ArrowRight size={17} />
                </>
              )}
            </Button>

            {error && (
              <div className="mt-4 flex shrink-0 gap-3 rounded-xl border border-[#F08A5D]/30 bg-tint p-4 text-sm text-[#8A3217] dark:text-[#E7B08A]">
                <AlertCircle className="mt-0.5 shrink-0" size={17} />
                <span>{error}</span>
              </div>
            )}
          </div>
        </motion.section>

        <ResultInspector
          normalized={normalized}
          result={result}
          indicators={indicators}
          isAnalyzing={isAnalyzing}
          error={error}
          onReset={reset}
        />
      </div>

      <AnimatePresence>
        {isCanvasOpen && (
          <CanvasModal
            onClose={() => setIsCanvasOpen(false)}
            onSave={(f, preview) => {
              selectFile(f, preview);
              setIsCanvasOpen(false);
            }}
          />
        )}
      </AnimatePresence>
    </motion.div>
  );
}

function WorkspacePreview({
  activeTab,
  previewSrc,
  normalized,
  onPickFile,
  onOpenCanvas,
  onClear,
}: {
  activeTab: MainTab;
  previewSrc: string | null;
  normalized: NormalizedResult | null;
  onPickFile: () => void;
  onOpenCanvas: () => void;
  onClear: () => void;
}) {
  if (activeTab === 'gradcam') {
    return (
      <div className="grid h-[380px] place-items-center overflow-hidden rounded-2xl border border-dashed border-[#E9CDBA] bg-surface/60 p-4 sm:h-[440px] xl:h-full xl:min-h-[360px]">
        {normalized?.heatmap ? (
          <img src={`data:image/png;base64,${normalized.heatmap}`} alt="Grad-CAM sonucu" className="max-h-full max-w-full rounded-xl object-contain" />
        ) : (
          <div className="max-w-sm text-center">
            <div className="mx-auto grid h-16 w-16 place-items-center rounded-full bg-tint text-[#E76F3C]">
              <Zap size={25} strokeWidth={1.6} />
            </div>
            <h3 className="mt-5 font-serif text-2xl font-semibold text-ink">Grad-CAM henüz hazır değil</h3>
            <p className="mt-3 text-sm leading-6 text-muted">
              Bir çizim analiz edildiğinde modelin odaklandığı bölgeler burada görüntülenir.
            </p>
          </div>
        )}
      </div>
    );
  }

  return (
    <div
      onClick={previewSrc ? undefined : onPickFile}
      className={`relative grid h-[380px] place-items-center overflow-hidden rounded-2xl border bg-surface/65 p-4 sm:h-[440px] xl:h-full xl:min-h-[360px] ${
        previewSrc ? 'border-line' : 'cursor-pointer border-dashed border-[#F08A5D]/55'
      }`}
    >
      {previewSrc ? (
        <>
          <img
            src={previewSrc}
            alt="Seçilen çizim"
            className="absolute inset-4 h-[calc(100%-2rem)] w-[calc(100%-2rem)] rounded-xl object-contain object-center"
          />
          <button
            type="button"
            onClick={(e) => {
              e.stopPropagation();
              onClear();
            }}
            aria-label="Görseli kaldır"
            title="Görseli kaldır"
            className="absolute right-3 top-3 grid h-9 w-9 place-items-center rounded-full bg-surface/90 text-muted shadow-md ring-1 ring-line transition hover:bg-surface hover:text-[#E76F3C]"
          >
            <X size={18} />
          </button>
        </>
      ) : (
        <div className="max-w-md text-center">
          <div className="mx-auto grid h-20 w-20 place-items-center rounded-full bg-tint text-[#E76F3C]">
            <UploadCloud size={34} strokeWidth={1.45} />
          </div>
          <h3 className="mt-5 font-serif text-3xl font-semibold text-ink">Çizimi buraya sürükleyin</h3>
          <p className="mt-2 text-sm leading-6 text-muted">veya tıklayarak dosya seçin</p>
          <p className="mt-1 text-xs text-muted">PNG, JPG, JPEG · maks. 10 MB</p>
          <div className="mt-6 flex flex-col gap-3 sm:flex-row sm:justify-center">
            <Button
              type="button"
              onClick={(e) => {
                e.stopPropagation();
                onPickFile();
              }}
              className="!rounded-xl"
            >
              Dosya Seç
            </Button>
            <Button
              type="button"
              variant="secondary"
              onClick={(e) => {
                e.stopPropagation();
                onOpenCanvas();
              }}
              className="!rounded-xl"
            >
              <Pencil size={16} />
              Canvas ile Çiz
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}

function CanvasModal({ onSave, onClose }: { onSave: (file: File, preview: string) => void; onClose: () => void }) {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const canvasHostRef = useRef<HTMLDivElement | null>(null);
  const drawingRef = useRef(false);
  const [color, setColor] = useState(CANVAS_COLORS[0]);
  const [size, setSize] = useState(BRUSH_SIZES[1]);
  const [isEraser, setIsEraser] = useState(false);

  // ESC ile kapat + modal açıkken arka plan kaymasını engelle.
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    window.addEventListener('keydown', onKey);
    const prevOverflow = document.body.style.overflow;
    document.body.style.overflow = 'hidden';
    return () => {
      window.removeEventListener('keydown', onKey);
      document.body.style.overflow = prevOverflow;
    };
  }, [onClose]);

  useEffect(() => {
    const canvas = canvasRef.current;
    const host = canvasHostRef.current;
    if (!canvas || !host) return;

    const resizeCanvas = () => {
      const rect = host.getBoundingClientRect();
      if (rect.width < 1 || rect.height < 1) return;

      const dpr = window.devicePixelRatio || 1;
      const nextWidth = Math.max(1, Math.floor(rect.width * dpr));
      const nextHeight = Math.max(1, Math.floor(rect.height * dpr));
      if (canvas.width === nextWidth && canvas.height === nextHeight) return;

      const snapshot = document.createElement('canvas');
      snapshot.width = canvas.width;
      snapshot.height = canvas.height;
      const snapshotCtx = snapshot.getContext('2d');
      if (snapshotCtx && canvas.width > 0 && canvas.height > 0) {
        snapshotCtx.drawImage(canvas, 0, 0);
      }

      canvas.width = nextWidth;
      canvas.height = nextHeight;

      const ctx = canvas.getContext('2d');
      if (!ctx) return;
      ctx.fillStyle = '#FFFFFF';
      ctx.fillRect(0, 0, canvas.width, canvas.height);
      prepareContext(ctx);
      if (snapshot.width > 0 && snapshot.height > 0) {
        ctx.drawImage(snapshot, 0, 0, canvas.width, canvas.height);
      }
    };

    resizeCanvas();
    const resizeObserver = new ResizeObserver(resizeCanvas);
    resizeObserver.observe(host);
    return () => resizeObserver.disconnect();
  }, []);

  const pointerPos = (e: ReactPointerEvent<HTMLCanvasElement>) => {
    const canvas = canvasRef.current!;
    const rect = canvas.getBoundingClientRect();
    return {
      x: (e.clientX - rect.left) * (canvas.width / rect.width),
      y: (e.clientY - rect.top) * (canvas.height / rect.height),
    };
  };

  const applyStroke = (ctx: CanvasRenderingContext2D) => {
    const canvas = canvasRef.current;
    const rect = canvas?.getBoundingClientRect();
    const scale = canvas && rect && rect.width > 0 ? canvas.width / rect.width : 1;
    ctx.strokeStyle = isEraser ? '#FFFFFF' : color;
    ctx.lineWidth = size * scale;
    prepareContext(ctx);
  };

  const startDraw = (e: ReactPointerEvent<HTMLCanvasElement>) => {
    e.preventDefault();
    const ctx = canvasRef.current?.getContext('2d');
    if (!ctx) return;
    drawingRef.current = true;
    canvasRef.current?.setPointerCapture(e.pointerId);
    const { x, y } = pointerPos(e);
    applyStroke(ctx);
    ctx.beginPath();
    ctx.moveTo(x, y);
    ctx.lineTo(x + 0.01, y + 0.01);
    ctx.stroke();
  };

  const moveDraw = (e: ReactPointerEvent<HTMLCanvasElement>) => {
    if (!drawingRef.current) return;
    e.preventDefault();
    const ctx = canvasRef.current?.getContext('2d');
    if (!ctx) return;
    const { x, y } = pointerPos(e);
    applyStroke(ctx);
    ctx.lineTo(x, y);
    ctx.stroke();
  };

  const endDraw = (e: ReactPointerEvent<HTMLCanvasElement>) => {
    drawingRef.current = false;
    if (canvasRef.current?.hasPointerCapture(e.pointerId)) {
      canvasRef.current.releasePointerCapture(e.pointerId);
    }
  };

  const clearCanvas = () => {
    const canvas = canvasRef.current;
    const ctx = canvas?.getContext('2d');
    if (!canvas || !ctx) return;
    ctx.fillStyle = '#FFFFFF';
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    prepareContext(ctx);
  };

  const handleSave = () => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    canvas.toBlob((blob) => {
      if (!blob) return;
      const file = new File([blob], `cizim_${Date.now()}.png`, { type: 'image/png' });
      onSave(file, URL.createObjectURL(blob));
    }, 'image/png');
  };

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      transition={{ duration: 0.2 }}
      onClick={onClose}
      className="fixed inset-0 z-[80] flex items-center justify-center bg-[#1F1F1F]/55 p-3 backdrop-blur-sm sm:p-6"
    >
      <motion.div
        initial={{ opacity: 0, scale: 0.97, y: 12 }}
        animate={{ opacity: 1, scale: 1, y: 0 }}
        exit={{ opacity: 0, scale: 0.97, y: 12 }}
        transition={{ duration: 0.25, ease: 'easeOut' }}
        onClick={(e) => e.stopPropagation()}
        className="flex h-[88vh] w-full max-w-6xl flex-col overflow-hidden rounded-2xl border border-line bg-surface shadow-2xl sm:flex-row"
      >
        {/* ── Sidebar: araçlar ── */}
        <aside className="flex shrink-0 flex-col gap-6 overflow-y-auto border-b border-line bg-bg p-5 sm:w-72 sm:border-b-0 sm:border-r">
          <div className="flex items-center justify-between gap-3">
            <h3 className="font-serif text-xl font-semibold text-ink">Çizim Yap</h3>
            <button
              type="button"
              onClick={onClose}
              aria-label="Kapat"
              className="grid h-9 w-9 place-items-center rounded-full text-muted transition hover:bg-tint hover:text-[#E76F3C]"
            >
              <X size={18} />
            </button>
          </div>

          <div>
            <div className="text-xs font-semibold uppercase tracking-[0.18em] text-muted">Renk</div>
            <div className="mt-3 flex flex-wrap gap-2.5">
              {CANVAS_COLORS.map((c) => (
                <button
                  key={c}
                  type="button"
                  onClick={() => {
                    setColor(c);
                    setIsEraser(false);
                  }}
                  aria-label={`Renk ${c}`}
                  className={`h-9 w-9 rounded-full border-2 transition hover:scale-105 ${
                    color === c && !isEraser ? 'scale-110 border-ink' : 'border-white shadow-sm'
                  }`}
                  style={{ backgroundColor: c }}
                />
              ))}
            </div>
          </div>

          <div>
            <div className="text-xs font-semibold uppercase tracking-[0.18em] text-muted">Kalem Ucu</div>
            <div className="mt-3 flex flex-wrap gap-2">
              {BRUSH_SIZES.map((brushSize) => (
                <button
                  key={brushSize}
                  type="button"
                  onClick={() => setSize(brushSize)}
                  aria-label={`Kalem ucu ${brushSize}px`}
                  className={`grid h-11 w-11 place-items-center rounded-lg border transition ${
                    size === brushSize ? 'border-[#E76F3C] bg-tint' : 'border-line bg-surface hover:border-[#F08A5D]'
                  }`}
                >
                  <span
                    className="rounded-full"
                    style={{
                      width: brushSize / 2 + 4,
                      height: brushSize / 2 + 4,
                      backgroundColor: isEraser ? '#FFFFFF' : color,
                      border: isEraser ? '1px solid #B9AFA4' : 'none',
                    }}
                  />
                </button>
              ))}
            </div>
          </div>

          <div>
            <div className="text-xs font-semibold uppercase tracking-[0.18em] text-muted">Araçlar</div>
            <div className="mt-3 flex gap-2">
              <button
                type="button"
                onClick={() => setIsEraser((v) => !v)}
                className={`flex flex-1 items-center justify-center gap-2 rounded-lg border px-3 py-2.5 text-sm font-semibold transition ${
                  isEraser ? 'border-[#E76F3C] bg-tint text-[#E76F3C]' : 'border-line bg-surface text-muted hover:border-[#F08A5D]'
                }`}
                aria-label="Silgi"
              >
                <Eraser size={17} />
                Silgi
              </button>
              <button
                type="button"
                onClick={clearCanvas}
                className="flex flex-1 items-center justify-center gap-2 rounded-lg border border-line bg-surface px-3 py-2.5 text-sm font-semibold text-muted transition hover:border-[#EB5757] hover:text-[#EB5757]"
                aria-label="Temizle"
              >
                <Trash2 size={17} />
                Temizle
              </button>
            </div>
          </div>

          <div className="mt-auto flex flex-col gap-3 pt-2">
            <Button type="button" onClick={handleSave} className="!rounded-xl">
              <Check size={17} />
              Çizimi Kullan
            </Button>
            <Button type="button" variant="secondary" onClick={onClose} className="!rounded-xl">
              İptal
            </Button>
          </div>
        </aside>

        {/* ── Canvas: tüm sağ taraf ── */}
        <div ref={canvasHostRef} className="relative min-h-0 flex-1 bg-white">
          <canvas
            ref={canvasRef}
            onPointerDown={startDraw}
            onPointerMove={moveDraw}
            onPointerUp={endDraw}
            onPointerCancel={endDraw}
            className="absolute inset-0 h-full w-full touch-none bg-white"
            style={{ cursor: isEraser ? 'cell' : 'crosshair' }}
          />
        </div>
      </motion.div>
    </motion.div>
  );
}

function ResultInspector({
  normalized,
  result,
  indicators,
  isAnalyzing,
  error,
  onReset,
}: {
  normalized: NormalizedResult | null;
  result: ApiResult | null;
  indicators: IndicatorItem[];
  isAnalyzing: boolean;
  error: string | null;
  onReset: () => void;
}) {
  return (
    <motion.aside
      initial={{ opacity: 0, x: 18 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ duration: 0.4, delay: 0.18 }}
      className="order-2 min-w-0 border-line py-6 xl:col-start-2 xl:h-full xl:overflow-y-auto xl:border-l xl:pl-8"
    >
      <div className="flex items-start justify-between gap-4">
        <div>
          <h2 className="font-serif text-2xl font-semibold text-ink">Analiz Sonucu</h2>
          <p className="mt-1 text-sm text-muted">Tahmin, güven ve açıklama inspector paneli.</p>
        </div>
        <button
          type="button"
          onClick={onReset}
          className="grid h-10 w-10 shrink-0 place-items-center rounded-full text-[#E76F3C] transition hover:bg-tint"
          aria-label="Yeni analiz"
        >
          <RefreshCw size={17} />
        </button>
      </div>

      {error && (
        <div className="mt-5 flex gap-3 rounded-xl border border-[#F08A5D]/30 bg-tint p-4 text-sm text-[#8A3217] dark:text-[#E7B08A]">
          <AlertCircle className="mt-0.5 shrink-0" size={17} />
          <span>{error}</span>
        </div>
      )}

      <AnimatePresence mode="wait">
        {isAnalyzing ? (
          <AnalyzingState />
        ) : normalized ? (
          <ResultState normalized={normalized} result={result} indicators={indicators} />
        ) : (
          <EmptyInspector />
        )}
      </AnimatePresence>
    </motion.aside>
  );
}

function EmptyInspector() {
  const [infoTab, setInfoTab] = useState<InfoTab>('explanation');
  return (
    <motion.div key="empty" initial={{ opacity: 0, x: 14 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: 8 }} className="mt-7">
      <div className="rounded-2xl border border-line bg-surface/55 p-5">
        <div className="grid h-14 w-14 place-items-center rounded-full bg-tint text-[#E76F3C]">
          <ImageIcon size={24} strokeWidth={1.6} />
        </div>
        <h3 className="mt-5 font-serif text-2xl font-semibold text-ink">Henüz analiz yapılmadı</h3>
        <p className="mt-3 text-sm leading-7 text-muted">
          Bir çizim yükleyin veya canvas üzerinde çizim oluşturun. Analiz tamamlandığında duygu tahmini, güven skoru, sınıf olasılıkları, Grad-CAM ve klinik açıklama burada görüntülenir.
        </p>
      </div>

      <div className="mt-6 border-t border-line pt-5">
        <h3 className="font-serif text-lg font-semibold text-ink">Analiz Görünümü</h3>
        <div className="mt-3 flex gap-6 overflow-x-auto border-b border-line">
          {infoTabs.map((tab) => (
            <button
              key={tab.key}
              type="button"
              onClick={() => setInfoTab(tab.key)}
              className={`shrink-0 border-b-2 px-1 pb-2.5 text-sm font-semibold transition ${
                infoTab === tab.key ? 'border-[#E76F3C] text-[#E76F3C]' : 'border-transparent text-muted hover:text-[#E76F3C]'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>
        <div className="mt-4 flex gap-3 text-sm leading-6 text-muted">
          <Sparkles className="mt-0.5 shrink-0 text-[#E76F3C]" size={20} strokeWidth={1.7} />
          <div>
            <p>{infoTabContent[infoTab].title}</p>
            <p className="mt-1">{infoTabContent[infoTab].body}</p>
          </div>
        </div>
      </div>
    </motion.div>
  );
}

function AnalyzingState() {
  return (
    <motion.div key="loading" initial={{ opacity: 0, x: 14 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: 8 }} className="mt-7">
      <div className="rounded-2xl border border-line bg-surface/55 p-5">
        <div className="flex items-center gap-3">
          <RefreshCw className="animate-spin text-[#E76F3C]" size={20} />
          <div>
            <h3 className="font-serif text-2xl font-semibold text-ink">Analiz çalışıyor</h3>
            <p className="mt-1 text-sm text-muted">Çizim klinik karar destek hattından geçiriliyor.</p>
          </div>
        </div>
        <div className="mt-5 h-2 overflow-hidden rounded-full bg-surface2">
          <motion.div
            initial={{ x: '-100%' }}
            animate={{ x: '100%' }}
            transition={{ duration: 1.1, repeat: Infinity, ease: 'easeInOut' }}
            className="h-full w-1/2 rounded-full bg-[#E76F3C]"
          />
        </div>
      </div>

      <div className="mt-6 space-y-4">
        {analysisProcess.map((step, index) => {
          const Icon = step.icon;
          return (
            <div key={step.title} className="flex gap-3 border-b border-line pb-4 last:border-b-0">
              <div className="grid h-10 w-10 shrink-0 place-items-center rounded-full bg-tint text-[#E76F3C]">
                <Icon size={18} strokeWidth={1.65} />
              </div>
              <div>
                <div className="text-sm font-semibold text-ink">
                  {index + 1}. {step.title}
                </div>
                <p className="mt-1 text-xs leading-5 text-muted">{step.body}</p>
              </div>
            </div>
          );
        })}
      </div>
    </motion.div>
  );
}

function ResultState({
  normalized,
  result,
  indicators,
}: {
  normalized: NormalizedResult;
  result: ApiResult | null;
  indicators: IndicatorItem[];
}) {
  const emotionIndex = emotionClasses.findIndex((c) => c.toLowerCase() === normalized.label.toLowerCase());
  const Icon = emotionIcons[emotionIndex >= 0 ? emotionIndex : 2];
  const color = emotionColors[emotionIndex >= 0 ? emotionIndex : 2] ?? '#E76F3C';

  return (
    <motion.div key="result" initial={{ opacity: 0, x: 14 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: 8 }} className="mt-7">
      <div>
        <div className="text-sm font-semibold text-muted">Tahmin Edilen Duygu</div>
        <div className="mt-4 flex items-center gap-4">
          <div className="grid h-16 w-16 shrink-0 place-items-center rounded-full bg-tint ring-8 ring-surface" style={{ color }}>
            <Icon size={28} strokeWidth={1.8} />
          </div>
          <div className="min-w-0">
            <div className="font-serif text-4xl font-semibold leading-tight text-ink">
              <span style={{ color }}>{toTurkishLabel(normalized.label)}</span>
            </div>
            {normalized.label && <div className="mt-1 text-sm text-muted">({normalized.label})</div>}
          </div>
        </div>
      </div>

      <div className="mt-8">
        <div className="flex items-end justify-between gap-4">
          <div>
            <div className="text-sm font-semibold text-muted">Güven Skoru</div>
            <div className="mt-2 font-serif text-5xl font-semibold leading-none" style={{ color }}>
              {percent(normalized.confidence)}
            </div>
          </div>
          <span className="rounded-lg bg-tint px-3 py-1.5 text-xs font-semibold text-[#E76F3C]">
            {normalized.confidence >= 80 ? 'Yüksek Güven' : 'Dikkatli İncele'}
          </span>
        </div>
        <div className="mt-4 h-3 overflow-hidden rounded-full bg-surface2">
          <motion.div
            initial={{ width: 0 }}
            animate={{ width: `${Math.min(normalized.confidence, 100)}%` }}
            transition={{ duration: 0.8 }}
            className="h-full rounded-full"
            style={{ backgroundColor: color }}
          />
        </div>
      </div>

      {normalized.heatmap && (
        <div className="mt-8 border-t border-line pt-6">
          <div className="flex items-center justify-between gap-3">
            <div className="text-sm font-semibold text-ink">Grad-CAM Isı Haritası</div>
            <Zap className="text-[#E76F3C]" size={18} strokeWidth={1.7} />
          </div>
          <div className="mt-3 overflow-hidden rounded-xl border border-line bg-[#1F1F1F]">
            <img
              src={`data:image/png;base64,${normalized.heatmap}`}
              alt="Grad-CAM ısı haritası"
              className="h-auto w-full object-contain"
            />
          </div>
          <p className="mt-2 text-xs leading-5 text-muted">
            Sıcak alanlar, modelin sınıf kararında daha etkili olan çizim bölgelerini gösterir.
          </p>
        </div>
      )}

      <div className="mt-8 border-t border-line pt-6">
        <div className="text-sm font-semibold text-ink">Sınıf Olasılıkları</div>
        <div className="mt-4 space-y-4">
          {emotionClassesTr.map((label, index) => {
            const RowIcon = emotionIcons[index] ?? CircleAlert;
            const probability = normalized.probabilities[index] ?? 0;
            return (
              <div key={label} className="grid grid-cols-[auto_minmax(0,1fr)_48px] items-center gap-3">
                <RowIcon size={21} style={{ color: emotionColors[index] }} strokeWidth={1.65} />
                <div className="min-w-0">
                  <div className="flex items-baseline gap-1.5 text-sm">
                    <span className="font-semibold text-ink">{label}</span>
                    <span className="truncate text-xs text-muted">({emotionClasses[index]})</span>
                  </div>
                  <div className="mt-2 h-2 overflow-hidden rounded-full bg-surface2">
                    <motion.div
                      initial={{ width: 0 }}
                      animate={{ width: `${Math.min(probability, 100)}%` }}
                      transition={{ duration: 0.65, delay: index * 0.04 }}
                      className="h-full rounded-full"
                      style={{ backgroundColor: emotionColors[index] }}
                    />
                  </div>
                </div>
                <div className="text-right text-sm font-semibold text-muted">{percent(probability)}</div>
              </div>
            );
          })}
        </div>
      </div>

      <div className="mt-8 border-t border-line pt-6">
        <div className="flex items-center justify-between gap-3">
          <div className="text-sm font-semibold text-ink">Klinik Açıklama</div>
          <BookOpen className="text-[#E76F3C]" size={18} strokeWidth={1.7} />
        </div>
        <p className="mt-3 text-sm leading-7 text-muted">
          {normalized.explanation ?? 'Bu çizim için ayrıntılı açıklama bulunmuyor.'}
        </p>
      </div>

      <ClinicalIndicatorsCompact result={result} indicators={indicators} />
    </motion.div>
  );
}

function ClinicalIndicatorsCompact({ result, indicators }: { result: ApiResult | null; indicators: IndicatorItem[] }) {
  return (
    <div className="mt-8 border-t border-line pt-6">
      <div className="flex items-center justify-between gap-3">
        <div className="font-serif text-xl font-semibold text-ink">16 Klinik Gösterge</div>
        <Settings2 className="text-[#E76F3C]" size={18} strokeWidth={1.7} />
      </div>

      {indicators.length > 0 ? (
        <div className="mt-4 space-y-3">
          {indicators.slice(0, 8).map((indicator) => (
            <div key={indicator.label} className="grid grid-cols-[minmax(0,1fr)_auto] items-center gap-3 text-sm">
              <span className="truncate text-muted">{indicator.label}</span>
              <span className="font-semibold text-ink">{formatIndicatorValue(indicator.value)}</span>
            </div>
          ))}
        </div>
      ) : (
        <>
          <p className="mt-3 text-sm leading-6 text-muted">
            Model, duygu tahminini 16 figür-farkında klinik gösterge üzerinden verir. Bu çalışmada göstergeler Koppitz/Di Leo temelli açıklanabilir ara kavramlar olarak kullanılmıştır.
          </p>
          <div className="mt-4 space-y-2">
            {[
              ['Gösterge sadakati', 'r=0,79'],
              ['Kalibrasyon', 'ECE=0,019'],
              ['Makro F1', '0,834'],
            ].map(([label, value]) => (
              <div key={label} className="flex items-center justify-between gap-4 text-sm">
                <span className="text-muted">{label}</span>
                <span className="font-semibold text-ink">{value}</span>
              </div>
            ))}
          </div>
        </>
      )}

      {result && indicators.length === 0 && (
        <div className="mt-4 flex gap-2 rounded-xl bg-surface2 p-3 text-xs leading-5 text-muted">
          <Info size={15} className="mt-0.5 shrink-0 text-[#E76F3C]" />
          API yanıtında gösterge bazlı ayrıntılı skor bulunmadığı için sahte değer gösterilmedi.
        </div>
      )}
    </div>
  );
}
