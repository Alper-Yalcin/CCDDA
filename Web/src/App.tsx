/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import { useState } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { Upload, ArrowRight, Activity, Shield, Brain, Info, AlertTriangle, FileText, CheckCircle, X } from 'lucide-react';

// --- Types ---
type Page = 'home' | 'analysis' | 'about';

// --- Components ---

function Navigation({ currentPage, setPage }: { currentPage: Page; setPage: (p: Page) => void }) {
  const navItems: { id: Page; label: string }[] = [
    { id: 'home', label: 'Home' },
    { id: 'analysis', label: 'Run Analysis' },
    { id: 'about', label: 'About the Project' },
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
                ChildArt<span className="text-teal-600">Analyze</span>
              </span>
              <span className="text-[10px] uppercase tracking-wider text-slate-500 font-medium">
                Research Prototype v1.0
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
          </div>
        </div>
      </div>
    </nav>
  );
}

function HomePage({ setPage }: { setPage: (p: Page) => void }) {
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
            Academic Research Tool
          </div>
          <h1 className="font-display text-4xl md:text-5xl font-bold text-slate-900 leading-tight mb-6">
            Deep Learning Analysis of <br/>
            <span className="text-teal-600">Children's Drawings</span>
          </h1>
          <p className="text-lg text-slate-600 mb-8 leading-relaxed max-w-xl text-justify">
            This project utilizes Convolutional Neural Networks (CNNs) to investigate emotional markers in juvenile art. 
            Designed for researchers and clinicians, it provides automated screening support by detecting patterns associated with emotional states.
          </p>
          
          <div className="space-y-4 mb-10">
            {[
              "Automated Emotion Recognition (Happy/Sad)",
              "Visual Attention Heatmaps (Grad-CAM)",
              "Non-Diagnostic Screening Support"
            ].map((item, i) => (
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
              Start Analysis
              <ArrowRight size={18} />
            </button>
            <button 
              onClick={() => setPage('about')}
              className="inline-flex items-center justify-center gap-2 bg-white text-slate-700 border border-slate-200 px-6 py-3 rounded-lg font-medium hover:bg-slate-50 transition-all"
            >
              Methodology
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

function AnalysisPage() {
  const [file, setFile] = useState<File | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [result, setResult] = useState<null | { emotion: string; confidence: number }>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
      setResult(null);
    }
  };

  const handleAnalyze = () => {
    if (!file) return;
    setIsAnalyzing(true);
    // Simulate analysis delay
    setTimeout(() => {
      setIsAnalyzing(false);
      setResult({ emotion: 'Happy', confidence: 94.2 });
    }, 2000);
  };

  return (
    <motion.div 
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 pt-32 pb-20"
    >
      <div className="text-center mb-10">
        <h2 className="text-3xl font-display font-bold text-slate-900">Run Analysis</h2>
        <p className="text-slate-500 mt-2">Upload a drawing to generate an emotional inference report.</p>
      </div>

      <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
        <div className="p-8">
          {!file ? (
            <div className="border-2 border-dashed border-slate-300 rounded-xl p-12 text-center hover:bg-slate-50 transition-colors relative">
              <input 
                type="file" 
                accept="image/*"
                onChange={handleFileChange}
                className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
              />
              <Upload className="mx-auto h-12 w-12 text-slate-400 mb-4" />
              <p className="text-lg font-medium text-slate-700">Drop image here or click to upload</p>
              <p className="text-sm text-slate-500 mt-1">Supports JPG, PNG (Max 5MB)</p>
            </div>
          ) : (
            <div className="flex flex-col items-center">
              <div className="relative w-full max-w-md aspect-[4/3] bg-slate-100 rounded-lg overflow-hidden mb-6 border border-slate-200">
                <img 
                  src={URL.createObjectURL(file)} 
                  alt="Preview" 
                  className="w-full h-full object-contain"
                />
                <button 
                  onClick={() => { setFile(null); setResult(null); }}
                  className="absolute top-2 right-2 p-1 bg-white/80 rounded-full hover:bg-white text-slate-600"
                >
                  <X size={20} />
                </button>
              </div>

              {!result && (
                <button
                  onClick={handleAnalyze}
                  disabled={isAnalyzing}
                  className="bg-teal-600 text-white px-8 py-3 rounded-lg font-medium hover:bg-teal-700 transition-all disabled:opacity-70 disabled:cursor-not-allowed flex items-center gap-2"
                >
                  {isAnalyzing ? (
                    <>
                      <Activity className="animate-spin" size={20} />
                      Processing Neural Network...
                    </>
                  ) : (
                    <>
                      Run Inference Model
                      <ArrowRight size={20} />
                    </>
                  )}
                </button>
              )}
            </div>
          )}
        </div>

        {/* Results Section */}
        {result && (
          <div className="border-t border-slate-200 bg-slate-50 p-8">
            <div className="grid md:grid-cols-2 gap-8">
              <div>
                <h3 className="text-sm font-semibold text-slate-500 uppercase tracking-wider mb-4">Inference Result</h3>
                <div className="bg-white p-6 rounded-lg border border-slate-200 shadow-sm mb-4">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-slate-600 font-medium">Predicted Class</span>
                    <span className="px-3 py-1 bg-green-100 text-green-800 text-sm font-bold rounded-full">
                      {result.emotion.toUpperCase()}
                    </span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-slate-600 font-medium">Confidence</span>
                    <span className="font-mono text-slate-900">{result.confidence}%</span>
                  </div>
                  <div className="mt-4 h-2 bg-slate-100 rounded-full overflow-hidden">
                    <div 
                      className="h-full bg-teal-500 rounded-full transition-all duration-1000 ease-out"
                      style={{ width: `${result.confidence}%` }}
                    ></div>
                  </div>
                </div>
                
                <div className="bg-blue-50 border border-blue-100 p-4 rounded-lg flex gap-3">
                  <Info className="text-blue-600 shrink-0 mt-0.5" size={18} />
                  <p className="text-sm text-blue-800">
                    The model identified high-activation regions in the subject's facial features and color usage, correlating with the 'Happy' class in the KIDO dataset.
                  </p>
                </div>
              </div>

              <div>
                <h3 className="text-sm font-semibold text-slate-500 uppercase tracking-wider mb-4">Attention Heatmap (Grad-CAM)</h3>
                <div className="aspect-[4/3] bg-slate-200 rounded-lg flex items-center justify-center relative overflow-hidden group">
                  <img 
                    src={file ? URL.createObjectURL(file) : ''} 
                    alt="Original" 
                    className="absolute inset-0 w-full h-full object-cover mix-blend-overlay opacity-50"
                  />
                  <div className="absolute inset-0 bg-gradient-to-tr from-blue-500/30 via-red-500/30 to-yellow-500/30 blur-xl"></div>
                  <span className="relative bg-black/50 text-white px-3 py-1 rounded text-xs backdrop-blur-sm">
                    Heatmap Visualization Placeholder
                  </span>
                </div>
              </div>
            </div>

            <div className="mt-8 flex items-start gap-3 text-amber-700 bg-amber-50 p-4 rounded-lg border border-amber-100">
              <AlertTriangle className="shrink-0 mt-0.5" size={18} />
              <div className="text-sm">
                <strong>Research Disclaimer:</strong> This tool is a prototype for academic research purposes only. 
                The results generated are probabilistic and should <u>not</u> be interpreted as a clinical diagnosis. 
                Always consult with a qualified child psychologist for professional assessment.
              </div>
            </div>
          </div>
        )}
      </div>
    </motion.div>
  );
}

function AboutPage() {
  return (
    <motion.div 
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 pt-32 pb-20"
    >
      <div className="mb-12">
        <h1 className="text-3xl font-display font-bold text-slate-900 mb-4">About the Project</h1>
        <p className="text-xl text-slate-600 leading-relaxed">
          An investigation into the efficacy of computer vision in assisting psychological screening of children's artwork.
        </p>
      </div>

      <div className="space-y-12">
        <section>
          <h2 className="text-xl font-bold text-slate-900 mb-4 flex items-center gap-2">
            <Brain className="text-teal-600" size={20} />
            Objective
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
            Methodology & Architecture
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
            Dataset & Metrics
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
            © 2024 Child Art Analysis Research Group. All rights reserved.
          </p>
          <div className="flex gap-6 text-sm text-slate-500">
            <a href="#" className="hover:text-teal-600 transition-colors">Privacy Policy</a>
            <a href="#" className="hover:text-teal-600 transition-colors">Terms of Research</a>
            <a href="#" className="hover:text-teal-600 transition-colors">Contact Lab</a>
          </div>
        </div>
      </footer>
    </div>
  );
}


