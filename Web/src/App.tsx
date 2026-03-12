/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import { useState, type ChangeEvent } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import {
  Upload,
  ArrowRight,
  Activity,
  Shield,
  Brain,
  AlertTriangle,
  FileText,
  CheckCircle,
  X,
  Database,
  Layers3,
  Target,
  FlaskConical,
  BarChart3,
  Cpu,
  Workflow,
  Sparkles,
  BookOpen,
  Rocket,
} from 'lucide-react';
import { useTranslation } from './i18n';

// --- Types ---
type Page = 'home' | 'analysis' | 'about';
type MetricCardItem = { value: string; label: string; note: string };
type FactItem = { label: string; value: string };
type ContentItem = { title: string; body: string };
type ContentGroup = { title: string; items: string[] };

// --- Components ---

function Navigation({ currentPage, setPage }: { currentPage: Page; setPage: (p: Page) => void }) {
  const { t, lang, setLang } = useTranslation();

  const navItems: { id: Page; label: string }[] = [
    { id: 'home', label: t('nav.home') },
    { id: 'analysis', label: t('nav.analysis') },
    { id: 'about', label: t('nav.about') },
  ];

  return (
    <nav className="fixed w-full bg-white/90 backdrop-blur-sm border-b border-slate-200 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16 items-center">
          <div 
            className="flex items-center gap-3 cursor-pointer" 
            onClick={() => setPage('home')}
          >
            <div className="w-8 h-8 bg-teal-600 rounded-lg flex items-center justify-center text-white">
              <Brain size={18} />
            </div>
            <div className="flex flex-col">
              <span className="font-display font-bold text-lg leading-none text-slate-800">
                {t('brand.title')}<span className="text-teal-600">{t('brand.accent')}</span>
              </span>
              <span className="text-[10px] uppercase tracking-wider text-slate-500 font-medium">
                {t('brand.subtitle')}
              </span>
            </div>
          </div>
          <div className="flex items-center gap-1 sm:gap-6">
            {navItems.map((item) => (
              <button
                key={item.id}
                onClick={() => setPage(item.id)}
                className={`text-sm font-medium px-3 py-2 rounded-md transition-colors ${
                  currentPage === item.id
                    ? 'text-teal-700 bg-teal-50'
                    : 'text-slate-600 hover:text-teal-600 hover:bg-slate-50'
                }`}
              >
                {item.label}
              </button>
            ))}

            <select
              aria-label="Language"
              value={lang}
              onChange={(e) => setLang(e.target.value as any)}
              className="ml-2 border rounded-md px-2 py-1 text-sm"
            >
              <option value="en">EN</option>
              <option value="tr">TR</option>
            </select>
          </div>
        </div>
      </div>
    </nav>
  );
}

function SectionLabel({ children }: { children: string }) {
  return (
    <div className="inline-flex items-center gap-2 rounded-full border border-stone-300/80 bg-white/80 px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.24em] text-stone-600 backdrop-blur-sm">
      <span className="h-1.5 w-1.5 rounded-full bg-teal-500" />
      {children}
    </div>
  );
}

