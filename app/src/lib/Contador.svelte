<script>
	import { untrack } from 'svelte';
	import { reduzirMovimento } from './motion.js';

	let { valor = 0, duracao = 900 } = $props();

	// Sempre começa em 0 (igual ao SSR — evita mismatch de hidratação).
	let atual = $state(0);
	// Variável simples (não reativa): guarda o último alvo já aplicado para não
	// reanimar/piscar quando o número é o mesmo de antes.
	let alvoAnterior;

	$effect(() => {
		const alvo = valor; // leitura reativa: reanima quando o valor muda
		if (alvo === alvoAnterior) return;
		const de = untrack(() => atual); // untrack: escrever `atual` não deve re-disparar
		alvoAnterior = alvo;

		if (reduzirMovimento()) {
			atual = alvo; // sem animação — salta direto para o valor final
			return;
		}

		let raf;
		const delta = alvo - de;
		const t0 = performance.now();
		const passo = (t) => {
			const p = Math.min(1, (t - t0) / duracao);
			// easing para fora (cubic-out): rápido no começo, assenta no fim
			atual = de + Math.round(delta * (1 - Math.pow(1 - p, 3)));
			if (p < 1) raf = requestAnimationFrame(passo);
		};
		raf = requestAnimationFrame(passo);
		return () => cancelAnimationFrame(raf);
	});
</script>

<span class="nums">{atual}</span>
