import { Menu, MoonStar, SunMedium, X } from 'lucide-react';
import { useState } from 'react';
import type { Page } from '../types';
import { useTheme } from '../theme';

function ThemeToggle({ className = '' }: { className?: string }) {
  const { theme, toggleTheme } = useTheme();
  const isDark = theme === 'dark';
  return (
    <button
      type="button"
      onClick={toggleTheme}
      className={`grid h-11 w-11 place-items-center rounded-full border border-[var(--color-line)] bg-surface/70 text-ink transition hover:text-[#E76F3C] ${className}`}
      aria-label={isDark ? 'Açık temaya geç' : 'Koyu temaya geç'}
      title={isDark ? 'Açık tema' : 'Koyu tema'}
    >
      {isDark ? <SunMedium size={18} strokeWidth={1.8} /> : <MoonStar size={18} strokeWidth={1.8} />}
    </button>
  );
}

type NavigationProps = {
  currentPage: Page;
  setPage: (page: Page) => void;
};

const navItems: { key: string; page: Page; label: string }[] = [
  { key: 'home', page: 'home', label: 'Ana Sayfa' },
  { key: 'analysis', page: 'analysis', label: 'Analiz' },
  { key: 'about', page: 'about', label: 'Hakkında' },
];

export function Logo({ compact = false }: { compact?: boolean }) {
  return (
    <div className="flex items-center gap-3">
      <div className="grid h-11 w-11 shrink-0 place-items-center rounded-xl border border-line bg-surface p-1 shadow-[0_10px_26px_-22px_rgba(52,31,17,0.6)]">
        <img src="/logo.svg" alt="ÇizimAnaliz logosu" className="h-full w-full" />
      </div>
      {!compact && (
        <div className="min-w-0">
          <div className="text-[13px] font-bold leading-snug text-[#E76F3C] sm:text-[14px]">
            Çocuk Çizimlerinin Analizinde Üretken Yapay Zeka ve<br className="hidden sm:block" />
            <span className="font-bold text-[12px] sm:text-[13px]">Klinik Gösterge Tabanlı Açıklanabilir Derin Öğrenme Sistemi</span>
          </div>
        </div>
      )}
    </div>
  );
}

export function Navigation({ currentPage, setPage }: NavigationProps) {
  const [open, setOpen] = useState(false);

  const go = (page: Page) => {
    setPage(page);
    setOpen(false);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  return (
    <header className="sticky top-0 z-40 border-b border-line/80 bg-surface/88 backdrop-blur-md">
      <div className="mx-auto flex h-20 w-full max-w-[1520px] items-center justify-between px-4 sm:px-6">
        <button onClick={() => go('home')} className="shrink-0 text-left" aria-label="Ana sayfa">
          <Logo />
        </button>

        <nav className="hidden items-center gap-9 lg:flex">
          {navItems.map((item) => {
            const active = currentPage === item.page && item.key !== 'project';
            return (
              <button
                key={item.key}
                onClick={() => go(item.page)}
                className={`relative py-2 text-[15px] font-medium transition-colors ${
                  active ? 'text-[#E76F3C]' : 'text-ink hover:text-[#E76F3C]'
                }`}
              >
                {item.label}
                <span
                  className={`absolute inset-x-0 -bottom-1 mx-auto h-0.5 rounded-full bg-[#E76F3C] transition-all ${
                    active ? 'w-full opacity-100' : 'w-0 opacity-0'
                  }`}
                />
              </button>
            );
          })}
        </nav>

        <div className="hidden items-center gap-3 lg:flex">
          <ThemeToggle />
        </div>

        <div className="flex items-center gap-2 lg:hidden">
          <ThemeToggle />
          <button
            onClick={() => setOpen((v) => !v)}
            className="grid h-11 w-11 place-items-center rounded-xl border border-line bg-surface"
            aria-label="Menü"
          >
            {open ? <X size={21} /> : <Menu size={21} />}
          </button>
        </div>
      </div>

      {open && (
        <div className="border-t border-line bg-surface px-5 py-4 lg:hidden">
          <div className="grid gap-2">
            {navItems.map((item) => {
              const active = currentPage === item.page && item.key !== 'project';
              return (
                <button
                  key={item.key}
                  onClick={() => go(item.page)}
                  className={`rounded-xl px-4 py-3 text-left text-sm font-semibold ${
                    active ? 'bg-tint text-[#E76F3C]' : 'text-ink'
                  }`}
                >
                  {item.label}
                </button>
              );
            })}
          </div>
        </div>
      )}
    </header>
  );
}

// Footer kaldırıldı — boş export ile mevcut import'lar kırılmasın
export function Footer() {
  return null;
}
