// Autenticação do produto: senhas com PBKDF2 (WebCrypto), sessão em cookie assinado (HMAC) e usuários no KV "USUARIOS".
// Segredos do projeto na Cloudflare: SESSION_SECRET (assinatura), SETUP_TOKEN (só para criar o primeiro administrador),
// GH_TOKEN (token do GitHub só com permissão de Actions no repositório do cliente) e GH_REPO (dono/repositorio).

const enc = new TextEncoder();
const b64u = buf => btoa(String.fromCharCode(...new Uint8Array(buf))).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
const unb64u = s => Uint8Array.from(atob(s.replace(/-/g, "+").replace(/_/g, "/") + "===".slice((s.length + 3) % 4)), c => c.charCodeAt(0));
export const ITER = 60000;
export const SESSAO_DIAS = 14;

export async function hashSenha(senha, salt = crypto.getRandomValues(new Uint8Array(16)), iter = ITER) {
  const key = await crypto.subtle.importKey("raw", enc.encode(senha), "PBKDF2", false, ["deriveBits"]);
  const bits = await crypto.subtle.deriveBits({ name: "PBKDF2", hash: "SHA-256", salt, iterations: iter }, key, 256);
  return { hash: b64u(bits), salt: b64u(salt), iter };
}
export async function confereSenha(senha, u) {
  if (!u || !u.hash) return false;
  const h = await hashSenha(senha, unb64u(u.salt), u.iter || ITER);
  return iguais(h.hash, u.hash);
}
function iguais(a, b) { if (a.length !== b.length) return false; let r = 0; for (let i = 0; i < a.length; i++) r |= a.charCodeAt(i) ^ b.charCodeAt(i); return r === 0 }

async function hmac(secret, data) {
  const key = await crypto.subtle.importKey("raw", enc.encode(secret), { name: "HMAC", hash: "SHA-256" }, false, ["sign"]);
  return b64u(await crypto.subtle.sign("HMAC", key, enc.encode(data)));
}
export async function criaSessao(env, u) {
  const p = b64u(enc.encode(JSON.stringify({ u: u.login, v: u.versao || 1, exp: Date.now() + SESSAO_DIAS * 864e5 })));
  return `${p}.${await hmac(env.SESSION_SECRET, p)}`;
}
export function cookieSessao(valor, maxAge = SESSAO_DIAS * 86400) {
  return `sessao=${valor}; Path=/; HttpOnly; Secure; SameSite=Lax; Max-Age=${maxAge}`;
}
export async function leSessao(request, env) {
  const m = (request.headers.get("Cookie") || "").match(/(?:^|;\s*)sessao=([^;]+)/);
  if (!m || !env.SESSION_SECRET) return null;
  const [p, sig] = m[1].split(".");
  if (!p || !sig || !iguais(sig, await hmac(env.SESSION_SECRET, p))) return null;
  let s; try { s = JSON.parse(new TextDecoder().decode(unb64u(p))) } catch (e) { return null }
  if (!s.exp || s.exp < Date.now()) return null;
  const u = await getUsuario(env, s.u);
  if (!u || u.ativo === false || (u.versao || 1) !== s.v) return null; // usuário removido, bloqueado ou com senha trocada
  return u;
}

const K = login => "u:" + String(login || "").toLowerCase();
export async function getUsuario(env, login) { const r = await env.USUARIOS.get(K(login)); return r ? JSON.parse(r) : null }
export async function putUsuario(env, u) { await env.USUARIOS.put(K(u.login), JSON.stringify(u)) }
export async function delUsuario(env, login) { await env.USUARIOS.delete(K(login)) }
export async function listaUsuarios(env) {
  const out = []; let cursor;
  do { const r = await env.USUARIOS.list({ prefix: "u:", cursor }); for (const k of r.keys) { const u = await getUsuario(env, k.name.slice(2)); if (u) out.push(u) } cursor = r.list_complete ? null : r.cursor } while (cursor);
  return out;
}
export const publico = u => ({ login: u.login, nome: u.nome, papel: u.papel, ativo: u.ativo !== false, criado: u.criado, ultimo_acesso: u.ultimo_acesso || null });

// limite de tentativas de login: 8 erros em 15 minutos por login e por IP
export async function bloqueado(env, chave) { const n = +(await env.USUARIOS.get("t:" + chave) || 0); return n >= 8 }
export async function erroLogin(env, chave) { const n = +(await env.USUARIOS.get("t:" + chave) || 0); await env.USUARIOS.put("t:" + chave, String(n + 1), { expirationTtl: 900 }) }
export async function limpaErros(env, chave) { await env.USUARIOS.delete("t:" + chave) }

export const json = (obj, status = 200, headers = {}) => new Response(JSON.stringify(obj), { status, headers: { "Content-Type": "application/json; charset=utf-8", "Cache-Control": "no-store", ...headers } });
export const loginValido = l => /^[a-z0-9._-]{3,40}$/.test(l || "");
export const senhaValida = s => typeof s === "string" && s.length >= 8 && s.length <= 200;
