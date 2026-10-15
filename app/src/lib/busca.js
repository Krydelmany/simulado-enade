/**
 * Busca de questões pelo texto.
 *
 *     import { buscar, destacar } from '$lib/busca.js';
 *     buscar(banco, 'fila estatica');   // -> [{ q, pontos, trechos }]
 *
 * Nasce de um pedido concreto: na hora de estudar não dá para digitar certo,
 * então a busca tem de aguentar "tensao" achando "tensão", "61131" achando a
 * norma IEC 61131-3 no meio do enunciado, e um pedaço de frase achando a
 * questão mesmo que a pessoa só grave metade das palavras.
 *
 * Regras que o desenho segue:
 *
 * 1. TUDO é normalizado antes de comparar (minúscula, sem acento, sem
 *    pontuação). "Máquina de Turing" e "maquina de turing" são a mesma busca.
 * 2. A query é quebrada em palavras e todas têm de aparecer (E). Se com E não
 *    vier nada, relaxa para OU — é melhor mostrar algo aproximado do que uma
 *    tela vazia quando a pessoa errou uma palavra.
 * 3. Número e identificador têm peso próprio e alto: quem digita "09" ou
 *    "2014-CE-Q09" quer AQUELA questão, não "questões que contêm 9".
 */

/**
 * Minúscula, sem acento, sem pontuação, espaços colapsados.
 * @param {string} s
 * @returns {string}
 */
export function normalizar(s) {
	return (s || '')
		.toLowerCase()
		.normalize('NFD')
		.replace(/[\u0300-\u036f]/g, '') // acentos
		.replace(/[^\p{L}\p{N}]+/gu, ' ') // pontuação, símbolos, código
		.trim();
}

/**
 * Query -> palavras significativas. Descarta as de 1 letra: sozinhas elas
 * casam em quase todo enunciado ("a", "e", "o") e só poluem o resultado.
 * @param {string} q
 * @returns {string[]}
 */
export function termos(q) {
	return normalizar(q).split(' ').filter((t) => t.length > 1);
}

/** Onde um termo bate, com o peso que aquele campo tem no resultado. */
const CAMPOS = [
	['numero', 40, (q) => numParaTexto(q)],
	['tema', 3, (q) => q.tema],
	['enunciado', 8, (q) => q.enunciado],
	['alternativas', 2, (q) => Object.values(q.alternativas || {}).join(' ')]
];

// "2014-CE-Q09" e "09" precisam bater no mesmo lugar: o número é o que a
// pessoa digita quando quer uma questão específica.
function numParaTexto(q) {
	const n = String(q.numero ?? '');
	return `${n} ${q.id ?? ''}`;
}

/** Todas as buscas possíveis, para o filtro da tela. */
export const FILTROS = [
	{ id: 'tudo', nome: 'Tudo' },
	{ id: 'numero', nome: 'Número' },
	{ id: 'enunciado', nome: 'Enunciado' },
	{ id: 'alternativas', nome: 'Alternativas' },
	{ id: 'tema', nome: 'Tema' }
];

/**
 * Procura no banco.
 *
 * @param {Array} banco questões no formato do app
 * @param {string} query texto digitado
 * @param {{campo?: string}} [opcoes] `campo` restringe a um dos FILTROS
 * @returns {Array<{q: object, pontos: number, onde: string[], trechos: object[]}>}
 *          ordenado por pontos; vazio se a query não tiver palavra útil.
 */
export function buscar(banco, query, opcoes = {}) {
	const palavras = termos(query);
	if (!palavras.length) return [];

	const campo = opcoes.campo && opcoes.campo !== 'tudo' ? opcoes.campo : null;
	const campos = campo ? CAMPOS.filter((c) => c[0] === campo) : CAMPOS;

	// índice pré-normalizado: normalizar 240 questões a cada tecla custa caro
	// e o texto delas não muda durante a sessão
	const ix = (banco || []).map((q) => {
		const t = {};
		for (const [nome, , pega] of campos) t[nome] = normalizar(pega(q));
		return { q, t };
	});

	// E primeiro: toda palavra tem de aparecer em ALGUM campo da questão.
	// Pontua a questão pelo total de acertos, então quem casa as palavras em
	// campo de peso alto (número, enunciado) sobe.
	const comE = [];
	for (const item of ix) {
		let pontos = 0;
		const onde = new Set();
		for (const p of palavras) {
			let achou = false;
			for (const [nome, peso] of campos) {
				if (item.t[nome].includes(p)) {
					pontos += peso;
					onde.add(nome);
					achou = true;
				}
			}
			if (!achou) {
				pontos = -1;
				break;
			}
		}
		if (pontos > 0) comE.push({ q: item.q, pontos, onde: [...onde] });
	}
	if (comE.length) return ordenar(comE, palavras, campos);

	// Nada com E: relaxa para OU e devolve o que tiver pelo menos uma palavra.
	// São os "possíveis" que o pedido original pedia.
	const comOu = [];
	for (const item of ix) {
		let pontos = 0;
		const onde = new Set();
		for (const p of palavras) {
			for (const [nome, peso] of campos) {
				if (item.t[nome].includes(p)) {
					pontos += peso;
					onde.add(nome);
				}
			}
		}
		if (pontos > 0) comOu.push({ q: item.q, pontos, onde: [...onde] });
	}
	return ordenar(comOu, palavras, campos);
}

