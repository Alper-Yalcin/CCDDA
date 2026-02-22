/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import { useState } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { Upload, ArrowRight, Activity, Shield, Brain, AlertTriangle, FileText, CheckCircle, X } from 'lucide-react';
import { useTranslation } from './i18n';

// --- Types ---
type Page = 'home' | 'analysis' | 'about';

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

function HomePage({ setPage }: { setPage: (p: Page) => void }) {
  const { t } = useTranslation();

  return (
    <motion.div 
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -10 }}
      className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-32 pb-20"
    >
      <div className="grid lg:grid-cols-2 gap-16 items-center">
        <div>
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-slate-100 border border-slate-200 text-slate-600 text-xs font-semibold uppercase tracking-wide mb-6">
            <Activity size={12} className="text-teal-600" />
            {t('hero.badge')}
          </div>
          <h1 className="font-display text-4xl md:text-5xl font-bold text-slate-900 leading-tight mb-6">
            {t('hero.title').split("\n").map((s, i) => (
              <span key={i}>
                {i > 0 && <br />}
                {i === 1 ? <span className="text-teal-600">{s}</span> : s}
              </span>
            ))}
          </h1>
          <p className="text-lg text-slate-600 mb-8 leading-relaxed max-w-xl text-justify">
            {t('hero.subtitle')}
          </p>
          
          <div className="space-y-4 mb-10">
            {t('hero.features').map((item: string, i: number) => (
              <div key={i} className="flex items-center gap-3 text-slate-700">
                <CheckCircle size={18} className="text-teal-500" />
                <span>{item}</span>
              </div>
            ))}
          </div>

          <div className="flex gap-4">
            <button 
              onClick={() => setPage('analysis')}
              className="inline-flex items-center justify-center gap-2 bg-teal-600 text-white px-6 py-3 rounded-lg font-medium hover:bg-teal-700 transition-all shadow-sm hover:shadow-md"
            >
              {t('hero.start')}
              <ArrowRight size={18} />
            </button>
            <button 
              onClick={() => setPage('about')}
              className="inline-flex items-center justify-center gap-2 bg-white text-slate-700 border border-slate-200 px-6 py-3 rounded-lg font-medium hover:bg-slate-50 transition-all"
            >
              {t('hero.methodology')}
            </button>
          </div>
        </div>

        <div className="relative">
          <div className="absolute -inset-4 bg-slate-100 rounded-full blur-3xl opacity-60"></div>
          <div className="relative bg-white rounded-xl shadow-lg border border-slate-200 p-2">
            <div className="aspect-[4/3] bg-slate-50 rounded-lg overflow-hidden relative">
               <img 
                 src="https://images.unsplash.com/photo-1513364776144-60967b0f800f?q=80&w=2071&auto=format&fit=crop" 
                 alt="Child drawing concept" 
                 className="w-full h-full object-cover opacity-90"
               />
               <div className="absolute inset-0 bg-gradient-to-t from-slate-900/60 to-transparent flex items-end p-6">
                 <div className="text-white">
                   <div className="text-xs font-mono bg-black/50 inline-block px-2 py-1 rounded mb-2 backdrop-blur-sm">
                     CONFIDENCE: 94.2%
                   </div>
                   <p className="font-medium">Analysis Visualization Preview</p>
                 </div>
               </div>
            </div>
          </div>
        </div>
      </div>
    </motion.div>
  );
}

// Use same-origin API path; Vite dev proxy forwards /api/* to the Python backend.
const API_URL = '/api';

type ApiResult = {
  pred_emotion: string;
  pred_gender: string;
  confidence_emotion: number;
  confidence_gender: number;
  probs_emotion: number[];
  probs_gender: number[];
  heatmap_emotion_b64: string | null;
  heatmap_gender_b64: string | null;
  tokens_emotion: { token: string; score: number }[];
  tokens_gender: { token: string; score: number }[];
};

