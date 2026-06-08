import { useEffect, useRef, useState, type PointerEvent as ReactPointerEvent } from 'react';
import { Check, Eraser, Trash2, X } from 'lucide-react';
import { motion } from 'motion/react';
import { Button } from './UI';

const COLORS = ['#1F1F1F', '#E76F3C', '#2F80ED', '#5BAE7B', '#9B5DE5', '#F2C94C', '#EB5757'];
const BRUSH_SIZES = [4, 8, 16, 28];

type DrawModalProps = {
  onClose: () => void;
  onSave: (file: File, preview: string) => void;
};

function prepareContext(ctx: CanvasRenderingContext2D) {
  ctx.lineCap = 'round';
  ctx.lineJoin = 'round';
}

export function DrawModal({ onClose, onSave }: DrawModalProps) {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const canvasHostRef = useRef<HTMLDivElement | null>(null);
  const drawingRef = useRef(false);
  const [color, setColor] = useState(COLORS[0]);
  const [size, setSize] = useState(BRUSH_SIZES[1]);
  const [isEraser, setIsEraser] = useState(false);

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

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [onClose]);

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
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-3 sm:p-4"
      onClick={onClose}
    >
      <motion.div
        initial={{ opacity: 0, scale: 0.96, y: 12 }}
        animate={{ opacity: 1, scale: 1, y: 0 }}
        exit={{ opacity: 0, scale: 0.96, y: 12 }}
        className="flex h-[92vh] max-h-[860px] w-[96vw] max-w-[1180px] flex-col overflow-hidden rounded-2xl border border-line bg-surface shadow-2xl md:flex-row"
        onClick={(e) => e.stopPropagation()}
      >
        <aside
          aria-label="Çizim araçları"
          className="flex w-full shrink-0 flex-col border-b border-line bg-surface p-4 md:h-full md:w-56 md:border-b-0 md:border-r md:p-5"
        >
          <div className="flex items-center justify-between gap-3">
            <h3 className="font-serif text-2xl font-semibold text-ink">Çizim Yap</h3>
            <button
              type="button"
              onClick={onClose}
              title="Kapat"
              aria-label="Kapat"
              className="grid h-9 w-9 shrink-0 place-items-center rounded-lg text-muted transition hover:bg-tint hover:text-[#E76F3C]"
            >
              <X size={20} />
            </button>
          </div>

          <div className="mt-5 grid gap-5 overflow-y-auto pr-1 md:block md:space-y-6">
            <section>
              <p className="text-sm font-semibold text-ink">Renk</p>
              <div className="mt-3 grid grid-cols-7 gap-2 md:grid-cols-4">
                {COLORS.map((c) => (
                  <button
                    key={c}
                    type="button"
                    onClick={() => {
                      setColor(c);
                      setIsEraser(false);
                    }}
                    title={`Renk ${c}`}
                    aria-label={`Renk ${c}`}
                    className={`h-8 w-8 rounded-full border-2 transition ${
                      color === c && !isEraser ? 'scale-110 border-ink' : 'border-white shadow-sm hover:scale-105'
                    }`}
                    style={{ backgroundColor: c }}
                  />
                ))}
              </div>
            </section>

            <section>
              <p className="text-sm font-semibold text-ink">Kalem ucu</p>
              <div className="mt-3 grid grid-cols-4 gap-2 md:grid-cols-2">
                {BRUSH_SIZES.map((brushSize) => (
                  <button
                    key={brushSize}
                    type="button"
                    onClick={() => setSize(brushSize)}
                    title={`${brushSize}px`}
                    aria-label={`Kalem ucu ${brushSize}px`}
                    className={`grid h-11 place-items-center rounded-lg border transition ${
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
            </section>

            <section>
              <p className="text-sm font-semibold text-ink">Araçlar</p>
              <div className="mt-3 grid grid-cols-2 gap-2">
                <button
                  type="button"
                  onClick={() => setIsEraser((v) => !v)}
                  title="Silgi"
                  aria-label="Silgi"
                  className={`grid h-11 place-items-center rounded-lg border transition ${
                    isEraser
                      ? 'border-[#E76F3C] bg-tint text-[#E76F3C]'
                      : 'border-line bg-surface text-muted hover:border-[#F08A5D]'
                  }`}
                >
                  <Eraser size={18} />
                </button>
                <button
                  type="button"
                  onClick={clearCanvas}
                  title="Temizle"
                  aria-label="Temizle"
                  className="grid h-11 place-items-center rounded-lg border border-line bg-surface text-muted transition hover:border-[#EB5757] hover:text-[#EB5757]"
                >
                  <Trash2 size={18} />
                </button>
              </div>
            </section>
          </div>

          <div className="mt-5 flex gap-2 md:mt-auto md:flex-col md:pt-5">
            <Button type="button" onClick={handleSave} className="min-w-0 flex-1 md:w-full">
              <Check size={17} />
              Onayla
            </Button>
            <Button type="button" variant="secondary" onClick={onClose} className="min-w-0 flex-1 md:w-full">
              İptal
            </Button>
          </div>
        </aside>

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