// Desempate: mais palavras diferentes casando, e antes as mais curtas — um
// enunciado de 2 linhas que casa o termo é match melhor do que um de 20.
function ordenar(lista, palavras, campos) {
	const contam = (r) => {
		const t = {};
		for (const [nome, , pega] of campos) t[nome] = normalizar(pega(r.q));
		return palavras.filter((p) => Object.values(t).some((v) => v.includes(p))).length;
	};
	return lista
		.map((r) => ({ ...r, _c: contam(r), _len: (r.q.enunciado || '').length }))
		.sort((a, b) => b._c - a._c || b.pontos - a.pontos || a._len - b._len)
		.map(({ q, pontos, onde }) => ({ q, pontos, onde }));
}

/**
 *Texto -> pedaços marcados, para pintar como o VSCode pinta o match.
 * @param {string} texto
 * @param {string[]} palavras já normalizadas
 * @returns {Array<{t: string, m: boolean}>}
 */
export function destacar(texto, palavras) {
	const original = String(texto ?? '');
	if (!palavras.length) return [{ t: original, m: false }];

	// Marca PALAVRAS INTEIRAS, não fatias de índice. A primeira versão procurava
	// o termo no texto normalizado e usava um mapa posição-a-posição para voltar
	// ao original — e o mapa desalinhava em 1 sempre que havia espaço ou
	// pontuação antes do termo (o normalizar dá `trim` e colapsa espaços, o mapa
	// não): " fila" marcava o espaço e "fil". Tokenizar é o que não desalinha.
	const marcas = new Array(original.length).fill(false);
	const TOKEN = /[\p{L}\p{N}]+/gu;
	let m;
	while ((m = TOKEN.exec(original)) !== null) {
		const palavra = normalizar(m[0]);
		if (!palavra) continue;
		// casa o termo igual ou contido: "tens" marca "tensão", "61131" marca
		// o token "61131" — palavra inteira, como o VSCode faz
		if (palavras.some((p) => palavra === p || palavra.includes(p))) {
			for (let k = m.index; k < m.index + m[0].length; k++) marcas[k] = true;
		}
	}

	const fora = [];
	let atual = '';
	let marcado = marcas[0] === true;
	for (let i = 0; i < original.length; i++) {
		if (marcas[i] === marcado) {
			atual += original[i];
		} else {
			fora.push({ t: atual, m: marcado });
			atual = original[i];
			marcado = marcas[i] === true;
		}
	}
	if (atual) fora.push({ t: atual, m: marcado });
	return fora;
}

/**
 * Primeiro trecho do enunciado que containha alguma palavra da busca, para o
 * resultado não precisar mostrar a questão inteira.
 * @param {string} texto
 * @param {string[]} palavras
 * @param {number} [max]
 * @returns {string}
 */
export function resumo(texto, palavras, max = 150) {
	const limpo = String(texto ?? '').replace(/\s+/g, ' ').trim();
	if (limpo.length <= max) return limpo;
	const norm = normalizar(limpo);
	let inicio = 0;
	for (const p of palavras) {
		const onde = norm.indexOf(p);
		if (onde > 0 && (inicio === 0 || onde < inicio)) inicio = onde;
	}
	// recua para a palavra anterior, para não cortar a frase no meio
	const corte = Math.max(0, inicio - Math.floor(max / 3));
	const espaco = limpo.indexOf(' ', corte);
	const de = espaco > 0 && espaco < inicio ? espaco + 1 : corte;
	return (de > 0 ? '… ' : '') + limpo.slice(de, de + max).trim() + '…';
}
