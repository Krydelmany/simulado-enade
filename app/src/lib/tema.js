// Tema claro/escuro. Igual aos outros módulos: sem `$app/environment`, só
// guardas de ambiente em tempo de execução — `iniciarTema` pode ser chamada
// fora do `onMount` (ou em Node) sem explodir.
//
// PORQUÊ o tema precisa de cuidado especial: o `app.html` aplica a classe
// `.dark` num script inline ANTES da primeira pintura (anti-flash). Se o JS
// aplicasse depois, a página piscaria clara. Este módulo mantém a MESMA regra
// de preferência desse script inline, para os dois não divergirem.

const CHAVE = 'enade-tema';
const CONSULTA_ESCURO = '(prefers-color-scheme: dark)';

function temDom() {
	return typeof window !== 'undefined' && typeof document !== 'undefined';
}

function mediaQuery() {
	try {
		if (typeof window !== 'undefined' && typeof window.matchMedia === 'function') {
			return window.matchMedia(CONSULTA_ESCURO);
		}
		if (typeof matchMedia === 'function') return matchMedia(CONSULTA_ESCURO);
	} catch {
		// matchMedia indisponível/quirky (SSR, jsdom antigo)
	}
	return null;
}

function sistemaPrefereEscuro() {
	const mq = mediaQuery();
	return mq ? mq.matches === true : false;
}

/** Escolha explícita do usuário (`'dark'`/`'light'`) ou `null` se nunca escolheu. */
function escolhaSalva() {
	if (typeof window === 'undefined') return null;
	try {
		const v = window.localStorage.getItem(CHAVE);
		return v === 'dark' || v === 'light' ? v : null;
	} catch {
		return null;
	}
}

/** `true` se o usuário já escolheu o tema (o sistema não deve sobrescrever). */
export function temEscolhaExplicita() {
	return escolhaSalva() !== null;
}

/**
 * Tema que deve estar aplicado: escolha do usuário manda; sem escolha, segue
 * o sistema. Mesma lógica do script inline do `app.html`.
 */
function temaPreferido() {
	return escolhaSalva() ?? (sistemaPrefereEscuro() ? 'dark' : 'light');
}

function definirClasse(modo) {
	if (!temDom()) return;
	document.documentElement.classList.toggle('dark', modo === 'dark');
}

function persistir(modo) {
	if (typeof window === 'undefined') return;
	try {
		window.localStorage.setItem(CHAVE, modo);
	} catch {
		// storage bloqueado — o tema vale para esta aba, só não é lembrado
	}
}

export function temaAtual() {
	if (!temDom()) return 'light';
	return document.documentElement.classList.contains('dark') ? 'dark' : 'light';
}

/**
 * Aplica um tema E grava como ESCOLHA EXPLÍCITA do usuário (é o que o botão
 * de alternar faz). Para aplicar sem marcar como escolha, use `iniciarTema`.
 */
export function aplicarTema(modo) {
	definirClasse(modo);
	persistir(modo);
}

/**
 * Aplica o tema inicial SEM gravar escolha — preserva a distinção entre
 * "usuário escolheu claro" e "sistema está claro", senão o tema do sistema
 * (que muda às 19h, p.ex.) nunca mais seria honrado.
 * @returns {'light'|'dark'} o tema aplicado.
 */
export function iniciarTema() {
	const modo = temaPreferido();
	definirClasse(modo);
	return modo;
}

export function alternarTema() {
	const proximo = temaAtual() === 'dark' ? 'light' : 'dark';
	aplicarTema(proximo);
	return proximo;
}

/**
 * Observa mudanças da preferência do sistema (o SO liga o dark mode à noite).
 * Se o usuário já escolheu explicitamente, NÃO sobrescreve — apenas avisa.
 *
 * @param {(modo: 'light'|'dark', opts: {sistema: boolean}) => void} cb
 * @returns {() => void} função para cancelar a observação.
 */
export function aoMudarTema(cb) {
	const mq = mediaQuery();
	if (!mq) return () => {};

	const handler = (evento) => {
		if (temEscolhaExplicita()) {
			// Escolha do usuário vence o sistema; só notifica, sem mexer na DOM.
			cb?.(temaAtual(), { sistema: false });
			return;
		}
		const modo = (evento?.matches ?? mq.matches) ? 'dark' : 'light';
		definirClasse(modo);
		cb?.(modo, { sistema: true });
	};

	// `addEventListener` é o padrão atual; `addListener` cobre navegadores antigos.
	if (typeof mq.addEventListener === 'function') {
		mq.addEventListener('change', handler);
		return () => mq.removeEventListener('change', handler);
	}
	if (typeof mq.addListener === 'function') {
		mq.addListener(handler);
		return () => mq.removeListener(handler);
	}
	return () => {};
}

/**
 * Snippet anti-flash para injetar no `<head>` do `app.html` (fora do escopo
 * destes módulos). Roda antes da primeira pintura e aplica `.dark` já na
 * largada. O `app.html` atual JÁ contém um script equivalente — se for trocar,
 * troque pelo retorno desta função para manter a regra num só lugar.
 *
 * @returns {string} o código (sem `<script>`/`</script>`).
 */
export function scriptAntiFlash() {
	return (
		`(function(){try{var t=localStorage.getItem('${CHAVE}');` +
		`if(t==='dark'||(t!=='light'&&matchMedia('${CONSULTA_ESCURO}').matches)){` +
		`document.documentElement.classList.add('dark')}}catch(e){}})();`
	);
}
