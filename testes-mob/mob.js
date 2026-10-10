#!/usr/bin/env node
// Pilota o Chromium em emulação mobile (Pixel 7) e fotografa fluxos reais.
// Uso: node mob.js [treino|estudo|home|all]
const { chromium } = require('playwright-core');

const BASE = 'http://127.0.0.1:8123';
const OUT = '/tmp/opencode/mobtest';
const FLOW = process.argv[2] || 'all';

(async () => {
  const browser = await chromium.launch({
    executablePath: '/root/.cache/ms-playwright/chromium-1243/chrome-linux64/chrome',
    args: ['--no-sandbox', '--disable-gpu'],
  });
  const ctx = await browser.newContext({
    viewport: { width: 390, height: 844 },
    deviceScaleFactor: 3,
    isMobile: true,
    hasTouch: true,
    userAgent:
      'Mozilla/5.0 (Linux; Android 14; Pixel 7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Mobile Safari/537.36',
  });
  const page = await ctx.newPage();

  // checa rolagem lateral: scrollWidth vs largura util
  async function checkOverflow(tag) {
    const r = await page.evaluate(() => ({
      sw: document.documentElement.scrollWidth,
      cw: document.documentElement.clientWidth,
      larguras: [...document.querySelectorAll('main *')]
        .map((el) => ({ t: (el.textContent || '').trim().slice(0, 40), r: el.getBoundingClientRect() }))
        .filter((x) => x.r.right > 391 || x.r.left < -1)
        .slice(0, 8),
    }));
    console.log(`[${tag}] scrollWidth=${r.sw} clientWidth=${r.cw}`);
    for (const x of r.larguras) console.log(`   ESTOURO right=${Math.round(x.r.right)} :: ${x.t.slice(0, 50)}`);
  }

  async function shot(name) {
    await page.waitForTimeout(900);
    await page.screenshot({ path: `${OUT}/${name}.png` });
    console.log('foto:', name);
  }

  if (FLOW === 'home' || FLOW === 'all') {
    await page.goto(BASE + '/', { waitUntil: 'networkidle' });
    await shot('m-home');
    await checkOverflow('home');
  }

  if (FLOW === 'treino' || FLOW === 'all') {
    await page.goto(BASE + '/treino/', { waitUntil: 'networkidle' });
    await shot('m-treino-q');
    await checkOverflow('treino-q');
    // responde a 1ª alternativa e fotografa o feedback
    const alts = page.getByRole('group', { name: 'Alternativas' }).getByRole('button');
    if ((await alts.count()) > 0) {
      await alts.first().click();
      await shot('m-treino-feedback');
      await checkOverflow('treino-feedback');
      await page.getByRole('button', { name: 'Próxima' }).click();
      await shot('m-treino-q2');
    }
  }

  if (FLOW === 'estudo' || FLOW === 'all') {
    await page.goto(BASE + '/estudo/', { waitUntil: 'networkidle' });
    await shot('m-estudo-niveis');
    await page.getByRole('button', { name: /N1/ }).click();
    await shot('m-estudo-q');
    await checkOverflow('estudo-q');
    const alts = page.getByRole('group', { name: 'Alternativas' }).getByRole('button');
    const nDisc = await page.getByRole('button', { name: /ver padrão oficial/i }).count();
    if ((await alts.count()) > 0) {
      await alts.first().click();
      await shot('m-estudo-feedback');
    } else if (nDisc > 0) {
      await page.getByRole('button', { name: /ver padrão oficial/i }).click();
      await shot('m-estudo-disc');
    }
  }

  await browser.close();
  console.log('OK');
})().catch((e) => {
  console.error('FALHA:', e.message);
  process.exit(1);
});
