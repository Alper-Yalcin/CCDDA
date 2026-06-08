import { ArrowRight, BadgeCheck, CirclePlay, Landmark, ShieldAlert } from 'lucide-react';
import { motion } from 'motion/react';
import { DrawingAnalysisHero, EditorialPipelineDiagram } from '../components/MedicalVisuals';
import { Button } from '../components/UI';
import { homeStats, howItWorks, technologyHighlights } from '../data/medvision';
import type { Page } from '../types';

const statsBandVariants = {
  hidden: {},
  show: { transition: { staggerChildren: 0.06 } },
};

const statItemVariants = {
  hidden: { opacity: 0, y: 14 },
  show: { opacity: 1, y: 0, transition: { duration: 0.42 } },
};

export function HomePage({ setPage }: { setPage: (page: Page) => void }) {
  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="overflow-hidden">
      <section className="relative border-b border-line/80 bg-bg">
        <div className="absolute inset-0 opacity-[0.42]" style={{ backgroundImage: 'linear-gradient(90deg, transparent 0 96%, #E9E1D7 96% 100%)', backgroundSize: '96px 96px' }} />
        <div className="relative mx-auto grid w-full max-w-[1520px] min-w-0 grid-cols-1 items-center gap-10 px-4 py-12 sm:px-6 lg:min-h-[760px] lg:grid-cols-[0.92fr_1.08fr] lg:py-14">
          <motion.div
            initial={{ opacity: 0, y: 24 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.55 }}
            className="min-w-0 max-w-[760px]"
          >
            <div className="mb-6 flex max-w-full flex-wrap items-start gap-3">
              <span className="inline-flex max-w-full rounded-full border border-line bg-surface/80 px-4 py-2 text-left text-[11px] font-bold uppercase leading-5 tracking-[0.14em] text-[#E76F3C] shadow-[0_10px_30px_-26px_rgba(52,31,17,0.55)] sm:text-xs sm:tracking-[0.2em]">
                Lisans Tezi Araştırma Çıktısı — 2026
              </span>
              <span className="inline-flex max-w-full items-center gap-2 rounded-full border border-[#E9CDBA] bg-tint/75 px-4 py-2 text-left text-[11px] font-bold uppercase leading-5 tracking-[0.12em] text-[#E76F3C] sm:text-xs sm:tracking-[0.16em]">
                <BadgeCheck size={14} className="shrink-0" strokeWidth={2.1} />
                <span>TÜBİTAK Onaylı Lisans Araştırma Projesi</span>
              </span>
            </div>

            <h1 className="max-w-4xl break-words font-serif text-5xl font-semibold leading-[1.02] tracking-[-0.025em] text-ink sm:text-6xl lg:text-7xl xl:text-[86px]">
              Çocuk Çizimlerinden Duyguları <span className="block text-[#E76F3C] sm:inline">Anlıyoruz.</span>
            </h1>

            <p className="mt-7 max-w-2xl text-base leading-8 text-muted sm:text-lg">
              ResNet-50 tabanlı Kavram Darboğazı (Concept Bottleneck) mimarisiyle KIDO veri setinde eğitilmiş; duyguya doğrudan pikselden değil, 16 figür-farkında klinik göstergeden ulaşan, Grad-CAM ve LLM destekli klinik açıklamayla karar desteği sunan prototip sistem.
            </p>

            <div className="mt-7 flex max-w-2xl gap-4 border-y border-line bg-surface/45 py-4">
              <div className="grid h-11 w-11 shrink-0 place-items-center rounded-full bg-[#0F4C81] text-white">
                <Landmark size={21} strokeWidth={1.75} />
              </div>
              <div>
                <div className="font-semibold text-ink">TÜBİTAK onaylı lisans tez projesi</div>
                <p className="mt-1 text-sm leading-6 text-muted">
                  Çalışma, lisans bitirme tezi kapsamında geliştirilen akademik araştırma ve prototip çıktılarıyla TÜBİTAK onaylı proje niteliğini ana proje kimliği olarak taşır.
                </p>
              </div>
            </div>

            <div className="mt-9 flex flex-col gap-3 sm:flex-row sm:flex-wrap sm:gap-4">
              <Button onClick={() => setPage('analysis')} className="group w-full !rounded-2xl px-8 py-4 text-base shadow-[0_20px_42px_-22px_rgba(231,111,60,1)] sm:w-auto">
                Analizi Başlat
                <ArrowRight size={18} className="transition-transform group-hover:translate-x-1" />
              </Button>
              <Button variant="secondary" onClick={() => setPage('about')} className="group w-full !rounded-2xl px-8 py-4 text-base sm:w-auto">
                <CirclePlay size={19} />
                Sistemi Keşfet
                <ArrowRight size={17} className="transition-transform group-hover:translate-x-1" />
              </Button>
            </div>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, x: 32, scale: 0.97 }}
            animate={{ opacity: 1, x: 0, scale: 1 }}
            transition={{ duration: 0.65, delay: 0.08 }}
            className="relative min-w-0"
          >
            <DrawingAnalysisHero />
          </motion.div>
        </div>
      </section>

      <StatsBand />

      <main className="mx-auto max-w-[1520px] px-4 sm:px-6">
        <section className="py-16 text-center sm:py-20">
          <div className="text-xs font-bold uppercase tracking-[0.42em] text-[#E76F3C]">SİSTEM YAKLAŞIMIMIZ</div>
          <h2 className="mx-auto mt-5 max-w-3xl font-serif text-4xl font-semibold leading-tight tracking-[-0.02em] text-ink md:text-5xl">
            Bilimsel. Açıklanabilir. Güvenilir.
          </h2>
          <div className="mx-auto mt-7 h-px w-24 bg-[#E76F3C]/55" />
        </section>

        <section className="border-y border-line py-16 sm:py-20">
          <div className="grid gap-10 lg:grid-cols-[0.35fr_1fr]">
            <div>
              <div className="text-xs font-bold uppercase tracking-[0.28em] text-[#E76F3C]">Nasıl Çalışır?</div>
              <h2 className="mt-4 font-serif text-4xl font-semibold leading-tight tracking-[-0.02em] text-ink">
                Çizimden açıklanabilir rapora uzanan süreç.
              </h2>
            </div>
            <div className="relative">
              <div className="absolute left-8 right-8 top-10 hidden h-px bg-line lg:block" />
              <div className="grid gap-8 lg:grid-cols-3">
                {howItWorks.map((step, index) => {
                  const Icon = step.icon;
                  return (
                    <motion.div
                      key={step.title}
                      initial={{ opacity: 0, y: 18 }}
                      whileInView={{ opacity: 1, y: 0 }}
                      viewport={{ once: true, amount: 0.35 }}
                      transition={{ duration: 0.42, delay: index * 0.07 }}
                      className="relative flex gap-5 border-t border-line pt-6 lg:block lg:border-t-0 lg:pt-0"
                    >
                      <div className="relative z-10 grid h-20 w-20 shrink-0 place-items-center rounded-full border border-line bg-surface text-[#E76F3C] shadow-[0_18px_42px_-34px_rgba(52,31,17,0.5)]">
                        <Icon size={30} strokeWidth={1.5} />
                        <span className="absolute -right-1 -top-1 grid h-7 w-7 place-items-center rounded-full bg-[#E76F3C] text-xs font-bold text-white">
                          {index + 1}
                        </span>
                      </div>
                      <div className="lg:mt-6">
                        <h3 className="font-serif text-2xl font-semibold leading-tight text-ink">{step.title}</h3>
                        <p className="mt-3 text-sm leading-7 text-muted">{step.body}</p>
                      </div>
                    </motion.div>
                  );
                })}
              </div>
            </div>
          </div>
        </section>

        <section className="py-16 sm:py-20">
          <div className="grid gap-10 lg:grid-cols-[0.35fr_1fr]">
            <div>
              <div className="text-xs font-bold uppercase tracking-[0.28em] text-[#E76F3C]">Sistem Mimarisi</div>
              <h2 className="mt-4 font-serif text-4xl font-semibold leading-tight tracking-[-0.02em] text-ink">
                Kavram darboğazı karar akışı.
              </h2>
              <p className="mt-5 text-sm leading-7 text-muted">
                Görüntüden önce klinik göstergeler çıkarılır; duygu sınıfı doğrudan piksellerden değil, bu açıklanabilir ara temsilden belirlenir.
              </p>
            </div>
            <EditorialPipelineDiagram />
          </div>
        </section>

        <section className="border-t border-line py-16 sm:py-20">
          <div className="grid gap-10 lg:grid-cols-[0.35fr_1fr]">
            <div>
              <div className="text-xs font-bold uppercase tracking-[0.28em] text-[#E76F3C]">Teknoloji & Yaklaşım</div>
              <h2 className="mt-4 font-serif text-4xl font-semibold leading-tight tracking-[-0.02em] text-ink">
                Tasarım gereği yorumlanabilir.
              </h2>
            </div>
            <div className="grid border-t border-line md:grid-cols-2">
              {technologyHighlights.map((item) => {
                const Icon = item.icon;
                return (
                  <div key={item.title} className="flex gap-4 border-b border-line py-6 md:odd:pr-7 md:even:border-l md:even:pl-7">
                    <div className="mt-1 grid h-11 w-11 shrink-0 place-items-center rounded-full bg-tint text-[#E76F3C]">
                      <Icon size={20} strokeWidth={1.75} />
                    </div>
                    <div>
                      <h3 className="font-semibold leading-snug text-ink">{item.title}</h3>
                      <p className="mt-2 text-sm leading-6 text-muted">{item.body}</p>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </section>

        <section className="mb-20 border-y border-line bg-tint/48 py-7">
          <div className="flex flex-col gap-6 px-1 md:flex-row md:items-center md:justify-between">
            <div className="flex items-start gap-4">
              <div className="grid h-12 w-12 shrink-0 place-items-center rounded-full bg-surface text-[#E76F3C]">
                <ShieldAlert size={23} strokeWidth={1.7} />
              </div>
              <div>
                <div className="font-serif text-2xl font-semibold text-ink">Kullanım Sınırı</div>
                <p className="mt-2 max-w-4xl text-sm leading-7 text-muted">
                  Bu sistem klinik tanı aracı değildir. Uzman değerlendirmesini desteklemek için tasarlanmış açıklanabilir bir karar destek prototipidir; tüm sonuçlar nitelikli bir uzman tarafından yorumlanmalıdır.
                </p>
              </div>
            </div>
            <Button variant="secondary" onClick={() => setPage('about')} className="group shrink-0 !rounded-2xl">
              Proje Hakkında
              <ArrowRight size={16} className="transition-transform group-hover:translate-x-1" />
            </Button>
          </div>
        </section>
      </main>
    </motion.div>
  );
}

function StatsBand() {
  return (
    <section className="relative bg-[#25231F] text-white">
      <div className="absolute inset-0 opacity-20" style={{ backgroundImage: 'linear-gradient(90deg, rgba(231,111,60,0.25) 1px, transparent 1px)', backgroundSize: '52px 52px' }} />
      <motion.div
        variants={statsBandVariants}
        initial="hidden"
        whileInView="show"
        viewport={{ once: true, amount: 0.25 }}
        className="relative mx-auto grid max-w-[1520px] sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6"
      >
        {homeStats.map((stat) => {
          const Icon = stat.icon;
          return (
            <motion.div
              key={stat.label}
              variants={statItemVariants}
              className="flex min-h-[116px] items-center gap-4 border-b border-white/10 px-5 py-6 sm:border-r lg:last:border-r-0 xl:border-b-0 xl:last:border-r-0"
            >
              <Icon size={27} className="shrink-0 text-[#F08A5D]" strokeWidth={1.55} />
              <div>
                <div className="font-serif text-3xl font-semibold leading-none text-[#FFF6EA]">{stat.value}</div>
                <div className="mt-2 text-sm leading-5 text-white/72">{stat.label}</div>
              </div>
            </motion.div>
          );
        })}
      </motion.div>
    </section>
  );
}
