<script>
	// Colunas de UMA série ao longo do tempo (semanas, dias). Sem legenda: o
	// título diz o que é. Regras do painel (skill dataviz): barra de até 24 px
	// com ponta arredondada e base reta, grade de 1 px recessiva, número só no
	// último ponto e no maior; o resto vai na dica (mouse, foco ou toque) e na
	// tabela escondida para leitor de tela.

	/**
	 * @type {{
	 *   titulo: string,
	 *   itens: Array<{ chave: string, rotulo: string, valor: number | null, dica: string }>,
	 *   maximo?: number,
	 *   formatar?: (v: number) => string,
	 *   altura?: number,
	 *   cadaRotulo?: number
	 * }}
	 */
	let { titulo, itens, maximo = 0, formatar = (v) => String(v), altura = 128, cadaRotulo = 1 } = $props();

	let topo = $derived(Math.max(maximo, ...itens.map((x) => x.valor ?? 0), 1));
	let maior = $derived(itens.reduce((m, x, k) => ((x.valor ?? -1) > (itens[m]?.valor ?? -1) ? k : m), 0));
	let ultimo = $derived(itens.findLastIndex((x) => x.valor !== null));
	let ativo = $state(-1);
</script>

<figure class="min-w-0">
	<figcaption class="text-sm font-bold">{titulo}</figcaption>
	<div class="relative mt-3" style="height: {altura}px" role="img" aria-label={titulo}>
		<!-- grade: base, meio e topo -->
		{#each [0, 0.5, 1] as f (f)}
			<div class="absolute inset-x-0 border-t border-line" style="bottom: {f * 100}%" aria-hidden="true">
				<!-- rótulo só onde o valor é exato: "2" na altura de 1,5 mentia a escala -->
				{#if f > 0 && Number.isInteger(topo * f)}<span class="nums absolute -top-2.5 left-0 bg-card pr-1 text-xs text-ink-soft">{formatar(topo * f)}</span>{/if}
			</div>
		{/each}
		<div class="absolute inset-0 left-8 flex items-end justify-around" aria-hidden="true">
			{#each itens as x, k (x.chave)}
				<!-- alvo de toque = a coluna inteira, maior que a barra -->
				<div
					role="presentation"
					class="relative flex h-full flex-1 items-end justify-center"
					onpointerenter={() => (ativo = k)}
					onpointerleave={() => (ativo = -1)}
					onpointerdown={() => (ativo = k)}
				>
					{#if x.valor !== null}
						<div
							class="w-full max-w-6 rounded-t bg-accent-bar"
							style="height: {Math.max((x.valor / topo) * 100, x.valor > 0 ? 2 : 0)}%; margin: 0 1px"
						></div>
						{#if (k === ultimo || k === maior) && x.valor > 0}
							<span class="nums absolute text-xs font-bold" style="bottom: calc({(x.valor / topo) * 100}% + 2px)">{formatar(x.valor)}</span>
						{/if}
					{/if}
					{#if ativo === k}
						<span class="pointer-events-none absolute bottom-full z-10 mb-1 w-max max-w-44 rounded-lg bg-bar px-2 py-1 text-xs font-semibold text-white shadow">
							{x.dica}
						</span>
					{/if}
				</div>
			{/each}
		</div>
	</div>
	<div class="ml-8 flex justify-around" aria-hidden="true">
		{#each itens as x, k (x.chave)}
			<span class="nums flex-1 text-center text-xs text-ink-soft">{k % cadaRotulo === 0 || k === itens.length - 1 ? x.rotulo : ''}</span>
		{/each}
	</div>
	<table class="sr-only">
		<caption>{titulo}</caption>
		<tbody>
			{#each itens as x (x.chave)}
				<tr><th scope="row">{x.rotulo}</th><td>{x.dica}</td></tr>
			{/each}
		</tbody>
	</table>
</figure>
