<script>
	import { ArrowSquareOut } from 'phosphor-svelte';

	let { texto = '' } = $props();

	const URL = /(https?:\/\/[^\s<>]+)/g;
	// Blocos ```lang … ``` viram <code class="codeblock"> — o resto é texto corrido.
	const FENCE = /```([^\n`]*)\n?([\s\S]*?)```/g;

	// O banco guarda fontes como <https://…> — tira os colchetes, vira link real.
	const blocos = $derived.by(() => {
		const limpo = texto.replace(/<(https?:\/\/[^<>\s]+)>/g, '$1');
		const partes = [];
		let ultimo = 0;
		let m;
		FENCE.lastIndex = 0;
		while ((m = FENCE.exec(limpo)) !== null) {
			if (m.index > ultimo) partes.push({ tipo: 'texto', valor: limpo.slice(ultimo, m.index) });
			partes.push({ tipo: 'codigo', lang: m[1].trim(), valor: m[2].replace(/\n$/, '') });
			ultimo = m.index + m[0].length;
		}
		if (ultimo < limpo.length) partes.push({ tipo: 'texto', valor: limpo.slice(ultimo) });
		return partes;
	});

	function ehUrl(s) {
		return /^https?:\/\/[^\s<>]+$/.test(s);
	}

	function pedacos(t) {
		return t.split(URL);
	}
</script>

<!-- Fica como <span> (conteúdo "phrasing") porque Questao usa este componente
     dentro de <p>: um <div>/<pre> ali faria o parser fechar o <p> e quebrar a
     hidratação. O layout de bloco vem do CSS (class "block" / ".codeblock"). -->
<span class="enunciado block max-w-[62ch]">
	{#each blocos as bloco, bi (bi)}
		{#if bloco.tipo === 'codigo'}
			<code class="codeblock" data-lang={bloco.lang || undefined}>{bloco.valor}</code>
		{:else}
			{#each pedacos(bloco.valor) as p, k (k)}
				{#if ehUrl(p)}
					<a
						href={p}
						target="_blank"
						rel="noopener"
						class="inline-flex max-w-full items-baseline gap-0.5 font-semibold text-accent-ink underline decoration-accent/50 decoration-2 underline-offset-2 [overflow-wrap:anywhere]"
					>
						<ArrowSquareOut size={13} weight="bold" class="shrink-0 self-center" aria-hidden="true" />
						<span class="[overflow-wrap:anywhere]">{p}</span>
					</a>
				{:else}
					{p}
				{/if}
			{/each}
		{/if}
	{/each}
</span>
