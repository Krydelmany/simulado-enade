<script>
	// Guia do Matheus (PDF de 41 páginas, compartilhado na turma em 25/11/2026).
	// Fica FORA do banco oficial: o conteúdo é autoral, então não entra no
	// Treino/Estudo/Simulado nem nas estatísticas — como o questionário de POO.
	import { onMount } from 'svelte';
	import Questao from '$lib/Questao.svelte';
	import TextoRico from '$lib/TextoRico.svelte';
	import { ArrowSquareOut, BookOpen, CheckCircle, FileText, ListNumbers } from 'phosphor-svelte';

	let dados = $state(null);
	let carregando = $state(true);
	let erro = $state('');
	let aba = $state('resumos');
	// resposta por id de questão (só memória da página; o guia não grava histórico)
	let respostas = $state({});
	let memoriaAberta = $state({});

	let objetivas = $derived(dados?.questoes ?? []);
	let feitas = $derived(objetivas.filter((q) => respostas[q.id]).length);
	let certas = $derived(objetivas.filter((q) => respostas[q.id]?.certa).length);

	onMount(async () => {
		try {
			const r = await fetch('/guia/matheus.json');
			if (!r.ok) throw new Error('Não deu para carregar o guia.');
			const d = await r.json();
			if (!d.capitulos?.length || !d.questoes?.length) throw new Error('O guia veio incompleto.');
			dados = d;
		} catch (e) {
			erro = e.message;
		} finally {
			carregando = false;
		}
	});

	function aoResponder(q, r) {
		respostas[q.id] = r;
	}
</script>

