import { json, publico } from "../../lib/auth.js";
export async function onRequestGet({ data }) { return json({ ...publico(data.usuario), troca_senha: !!data.usuario.troca_senha }) }
