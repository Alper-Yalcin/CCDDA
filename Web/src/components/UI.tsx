import { ArrowRight, type LucideIcon } from 'lucide-react';
import type { ButtonHTMLAttributes, ReactNode } from 'react';

type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: 'primary' | 'secondary';
  children: ReactNode;
};

export function Button({ variant = 'primary', children, className = '', ...props }: ButtonProps) {
  const classes =
    variant === 'primary'
      ? 'bg-[#E76F3C] text-white shadow-[0_16px_32px_-20px_rgba(231,111,60,0.95)] hover:bg-[#D95F2C]'
      : 'border border-[#E9CDBA] bg-surface text-ink hover:border-[#F08A5D] hover:bg-surface2';

  return (
    <button
      className={`inline-flex items-center justify-center gap-2 rounded-xl px-6 py-3 text-sm font-semibold transition hover:-translate-y-0.5 ${classes} ${className}`}
      {...props}
    >
      {children}
    </button>
  );
}

export function SectionEyebrow({ children }: { children: ReactNode }) {
  return (
    <div className="mb-5 inline-flex items-center rounded-full bg-tint px-4 py-2 text-xs font-bold uppercase tracking-[0.22em] text-[#E76F3C]">
      {children}
    </div>
  );
}

export function SectionTitle({ children, className = '' }: { children: ReactNode; className?: string }) {
  return (
    <h2 className={`font-serif text-3xl font-semibold leading-tight tracking-[-0.02em] text-ink md:text-4xl ${className}`}>
      {children}
    </h2>
  );
}

export function Card({ children, className = '' }: { children: ReactNode; className?: string }) {
  return (
    <section className={`rounded-2xl border border-line bg-surface shadow-[0_22px_55px_-44px_rgba(52,31,17,0.45)] ${className}`}>
      {children}
    </section>
  );
}

export function IconBubble({ icon: Icon, className = '' }: { icon: LucideIcon; className?: string }) {
  return (
    <div className={`grid h-14 w-14 place-items-center rounded-full bg-tint text-[#E76F3C] ${className}`}>
      <Icon size={24} strokeWidth={1.75} />
    </div>
  );
}

export function ArrowLink({ children, onClick }: { children: ReactNode; onClick?: () => void }) {
  return (
    <button onClick={onClick} className="inline-flex items-center gap-2 text-sm font-semibold text-[#E76F3C] transition hover:gap-3">
      {children}
      <ArrowRight size={16} />
    </button>
  );
}

export function PageMotion({ children, className = '' }: { children: ReactNode; className?: string }) {
  return (
    <div className={`mx-auto w-full max-w-[1720px] px-4 py-10 sm:px-6 lg:py-14 ${className}`}>
      {children}
    </div>
  );
}