function HomePage({ setPage }: { setPage: (p: Page) => void }) {
  const { t } = useTranslation();
  const highlights = t('hero.highlights') as string[];
  const stats = t('home.stats') as MetricCardItem[];
  const workflowSteps = t('home.workflowSteps') as ContentItem[];
  const modules = t('home.modules') as ContentItem[];
  const outcomes = t('home.outcomes') as string[];

  return (
    <motion.div 
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -10 }}
      className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-32 pb-20"
    >
      <section className="relative overflow-hidden rounded-[32px] border border-stone-200 bg-[linear-gradient(135deg,#fffdf7_0%,#f5efe5_48%,#e1f0eb_100%)] px-6 py-8 shadow-[0_28px_90px_-48px_rgba(15,23,42,0.55)] sm:px-10 sm:py-10 lg:px-12 lg:py-12">
        <div className="absolute inset-y-0 right-0 w-1/2 bg-[radial-gradient(circle_at_top,#0f766e18,transparent_60%)]" />
        <div className="absolute -left-10 top-10 h-40 w-40 rounded-full bg-amber-200/30 blur-3xl" />
        <div className="absolute bottom-0 right-0 h-52 w-52 rounded-full bg-teal-300/20 blur-3xl" />

        <div className="relative grid items-center gap-10 lg:grid-cols-[1.05fr_0.95fr]">
          <div>
            <div className="inline-flex items-center gap-2 rounded-full border border-stone-300 bg-white/80 px-3 py-1 text-xs font-semibold uppercase tracking-[0.18em] text-stone-600 backdrop-blur-sm">
              <Activity size={12} className="text-teal-600" />
              {t('hero.badge')}
            </div>
            <h1 className="mt-6 max-w-3xl font-display text-4xl font-bold leading-[1.05] text-slate-900 md:text-5xl lg:text-6xl">
              {t('hero.title')}
            </h1>
            <p className="mt-6 max-w-2xl text-lg leading-relaxed text-slate-700">
              {t('hero.subtitle')}
            </p>

            <div className="mt-8 grid gap-3 sm:grid-cols-3">
              {highlights.map((item, index) => (
                <div
                  key={index}
                  className="rounded-2xl border border-stone-200 bg-white/70 px-4 py-4 text-sm leading-relaxed text-slate-700 shadow-sm backdrop-blur-sm"
                >
                  <CheckCircle size={16} className="mb-3 text-teal-600" />
                  {item}
                </div>
              ))}
            </div>

            <div className="mt-8 flex flex-wrap gap-4">
              <button 
                onClick={() => setPage('analysis')}
                className="inline-flex items-center justify-center gap-2 rounded-xl bg-slate-950 px-6 py-3 font-medium text-white transition-all hover:-translate-y-0.5 hover:bg-slate-800"
              >
                {t('hero.start')}
                <ArrowRight size={18} />
              </button>
              <button 
                onClick={() => setPage('about')}
                className="inline-flex items-center justify-center gap-2 rounded-xl border border-slate-300 bg-white/80 px-6 py-3 font-medium text-slate-700 transition-all hover:-translate-y-0.5 hover:bg-white"
              >
                {t('hero.methodology')}
              </button>
            </div>
          </div>

          <div className="relative">
            <div className="absolute -inset-5 rounded-[36px] bg-[radial-gradient(circle_at_18%_18%,rgba(20,184,166,0.22),transparent_28%),radial-gradient(circle_at_82%_18%,rgba(239,68,68,0.22),transparent_24%),radial-gradient(circle_at_82%_82%,rgba(249,115,22,0.28),transparent_36%)] blur-3xl opacity-80" />

            <div className="relative overflow-hidden rounded-[30px] border border-white/70 bg-white/55 p-2 shadow-[0_28px_90px_-36px_rgba(15,23,42,0.7)] backdrop-blur-sm">
              <div className="relative aspect-[4/3] overflow-hidden rounded-[24px] bg-slate-100">
                <img
                  src="/home-preview.jpg"
                  alt="Child drawing preview"
                  className="h-full w-full object-cover"
                />
                <div className="absolute inset-0 bg-[linear-gradient(180deg,rgba(15,23,42,0.02)_0%,rgba(15,23,42,0.04)_44%,rgba(15,23,42,0.58)_100%)]" />
                <div className="absolute inset-x-0 bottom-0 h-[42%] bg-[radial-gradient(ellipse_at_bottom,rgba(15,23,42,0.16),transparent_58%)]" />

                <div className="absolute bottom-6 left-6 right-6">
                  <div className="inline-flex items-center rounded-md border border-white/18 bg-black/40 px-3 py-1 text-xs font-mono font-semibold text-white/95 shadow-lg backdrop-blur-sm">
                    {t('ui.confidenceLabel', { val: '94.2' })}
                  </div>
                  <p className="mt-4 max-w-xs font-display text-[1.65rem] font-semibold leading-tight text-white drop-shadow-sm sm:text-[1.85rem]">
                    {t('home.previewTitle')}
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section className="mt-12 grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        {stats.map((item, index) => (
          <motion.div
            key={item.label}
            initial={{ opacity: 0, y: 14 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.06 * index }}
            className="rounded-[24px] border border-stone-200 bg-white p-5 shadow-sm"
          >
            <div className="text-3xl font-display font-bold text-slate-900">{item.value}</div>
            <div className="mt-2 text-sm font-semibold text-slate-700">{item.label}</div>
            <p className="mt-2 text-sm leading-relaxed text-slate-500">{item.note}</p>
          </motion.div>
        ))}
      </section>

      <section className="mt-16 grid gap-8 lg:grid-cols-[0.92fr_1.08fr]">
        <div className="rounded-[28px] border border-stone-200 bg-white p-6 shadow-sm sm:p-8">
          <SectionLabel>{t('home.workflowEyebrow')}</SectionLabel>
          <h2 className="mt-4 font-display text-3xl font-semibold text-slate-900">
            {t('home.workflowTitle')}
          </h2>
          <p className="mt-3 max-w-xl text-slate-600 leading-relaxed">
            {t('home.workflowIntro')}
          </p>

          <div className="mt-8 space-y-4">
            {workflowSteps.map((step, index) => (
              <div key={step.title} className="rounded-2xl border border-stone-200 bg-stone-50 px-5 py-5">
                <div className="flex items-start gap-4">
                  <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-2xl bg-slate-900 text-sm font-semibold text-white">
                    {index + 1}
                  </div>
                  <div>
                    <h3 className="text-lg font-semibold text-slate-900">{step.title}</h3>
                    <p className="mt-2 text-sm leading-relaxed text-slate-600">{step.body}</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="rounded-[28px] border border-stone-200 bg-white p-6 shadow-sm sm:p-8">
          <SectionLabel>{t('home.modulesEyebrow')}</SectionLabel>
          <h2 className="mt-4 font-display text-3xl font-semibold text-slate-900">
            {t('home.modulesTitle')}
          </h2>
          <p className="mt-3 text-slate-600 leading-relaxed">
            {t('home.modulesIntro')}
          </p>

          <div className="mt-8 grid gap-4 md:grid-cols-2">
            {modules.map((module, index) => {
              const Icon = [Database, Layers3, BarChart3, Rocket][index] ?? FileText;
              return (
                <div key={module.title} className="rounded-2xl border border-stone-200 bg-[linear-gradient(180deg,#ffffff_0%,#f8fafc_100%)] p-5">
                  <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-teal-50 text-teal-700">
                    <Icon size={18} />
                  </div>
                  <h3 className="mt-4 text-lg font-semibold text-slate-900">{module.title}</h3>
                  <p className="mt-2 text-sm leading-relaxed text-slate-600">{module.body}</p>
                </div>
              );
            })}
          </div>
        </div>
      </section>

      <section className="mt-16 overflow-hidden rounded-[32px] bg-[linear-gradient(135deg,#0f172a_0%,#111827_58%,#134e4a_100%)] px-6 py-8 text-white shadow-[0_24px_80px_-40px_rgba(2,6,23,0.75)] sm:px-8 sm:py-10">
        <div className="grid gap-8 lg:grid-cols-[1fr_0.95fr]">
          <div>
            <SectionLabel>{t('home.outcomesEyebrow')}</SectionLabel>
            <h2 className="mt-4 font-display text-3xl font-semibold text-white">
              {t('home.outcomesTitle')}
            </h2>
            <p className="mt-3 max-w-2xl text-slate-300 leading-relaxed">
              {t('home.outcomesIntro')}
            </p>
          </div>
          <div className="rounded-[28px] border border-white/10 bg-white/5 p-6 backdrop-blur-sm">
            <div className="grid gap-3">
              {outcomes.map((item, index) => (
                <div key={index} className="flex gap-3 rounded-2xl border border-white/10 bg-black/10 px-4 py-4">
                  <BookOpen size={18} className="mt-0.5 shrink-0 text-emerald-300" />
                  <p className="text-sm leading-relaxed text-slate-200">{item}</p>
                </div>
              ))}
            </div>
          </div>
        </div>

        <div className="mt-8 rounded-[28px] border border-amber-300/20 bg-amber-50/10 p-5">
          <div className="flex items-start gap-3">
            <Shield className="mt-0.5 shrink-0 text-amber-300" size={18} />
            <div>
              <h3 className="text-sm font-semibold uppercase tracking-[0.18em] text-amber-200">
                {t('home.ethicsTitle')}
              </h3>
              <p className="mt-2 text-sm leading-relaxed text-slate-200">{t('home.ethicsText')}</p>
            </div>
          </div>
        </div>
      </section>
    </motion.div>
  );
}

// Use same-origin API path; Vite dev proxy forwards /api/* to the Python backend.
const API_URL = '/api';

const EMOTION_TR_MAP: Record<string, string> = {
  Happiness: 'Mutluluk',
  Sadness: 'Üzüntü',
};

const GENDER_TR_MAP: Record<string, string> = {
  Female: 'Kız',
  Male: 'Erkek',
};

function localizeClassLabel(value: string, type: 'emotion' | 'gender', lang: 'en' | 'tr') {
  if (lang !== 'tr') return value;
  if (type === 'emotion') return EMOTION_TR_MAP[value] ?? value;
  return GENDER_TR_MAP[value] ?? value;
}

function localizeBackendExplanation(explanation: string, lang: 'en' | 'tr') {
  if (lang !== 'tr') return explanation;

  let out = explanation;

  out = out.replace(
    /Model predicts emotion '([^']+)' with ([\d.]+)% confidence\./g,
    (_m, emotion, conf) =>
      `Model, duygu tahminini '${localizeClassLabel(String(emotion), 'emotion', 'tr')}' olarak %${String(conf)} güvenle yaptı.`,
  );
  out = out.replace(
    /Model predicts gender '([^']+)' with ([\d.]+)% confidence\./g,
    (_m, gender, conf) =>
      `Model, cinsiyet tahminini '${localizeClassLabel(String(gender), 'gender', 'tr')}' olarak %${String(conf)} güvenle yaptı.`,
  );
  out = out.replace(
    /Visual pattern appears more balanced and positive\./g,
    'Görsel örüntü daha dengeli ve olumlu görünüyor.',
  );
  out = out.replace(
    /Visual pattern appears more restrained and low-energy\./g,
    'Görsel örüntü daha kısıtlı ve düşük enerjili görünüyor.',
  );
  out = out.replace(
    /Stroke style is interpreted as stronger and sharper by the model\./g,
    'Çizgi stili model tarafından daha güçlü ve keskin olarak yorumlandı.',
  );
  out = out.replace(
    /Stroke style is interpreted as softer and more detailed by the model\./g,
    'Çizgi stili model tarafından daha yumuşak ve daha detaylı olarak yorumlandı.',
  );
  out = out.replace(
    /Text input was included in the multimodal decision\./g,
    'Metin girdisi çok modlu karara dahil edildi.',
  );
  out = out.replace(
    /No text input was provided, so the decision is image-heavy\./g,
    'Metin girdisi sağlanmadığı için karar ağırlıklı olarak görsele dayanıyor.',
  );

  // We no longer collect text input; remove any text-related rationale sentence.
  out = out.replace(/Text input was included in the multimodal decision\./g, '');
  out = out.replace(/No text input was provided, so the decision is image-heavy\./g, '');
  out = out.replace(/Metin girdisi[^.]*\./g, '');
  out = out.replace(/\s{2,}/g, ' ').trim();

  return out;
}

