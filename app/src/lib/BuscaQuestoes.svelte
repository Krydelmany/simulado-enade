<script>
	/**
	 * Busca de questões, no topo do treino.
	 *
	 * O pedido era: digitar um pedaço do enunciado — ou o número da questão — e
	 * ver as que parecem, já dando para identificar qual é qual. Daí duas
	 * decisões que não são estéticas:
	 *
	 *  - cada resultado mostra o GABARITO. Sem isso a lista é só um punhado de
	 *    textos parecidos e o aluno continua sem saber onde está a que quer;
	 *  - os chips dizem ONDE o termo bateu (enunciado / alternativas / tema /
	 *    número), porque "bateu na alternativa" e "bateu no enunciado" são
	 *    informações diferentes sobre o resultado.
	 *
	 * O motor é `lib/busca.js`, puro e testado; aqui só entra a lista.
	 */
	import { buscar, destacar, resumo, FILTROS } from './busca.js';
	import { nomeMateria } from './materias.js';
	import { rotuloQuestao } from './banco.js';
	import { MagnifyingGlass, X } from 'phosphor-svelte';

	let { banco, aoPular } = $props();

	let query = $state('');
	let campo = $state('tudo');
	// acima disso a lista vira um balde: ninguém lê 40 resultados, e o custo de
	// renderizar o destaque de 40 enunciados numa tela que também tem a questão
	// não vale a pena
	const TETO = 25;
	// o banco chega assíncrono (carregarBanco). Buscar antes disso devolvia
	// "nada encontrado" — que é mentira: o banco é que não tinha chegado.
	let vazio = $derived(!banco || banco.length === 0);

	// palavras da busca, do jeito que `destacar` espera (normalizadas)
	let palavras = $derived(
		query
			.trim()
			.toLowerCase()
			.normalize('NFD')
			.replace(/[\u0300-\u036f]/g, '')
			.replace(/[^\p{L}\p{N}]+/gu, ' ')
			.split(' ')
			.filter((t) => t.length > 1)
	);
	let resultados = $derived(vazio ? [] : buscar(banco, query, { campo }));

	function fechar() {
		query = '';
	}
</script>

