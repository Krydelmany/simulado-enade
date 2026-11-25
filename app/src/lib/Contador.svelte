<script>
	import { untrack } from 'svelte';
	import { reduzirMovimento } from './motion.js';

	// `pular` mostra o valor final na hora (aluno tocou no palco, ou a tela está
	// sendo reaberta); `atraso` encaixa a contagem na coreografia do resumo.
	let { valor = 0, duracao = 900, atraso = 0, pular = false } = $props();

	// Sempre começa em 0 (igual ao SSR — evita mismatch de hidratação).
	let atual = $state(0);
	// Variável simples (não reativa): guarda o último alvo já aplicado para não
	// reanimar/piscar quando o número é o mesmo de antes.
	let alvoAnterior;

	$effect(() => {
		const alvo = valor; // leitura reativa: reanima quando o valor muda
		if (pular || reduzirMovimento()) {
			alvoAnterior = alvo;
			atual = alvo; // sem animação — salta direto para o valor final
			return;
		}
		if (alvo === alvoAnterior) return;
		const de = untrack(() => atual); // untrack: escrever `atual` não deve re-disparar
		alvoAnterior = alvo;

		let raf;
		const delta = alvo - de;
		const t0 = performance.now() + atraso;
		const passo = (t) => {
			const p = Math.min(1, Math.max(0, (t - t0) / duracao));
			// easing para fora (cubic-out): rápido no começo, assenta no fim
			atual = de + Math.round(delta * (1 - Math.pow(1 - p, 3)));
			if (p < 1) raf = requestAnimationFrame(passo);
		};
		raf = requestAnimationFrame(passo);
		return () => cancelAnimationFrame(raf);
	});
</script>

<!-- leitor de tela recebe o valor final, não a contagem no meio do caminho -->
<span class="nums" aria-hidden="true">{atual}</span><span class="sr-only">{valor}</span>