function AnalysisPage() {
  const { t } = useTranslation();
  const [file, setFile] = useState<File | null>(null);
  const [text, setText] = useState('');
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [result, setResult] = useState<ApiResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
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
      form.append('text', text);

      const res = await fetch(`${API_URL}/predict`, { method: 'POST', body: form });
      if (!res.ok) {
        const detail = await res.json().catch(() => ({}));
        throw new Error(detail?.detail || `HTTP ${res.status}`);
      }
      const raw = await res.json();

      // Normalize backend responses: older/newer backends may use different keys.
      const data: ApiResult = ((): ApiResult => {
        if (raw.pred_emotion) return raw as ApiResult;
        // fallback when backend returns { emotion, emotion_confidence, gender, gender_confidence, ... }
        if (raw.emotion || raw.gender) {
          const emotion_conf = Number(raw.emotion_confidence ?? raw.emotion_confidence) || 0;
          const gender_conf = Number(raw.gender_confidence ?? raw.gender_confidence) || 0;
          const toPct = (v: number) => (v > 0 && v <= 1 ? Math.round(v * 1000) / 10 : Math.round(v * 10) / 10);
          return {
            pred_emotion: raw.emotion ?? String(raw.pred_emotion ?? ''),
            pred_gender: raw.gender ?? String(raw.pred_gender ?? ''),
            confidence_emotion: toPct(emotion_conf),
            confidence_gender: toPct(gender_conf),
            probs_emotion: raw.probs_emotion ?? [],
            probs_gender: raw.probs_gender ?? [],
            heatmap_emotion_b64: raw.heatmap_emotion_b64 ?? raw.heatmap_emotion ?? null,
            heatmap_gender_b64: raw.heatmap_gender_b64 ?? raw.heatmap_gender ?? null,
            tokens_emotion: raw.tokens_emotion ?? [],
            tokens_gender: raw.tokens_gender ?? [],
          } as ApiResult;
        }

        // Default safe cast
        return raw as ApiResult;
      })();

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
                  onClick={() => { setFile(null); setResult(null); setError(null); setText(''); }}
                  className="absolute top-2 right-2 p-1 bg-white/80 rounded-full hover:bg-white text-slate-600"
                >
                  <X size={20} />
                </button>
              </div>

              {/* Optional text input */}
              <div className="w-full">
                <label className="block text-sm font-medium text-slate-700 mb-1">
                  {t('analysis.textLabel')}
                </label>
                <textarea
                  rows={3}
                  value={text}
                  onChange={(e) => setText(e.target.value)}
                  placeholder={t('analysis.textPlaceholder')}
                  className="w-full border border-slate-300 rounded-lg px-3 py-2 text-sm text-slate-800 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-teal-500 resize-none"
                />
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
                  <span className="text-2xl font-bold text-slate-800">{result.pred_emotion}</span>
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
                  <span className="text-2xl font-bold text-slate-800">{result.pred_gender}</span>
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

  return (
    <motion.div 
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 pt-32 pb-20"
    >
      <div className="mb-12">
        <h1 className="text-3xl font-display font-bold text-slate-900 mb-4">{t('about.aboutTitle')}</h1>
        <p className="text-xl text-slate-600 leading-relaxed">
          {t('about.objectiveText')}
        </p>
      </div>

      <div className="space-y-12">
        <section>
          <h2 className="text-xl font-bold text-slate-900 mb-4 flex items-center gap-2">
            <Brain className="text-teal-600" size={20} />
            {t('about.objective')}
          </h2>
          <p className="text-slate-700 leading-relaxed">
            The primary objective of this research is to develop a supportive tool for child psychologists and educators. 
            By automating the detection of emotional markers in drawings, we aim to provide an objective "second opinion" 
            that can highlight cases requiring further human attention. This tool is not intended to replace human judgment 
            but to augment it with data-driven insights.
          </p>
        </section>

        <section>
          <h2 className="text-xl font-bold text-slate-900 mb-4 flex items-center gap-2">
            <Activity className="text-teal-600" size={20} />
            {t('about.methodologyTitle')}
          </h2>
          <div className="bg-slate-50 border border-slate-200 rounded-lg p-6 mb-4">
            <div className="flex items-center justify-center h-32 text-slate-400 text-sm border-2 border-dashed border-slate-300 rounded">
              [CNN Architecture Diagram Placeholder: Input &rarr; Conv2D &rarr; MaxPool &rarr; Dense &rarr; Softmax]
            </div>
          </div>
          <p className="text-slate-700 leading-relaxed">
            The model employs a custom Convolutional Neural Network (CNN) architecture optimized for feature extraction 
            from sparse line drawings. It utilizes Grad-CAM (Gradient-weighted Class Activation Mapping) to provide 
            explainability, ensuring that the model's decisions are transparent and interpretable by clinicians.
          </p>
        </section>

        <section>
          <h2 className="text-xl font-bold text-slate-900 mb-4 flex items-center gap-2">
            <FileText className="text-teal-600" size={20} />
            {t('about.datasetTitle')}
          </h2>
          <p className="text-slate-700 leading-relaxed mb-6">
            The model was trained on the <strong>KIDO Dataset</strong>, comprising 5,000+ annotated drawings 
            labeled by child psychologists.
          </p>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {[
              { label: "Accuracy", val: "88.5%" },
              { label: "Precision", val: "86.2%" },
              { label: "Recall", val: "89.1%" },
              { label: "F1 Score", val: "87.6%" },
            ].map((m, i) => (
              <div key={i} className="bg-white p-4 rounded-lg border border-slate-200 shadow-sm text-center">
                <div className="text-xs text-slate-500 uppercase tracking-wider mb-1">{m.label}</div>
                <div className="text-xl font-bold text-teal-700">{m.val}</div>
              </div>
            ))}
          </div>
        </section>

        <section>
          <h2 className="text-xl font-bold text-slate-900 mb-4 flex items-center gap-2">
            <Shield className="text-teal-600" size={20} />
            Ethical Considerations
          </h2>
          <ul className="space-y-3 text-slate-700">
            <li className="flex gap-3">
              <span className="w-1.5 h-1.5 bg-slate-400 rounded-full mt-2 shrink-0"></span>
              <span><strong>Data Privacy:</strong> All images processed are ephemeral and are not stored on our servers post-analysis.</span>
            </li>
            <li className="flex gap-3">
              <span className="w-1.5 h-1.5 bg-slate-400 rounded-full mt-2 shrink-0"></span>
              <span><strong>Bias Mitigation:</strong> The dataset was balanced across diverse cultural backgrounds to minimize cultural bias in artistic expression.</span>
            </li>
            <li className="flex gap-3">
              <span className="w-1.5 h-1.5 bg-slate-400 rounded-full mt-2 shrink-0"></span>
              <span><strong>Human-in-the-Loop:</strong> This system is strictly designed as a decision-support system, not an autonomous diagnostic agent.</span>
            </li>
          </ul>
        </section>
      </div>
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
        {page === 'home' && <HomePage key="home" setPage={setPage} />}
        {page === 'analysis' && <AnalysisPage key="analysis" />}
        {page === 'about' && <AboutPage key="about" />}
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

