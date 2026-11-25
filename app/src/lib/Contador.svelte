<script>
	import { untrack } from 'svelte';
	import { reduzirMovimento } from './motion.js';

	// `pular` mostra o valor final na hora (aluno tocou no palco, ou a tela está
	// sendo reaberta); `atraso` encaixa a contagem na coreografia do resumo.
	let { valor = 0, duracao = 900, atraso = 0, pular = false } = $props();

	// Sempre começa em 0 (igual ao SSR — evita mismatch de hidratação).
	let atual = $state(0);
	// Derivado: só muda quando o NÚMERO muda. Lendo a prop direto, a rota que
	// recriasse a lista com o mesmo valor cancelava a contagem no meio.
	let alvo = $derived(valor);

	$effect(() => {
		const ate = alvo; // leitura reativa: reanima quando o valor muda
		if (pular || reduzirMovimento()) {
			atual = ate; // sem animação — salta direto para o valor final
			return;
		}
		const de = untrack(() => atual); // untrack: escrever `atual` não deve re-disparar

		let raf;
		const delta = ate - de;
		const t0 = performance.now() + untrack(() => atraso);
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