<div class="relative">
	<div class="flex items-center gap-2">
		<div class="relative min-w-0 flex-1">
			<MagnifyingGlass
				size={18}
				weight="bold"
				class="pointer-events-none absolute top-1/2 left-3 -translate-y-1/2 text-ink-soft"
				aria-hidden="true"
			/>
			<input
				bind:value={query}
				type="search"
				enterkeyhint="search"
				placeholder="Buscar por enunciado, tema ou número da questão"
				aria-label="Buscar questões no banco"
				class="h-12 w-full rounded-2xl border-2 border-line bg-card pr-10 pl-11 text-[15px] font-semibold text-ink outline-offset-2 placeholder:font-normal placeholder:text-ink-soft focus:border-ink"
			/>
			{#if query}
				<button
					type="button"
					onclick={fechar}
					aria-label="Limpar busca"
					class="absolute top-1/2 right-2 flex h-9 min-w-9 -translate-y-1/2 items-center justify-center rounded-full text-ink-soft transition-transform active:scale-95"
				>
					<X size={18} weight="bold" aria-hidden="true" />
				</button>
			{/if}
		</div>
	</div>

	<!-- Filtros: chips de campo. Só aparecem com busca ativa — uma fileira de
	     chips numa tela que não está buscando é só ruído. -->
	{#if query.trim()}
		<div class="mt-2 flex flex-wrap gap-1.5" role="group" aria-label="Filtrar a busca por campo">
			{#each FILTROS as f (f.id)}
				<button
					type="button"
					onclick={() => (campo = f.id)}
					aria-pressed={campo === f.id}
					class="min-h-9 rounded-full px-3 text-xs font-bold transition-colors {campo === f.id
						? 'bg-ink text-paper'
						: 'border border-line bg-card text-ink-soft'}"
				>
					{f.nome}
				</button>
			{/each}
		</div>
	{/if}

	{#if query.trim()}
		<div
			class="absolute inset-x-0 top-full z-30 mt-2 max-h-[62vh] overflow-y-auto rounded-3xl border border-line bg-card p-2 shadow-[0_18px_50px_-16px_rgba(20,33,61,0.45)]"
			role="listbox"
			aria-label="Resultados da busca"
		>
			{#if vazio}
				<p class="p-4 text-center text-sm text-ink-soft" role="status">Carregando o banco de questões…</p>
			{:else if palavras.length === 0}
				<!--
					Escrever 1 letra não é busca: `termos()` descarta as de 1
					caractere, então a query não tem palavra útil nenhuma. Dizer
					"nada encontrado para f" manda o aluno procurar palavras
					menores quando o problema é digitar mais.
				-->
				<p class="p-4 text-center text-sm text-ink-soft" role="status">
					Digite ao menos duas letras, ou o número da questão.
				</p>
			{:else if resultados.length === 0}
				<p class="p-4 text-center text-sm text-ink-soft" role="status">
					Nada encontrado para <span class="font-bold">{query}</span>. Tente outras palavras ou o número da questão.
				</p>
			{:else}
				<p class="px-2 py-1 text-[11px] font-bold text-ink-soft" role="status">
					{Math.min(resultados.length, TETO)} de {resultados.length}
					{resultados.length > 1 ? 'questões' : 'questão'} · clique para ir direto nela
				</p>
				<ul class="mt-1 space-y-1">
					{#each resultados.slice(0, TETO) as r (r.q.id)}
						<li>
							<button
								type="button"
								onclick={() => {
									aoPular?.(r.q.id);
									fechar();
								}}
								class="w-full rounded-2xl border border-line bg-card p-3 text-left transition-colors hover:border-ink/40 active:scale-[0.99]"
							>
								<div class="flex flex-wrap items-center gap-1.5">
									<span class="font-code text-[11px] font-bold text-accent-ink uppercase">
										{rotuloQuestao(r.q)}
									</span>
									{#if r.q.materia}
										<span class="rounded-full bg-tile px-2 py-0.5 text-[10px] font-bold text-ink-soft">
											{ nomeMateria(r.q.materia) }
										</span>
									{/if}
								</div>

								<!-- Gabarito aparece de propósito: é o que permite
								     reconhecer a questão na lista. -->
								<p class="mt-1.5 flex items-center gap-1.5 text-xs font-bold">
									<span class="text-ink-soft">Resposta:</span>
									<span
										class="nums inline-flex h-5 min-w-5 items-center justify-center rounded-md px-1 font-display text-[11px] {r.q.gabarito ===
										'ANULADA'
											? 'bg-warn-bg text-warn-fg'
											: 'bg-ok-solid text-white'}"
									>
										{r.q.gabarito}
									</span>
								</p>

								<p class="enunciado mt-1 text-[13px] leading-relaxed text-ink-soft">
									{#each destacar(resumo(r.q.enunciado, palavras), palavras) as p (p.t + p.m)}
										{#if p.m}
											<mark
												class="rounded-[3px] bg-accent-soft px-0.5 font-bold text-accent-ink"
												>{p.t}</mark
											>
										{:else}{p.t}{/if}
									{/each}
								</p>

								{#if r.onde.length}
									<p class="mt-1.5 flex flex-wrap gap-1">
										{#each r.onde as o (o)}
											<span class="rounded-full border border-line px-1.5 py-0.5 text-[10px] font-bold text-ink-soft">
												{ o === 'alternativas' ? 'nas alternativas' : o }
											</span>
										{/each}
									</p>
								{/if}
							</button>
						</li>
					{/each}
				</ul>
				{#if resultados.length > TETO}
					<p class="mt-1 px-2 pb-1 text-[11px] text-ink-soft">
						Refine a busca para ver as outras {resultados.length - TETO}.
					</p>
				{/if}
			{/if}
		</div>
	{/if}
</div>