type ApiResult = {
  pred_emotion: string;
  pred_gender: string;
  confidence_emotion: number;
  confidence_gender: number;
  explanation: string | null;
  probs_emotion: number[];
  probs_gender: number[];
  heatmap_emotion_b64: string | null;
  heatmap_gender_b64: string | null;
  tokens_emotion: { token: string; score: number }[];
  tokens_gender: { token: string; score: number }[];
};

function AnalysisPage() {
  const { t, lang } = useTranslation();
  const [file, setFile] = useState<File | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [result, setResult] = useState<ApiResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleFileChange = (e: ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
      setResult(null);
      setError(null);
    }
  };

  const handleAnalyze = async () => {
    if (!file) return;
    setIsAnalyzing(true);
    setError(null);
    setResult(null);

    try {
      const form = new FormData();
      // The backend OpenAPI expects the multipart field named `image` (see /api/predict schema)
      form.append('image', file as Blob);
      form.append('lang', lang);

      const res = await fetch(`${API_URL}/predict`, {
        method: 'POST',
        body: form,
        headers: {
          'Accept-Language': lang,
        },
      });
      if (!res.ok) {
        const detail = await res.json().catch(() => ({}));
        throw new Error(detail?.detail || `HTTP ${res.status}`);
      }
      const raw = await res.json();

      // Normalize backend responses: older/newer backends may use different keys.
      const toPct = (v: number) => (v > 0 && v <= 1 ? Math.round(v * 1000) / 10 : Math.round(v * 10) / 10);
      const data: ApiResult = {
        pred_emotion: String(raw.pred_emotion ?? raw.emotion ?? ''),
        pred_gender: String(raw.pred_gender ?? raw.gender ?? ''),
        confidence_emotion: toPct(Number(raw.confidence_emotion ?? raw.emotion_confidence ?? 0) || 0),
        confidence_gender: toPct(Number(raw.confidence_gender ?? raw.gender_confidence ?? 0) || 0),
        explanation:
          typeof raw.explanation === 'string' && raw.explanation.trim().length > 0
            ? localizeBackendExplanation(raw.explanation.trim(), lang)
            : null,
        probs_emotion: Array.isArray(raw.probs_emotion) ? raw.probs_emotion : [],
        probs_gender: Array.isArray(raw.probs_gender) ? raw.probs_gender : [],
        heatmap_emotion_b64: raw.heatmap_emotion_b64 ?? raw.heatmap_emotion ?? null,
        heatmap_gender_b64: raw.heatmap_gender_b64 ?? raw.heatmap_gender ?? null,
        tokens_emotion: Array.isArray(raw.tokens_emotion) ? raw.tokens_emotion : [],
        tokens_gender: Array.isArray(raw.tokens_gender) ? raw.tokens_gender : [],
      };

      setResult(data);
    } catch (err: any) {
      setError(err.message ?? 'Unknown error');
    } finally {
      setIsAnalyzing(false);
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 pt-32 pb-20"
    >
      <div className="text-center mb-10">
        <h2 className="text-3xl font-display font-bold text-slate-900">{t('analysis.title')}</h2>
        <p className="text-slate-500 mt-2">{t('analysis.subtitle')}</p>
      </div>

      <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
        <div className="p-8 space-y-6">
          {/* ── Upload zone ─────────────────────────────────────── */}
          {!file ? (
            <div className="border-2 border-dashed border-slate-300 rounded-xl p-12 text-center hover:bg-slate-50 transition-colors relative">
              <input
                type="file"
                accept="image/*"
                onChange={handleFileChange}
                className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
              />
              <Upload className="mx-auto h-12 w-12 text-slate-400 mb-4" />
              <p className="text-lg font-medium text-slate-700">{t('analysis.drop')}</p>
              <p className="text-sm text-slate-500 mt-1">{t('analysis.support')}</p>
            </div>
          ) : (
            <div className="flex flex-col items-center gap-4">
              {/* Preview */}
              <div className="relative w-full max-w-md aspect-[4/3] bg-slate-100 rounded-lg overflow-hidden border border-slate-200">
                <img
                  src={URL.createObjectURL(file)}
                  alt="Preview"
                  className="w-full h-full object-contain"
                />
                <button
                  onClick={() => { setFile(null); setResult(null); setError(null); }}
                  className="absolute top-2 right-2 p-1 bg-white/80 rounded-full hover:bg-white text-slate-600"
                >
                  <X size={20} />
                </button>
              </div>

              {/* Run button */}
              {!result && (
                <button
                  onClick={handleAnalyze}
                  disabled={isAnalyzing}
                  className="bg-teal-600 text-white px-8 py-3 rounded-lg font-medium hover:bg-teal-700 transition-all disabled:opacity-70 disabled:cursor-not-allowed flex items-center gap-2"
                >
                  {isAnalyzing ? (
                    <>
                      <Activity className="animate-spin" size={20} />
                      {t('analysis.processing')}
                    </>
                  ) : (
                    <>
                      {t('analysis.run')}
                      <ArrowRight size={20} />
                    </>
                  )}
                </button>
              )}
            </div>
          )}

          {/* ── Error state ─────────────────────────────────────── */}
          {error && (
            <div className="flex items-start gap-3 text-red-700 bg-red-50 p-4 rounded-lg border border-red-100">
              <AlertTriangle className="shrink-0 mt-0.5" size={18} />
              <div className="text-sm">
                <strong>{t('analysis.errorTitle')}:</strong> {error}
                <p className="mt-1 text-red-500 text-xs">{t('analysis.backendHint')}</p>
              </div>
            </div>
          )}
        </div>

        {/* ── Results Section ───────────────────────────────────── */}
        {result && (
          <div className="border-t border-slate-200 bg-slate-50 p-8 space-y-8">

            {/* Prediction cards */}
            <div className="grid md:grid-cols-2 gap-6">
              {/* Emotion */}
              <div className="bg-white p-6 rounded-lg border border-slate-200 shadow-sm">
                <h3 className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-4">
                  {t('analysis.predictedEmotion')}
                </h3>
                <div className="flex items-center justify-between mb-2">
                  <span className="text-2xl font-bold text-slate-800">
                    {localizeClassLabel(result.pred_emotion, 'emotion', lang)}
                  </span>
                  <span className="px-3 py-1 bg-green-100 text-green-800 text-sm font-bold rounded-full">
                    {result.confidence_emotion}%
                  </span>
                </div>
                <div className="h-2 bg-slate-100 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-teal-500 rounded-full transition-all duration-1000 ease-out"
                    style={{ width: `${result.confidence_emotion}%` }}
                  />
                </div>
              </div>

              {/* Gender */}
              <div className="bg-white p-6 rounded-lg border border-slate-200 shadow-sm">
                <h3 className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-4">
                  {t('analysis.predictedGender')}
                </h3>
                <div className="flex items-center justify-between mb-2">
                  <span className="text-2xl font-bold text-slate-800">
                    {localizeClassLabel(result.pred_gender, 'gender', lang)}
                  </span>
                  <span className="px-3 py-1 bg-blue-100 text-blue-800 text-sm font-bold rounded-full">
                    {result.confidence_gender}%
                  </span>
                </div>
                <div className="h-2 bg-slate-100 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-blue-400 rounded-full transition-all duration-1000 ease-out"
                    style={{ width: `${result.confidence_gender}%` }}
                  />
                </div>
              </div>
            </div>

            {/* Model explanation */}
            <div className="bg-white p-5 rounded-lg border border-slate-200 shadow-sm">
              <h3 className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2">
                {t('analysis.resultExplanation')}
              </h3>
              <p className="text-sm text-slate-700 leading-relaxed">
                {result.explanation ?? t('analysis.noExplanation')}
              </p>
            </div>

            {/* Grad-CAM Heatmaps */}
            <div className="grid md:grid-cols-2 gap-6">
              {result.heatmap_emotion_b64 && (
                <div>
                  <h3 className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-3">
                    {t('analysis.emotionHeatmap')}
                  </h3>
                  <img
                    src={`data:image/jpeg;base64,${result.heatmap_emotion_b64}`}
                    alt="Emotion Grad-CAM"
                    className="w-full rounded-lg border border-slate-200 shadow-sm"
                  />
                </div>
              )}
              {result.heatmap_gender_b64 && (
                <div>
                  <h3 className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-3">
                    {t('analysis.genderHeatmap')}
                  </h3>
                  <img
                    src={`data:image/jpeg;base64,${result.heatmap_gender_b64}`}
                    alt="Gender Grad-CAM"
                    className="w-full rounded-lg border border-slate-200 shadow-sm"
                  />
                </div>
              )}
            </div>

            {/* Token attributions */}
            {result.tokens_emotion.length > 0 && (
              <div>
                <h3 className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-3">
                  {t('analysis.topTokens')}
                </h3>
                <div className="flex flex-wrap gap-2">
                  {[...result.tokens_emotion]
                    .sort((a, b) => b.score - a.score)
                    .slice(0, 12)
                    .map((tk, i) => (
                      <span
                        key={i}
                        className="px-2 py-1 rounded text-xs font-mono border"
                        style={{
                          background: `rgba(13,148,136,${Math.min(tk.score, 1) * 0.7 + 0.1})`,
                          borderColor: 'rgba(13,148,136,0.3)',
                          color: tk.score > 0.5 ? '#fff' : '#334155',
                        }}
                      >
                        {tk.token}
                      </span>
                    ))}
                </div>
              </div>
            )}

            {/* Disclaimer */}
            <div className="flex items-start gap-3 text-amber-700 bg-amber-50 p-4 rounded-lg border border-amber-100">
              <AlertTriangle className="shrink-0 mt-0.5" size={18} />
              <div className="text-sm">
                <strong>{t('analysis.disclaimerTitle')}:</strong> {t('analysis.disclaimer')}
              </div>
            </div>
          </div>
        )}
      </div>
    </motion.div>
  );
}

