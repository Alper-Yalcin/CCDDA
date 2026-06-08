import { useState } from 'react';
import { AnimatePresence } from 'motion/react';
import { Navigation, Footer } from './components/Layout';
import { HomePage } from './pages/HomePage';
import { AnalysisPage } from './pages/AnalysisPage';
import { AboutPage } from './pages/AboutPage';
import type { Page } from './types';

export default function App() {
  const [page, setPage] = useState<Page>('home');

  return (
    <div className="min-h-screen bg-bg text-ink font-sans selection:bg-[#F08A5D]/20 selection:text-ink">
      <Navigation currentPage={page} setPage={setPage} />
      <main>
        <AnimatePresence mode="wait">
          {page === 'home' && <HomePage setPage={setPage} />}
          {page === 'analysis' && <AnalysisPage />}
          {page === 'about' && <AboutPage setPage={setPage} />}
        </AnimatePresence>
      </main>
      <Footer />
    </div>
  );
}
