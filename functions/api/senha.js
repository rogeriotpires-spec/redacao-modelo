// O próprio usuário troca a senha (pede a atual). Trocar a senha encerra as outras sessões dele.
import { json, confereSenha, hashSenha, putUsuario, senhaValida, criaSessao, cookieSessao } from "../../lib/auth.js";
export async function onRequestPost({ request, env, data }) {
  const b = await request.json().catch(() => ({})), u = data.usuario;
  if (!(await confereSenha(String(b.atual || ""), u))) return json({ error: "Senha atual incorreta." }, 400);
  if (!senhaValida(b.nova)) return json({ error: "A nova senha precisa ter pelo menos 8 caracteres." }, 400);
  Object.assign(u, await hashSenha(b.nova)); u.versao = (u.versao || 1) + 1; delete u.troca_senha;
  await putUsuario(env, u);
  return json({ ok: true }, 200, { "Set-Cookie": cookieSessao(await criaSessao(env, u)) });
}
