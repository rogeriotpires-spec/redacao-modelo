import { json, cookieSessao } from "../../lib/auth.js";
export async function onRequestPost() { return json({ ok: true }, 200, { "Set-Cookie": cookieSessao("", 0) }) }
