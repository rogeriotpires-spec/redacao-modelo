/* Paleta a partir do logo: lê as cores do logo no navegador, escolhe a principal e monta
   combinações harmônicas (em OKLCH) com contraste conferido para texto e botões. */
window.Paleta = (() => {
  const hex = c => "#" + c.map(v => Math.round(Math.min(255, Math.max(0, v))).toString(16).padStart(2, "0")).join("");
  const rgb = h => [1, 3, 5].map(i => parseInt(h.slice(i, i + 2), 16));
  const lin = v => (v /= 255) <= 0.04045 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4;
  const delin = v => 255 * (v <= 0.0031308 ? 12.92 * v : 1.055 * v ** (1 / 2.4) - 0.055);
  function toOklch(h) {
    const [r, g, b] = rgb(h).map(lin);
    const l = Math.cbrt(0.4122214708 * r + 0.5363325363 * g + 0.0514459929 * b), m = Math.cbrt(0.2119034982 * r + 0.6806995451 * g + 0.1073969566 * b), s = Math.cbrt(0.0883024619 * r + 0.2817188376 * g + 0.6299787005 * b);
    const L = 0.2104542553 * l + 0.793617785 * m - 0.0040720468 * s, A = 1.9779984951 * l - 2.428592205 * m + 0.4505937099 * s, B = 0.0259040371 * l + 0.7827717662 * m - 0.808675766 * s;
    return { L, C: Math.hypot(A, B), H: (Math.atan2(B, A) * 180 / Math.PI + 360) % 360 };
  }
  function fromOklch({ L, C, H }) {
    for (let c = C; c >= 0; c -= 0.005) { // reduz o croma até caber em sRGB
      const a = c * Math.cos(H * Math.PI / 180), b = c * Math.sin(H * Math.PI / 180);
      const l = (L + 0.3963377774 * a + 0.2158037573 * b) ** 3, m = (L - 0.1055613458 * a - 0.0638541728 * b) ** 3, s = (L - 0.0894841775 * a - 1.291485548 * b) ** 3;
      const r = 4.0767416621 * l - 3.3077115913 * m + 0.2309699292 * s, g = -1.2684380046 * l + 2.6097574011 * m - 0.3413193965 * s, bb = -0.0041960863 * l - 0.7034186147 * m + 1.707614701 * s;
      if ([r, g, bb].every(v => v >= -0.0005 && v <= 1.0005)) return hex([r, g, bb].map(v => delin(Math.min(1, Math.max(0, v)))));
    }
    return hex([L, L, L].map(v => delin(v)));
  }
  const lum = h => { const [r, g, b] = rgb(h).map(lin); return 0.2126 * r + 0.7152 * g + 0.0722 * b };
  const contraste = (a, b) => { const x = lum(a), y = lum(b); return (Math.max(x, y) + 0.05) / (Math.min(x, y) + 0.05) };
  const comL = (h, L, Cmax) => { const o = toOklch(h); return fromOklch({ L, C: Math.min(o.C, Cmax ?? o.C), H: o.H }) };
  const giro = (h, g, L, C) => { const o = toOklch(h); return fromOklch({ L, C, H: (o.H + g + 360) % 360 }) };
  const dh = (a, b) => { const d = Math.abs(a - b) % 360; return d > 180 ? 360 - d : d };

  // cores do logo: amostra os pixels, ignora transparente, quase branco e quase preto, agrupa por tom
  function cores(img) {
    const k = Math.min(1, 160 / Math.max(img.naturalWidth, img.naturalHeight));
    const w = Math.max(1, Math.round(img.naturalWidth * k)), h = Math.max(1, Math.round(img.naturalHeight * k));
    const cv = Object.assign(document.createElement("canvas"), { width: w, height: h }), cx = cv.getContext("2d", { willReadFrequently: true });
    cx.drawImage(img, 0, 0, w, h);
    const d = cx.getImageData(0, 0, w, h).data, grupos = new Map(); let neutros = new Map();
    for (let i = 0; i < d.length; i += 4) {
      if (d[i + 3] < 128) continue;
      const hx = hex([d[i], d[i + 1], d[i + 2]]), o = toOklch(hx);
      if (o.L > 0.96 || o.L < 0.12) continue;
      const alvo = o.C < 0.04 ? neutros : grupos, key = o.C < 0.04 ? Math.round(o.L * 10) : Math.round(o.H / 15);
      const g = alvo.get(key) || { n: 0, r: 0, g: 0, b: 0 }; g.n++; g.r += d[i]; g.g += d[i + 1]; g.b += d[i + 2]; alvo.set(key, g);
    }
    const media = g => hex([g.r / g.n, g.g / g.n, g.b / g.n]);
    const vivas = [...grupos.values()].sort((a, b) => b.n - a.n).map(g => ({ hex: media(g), n: g.n }));
    const unicas = [];
    for (const c of vivas) if (!unicas.some(u => dh(toOklch(u.hex).H, toOklch(c.hex).H) < 25)) unicas.push(c);
    const neutras = [...neutros.values()].sort((a, b) => b.n - a.n).map(g => ({ hex: media(g), n: g.n }));
    return { vivas: unicas.slice(0, 5), neutras: neutras.slice(0, 2) };
  }

  // monta a paleta completa a partir de uma cor principal e (opcional) uma segunda cor
  function monta(primaria, segunda, nome) {
    const p = toOklch(primaria);
    const prim = fromOklch({ L: Math.min(Math.max(p.L, 0.38), 0.55), C: Math.min(p.C, 0.2), H: p.H });
    const escura = fromOklch({ L: 0.22, C: Math.min(p.C * 0.5, 0.06), H: p.H });
    let acento = fromOklch({ L: 0.5, C: Math.min(p.C, 0.17), H: p.H });
    while (contraste(acento, "#fcfcfb") < 4.6 && toOklch(acento).L > 0.2) acento = comL(acento, toOklch(acento).L - 0.03);
    const s = segunda ? toOklch(segunda) : null;
    const destaque = s && s.C > 0.05 && dh(s.H, p.H) > 30 ? fromOklch({ L: 0.86, C: Math.min(Math.max(s.C, 0.1), 0.17), H: s.H }) : dh(p.H, 95) > 40 ? fromOklch({ L: 0.87, C: 0.16, H: 92 }) : fromOklch({ L: 0.92, C: 0.1, H: p.H }); // sem segunda cor: dourado, que combina com quase tudo
    const sobre = contraste(escura, destaque) >= 4.5 ? escura : "#111111";
    return { nome, primaria: prim, escura, acento, destaque, sobre_destaque: sobre };
  }
  // três propostas: com as cores do próprio logo, análoga (vizinha no círculo) e complementar
  function propostas(c) {
    const base = c.vivas[0]?.hex || c.neutras[0]?.hex || "#0b3d91", seg = c.vivas[1]?.hex;
    const o = toOklch(base), cinza = o.C < 0.04;
    const out = [monta(cinza ? "#1f3b63" : base, seg, seg ? "Cores do logo" : "Cor do logo")];
    if (!cinza) {
      out.push(monta(base, giro(base, 35, 0.8, 0.14), "Análoga"));
      out.push(monta(base, giro(base, 180, 0.8, 0.15), "Complementar"));
    } else {
      out.push(monta("#7a1f2b", null, "Sóbria vinho"), monta("#0f5c4a", null, "Sóbria verde"));
    }
    return out;
  }
  // aplica nas variáveis de CSS das páginas
  function aplica(p, raiz = document.documentElement) {
    if (!p) return;
    const v = { "--marca": p.primaria, "--marca-esc": p.escura, "--acento": p.acento, "--destaque": p.destaque, "--sobre-destaque": p.sobre_destaque };
    for (const [k, x] of Object.entries(v)) if (x) raiz.style.setProperty(k, x);
  }
  return { cores, monta, propostas, aplica, contraste, toOklch };
})();
