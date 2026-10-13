// Banco de questões: carregamento, cache e utilidades de classificação.
//
// Sem `$app/environment`: guardas em tempo de execução (`typeof window`) —
// assim a lógica roda igual em Node (testes) e no SSR.
//
// PORQUÊ cache + paralelismo: no 3G/4G do celular, 8 `await` em fila somam a
// latência de 8 idas ao servidor; em `Promise.all` é uma só. E a cache de
// sessão evita repetir tudo na navegação entre páginas (no SPA o módulo é
// recarregado, a rede não precisa ser).

/**
 * Versão do banco embutida no código. **Bumpe a cada deploy que adicione/
 * altere JSON em `static/banco`** — é o que invalida a cache sem depender da
 * rede (um deploy novo sempre traz uma versão nova).
 */
export const VERSAO_BANCO = '7b6629db0240';

/** Arquivos do banco (um por edição+parte). Exportado para o preload. */
export const ARQUIVOS_BANCO = [
	'enade2019-fg.json',
	'enade2019-ce.json',
	'enade2023-fg.json',
	'enade2023-ce.json',
	'enade2014-fg.json',
	'enade2014-ce.json',
	'enade2017-fg.json',
	'enade2017-ce.json'
];

const CHAVE_CACHE = 'enade-banco';
const TTL_CACHE_MS = 6 * 60 * 60 * 1000; // 6 h: cobre o dia de estudo, não atrapalha deploy

/** Tamanho mínimo de uma sessão por nível (as telas pedem 10 questões). */
export const NIVEL_MINIMO = 10;

const ROTULO_NIVEL = { 1: 'Fácil', 2: 'Média', 3: 'Difícil' };

function session() {
	if (typeof window === 'undefined') return null;
	try {
		return window.sessionStorage || null;
	} catch {
		return null;
	}
}

function lerCache() {
	const s = session();
	if (!s) return null;
	try {
		const raw = s.getItem(CHAVE_CACHE);
		if (!raw) return null;
		const c = JSON.parse(raw);
		// A versão vem do código, não da rede: deploy novo = cache descartada.
		if (!c || c.versao !== VERSAO_BANCO || !Array.isArray(c.questoes)) return null;
		if (Date.now() - c.em > TTL_CACHE_MS) return null;
		return c.questoes;
	} catch {
		return null;
	}
}

function gravarCache(questoes) {
	const s = session();
	if (!s) return false;
	try {
		s.setItem(CHAVE_CACHE, JSON.stringify({ versao: VERSAO_BANCO, em: Date.now(), questoes }));
		return true;
	} catch {
		// cota do sessionStorage — segue sem cache
		return false;
	}
}

/**
 * Carrega todos os JSONs do banco (pasta `static/banco`) EM PARALELO.
 * Só grava a cache quando os 8 arquivos vieram — cache parcial seria pior que
 * nenhuma, porque o TTL a manteria por 6 h.
 */
export async function carregarBanco() {
	if (typeof fetch !== 'function') return [];
	const cache = lerCache();
	if (cache) return cache;

	const resultados = await Promise.all(
		ARQUIVOS_BANCO.map(async (arquivo) => {
			try {
				const r = await fetch(`/banco/${arquivo}`);
				if (!r.ok) return { questoes: [], ok: false };
				const lote = await r.json();
				return { questoes: Array.isArray(lote) ? lote : [], ok: true };
			} catch {
				// arquivo ainda não existe / offline — ignora este lote
				return { questoes: [], ok: false };
			}
		})
	);

	const questoes = [];
	let completo = true;
	for (const r of resultados) {
		questoes.push(...r.questoes);
		if (!r.ok) completo = false;
	}
	if (completo && questoes.length) gravarCache(questoes);
	return questoes;
}

/**
 * Dispara o download do banco cedo, antes do JS pedir: injeta um
 * `<link rel="preload" as="fetch" crossorigin>` por arquivo. Deve rodar no
 * cliente e idealmente ANTES de `carregarBanco()`.
 *
 * Como chamar (não mexe em `app.html`, que está fora deste escopo):
 *  - opção A (melhor): colar no `<head>` de `app.html`, estático, antes de
 *    `%sveltekit.head%`:
 *      {ARQUIVOS_BANCO.map(a => `<link rel="preload" as="fetch" crossorigin href="/banco/${a}">`)}
 *  - opção B: chamar `precarregar()` no início do `onMount` do layout/home.
 *
 * @returns {string[]} as URLs enfileiradas (útil para teste/telemetria).
 */
