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

/** Sessão de treino pausada (para continuar depois). */
export function salvarSessao(s) {
	gravar('enade-sessao', s);
}
export function carregarSessao() {
	return ler('enade-sessao', null);
}
export function limparSessao() {
	if (!browser) return;
	try {
		localStorage.removeItem('enade-sessao');
	} catch {
		// ignora
	}
}
