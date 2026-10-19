// Gera programa/AAAA-MM-DD.pdf para as pautas mais recentes do programa.
// Uso (no GitHub Actions): servidor local na porta 8777 servindo a raiz do repositório e depois
//   node tools/pdf-programa.js [AAAA-MM-DD ...]
const { chromium } = require('playwright');
const fs = require('fs');
(async () => {
  let days = process.argv.slice(2);
  if (!days.length) days = (JSON.parse(fs.readFileSync('programa/index.json', 'utf8')).days || []).sort().slice(-2);
  const opts = process.env.CHROME_PATH ? { executablePath: process.env.CHROME_PATH } : { channel: 'chrome' };
  const browser = await chromium.launch(opts);
  for (const d of days) {
    if (!fs.existsSync(`programa/${d}.json`)) continue;
    const page = await browser.newPage();
    await page.goto(`http://localhost:8777/programa-pdf.html?d=${d}`, { waitUntil: 'networkidle' });
    await page.waitForFunction(() => window.__pronto === true, null, { timeout: 60000 });
    await page.emulateMedia({ media: 'print' });
    await page.pdf({ path: `programa/${d}.pdf`, printBackground: true, preferCSSPageSize: true });
    console.log('PDF', d);
    await page.close();
  }
  await browser.close();
})().catch(e => { console.error(e); process.exit(1); });
