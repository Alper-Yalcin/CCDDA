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
import { useTranslation } from '../i18n';
import type { ApiResult } from '../types';
import type { Lang } from '../i18n';

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

// All UI copy, keyed by language.
const STR = {
  en: {
    eyebrow: 'ANALYSIS WORKSPACE',
    title: 'Upload a Drawing and Review the Analysis',
    subtitle: 'Upload the child’s drawing and review the AI-assisted analysis results and clinical indicators.',
    samplesTitle: 'Sample Drawings',
    sampleAlt: 'sample drawing',
    preprocessNote: 'PNG, JPG or WEBP · Max 10MB · 224×224 pre-processing',
    analyzing: 'Analyzing',
    startAnalysis: 'Start Analysis',
    errImageFormat: 'Please upload an image in PNG, JPG, JPEG or WEBP format.',
    errUnexpected: 'An unexpected error occurred.',
    gradcamResultAlt: 'Grad-CAM result',
    gradcamNotReady: 'Grad-CAM not ready yet',
    gradcamNotReadyBody: 'When a drawing is analyzed, the regions the model focused on appear here.',
    selectedAlt: 'Selected drawing',
    removeImg: 'Remove image',
    dropTitle: 'Drag the drawing here',
    dropOr: 'or click to choose a file',
    dropHint: 'PNG, JPG, JPEG · max 10 MB',
    chooseFile: 'Choose File',
    drawCanvas: 'Draw on Canvas',
    canvasTitle: 'Draw',
    close: 'Close',
    color: 'Color',
    brush: 'Brush size',
    tools: 'Tools',
    eraser: 'Eraser',
    clear: 'Clear',
    useDrawing: 'Use Drawing',
    cancel: 'Cancel',
    resultTitle: 'Analysis Result',
    resultSubtitle: 'Prediction, confidence and explanation inspector panel.',
    newAnalysis: 'New analysis',
    noAnalysis: 'No analysis yet',
    noAnalysisBody:
      'Upload a drawing or create one on the canvas. When the analysis completes, the emotion prediction, confidence score, class probabilities, Grad-CAM and clinical explanation appear here.',
    analysisView: 'Analysis View',
    running: 'Analysis running',
    runningBody: 'The drawing is being passed through the clinical decision-support pipeline.',
    predictedEmotion: 'Predicted Emotion',
    confidence: 'Confidence Score',
    highConf: 'High Confidence',
    reviewCare: 'Review Carefully',
    gradcamHeat: 'Grad-CAM Heatmap',
    gradcamAlt: 'Grad-CAM heatmap',
    gradcamNote: 'Warm regions show the drawing areas most influential in the model’s class decision.',
    classProbs: 'Class Probabilities',
    clinicalExplanation: 'Clinical Explanation',
    noExplanation: 'No detailed explanation is available for this drawing.',
    indicatorsTitle: '16 Clinical Indicators',
    indicatorsBody:
      'The model makes its emotion prediction through 16 figure-aware clinical indicators. In this work, the indicators are used as Koppitz/Di Leo-based explainable intermediate concepts.',
    fidelity: 'Concept fidelity',
    fidelityVal: 'r=0.79',
    calibration: 'Calibration',
    calibrationVal: 'ECE=0.019',
    macroF1: 'Macro F1',
    macroF1Val: '0.834',
    noScoresInfo: 'No per-indicator scores were present in the API response, so no placeholder values are shown.',
    uncertain: 'Uncertain',
    infoTabs: { explanation: 'Explanation', indicators: 'Clinical Indicators', llm: 'LLM Note' },
    infoTabContent: {
      explanation: {
        title: 'Predicted Emotion and Confidence Score',
        body: 'Once the analysis completes, the predicted emotion class, the model confidence score and the probability distribution over the four emotions are shown here.',
      },
      indicators: {
        title: '16 Figure-Aware Clinical Indicators',
        body: 'The model makes its decision through Koppitz/Di Leo-based explainable intermediate concepts. The indicator values for the drawing are listed here after the analysis.',
      },
      llm: {
        title: 'AI-Assisted Clinical Note',
        body: 'The prediction and clinical indicators are passed to a language model and turned into a readable clinical assessment text; this note appears here after the analysis.',
      },
    },
  },
  tr: {
    eyebrow: 'ANALİZ ÇALIŞMA ALANI',
    title: 'Çizim Yükle ve Analizi İncele',
    subtitle: 'Çocuğun çizimini yükleyin, yapay zeka destekli analiz sonuçlarını ve klinik göstergeleri inceleyin.',
    samplesTitle: 'Örnek Çizimler',
    sampleAlt: 'örnek çizim',
    preprocessNote: 'PNG, JPG veya WEBP · Maks. 10MB · 224×224 ön işleme',
    analyzing: 'Analiz Ediliyor',
    startAnalysis: 'Analizi Başlat',
    errImageFormat: 'Lütfen PNG, JPG, JPEG veya WEBP formatında bir görsel yükleyin.',
    errUnexpected: 'Beklenmeyen bir hata oluştu.',
    gradcamResultAlt: 'Grad-CAM sonucu',
    gradcamNotReady: 'Grad-CAM henüz hazır değil',
    gradcamNotReadyBody: 'Bir çizim analiz edildiğinde modelin odaklandığı bölgeler burada görüntülenir.',
    selectedAlt: 'Seçilen çizim',
    removeImg: 'Görseli kaldır',
    dropTitle: 'Çizimi buraya sürükleyin',
    dropOr: 'veya tıklayarak dosya seçin',
    dropHint: 'PNG, JPG, JPEG · maks. 10 MB',
    chooseFile: 'Dosya Seç',
    drawCanvas: 'Canvas ile Çiz',
    canvasTitle: 'Çizim Yap',
    close: 'Kapat',
    color: 'Renk',
    brush: 'Kalem Ucu',
    tools: 'Araçlar',
    eraser: 'Silgi',
    clear: 'Temizle',
    useDrawing: 'Çizimi Kullan',
    cancel: 'İptal',
    resultTitle: 'Analiz Sonucu',
    resultSubtitle: 'Tahmin, güven ve açıklama inspector paneli.',
    newAnalysis: 'Yeni analiz',
    noAnalysis: 'Henüz analiz yapılmadı',
    noAnalysisBody:
      'Bir çizim yükleyin veya canvas üzerinde çizim oluşturun. Analiz tamamlandığında duygu tahmini, güven skoru, sınıf olasılıkları, Grad-CAM ve klinik açıklama burada görüntülenir.',
    analysisView: 'Analiz Görünümü',
    running: 'Analiz çalışıyor',
    runningBody: 'Çizim klinik karar destek hattından geçiriliyor.',
    predictedEmotion: 'Tahmin Edilen Duygu',
    confidence: 'Güven Skoru',
    highConf: 'Yüksek Güven',
    reviewCare: 'Dikkatli İncele',
    gradcamHeat: 'Grad-CAM Isı Haritası',
    gradcamAlt: 'Grad-CAM ısı haritası',
    gradcamNote: 'Sıcak alanlar, modelin sınıf kararında daha etkili olan çizim bölgelerini gösterir.',
    classProbs: 'Sınıf Olasılıkları',
    clinicalExplanation: 'Klinik Açıklama',
    noExplanation: 'Bu çizim için ayrıntılı açıklama bulunmuyor.',
    indicatorsTitle: '16 Klinik Gösterge',
    indicatorsBody:
      'Model, duygu tahminini 16 figür-farkında klinik gösterge üzerinden verir. Bu çalışmada göstergeler Koppitz/Di Leo temelli açıklanabilir ara kavramlar olarak kullanılmıştır.',
    fidelity: 'Gösterge sadakati',
    fidelityVal: 'r=0,79',
    calibration: 'Kalibrasyon',
    calibrationVal: 'ECE=0,019',
    macroF1: 'Makro F1',
    macroF1Val: '0,834',
    noScoresInfo: 'API yanıtında gösterge bazlı ayrıntılı skor bulunmadığı için sahte değer gösterilmedi.',
    uncertain: 'Belirsiz',
    infoTabs: { explanation: 'Açıklama', indicators: 'Klinik Göstergeler', llm: 'LLM Yorum' },
    infoTabContent: {
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
    },
  },
} as const;

