import { browser } from '$app/environment';

function ler(chave, padrao) {
	if (!browser) return padrao;
	try {
		const v = localStorage.getItem(chave);
		return v === null ? padrao : JSON.parse(v);
	} catch {
		return padrao;
	}
}

function gravar(chave, valor) {
	if (!browser) return;
	try {
		localStorage.setItem(chave, JSON.stringify(valor));
	} catch {
		// armazenamento cheio/bloqueado — segue sem salvar
	}
}

export function getXP() {
	return ler('enade-xp', 0);
}
export function somarXP(n) {
	const total = getXP() + n;
	gravar('enade-xp', total);
	return total;
}

/** Streak de dias com pelo menos 1 resposta. Devolve {dias, ultimo}. */
export function registrarAtividade() {
	const hoje = new Date().toISOString().slice(0, 10);
	const st = ler('enade-streak', { dias: 0, ultimo: '' });
	if (st.ultimo === hoje) return st;
	const ontem = new Date(Date.now() - 86400000).toISOString().slice(0, 10);
	st.dias = st.ultimo === ontem ? st.dias + 1 : 1;
	st.ultimo = hoje;
	gravar('enade-streak', st);
	const hist = ler('enade-hist', []);
	if (!hist.includes(hoje)) {
		hist.push(hoje);
		gravar('enade-hist', hist.slice(-60));
	}
	return st;
}

/** Últimos N dias (ISO) com atividade, para os pontinhos da semana. */
export function getHistorico(n = 7) {
	const hist = ler('enade-hist', []);
	const dias = [];
	for (let k = n - 1; k >= 0; k--) {
		dias.push(new Date(Date.now() - k * 86400000).toISOString().slice(0, 10));
	}
	return dias.map((d) => hist.includes(d));
}
export function getStreak() {
	return ler('enade-streak', { dias: 0, ultimo: '' });
}

export function registrarErro(id) {
	const erros = ler('enade-erros', []);
	if (!erros.includes(id)) {
		erros.push(id);
		gravar('enade-erros', erros);
	}
}
export function removerErro(id) {
	gravar(
		'enade-erros',
		ler('enade-erros', []).filter((e) => e !== id)
	);
}
export function getErros() {
	return ler('enade-erros', []);
}
