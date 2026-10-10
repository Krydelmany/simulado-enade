<script>
	import { ArrowSquareOut } from 'phosphor-svelte';

	let { texto = '' } = $props();

	const URL = /(https?:\/\/[^\s<>]+)/g;
	// o banco guarda fontes como <https://…> — tira os colchetes, vira link de verdade
	const limpo = texto.replace(/<(https?:\/\/[^<>\s]+)>/g, '$1');
	const partes = limpo.split(URL);

	function ehUrl(s) {
		return /^https?:\/\/[^\s<>]+$/.test(s);
	}
</script>

<span class="enunciado"
	>{#each partes as p, k (k)}{#if ehUrl(p)}<a
				href={p}
				target="_blank"
				rel="noopener"
				class="inline-flex max-w-full items-baseline gap-0.5 font-semibold text-accent-ink underline decoration-accent/50 decoration-2 underline-offset-2 [overflow-wrap:anywhere]"
				><ArrowSquareOut size={13} weight="bold" class="shrink-0 self-center" aria-hidden="true" /><span
					class="[overflow-wrap:anywhere]">{p}</span
				></a
			>{:else}{p}{/if}{/each}</span
>
