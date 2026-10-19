import { getUsuario, putUsuario, confereSenha, criaSessao, cookieSessao, json, bloqueado, erroLogin, limpaErros } from "../../lib/auth.js";
export async function onRequestPost({ request, env }) {
  const b = await request.json().catch(() => ({}));
  const login = String(b.login || "").trim().toLowerCase(), senha = String(b.senha || "");
  const ip = request.headers.get("CF-Connecting-IP") || "?";
  if (await bloqueado(env, "l:" + login) || await bloqueado(env, "i:" + ip)) return json({ error: "Muitas tentativas. Espere 15 minutos." }, 429);
  const u = await getUsuario(env, login);
  if (!u || u.ativo === false || !(await confereSenha(senha, u))) {
    await erroLogin(env, "l:" + login); await erroLogin(env, "i:" + ip);
    return json({ error: "Usuário ou senha incorretos." }, 401);
  }
  await limpaErros(env, "l:" + login);
  u.ultimo_acesso = new Date().toISOString(); await putUsuario(env, u);
  return json({ ok: true, nome: u.nome, troca_senha: !!u.troca_senha }, 200, { "Set-Cookie": cookieSessao(await criaSessao(env, u)) });
}
