import { browser } from '$app/environment';

const CHAVE = 'enade-tema';

function preferencia() {
	if (!browser) return 'light';
	try {
		const salvo = localStorage.getItem(CHAVE);
		if (salvo === 'dark' || salvo === 'light') return salvo;
	} catch {
		// ignora
	}
	return matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
}

export function temaAtual() {
	if (!browser) return 'light';
	return document.documentElement.classList.contains('dark') ? 'dark' : 'light';
}

export function aplicarTema(modo) {
	if (!browser) return;
	document.documentElement.classList.toggle('dark', modo === 'dark');
	try {
		localStorage.setItem(CHAVE, modo);
	} catch {
		// ignora
	}
}

export function iniciarTema() {
	aplicarTema(preferencia());
}

export function alternarTema() {
	const proximo = temaAtual() === 'dark' ? 'light' : 'dark';
	aplicarTema(proximo);
	return proximo;
}