function AboutPage() {
  const { t } = useTranslation();
  const facts = t('about.facts') as FactItem[];
  const goals = t('about.goals') as string[];
  const dataPoints = t('about.dataPoints') as string[];
  const methodologyCards = t('about.methodologyCards') as ContentGroup[];
  const emotionMetrics = t('about.emotionMetrics') as FactItem[];
  const genderMetrics = t('about.genderMetrics') as FactItem[];
  const deliverables = t('about.deliverables') as string[];
  const limitations = t('about.limitations') as string[];
  const futureWork = t('about.futureWork') as string[];

  return (
    <motion.div 
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-32 pb-20"
    >
      <section className="rounded-[32px] border border-stone-200 bg-[linear-gradient(135deg,#ffffff_0%,#f8fafc_50%,#eef7f4_100%)] p-6 shadow-sm sm:p-8 lg:p-10">
        <SectionLabel>{t('about.eyebrow')}</SectionLabel>
        <div className="mt-4 grid gap-8 xl:grid-cols-[0.95fr_1.05fr]">
          <div>
            <h1 className="font-display text-3xl font-bold text-slate-900 sm:text-4xl">
              {t('about.aboutTitle')}
            </h1>
            <p className="mt-4 text-lg leading-relaxed text-slate-700">
              {t('about.objectiveText')}
            </p>
          </div>
          <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
            {facts.map((item) => (
              <div key={item.label} className="rounded-2xl border border-stone-200 bg-white/85 p-4 shadow-sm">
                <div className="text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-500">{item.label}</div>
                <div className="mt-2 text-sm leading-relaxed text-slate-800">{item.value}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="mt-10 grid gap-8 xl:grid-cols-[0.92fr_1.08fr]">
        <div className="space-y-8">
          <div className="rounded-[28px] border border-stone-200 bg-white p-6 shadow-sm">
            <div className="flex items-center gap-3">
              <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-teal-50 text-teal-700">
                <Target size={20} />
              </div>
              <h2 className="font-display text-2xl font-semibold text-slate-900">{t('about.goalsTitle')}</h2>
            </div>
            <div className="mt-6 space-y-3">
              {goals.map((item, index) => (
                <div key={index} className="flex gap-3 rounded-2xl bg-stone-50 px-4 py-4">
                  <CheckCircle size={17} className="mt-0.5 shrink-0 text-teal-600" />
                  <p className="text-sm leading-relaxed text-slate-700">{item}</p>
                </div>
              ))}
            </div>
          </div>

          <div className="rounded-[28px] border border-stone-200 bg-white p-6 shadow-sm">
            <div className="flex items-center gap-3">
              <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-amber-50 text-amber-700">
                <Database size={20} />
              </div>
              <h2 className="font-display text-2xl font-semibold text-slate-900">{t('about.dataTitle')}</h2>
            </div>
            <p className="mt-4 text-sm leading-relaxed text-slate-600">{t('about.dataIntro')}</p>
            <div className="mt-5 space-y-3">
              {dataPoints.map((item, index) => (
                <div key={index} className="flex gap-3 border-b border-stone-100 pb-3 last:border-b-0 last:pb-0">
                  <span className="mt-2 h-1.5 w-1.5 shrink-0 rounded-full bg-slate-400" />
                  <p className="text-sm leading-relaxed text-slate-700">{item}</p>
                </div>
              ))}
            </div>
          </div>

          <div className="rounded-[28px] border border-stone-200 bg-white p-6 shadow-sm">
            <div className="flex items-center gap-3">
              <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-sky-50 text-sky-700">
                <Rocket size={20} />
              </div>
              <h2 className="font-display text-2xl font-semibold text-slate-900">{t('about.deliverablesTitle')}</h2>
            </div>
            <div className="mt-6 grid gap-3">
              {deliverables.map((item, index) => (
                <div key={index} className="rounded-2xl border border-stone-200 bg-stone-50 px-4 py-4 text-sm leading-relaxed text-slate-700">
                  {item}
                </div>
              ))}
            </div>
          </div>
        </div>

        <div className="rounded-[28px] border border-stone-200 bg-white p-6 shadow-sm sm:p-8">
          <div className="flex items-center gap-3">
            <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-emerald-50 text-emerald-700">
              <Workflow size={20} />
            </div>
            <div>
              <h2 className="font-display text-2xl font-semibold text-slate-900">{t('about.methodologyTitle')}</h2>
              <p className="mt-1 text-sm text-slate-500">{t('about.methodologyIntro')}</p>
            </div>
          </div>

          <div className="mt-6 grid gap-4 md:grid-cols-2">
            {methodologyCards.map((group, index) => {
              const Icon = [Layers3, Cpu, FlaskConical, Sparkles][index] ?? FileText;
              return (
                <div key={group.title} className="rounded-2xl border border-stone-200 bg-[linear-gradient(180deg,#ffffff_0%,#f8fafc_100%)] p-5">
                  <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-slate-900 text-white">
                    <Icon size={18} />
                  </div>
                  <h3 className="mt-4 text-lg font-semibold text-slate-900">{group.title}</h3>
                  <div className="mt-4 space-y-3">
                    {group.items.map((item, itemIndex) => (
                      <div key={itemIndex} className="flex gap-3">
                        <span className="mt-2 h-1.5 w-1.5 shrink-0 rounded-full bg-teal-500" />
                        <p className="text-sm leading-relaxed text-slate-600">{item}</p>
                      </div>
                    ))}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </section>

      <section className="mt-10 rounded-[32px] border border-stone-200 bg-white p-6 shadow-sm sm:p-8">
        <div className="flex flex-col gap-3 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <SectionLabel>{t('about.resultsEyebrow')}</SectionLabel>
            <h2 className="mt-4 font-display text-3xl font-semibold text-slate-900">{t('about.resultsTitle')}</h2>
          </div>
          <p className="max-w-2xl text-sm leading-relaxed text-slate-600">{t('about.resultsIntro')}</p>
        </div>

        <div className="mt-8 grid gap-6 lg:grid-cols-2">
          <div className="rounded-[28px] border border-stone-200 bg-[linear-gradient(180deg,#f8fffd_0%,#ffffff_100%)] p-6">
            <div className="flex items-center gap-3">
              <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-teal-50 text-teal-700">
                <BarChart3 size={20} />
              </div>
              <div>
                <h3 className="text-xl font-semibold text-slate-900">{t('about.emotionResultsTitle')}</h3>
                <p className="mt-1 text-sm text-slate-500">{t('about.emotionResultsText')}</p>
              </div>
            </div>
            <div className="mt-6 grid grid-cols-2 gap-4">
              {emotionMetrics.map((item) => (
                <div key={item.label} className="rounded-2xl border border-stone-200 bg-white p-4 shadow-sm">
                  <div className="text-2xl font-display font-bold text-slate-900">{item.value}</div>
                  <div className="mt-1 text-xs uppercase tracking-[0.16em] text-slate-500">{item.label}</div>
                </div>
              ))}
            </div>
          </div>

          <div className="rounded-[28px] border border-stone-200 bg-[linear-gradient(180deg,#fff9f2_0%,#ffffff_100%)] p-6">
            <div className="flex items-center gap-3">
              <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-amber-50 text-amber-700">
                <Activity size={20} />
              </div>
              <div>
                <h3 className="text-xl font-semibold text-slate-900">{t('about.genderResultsTitle')}</h3>
                <p className="mt-1 text-sm text-slate-500">{t('about.genderResultsText')}</p>
              </div>
            </div>
            <div className="mt-6 grid grid-cols-2 gap-4">
              {genderMetrics.map((item) => (
                <div key={item.label} className="rounded-2xl border border-stone-200 bg-white p-4 shadow-sm">
                  <div className="text-2xl font-display font-bold text-slate-900">{item.value}</div>
                  <div className="mt-1 text-xs uppercase tracking-[0.16em] text-slate-500">{item.label}</div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      <section className="mt-10 grid gap-8 lg:grid-cols-2">
        <div className="rounded-[28px] border border-stone-200 bg-white p-6 shadow-sm">
          <div className="flex items-center gap-3">
            <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-rose-50 text-rose-700">
              <AlertTriangle size={20} />
            </div>
            <h2 className="font-display text-2xl font-semibold text-slate-900">{t('about.limitationsTitle')}</h2>
          </div>
          <div className="mt-6 space-y-3">
            {limitations.map((item, index) => (
              <div key={index} className="flex gap-3 rounded-2xl bg-stone-50 px-4 py-4">
                <span className="mt-2 h-1.5 w-1.5 shrink-0 rounded-full bg-rose-400" />
                <p className="text-sm leading-relaxed text-slate-700">{item}</p>
              </div>
            ))}
          </div>
        </div>

        <div className="rounded-[28px] border border-stone-200 bg-white p-6 shadow-sm">
          <div className="flex items-center gap-3">
            <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-violet-50 text-violet-700">
              <FlaskConical size={20} />
            </div>
            <h2 className="font-display text-2xl font-semibold text-slate-900">{t('about.futureWorkTitle')}</h2>
          </div>
          <div className="mt-6 space-y-3">
            {futureWork.map((item, index) => (
              <div key={index} className="flex gap-3 rounded-2xl bg-stone-50 px-4 py-4">
                <span className="mt-2 h-1.5 w-1.5 shrink-0 rounded-full bg-violet-400" />
                <p className="text-sm leading-relaxed text-slate-700">{item}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="mt-10 rounded-[30px] border border-amber-200 bg-amber-50 p-6 shadow-sm">
        <div className="flex items-start gap-4">
          <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl bg-amber-100 text-amber-700">
            <Shield size={20} />
          </div>
          <div>
            <h2 className="font-display text-xl font-semibold text-amber-900">{t('about.disclaimerTitle')}</h2>
            <p className="mt-3 text-sm leading-relaxed text-amber-900/90">{t('about.disclaimer')}</p>
          </div>
        </div>
      </section>
    </motion.div>
  );
}

// --- Main App Component ---

export default function App() {
  const [page, setPage] = useState<Page>('home');
  const { t } = useTranslation();

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900 font-sans selection:bg-teal-100 selection:text-teal-900">
      <Navigation currentPage={page} setPage={setPage} />
      
      <AnimatePresence mode="wait">
        {page === 'home' && <HomePage setPage={setPage} />}
        {page === 'analysis' && <AnalysisPage />}
        {page === 'about' && <AboutPage />}
      </AnimatePresence>

      <footer className="bg-white border-t border-slate-200 py-8 mt-auto">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col md:flex-row justify-between items-center gap-4">
          <p className="text-sm text-slate-500">
            {t('footer.copyright')}
          </p>
          <div className="flex gap-6 text-sm text-slate-500">
            <a href="#" className="hover:text-teal-600 transition-colors">{t('footer.privacy')}</a>
            <a href="#" className="hover:text-teal-600 transition-colors">{t('footer.terms')}</a>
            <a href="#" className="hover:text-teal-600 transition-colors">{t('footer.contact')}</a>
          </div>
        </div>
      </footer>
    </div>
  );
}
