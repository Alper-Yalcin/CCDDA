import React, { createContext, useContext, useEffect, useState } from 'react';
import en from './locales/en.json';
import tr from './locales/tr.json';

type Lang = 'en' | 'tr';

const resources: Record<Lang, any> = {
  en,
  tr,
};

type I18nContextType = {
  lang: Lang;
  setLang: (l: Lang) => void;
  t: (key: string, vars?: Record<string, any>) => string;
};

const I18nContext = createContext<I18nContextType>({
  lang: 'en',
  setLang: () => {},
  t: (k) => k,
});

export function I18nProvider({ children }: { children: React.ReactNode }) {
  const [lang, setLangState] = useState<Lang>(() => (localStorage.getItem('lang') as Lang) || 'en');

  useEffect(() => {
    localStorage.setItem('lang', lang);
  }, [lang]);

  const setLang = (l: Lang) => setLangState(l);

  const t = (key: string, vars?: Record<string, any>) => {
    const parts = key.split('.');
    let v: any = resources[lang];
    for (const p of parts) {
      v = v?.[p];
      if (v === undefined) return key;
    }
    // If the resolved value is a string, perform variable replacement and return string
    if (typeof v === 'string') {
      let s = v as string;
      if (vars) {
        Object.keys(vars).forEach((k) => {
          s = s.replace(new RegExp(`{{${k}}}`, 'g'), String(vars[k]));
        });
      }
      return s;
    }
    // For arrays or objects, return as-is so callers can use .map or access properties
    return v;
  };

  return <I18nContext.Provider value={{ lang, setLang, t }}>{children}</I18nContext.Provider>;
}

export function useTranslation() {
  return useContext(I18nContext);
}

export default I18nProvider;
