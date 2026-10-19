# Redação Inteligente: modelo por cliente

Painel com **Notícias do dia** e **Pauta do programa**, atrás de login com usuário e senha por pessoa.
Cada cliente tem a sua própria cópia deste repositório (privada), o seu site na Cloudflare e a sua chave da Anthropic. Nada é compartilhado entre clientes.

## Como funciona

| Peça | Onde roda | O que faz |
|---|---|---|
| `noticias.yml` | GitHub Actions, nos horários de `cliente.json > noticias` | Coleta os portais, o Claude seleciona e resume, publica |
| `programa.yml` | GitHub Actions, em `programa.gera_pauta_as` nos dias do programa | Gera a pauta do dia e o PDF, publica |
| `programa-avulso.yml` | Disparado pelo painel | Inclui um item pedido pela redação na pauta |
| `pauta-excluir.yml` | Disparado pelo painel | Tira um item da pauta (e ele não volta) |
| `publicar.yml` | A cada push | Monta `dist/` e publica na Cloudflare Pages |
| `functions/` | Cloudflare Pages | Porteiro (login), usuários, disparo das rotinas |

Todas as páginas e todos os dados (`/noticias/*.json`, `/programa/*.json`, PDFs) só saem com sessão válida.
Senhas ficam com PBKDF2 no KV; a sessão é um cookie assinado, HttpOnly, de 14 dias. Bloquear, remover ou trocar a senha de alguém derruba a sessão dele na hora. O login trava por 15 minutos depois de 8 erros.

## Implantar um cliente novo (cerca de 30 minutos)

> Chaves e tokens vão **direto** nas telas de segredos do GitHub e da Cloudflare. Nunca em chat, e-mail ou print.

1. **Repositório privado.** Crie `redacao-<cliente>` como privado e envie este modelo para ele.
2. **Configuração.** Edite `cliente.json` (veículo, programa, horários, apresentadores, blocos, linha editorial, região e portais regionais, buscas de esporte, cor e logo em `marca/logo.png`). Rode `python3 tools/configurar.py` e faça commit.
3. **Cloudflare** (conta do cliente ou a sua):
   - Workers & Pages → Create → Pages → *Upload assets* → nome do projeto, por exemplo `redacao-jpbh`. Publique qualquer pasta só para criar o projeto.
   - Workers & Pages → KV → crie o namespace `usuarios-<cliente>`.
   - No projeto Pages → Settings → Bindings → **KV namespace**: nome da variável `USUARIOS`, escolha o namespace.
   - No projeto Pages → Settings → Variables and Secrets (tipo **Secret**):
     - `SESSION_SECRET`: um texto aleatório longo (por exemplo, `openssl rand -base64 48`).
     - `SETUP_TOKEN`: uma senha de uso único para criar o primeiro administrador.
     - `GH_TOKEN`: token *fine-grained* do GitHub, só para o repositório do cliente, permissão **Actions: Read and write**.
     - `GH_REPO`: `dono/redacao-<cliente>`.
   - Crie um token da API da Cloudflare com o modelo *Edit Cloudflare Workers* (ou permissão **Cloudflare Pages: Edit**).
4. **GitHub** → Settings → Secrets and variables → Actions:
   - Secrets: `ANTHROPIC_API_KEY` (chave do workspace do cliente no console da Anthropic, com limite de gasto), `CLOUDFLARE_API_TOKEN`, `CLOUDFLARE_ACCOUNT_ID`.
   - Variables: `CF_PROJECT` = nome do projeto Pages.
5. **Primeira publicação.** Actions → *Publicar o site* → Run workflow. Depois *Notícias* → Run workflow e *Pauta do programa* → Run workflow.
6. **Primeiro administrador.** Abra `https://<projeto>.pages.dev/setup.html`, informe o `SETUP_TOKEN`, nome, usuário e senha. A tela só funciona enquanto não existe nenhum usuário. Depois disso, pode apagar o `SETUP_TOKEN` na Cloudflare.
7. **Equipe.** Entre como administrador → menu do nome → *Usuários* → crie cada pessoa com senha provisória. Ela troca a senha no primeiro acesso.
8. **Domínio próprio (opcional).** No projeto Pages → Custom domains, por exemplo `redacao.cliente.com.br`.

## Custos a acompanhar

- **Anthropic:** cada edição de notícias e cada pauta é uma chamada longa do Claude. Use um workspace por cliente no console, com limite de gasto mensal, e meça o custo real na primeira semana.
- **GitHub Actions:** repositório privado consome minutos do plano (cada rotina leva de 5 a 15 minutos).
- **Cloudflare Pages e KV:** dentro do plano gratuito para o volume de uma redação.

## Teste local

```bash
bash tools/montar.sh
printf 'SESSION_SECRET=teste-local-123456789\nSETUP_TOKEN=teste\nGH_TOKEN=x\nGH_REPO=dono/repo\n' > .dev.vars
npx wrangler@3.78.12 pages dev dist --kv USUARIOS --port 8788
# abra http://127.0.0.1:8788/setup.html
```