<div class="mx-auto w-full max-w-3xl">
	{#if carregando}
		<div class="space-y-3" role="status" aria-label="Carregando o guia">
			<div class="h-32 animate-pulse rounded-3xl bg-skel"></div>
			<div class="h-20 animate-pulse rounded-3xl bg-skel"></div>
			<div class="h-20 animate-pulse rounded-3xl bg-skel"></div>
		</div>
	{:else if erro}
		<div class="rounded-3xl bg-card p-6 text-center shadow-sm" role="alert">
			<p class="font-display text-lg font-bold">{erro}</p>
			<p class="mt-1 text-sm text-ink-soft">Verifique sua conexão e tente de novo.</p>
			<button type="button" onclick={() => location.reload()} class="btn3d duo-accent mt-4 w-full rounded-2xl p-3.5 font-bold">
				Tentar de novo
			</button>
		</div>
	{:else}
		<header class="blueprint faixa px-4 pt-7 pb-8 text-white sm:p-8">
			<p class="inline-flex items-center gap-2 rounded-full bg-white/10 px-3 py-1 text-sm font-semibold text-bar-fg">
				<BookOpen size={16} weight="bold" aria-hidden="true" />
				Conteúdo do Matheus · autoral
			</p>
			<h1 class="mt-4 font-display text-hero font-black text-balance">Guia de estudo</h1>
			<p class="mt-3 max-w-[52ch] text-base leading-relaxed text-pretty text-bar-fg">
				Resumo das disciplinas do boletim, com exemplos resolvidos, folha de fórmulas, perguntas de
				memória e um simulado de 24 objetivas + 2 discursivas.
			</p>
			<a
				href={dados.pdf}
				target="_blank"
				rel="noopener"
				class="mt-5 inline-flex min-h-11 items-center gap-2 rounded-[14px] border-2 border-white/25 px-4 text-sm font-bold transition-colors hover:bg-white/10"
			>
				<FileText size={18} weight="bold" aria-hidden="true" />
				Abrir o PDF original (41 páginas)
				<ArrowSquareOut size={15} weight="bold" aria-hidden="true" />
			</a>
		</header>

		<p class="mt-4 rounded-2xl border border-line bg-card p-4 text-sm leading-relaxed text-ink-soft">
			{dados.nota}
		</p>

		<div class="mt-5 flex gap-2" role="group" aria-label="O que ver no guia">
			<button
				type="button"
				onclick={() => (aba = 'resumos')}
				aria-pressed={aba === 'resumos'}
				class="flex min-h-11 flex-1 items-center justify-center gap-2 rounded-2xl border-2 px-3 text-sm font-bold {aba === 'resumos'
					? 'border-accent bg-accent-soft text-accent-ink'
					: 'border-line bg-card text-ink-soft'}"
			>
				<BookOpen size={17} weight="bold" aria-hidden="true" /> Resumos
			</button>
			<button
				type="button"
				onclick={() => (aba = 'questoes')}
				aria-pressed={aba === 'questoes'}
				class="flex min-h-11 flex-1 items-center justify-center gap-2 rounded-2xl border-2 px-3 text-sm font-bold {aba === 'questoes'
					? 'border-accent bg-accent-soft text-accent-ink'
					: 'border-line bg-card text-ink-soft'}"
			>
				<ListNumbers size={17} weight="bold" aria-hidden="true" /> 24 + 2 questões
			</button>
		</div>

		{#if aba === 'resumos'}
			<p class="mt-5 text-sm leading-relaxed text-ink-soft">
				Leia um capítulo, feche o texto e responda ao quadro <strong>De memória</strong> sem olhar. Se
				travar, refaça o exemplo.
			</p>
			<div class="mt-3 space-y-3">
				{#each dados.capitulos as c (c.id)}
					<details class="group rounded-3xl border border-line bg-card">
						<summary class="flex cursor-pointer items-center gap-3 p-4 sm:p-5">
							<span class="nums flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-tile text-sm font-extrabold text-ink-soft">
								{c.numero}
							</span>
							<span class="font-display text-base font-bold text-pretty">{c.titulo}</span>
							<span class="ml-auto shrink-0 text-ink-soft transition-transform group-open:rotate-180" aria-hidden="true">▾</span>
						</summary>
						<div class="space-y-5 border-t border-line p-4 sm:p-5">
							<p class="text-sm leading-relaxed text-ink-soft">{c.intro}</p>
							{#each c.blocos as b, bi (bi)}
								{#if b.exemplo}
									<div class="rounded-2xl bg-tile p-4">
										<p class="text-label font-bold text-accent-ink">Exemplo · {b.exemplo}</p>
										{#each b.paragrafos as p, pi (pi)}
											<p class="enunciado mt-2 text-sm leading-relaxed"><TextoRico texto={p} /></p>
										{/each}
									</div>
								{:else}
									<section>
										<h3 class="font-display text-base font-bold">{b.subtitulo}</h3>
										{#each b.paragrafos as p, pi (pi)}
											<p class="enunciado mt-2 text-sm leading-relaxed"><TextoRico texto={p} /></p>
										{/each}
										{#if b.lista?.length}
											<ul class="mt-2 space-y-1.5 text-sm leading-relaxed">
												{#each b.lista as item, ii (ii)}
													<li class="flex gap-2">
														<span class="shrink-0 text-accent" aria-hidden="true">•</span>
														<span>{item}</span>
													</li>
												{/each}
											</ul>
										{/if}
									</section>
								{/if}
							{/each}
							<div class="rounded-2xl border border-accent/40 bg-accent-soft p-4">
								<p class="text-label font-bold text-accent-ink">De memória · {c.memoria.letra}</p>
								<p class="mt-1.5 text-sm font-semibold">{c.memoria.pergunta}</p>
								{#if memoriaAberta[c.memoria.letra]}
									<p class="enunciado mt-2 text-sm leading-relaxed text-ink-soft">
										{dados.respostasMemoria[c.memoria.letra]}
									</p>
								{:else}
									<button
										type="button"
										onclick={() => (memoriaAberta[c.memoria.letra] = true)}
										class="mt-2 min-h-11 text-sm font-bold text-accent-ink underline underline-offset-2"
									>
										Ver resposta
									</button>
								{/if}
							</div>
						</div>
					</details>
				{/each}
			</div>

			<section class="mt-6 rounded-3xl border border-line bg-card p-5 sm:p-6" aria-labelledby="titulo-formulas">
				<h2 id="titulo-formulas" class="font-display text-title font-extrabold">Folha de fórmulas</h2>
				<p class="mt-1 text-sm text-ink-soft">
					Tente reconstruir cada relação no papel e diga em uma frase quando ela pode ser usada.
				</p>
				<dl class="mt-4 space-y-3">
					{#each dados.formulas as f (f.assunto)}
						<div class="rounded-2xl bg-tile p-3.5">
							<dt class="text-label font-bold text-ink-soft">{f.assunto}</dt>
							<dd class="mt-1 font-mono text-[13px] font-semibold break-words">{f.relacao}</dd>
							<dd class="mt-1 text-xs leading-relaxed text-ink-soft">{f.conferencia}</dd>
						</div>
					{/each}
				</dl>
			</section>
		{:else}
			<div class="mt-5 rounded-3xl border border-line bg-card p-5">
				<p class="text-label font-bold text-ink-soft">Simulado autoral do guia</p>
				<p class="mt-1 text-sm leading-relaxed text-ink-soft">
					24 objetivas com correção na hora e comentário do gabarito. Depois, 2 discursivas com os
					modelos de resposta — não são questões do INEP.
				</p>
				<p class="nums mt-3 font-display text-2xl font-extrabold">
					{certas}<span class="text-base font-semibold text-ink-soft">/{objetivas.length} certas</span>
				</p>
				<p class="mt-1 flex items-center gap-1.5 text-sm text-ink-soft">
					<CheckCircle size={16} weight="bold" aria-hidden="true" />
					{feitas} respondidas · {objetivas.length - feitas} por fazer
				</p>
			</div>

			<div class="mt-4 space-y-4">
				{#each objetivas as q (q.id)}
					<div>
						<Questao {q} onResponder={(r) => aoResponder(q, r)} />
						{#if respostas[q.id] && q.comentario}
							<div class="mx-1 rounded-b-2xl border border-t-0 border-line bg-panel p-4">
								<p class="text-label font-bold text-ink-soft">
									Gabarito comentado · {q.assunto}
								</p>
								<p class="enunciado mt-1.5 text-sm leading-relaxed"><TextoRico texto={q.comentario} /></p>
								{#if q.revisarPagina}
									<p class="mt-2 text-xs font-semibold text-ink-soft">
										Para revisar: capítulo da página {q.revisarPagina} do PDF.
									</p>
								{/if}
							</div>
						{/if}
					</div>
				{/each}
			</div>

			<h2 class="mt-8 font-display text-title font-extrabold">Discursivas do guia</h2>
			<p class="mt-1 text-sm text-ink-soft">
				Escreva no papel, compare com o modelo e avalie cada item (a, b e c valem 1 ponto no guia).
			</p>
			<div class="mt-4 space-y-4">
				{#each dados.discursivas as q (q.id)}
					<Questao {q} onResponder={(r) => aoResponder(q, r)} />
				{/each}
			</div>
		{/if}
	{/if}
</div>