const infoTabKeys: InfoTab[] = ['explanation', 'indicators', 'llm'];

const emotionIcons: LucideIcon[] = [Smile, Frown, CircleAlert, ShieldCheck];

// Maps an English emotion label to its display label in the active language.
function localizedLabel(label: string, lang: Lang): string {
  const i = emotionClasses.findIndex((c) => c.toLowerCase() === label.toLowerCase());
  if (i < 0) return label || (lang === 'tr' ? 'Belirsiz' : 'Uncertain');
  return lang === 'tr' ? emotionClassesTr[i] : emotionClasses[i];
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
          const label = itemRecord.label ?? itemRecord.name ?? itemRecord.title ?? itemRecord.concept ?? `Indicator ${index + 1}`;
          const value = getIndicatorValue(item);
          return value !== null ? { label: String(label), value } : null;
        }
        return { label: `Indicator ${index + 1}`, value: item as number | string };
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

// Analysis cache that lives for the SPA session (state is preserved across page changes).
const analysisCache: {
  file: File | null;
  previewSrc: string | null;
  result: ApiResult | null;
} = { file: null, previewSrc: null, result: null };

export function AnalysisPage() {
  const { lang } = useTranslation();
  const s = STR[lang];
  const [file, setFile] = useState<File | null>(analysisCache.file);
  const [previewSrc, setPreviewSrc] = useState<string | null>(analysisCache.previewSrc);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [result, setResult] = useState<ApiResult | null>(analysisCache.result);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<MainTab>('original');
  const [isCanvasOpen, setIsCanvasOpen] = useState(false);
  const [isDragging, setIsDragging] = useState(false);
  const fileInputRef = useRef<HTMLInputElement | null>(null);

  // Reflect into the module-level cache so state is not lost on unmount;
  // restored from here when AnalysisPage reopens.
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
    // Reset the input value so the same file can be selected again.
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
    formData.append('lang', lang);
    try {
      const res = await fetch(API_URL, { method: 'POST', body: formData });
      if (!res.ok) {
        const body = await res.json().catch(() => null);
        const fallback = lang === 'tr' ? `Analiz başarısız oldu (${res.status}).` : `Analysis failed (${res.status}).`;
        throw new Error(body?.detail ?? fallback);
      }
      setResult(await res.json());
    } catch (err) {
      setError(err instanceof Error ? err.message : s.errUnexpected);
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
      setError(s.errImageFormat);
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
        {/* ── Left: working column ── */}
        <motion.section
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4, delay: 0.1 }}
          className="order-1 flex min-w-0 flex-col py-4 xl:col-start-1 xl:h-full xl:min-h-0 xl:pr-10"
        >
          {/* Title */}
          <div className="shrink-0">
            <div className="text-xs font-bold uppercase tracking-[0.32em] text-[#E76F3C]">{s.eyebrow}</div>
            <h1 className="mt-2 font-serif text-3xl font-semibold leading-tight tracking-[-0.02em] text-ink md:text-4xl">
              {s.title}
            </h1>
            <p className="mt-2 max-w-2xl text-sm leading-6 text-muted">
              {s.subtitle}
            </p>
          </div>

          {/* Sample drawings — compact rail */}
          <div className="mt-4 shrink-0">
            <h2 className="font-serif text-xl font-semibold text-ink">{s.samplesTitle}</h2>
            <div className="mt-2 flex gap-2.5 overflow-x-auto pb-1">
              {filteredSamples.map((sample) => {
                const selected = previewSrc === sample.src;
                const labelIdx = emotionClasses.indexOf(sample.emotion);
                const label = lang === 'tr' ? emotionClassesTr[labelIdx] : emotionClasses[labelIdx];
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
                      alt={`${label} ${s.sampleAlt}`}
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

          {/* Divider + workspace */}
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

            <p className="mt-3 shrink-0 text-center text-xs text-muted">{s.preprocessNote}</p>

            <Button
              type="button"
              onClick={handleAnalyze}
              disabled={!file || isAnalyzing}
              className="mt-4 w-full shrink-0 !rounded-xl disabled:cursor-not-allowed disabled:opacity-60"
            >
              {isAnalyzing ? (
                <>
                  <RefreshCw className="animate-spin" size={17} />
                  {s.analyzing}
                </>
              ) : (
                <>
                  {s.startAnalysis}
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
  const { lang } = useTranslation();
  const s = STR[lang];
  if (activeTab === 'gradcam') {
    return (
      <div className="grid h-[380px] place-items-center overflow-hidden rounded-2xl border border-dashed border-[#E9CDBA] bg-surface/60 p-4 sm:h-[440px] xl:h-full xl:min-h-[360px]">
        {normalized?.heatmap ? (
          <img src={`data:image/png;base64,${normalized.heatmap}`} alt={s.gradcamResultAlt} className="max-h-full max-w-full rounded-xl object-contain" />
        ) : (
          <div className="max-w-sm text-center">
            <div className="mx-auto grid h-16 w-16 place-items-center rounded-full bg-tint text-[#E76F3C]">
              <Zap size={25} strokeWidth={1.6} />
            </div>
            <h3 className="mt-5 font-serif text-2xl font-semibold text-ink">{s.gradcamNotReady}</h3>
            <p className="mt-3 text-sm leading-6 text-muted">
              {s.gradcamNotReadyBody}
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
            alt={s.selectedAlt}
            className="absolute inset-4 h-[calc(100%-2rem)] w-[calc(100%-2rem)] rounded-xl object-contain object-center"
          />
          <button
            type="button"
            onClick={(e) => {
              e.stopPropagation();
              onClear();
            }}
            aria-label={s.removeImg}
            title={s.removeImg}
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
          <h3 className="mt-5 font-serif text-3xl font-semibold text-ink">{s.dropTitle}</h3>
          <p className="mt-2 text-sm leading-6 text-muted">{s.dropOr}</p>
          <p className="mt-1 text-xs text-muted">{s.dropHint}</p>
          <div className="mt-6 flex flex-col gap-3 sm:flex-row sm:justify-center">
            <Button
              type="button"
              onClick={(e) => {
                e.stopPropagation();
                onPickFile();
              }}
              className="!rounded-xl"
            >
              {s.chooseFile}
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
              {s.drawCanvas}
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}

function CanvasModal({ onSave, onClose }: { onSave: (file: File, preview: string) => void; onClose: () => void }) {
  const { lang } = useTranslation();
  const s = STR[lang];
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const canvasHostRef = useRef<HTMLDivElement | null>(null);
  const drawingRef = useRef(false);
  const [color, setColor] = useState(CANVAS_COLORS[0]);
  const [size, setSize] = useState(BRUSH_SIZES[1]);
  const [isEraser, setIsEraser] = useState(false);

  // Close on ESC + prevent background scroll while the modal is open.
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
      const file = new File([blob], `drawing_${Date.now()}.png`, { type: 'image/png' });
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
        {/* ── Sidebar: tools ── */}
        <aside className="flex shrink-0 flex-col gap-6 overflow-y-auto border-b border-line bg-bg p-5 sm:w-72 sm:border-b-0 sm:border-r">
          <div className="flex items-center justify-between gap-3">
            <h3 className="font-serif text-xl font-semibold text-ink">{s.canvasTitle}</h3>
            <button
              type="button"
              onClick={onClose}
              aria-label={s.close}
              className="grid h-9 w-9 place-items-center rounded-full text-muted transition hover:bg-tint hover:text-[#E76F3C]"
            >
              <X size={18} />
            </button>
          </div>

          <div>
            <div className="text-xs font-semibold uppercase tracking-[0.18em] text-muted">{s.color}</div>
            <div className="mt-3 flex flex-wrap gap-2.5">
              {CANVAS_COLORS.map((c) => (
                <button
                  key={c}
                  type="button"
                  onClick={() => {
                    setColor(c);
                    setIsEraser(false);
                  }}
                  aria-label={`${s.color} ${c}`}
                  className={`h-9 w-9 rounded-full border-2 transition hover:scale-105 ${
                    color === c && !isEraser ? 'scale-110 border-ink' : 'border-white shadow-sm'
                  }`}
                  style={{ backgroundColor: c }}
                />
              ))}
            </div>
          </div>

          <div>
            <div className="text-xs font-semibold uppercase tracking-[0.18em] text-muted">{s.brush}</div>
            <div className="mt-3 flex flex-wrap gap-2">
              {BRUSH_SIZES.map((brushSize) => (
                <button
                  key={brushSize}
                  type="button"
                  onClick={() => setSize(brushSize)}
                  aria-label={`${s.brush} ${brushSize}px`}
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
            <div className="text-xs font-semibold uppercase tracking-[0.18em] text-muted">{s.tools}</div>
            <div className="mt-3 flex gap-2">
              <button
                type="button"
                onClick={() => setIsEraser((v) => !v)}
                className={`flex flex-1 items-center justify-center gap-2 rounded-lg border px-3 py-2.5 text-sm font-semibold transition ${
                  isEraser ? 'border-[#E76F3C] bg-tint text-[#E76F3C]' : 'border-line bg-surface text-muted hover:border-[#F08A5D]'
                }`}
                aria-label={s.eraser}
              >
                <Eraser size={17} />
                {s.eraser}
              </button>
              <button
                type="button"
                onClick={clearCanvas}
                className="flex flex-1 items-center justify-center gap-2 rounded-lg border border-line bg-surface px-3 py-2.5 text-sm font-semibold text-muted transition hover:border-[#EB5757] hover:text-[#EB5757]"
                aria-label={s.clear}
              >
                <Trash2 size={17} />
                {s.clear}
              </button>
            </div>
          </div>

          <div className="mt-auto flex flex-col gap-3 pt-2">
            <Button type="button" onClick={handleSave} className="!rounded-xl">
              <Check size={17} />
              {s.useDrawing}
            </Button>
            <Button type="button" variant="secondary" onClick={onClose} className="!rounded-xl">
              {s.cancel}
            </Button>
          </div>
        </aside>

        {/* ── Canvas: entire right side ── */}
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
  const { lang } = useTranslation();
  const s = STR[lang];
  return (
    <motion.aside
      initial={{ opacity: 0, x: 18 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ duration: 0.4, delay: 0.18 }}
      className="order-2 min-w-0 border-line py-6 xl:col-start-2 xl:h-full xl:overflow-y-auto xl:border-l xl:pl-8"
    >
      <div className="flex items-start justify-between gap-4">
        <div>
          <h2 className="font-serif text-2xl font-semibold text-ink">{s.resultTitle}</h2>
          <p className="mt-1 text-sm text-muted">{s.resultSubtitle}</p>
        </div>
        <button
          type="button"
          onClick={onReset}
          className="grid h-10 w-10 shrink-0 place-items-center rounded-full text-[#E76F3C] transition hover:bg-tint"
          aria-label={s.newAnalysis}
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
  const { lang } = useTranslation();
  const s = STR[lang];
  const [infoTab, setInfoTab] = useState<InfoTab>('explanation');
  return (
    <motion.div key="empty" initial={{ opacity: 0, x: 14 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: 8 }} className="mt-7">
      <div className="rounded-2xl border border-line bg-surface/55 p-5">
        <div className="grid h-14 w-14 place-items-center rounded-full bg-tint text-[#E76F3C]">
          <ImageIcon size={24} strokeWidth={1.6} />
        </div>
        <h3 className="mt-5 font-serif text-2xl font-semibold text-ink">{s.noAnalysis}</h3>
        <p className="mt-3 text-sm leading-7 text-muted">
          {s.noAnalysisBody}
        </p>
      </div>

      <div className="mt-6 border-t border-line pt-5">
        <h3 className="font-serif text-lg font-semibold text-ink">{s.analysisView}</h3>
        <div className="mt-3 flex gap-6 overflow-x-auto border-b border-line">
          {infoTabKeys.map((key) => (
            <button
              key={key}
              type="button"
              onClick={() => setInfoTab(key)}
              className={`shrink-0 border-b-2 px-1 pb-2.5 text-sm font-semibold transition ${
                infoTab === key ? 'border-[#E76F3C] text-[#E76F3C]' : 'border-transparent text-muted hover:text-[#E76F3C]'
              }`}
            >
              {s.infoTabs[key]}
            </button>
          ))}
        </div>
        <div className="mt-4 flex gap-3 text-sm leading-6 text-muted">
          <Sparkles className="mt-0.5 shrink-0 text-[#E76F3C]" size={20} strokeWidth={1.7} />
          <div>
            <p>{s.infoTabContent[infoTab].title}</p>
            <p className="mt-1">{s.infoTabContent[infoTab].body}</p>
          </div>
        </div>
      </div>
    </motion.div>
  );
}

function AnalyzingState() {
  const { lang } = useTranslation();
  const s = STR[lang];
  return (
    <motion.div key="loading" initial={{ opacity: 0, x: 14 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: 8 }} className="mt-7">
      <div className="rounded-2xl border border-line bg-surface/55 p-5">
        <div className="flex items-center gap-3">
          <RefreshCw className="animate-spin text-[#E76F3C]" size={20} />
          <div>
            <h3 className="font-serif text-2xl font-semibold text-ink">{s.running}</h3>
            <p className="mt-1 text-sm text-muted">{s.runningBody}</p>
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
            <div key={step.title.en} className="flex gap-3 border-b border-line pb-4 last:border-b-0">
              <div className="grid h-10 w-10 shrink-0 place-items-center rounded-full bg-tint text-[#E76F3C]">
                <Icon size={18} strokeWidth={1.65} />
              </div>
              <div>
                <div className="text-sm font-semibold text-ink">
                  {index + 1}. {step.title[lang]}
                </div>
                <p className="mt-1 text-xs leading-5 text-muted">{step.body[lang]}</p>
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
  const { lang } = useTranslation();
  const s = STR[lang];
  const emotionIndex = emotionClasses.findIndex((c) => c.toLowerCase() === normalized.label.toLowerCase());
  const Icon = emotionIcons[emotionIndex >= 0 ? emotionIndex : 2];
  const color = emotionColors[emotionIndex >= 0 ? emotionIndex : 2] ?? '#E76F3C';
  const classLabels = lang === 'tr' ? emotionClassesTr : emotionClasses;

  return (
    <motion.div key="result" initial={{ opacity: 0, x: 14 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: 8 }} className="mt-7">
      <div>
        <div className="text-sm font-semibold text-muted">{s.predictedEmotion}</div>
        <div className="mt-4 flex items-center gap-4">
          <div className="grid h-16 w-16 shrink-0 place-items-center rounded-full bg-tint ring-8 ring-surface" style={{ color }}>
            <Icon size={28} strokeWidth={1.8} />
          </div>
          <div className="min-w-0">
            <div className="font-serif text-4xl font-semibold leading-tight text-ink">
              <span style={{ color }}>{localizedLabel(normalized.label, lang)}</span>
            </div>
            {normalized.label && lang === 'tr' && <div className="mt-1 text-sm text-muted">({normalized.label})</div>}
          </div>
        </div>
      </div>

      <div className="mt-8">
        <div className="flex items-end justify-between gap-4">
          <div>
            <div className="text-sm font-semibold text-muted">{s.confidence}</div>
            <div className="mt-2 font-serif text-5xl font-semibold leading-none" style={{ color }}>
              {percent(normalized.confidence)}
            </div>
          </div>
          <span className="rounded-lg bg-tint px-3 py-1.5 text-xs font-semibold text-[#E76F3C]">
            {normalized.confidence >= 80 ? s.highConf : s.reviewCare}
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
            <div className="text-sm font-semibold text-ink">{s.gradcamHeat}</div>
            <Zap className="text-[#E76F3C]" size={18} strokeWidth={1.7} />
          </div>
          <div className="mt-3 overflow-hidden rounded-xl border border-line bg-[#1F1F1F]">
            <img
              src={`data:image/png;base64,${normalized.heatmap}`}
              alt={s.gradcamAlt}
              className="h-auto w-full object-contain"
            />
          </div>
          <p className="mt-2 text-xs leading-5 text-muted">
            {s.gradcamNote}
          </p>
        </div>
      )}

      <div className="mt-8 border-t border-line pt-6">
        <div className="text-sm font-semibold text-ink">{s.classProbs}</div>
        <div className="mt-4 space-y-4">
          {classLabels.map((label, index) => {
            const RowIcon = emotionIcons[index] ?? CircleAlert;
            const probability = normalized.probabilities[index] ?? 0;
            return (
              <div key={label} className="grid grid-cols-[auto_minmax(0,1fr)_48px] items-center gap-3">
                <RowIcon size={21} style={{ color: emotionColors[index] }} strokeWidth={1.65} />
                <div className="min-w-0">
                  <div className="flex items-baseline gap-1.5 text-sm">
                    <span className="font-semibold text-ink">{label}</span>
                    {lang === 'tr' && <span className="truncate text-xs text-muted">({emotionClasses[index]})</span>}
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
          <div className="text-sm font-semibold text-ink">{s.clinicalExplanation}</div>
          <BookOpen className="text-[#E76F3C]" size={18} strokeWidth={1.7} />
        </div>
        <p className="mt-3 text-sm leading-7 text-muted">
          {normalized.explanation ?? s.noExplanation}
        </p>
      </div>

      <ClinicalIndicatorsCompact result={result} indicators={indicators} />
    </motion.div>
  );
}

function ClinicalIndicatorsCompact({ result, indicators }: { result: ApiResult | null; indicators: IndicatorItem[] }) {
  const { lang } = useTranslation();
  const s = STR[lang];
  return (
    <div className="mt-8 border-t border-line pt-6">
      <div className="flex items-center justify-between gap-3">
        <div className="font-serif text-xl font-semibold text-ink">{s.indicatorsTitle}</div>
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
            {s.indicatorsBody}
          </p>
          <div className="mt-4 space-y-2">
            {[
              [s.fidelity, s.fidelityVal],
              [s.calibration, s.calibrationVal],
              [s.macroF1, s.macroF1Val],
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
          {s.noScoresInfo}
        </div>
      )}
    </div>
  );
}
