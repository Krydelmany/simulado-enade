import { untrack } from 'svelte';
import { page } from '$app/state';
import { goto, pushState, replaceState } from '$app/navigation';

/**
 * Liga as CAMADAS internas de uma rota (tela montada dentro da página,
 * modal, overlay) ao histórico do navegador, para o voltar do sistema — o
 * gesto da borda no celular, o botão do Android — fechar a camada de cima em
 * vez de sair do modo inteiro. Antes, o voltar no meio da prova do simulado
 * ou do quiz do estudo caía na home.
 *
 * Cada entrada rasa do histórico guarda `page.state = { camadas, idade }`:
 *  - `camadas`: o que está aberto, de baixo para cima;
 *  - `idade`: cresce sempre; serve para distinguir voltar de avançar.
 *
 * INVARIANTE: uma entrada com N camadas fica exatamente N entradas acima da
 * base da mesma URL. Por isso `history.go(-k)` com k ≤ N nunca sai da rota.
 *
 * O histórico só FECHA camada, nunca abre: avançar, ou cair numa entrada
 * velha, é desfeito na hora. Uma entrada "prova" antiga não pode religar o
 * relógio do simulado.
 *
 * Arquivo próprio (com `page` de `$app/state`) para o treino e o layout
 * continuarem com `$page` de `$app/stores` sem misturar os dois.
 */

let ultimaIdade = 0;
function novaIdade() {
	ultimaIdade = Math.max(Date.now(), ultimaIdade + 1);
	return ultimaIdade;
}

function prefixoComum(a, b) {
	let c = 0;
	while (c < a.length && c < b.length && a[c] === b[c]) c++;
	return c;
}

function camadasAtuais() {
	return page.state?.camadas || [];
}

/**
 * Chame UMA vez na inicialização da página (no `<script>`).
 *
 * @param {() => string[]} abertas camadas abertas agora, de baixo para cima
 * @param {(nome: string) => void} fechar fecha UMA camada mexendo só no estado
 *   da página, sem tocar no histórico
 */
export function ligarCamadas(abertas, fechar) {
	let hrefVisto = null;
	let idadeVista = 0;
	// fomos NÓS que chamamos history.go(-k): o popstate que vier é nosso
	let espera = null;

	function alinhar(h, l) {
		const c = prefixoComum(h, l);
		const tirar = h.length - c;
		if (tirar === 0) {
			for (let k = h.length; k < l.length; k++) {
				const idade = novaIdade();
				// antes do push: senão o próprio push parece um "avançar"
				idadeVista = idade;
				pushState('', { camadas: l.slice(0, k + 1), idade });
			}
		} else if (tirar === 1 && l.length > c) {
			// troca no mesmo nível (prova → resultado): substitui e empurra o resto
			replaceState('', { camadas: l.slice(0, c + 1), idade: idadeVista });
			for (let k = c + 1; k < l.length; k++) {
				const idade = novaIdade();
				idadeVista = idade;
				pushState('', { camadas: l.slice(0, k + 1), idade });
			}
		} else {
			// No popstate raso o Kit rola para a posição salva da entrada.
			// Quando foi a TELA que fechou a camada (ex.: o irPara do cartão,
			// que já subiu a página), essa rolagem velha desfaria o topo.
			espera = { rolagem: window.scrollY };
			history.go(-tirar);
			const minha = espera;
			setTimeout(() => {
				if (espera === minha) espera = null;
			}, 1000);
		}
	}

	$effect(() => {
		const h = page.state?.camadas || [];
		const idade = page.state?.idade ?? 0;
		const href = page.url.href;
		const l = abertas();
		untrack(() => {
			if (href !== hrefVisto) {
				// montagem, ou outra URL
				hrefVisto = href;
				idadeVista = idade;
				espera = null;
			} else if (idade !== idadeVista) {
				// a entrada mudou (popstate)
				const anterior = idadeVista;
				idadeVista = idade;
				if (espera) {
					const y = espera.rolagem;
					espera = null;
					window.scrollTo(0, y);
				} else if (idade < anterior && l.length) {
					// voltar do aluno: fecha o que está acima da entrada
					const n = Math.max(1, l.length - prefixoComum(l, h));
					for (let k = 0; k < n; k++) fechar(l[l.length - 1 - k]);
					// o estado mudou; o efeito roda de novo e alinha
					return;
				}
				// avançar: cai no alinhar, que desfaz
			}
			if (espera) return;
			alinhar(h, l);
		});
	});
}

/**
 * Sai da rota sem deixar camada morta no histórico.
 * @param {string} url
 */
export function sairDaRota(url) {
	return goto(url, { replaceState: camadasAtuais().length > 0 });
}

/** Há camada aberta registrada no histórico? (usada pela `BordaVoltar`) */
export function temCamadas() {
	return camadasAtuais().length > 0;
}