export function precarregar() {
	const urls = ARQUIVOS_BANCO.map((a) => `/banco/${a}`);
	if (typeof document === 'undefined') return urls;
	for (const href of urls) {
		try {
			if (document.querySelector(`link[data-enade-preload="${href}"]`)) continue;
			const link = document.createElement('link');
			link.rel = 'preload';
			link.as = 'fetch';
			link.crossOrigin = 'anonymous'; // exigido pelo preload de fetch
			link.href = href;
			link.dataset.enadePreload = href;
			document.head.appendChild(link);
		} catch {
			// DOM indisponível/estranho — sem preload, o fetch normal resolve
		}
	}
	return urls;
}

export function embaralhar(lista) {
	const a = [...(Array.isArray(lista) ? lista : [])];
	for (let i = a.length - 1; i > 0; i--) {
		const j = Math.floor(Math.random() * (i + 1));
		[a[i], a[j]] = [a[j], a[i]];
	}
	return a;
}

/** Nível de estudo -> dificuldade. Sem dificuldade definida cai em todos (até a revisão). */
export function doNivel(q, nivel) {
	if (!q.dificuldade) return true;
	return q.dificuldade === ROTULO_NIVEL[nivel];
}

/**
 * Quantas questões o banco oferece para um nível. A UI usa para avisar em vez
 * de montar sessão vazia/curta em silêncio.
 *
 * Verificado no banco real (12/10/2026): Fácil 19, Média 50, Difícil 54 —
 * todos ≥ 10 no banco inteiro, MAS por parte o FG tem só 9 "Fácil"; se um
 * filtro por parte for adicionado, o aviso passa a importar.
 *
 * @returns {{ok: boolean, total: number, minimo: number, nivel: number, rotulo: string|null}}
 */
export function nivelDisponivel(banco, nivel, minimo = NIVEL_MINIMO) {
	const lista = Array.isArray(banco) ? banco : [];
	const total = lista.filter((q) => doNivel(q, nivel)).length;
	return { ok: total >= minimo, total, minimo, nivel, rotulo: ROTULO_NIVEL[nivel] ?? null };
}

/**
 * Contagens prontas para a home (evita a UI varrer o banco e reimplementar).
 * `fg`/`ce` seguem a convenção da home: OBJETIVAS por parte (batem com a
 * grade "FG objetivas / CE objetivas / Discursivas", que não soma o total
 * porque a discursiva aparece nos dois eixos). `fgTotal`/`ceTotal` dão o
 * número completo por parte quando precisar.
 */
export function contagens(banco) {
	const lista = Array.isArray(banco) ? banco : [];
	const c = {
		total: lista.length,
		objetivas: 0,
		discursivas: 0,
		fg: 0,
		ce: 0,
		fgTotal: 0,
		ceTotal: 0,
		porEdicao: {},
		porDificuldade: {}
	};
	for (const q of lista) {
		const discursiva = q.tipo === 'discursiva';
		if (discursiva) c.discursivas++;
		else c.objetivas++;

		if (q.parte === 'FG') {
			c.fgTotal++;
			if (!discursiva) c.fg++;
		} else {
			c.ceTotal++;
			if (!discursiva) c.ce++;
		}

		const edicao = String(q.edicao ?? '?');
		c.porEdicao[edicao] = (c.porEdicao[edicao] || 0) + 1;

		const dif = q.dificuldade || 'Sem nível';
		c.porDificuldade[dif] = (c.porDificuldade[dif] || 0) + 1;
	}
	return c;
}

/**
 * Chave estável de uma questão para histórico/erros. O `id` do banco já é
 * único entre edições (`2019-CE-Q09` ≠ `2023-CE-Q09`), então ele manda; o
 * fallback monta a mesma forma a partir dos campos, para questões antigas ou
 * importadas à mão.
 */
export function chaveQuestao(q) {
	if (!q) return '';
	if (q.id) return String(q.id);
	const prefixo = q.tipo === 'discursiva' ? 'D' : 'Q';
	return `${q.edicao ?? ''}-${q.parte ?? ''}-${prefixo}${q.numero ?? ''}`;
}

/** Alias explícito de `chaveQuestao` (mesma função). */
export const idEstavel = chaveQuestao;

export function rotuloQuestao(q) {
	if (!q) return '';
	// `numero` pode vir número em algum JSON — normaliza antes de montar o rótulo.
	const numero = String(q.numero ?? '');
	const n = q.tipo === 'discursiva' ? `D${numero}` : `Q${numero}`;
	return `REF ${q.edicao}-${q.parte}-${n}`;
}
