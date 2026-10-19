// Configurações do cliente (só administrador; o porteiro confere).
// Lê e grava cliente.json e marca/logo.png no repositório do cliente. Cada gravação dispara,
// no GitHub, a rotina que recalcula fontes e horários e publica o painel de novo.
import { json } from "../../lib/auth.js";
import { validaConfig, validaLogo } from "../../lib/config.js";
const gh = (env, path, init = {}) => fetch(`${env.GH_API || "https://api.github.com"}/repos/${env.GH_REPO}${path}`, { ...init, headers: { Authorization: `Bearer ${env.GH_TOKEN}`, Accept: "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28", "User-Agent": "redacao-inteligente", "Content-Type": "application/json" } });
const b64dec = b => new TextDecoder().decode(Uint8Array.from(atob(b.replace(/\s/g, "")), c => c.charCodeAt(0)));
const b64enc = t => { const u = new TextEncoder().encode(t); let s = ""; for (let i = 0; i < u.length; i += 0x8000) s += String.fromCharCode(...u.subarray(i, i + 0x8000)); return btoa(s) };
async function le(env, caminho) {
  const r = await gh(env, `/contents/${caminho}?ref=main`);
  if (r.status === 404) return null;
  if (!r.ok) throw new Error(`O GitHub respondeu ${r.status} ao ler ${caminho}.`);
  return r.json();
}
// Um commit só com todos os arquivos (logo e configuração), para a rotina de configuração rodar uma vez.
async function commit(env, arquivos, msg) {
  const ok = async (r, o) => { if (!r.ok) throw new Error(`O GitHub respondeu ${r.status} ao ${o}.`); return r.json() };
  for (let tentativa = 0; tentativa < 2; tentativa++) {
    const ref = await ok(await gh(env, "/git/ref/heads/main"), "ler o repositório");
    const base = await ok(await gh(env, `/git/commits/${ref.object.sha}`), "ler o último commit");
    const tree = [];
    for (const f of arquivos) {
      const blob = await ok(await gh(env, "/git/blobs", { method: "POST", body: JSON.stringify({ content: f.b64, encoding: "base64" }) }), "enviar " + f.path);
      tree.push({ path: f.path, mode: "100644", type: "blob", sha: blob.sha });
    }
    const t = await ok(await gh(env, "/git/trees", { method: "POST", body: JSON.stringify({ base_tree: base.tree.sha, tree }) }), "montar o commit");
    const c = await ok(await gh(env, "/git/commits", { method: "POST", body: JSON.stringify({ message: msg, tree: t.sha, parents: [ref.object.sha] }) }), "criar o commit");
    const u = await gh(env, "/git/refs/heads/main", { method: "PATCH", body: JSON.stringify({ sha: c.sha, force: false }) });
    if (u.ok) return c.sha;
    if (u.status !== 422) throw new Error(`O GitHub respondeu ${u.status} ao gravar.`);
  }
  throw new Error("O repositório mudou durante a gravação. Tente de novo.");
}
export async function onRequestGet({ env }) {
  try {
    const f = await le(env, "cliente.json");
    if (!f) return json({ error: "cliente.json não encontrado no repositório." }, 404);
    return json({ cliente: JSON.parse(b64dec(f.content)), sha: f.sha });
  } catch (e) { return json({ error: e.message }, 502) }
}
export async function onRequestPost({ request, env, data }) {
  const b = await request.json().catch(() => ({}));
  try {
    const f = await le(env, "cliente.json");
    const atual = f ? JSON.parse(b64dec(f.content)) : {};
    if (f && b.sha && b.sha !== f.sha) return json({ error: "Alguém salvou as configurações depois que você abriu a página. Recarregue e confira antes de salvar." }, 409);
    const { config, erros } = validaConfig(b.cliente, atual);
    if (erros.length) return json({ error: erros.join(" ") }, 400);
    const quem = data.usuario.login, arquivos = [];
    if (b.logo) {
      const L = validaLogo(b.logo);
      if (L.erro) return json({ error: L.erro }, 400);
      arquivos.push({ path: "marca/logo.png", b64: L.b64 });
      config.marca.logo = "marca/logo.png";
    }
    arquivos.unshift({ path: "cliente.json", b64: b64enc(JSON.stringify(config, null, 2) + "\n") });
    await commit(env, arquivos, `Configurações atualizadas por ${quem}`);
    const g = await le(env, "cliente.json");
    return json({ ok: true, sha: g && g.sha });
  } catch (e) { return json({ error: e.message }, e.status || 502) }
}
