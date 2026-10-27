<script>
	// Resultado do simulado em PAPEL, importado do site do professor
	// (pilar.ia.br). Não é o simulado do site: o dado é um retrato fixo, então
	// esta tela só lê a tabela `desempenho_papel` — nada de scraping aqui.
	import { onMount } from 'svelte';
	import { ArrowLeft, ArrowRight, ArrowSquareOut, Target } from 'phosphor-svelte';
	import { desempenhoPapel, minhasTurmas, nuvemLigada, usuarioAtual } from '$lib/nuvem.js';
	import { materiaPorArea, nomeMateria } from '$lib/materias.js';

	let carregando = $state(true);
	let usuario = $state(null);
	let turmas = $state([]);
	let linhas = $state([]);
	let erro = $state('');
	let simuladoId = $state('');

	let temRa = $derived(turmas.some((m) => m.ra));
	let atual = $derived(linhas.find((l) => l.simulado_id === simuladoId) ?? linhas[0] ?? null);
	let pctAtual = $derived(atual ? Math.round(Number(atual.percentual) * 100) : 0);
	let turma = $derived(atual?.turma ?? {});
	let media = $derived(turma.media_acertos == null ? null : Number(turma.media_acertos));
	let mediana = $derived(turma.mediana_acertos == null ? null : Number(turma.mediana_acertos));
	let totalQuestoes = $derived(Number(turma.total_questoes ?? atual?.total ?? 0));
	let notas = $derived(
		atual?.discursiva ? [atual.discursiva.nota_1, atual.discursiva.nota_2].filter((n) => n != null) : []
	);

	// As áreas do pilar com o nome que o site usa. O pilar manda percentual
	// 0–1; a tela trabalha em 0–100. Área sem par em `materias.json` aparece
	// com o nome cru e sem link de treino — melhor que chutar a matéria errada.
	let areas = $derived.by(() => {
		const doAluno = atual?.areas ?? {};
		const prioridades = new Map((atual?.prioridades ?? []).map((p) => [p.area, p]));
		return Object.entries(doAluno)
			.map(([nome, valor]) => {
				const id = materiaPorArea(nome);
				return {
					nome,
					id,
					rotulo: id ? nomeMateria(id) : nome,
					percentual: Math.round(Number(valor?.percentual ?? 0) * 100),
					turma: valor?.turma == null ? null : Math.round(Number(valor.turma) * 100),
					total: Number(valor?.total ?? 0),
					tendencia: prioridades.get(nome)?.tendencia ?? null
				};
			})
			.filter((a) => a.total > 0)
			.sort((a, b) => a.percentual - b.percentual || a.rotulo.localeCompare(b.rotulo, 'pt-BR'));
	});
	let foco = $derived(areas.slice(0, 5));
	let resto = $derived(areas.slice(5));

	function dia(iso) {
		const d = new Date(iso);
		return Number.isNaN(d.getTime())
			? ''
			: d.toLocaleDateString('pt-BR', { day: '2-digit', month: 'long' });
	}

	onMount(async () => {
		if (!nuvemLigada) {
			carregando = false;
			return;
		}
		try {
			usuario = await usuarioAtual();
			if (!usuario) return;
			turmas = await minhasTurmas();
			if (!temRa) return;
			linhas = await desempenhoPapel();
			simuladoId = linhas[0]?.simulado_id ?? '';
		} catch (e) {
			erro = e.message;
		} finally {
			carregando = false;
		}
	});
</script>

<svelte:head>
	<title>Simulado em papel · Simulado ENADE</title>
</svelte:head>

{#if carregando}
	<div class="space-y-3" role="status" aria-label="Carregando o seu resultado">
		<div class="h-48 animate-pulse rounded-3xl bg-skel"></div>
		<div class="h-24 animate-pulse rounded-3xl bg-skel"></div>
		<div class="h-40 animate-pulse rounded-3xl bg-skel"></div>
	</div>
{:else if erro}
	<p role="alert" class="rounded-2xl border border-bad-fg/30 bg-bad-bg p-3 text-sm font-semibold text-bad-fg">
		{erro}
	</p>
{:else if !nuvemLigada}
	<section class="rounded-3xl border border-line bg-card p-5 sm:p-6">
		<h1 class="font-display text-title font-extrabold">Simulado em papel</h1>
		<p class="mt-2 text-[15px] leading-relaxed text-pretty">
			A conta ainda não está ligada neste site. O resultado do simulado em papel aparece aqui quando
			você entra na turma com o seu RA.
		</p>
		<a href="/treino/" class="mt-4 inline-flex min-h-11 items-center gap-2 font-bold text-accent-ink">
			Ir para o treino <ArrowRight size={17} weight="bold" aria-hidden="true" />
		</a>
	</section>
{:else if !usuario}
	<section class="rounded-3xl border border-line bg-card p-5 sm:p-6">
		<h1 class="font-display text-title font-extrabold">Simulado em papel</h1>
		<p class="mt-2 text-[15px] leading-relaxed text-pretty text-ink-soft">
			Entre na sua conta para ver o seu resultado do simulado em papel. É o mesmo login que você usa
			para entrar na turma.
		</p>
		<a
			href="/conta/"
			class="btn3d duo-accent mt-5 flex min-h-[52px] items-center justify-center gap-2 rounded-[14px] px-6 font-display text-base font-bold"
		>
			Entrar na conta
		</a>
	</section>
{:else if !temRa}
	<section class="rounded-3xl border border-line bg-card p-5 sm:p-6">
		<h1 class="font-display text-title font-extrabold">Simulado em papel</h1>
		<p class="mt-2 text-[15px] leading-relaxed text-pretty text-ink-soft">
			Para ver o seu resultado, informe o seu RA em <strong class="text-ink">Conta e turma</strong>. Só
			quem fez o simulado em papel tem resultado para mostrar.
		</p>
		<a
			href="/conta/"
			class="btn3d duo-accent mt-5 flex min-h-[52px] items-center justify-center gap-2 rounded-[14px] px-6 font-display text-base font-bold"
		>
			Informar o RA
		</a>
	</section>
{:else if !atual}
	<section class="rounded-3xl border border-line bg-card p-5 sm:p-6">
		<h1 class="font-display text-title font-extrabold">Simulado em papel</h1>
		<p class="mt-2 text-[15px] leading-relaxed text-pretty text-ink-soft">
			Ainda não há resultado importado para o seu RA. O professor importa a lista de quem fez a prova;
			se você informou o RA agora, pode levar um tempo até aparecer.
		</p>
		<div class="mt-4 flex flex-wrap gap-3">
			<a href="/treino/" class="min-h-11 font-bold text-accent-ink">Treinar enquanto isso</a>
			<a href="/conta/" class="min-h-11 font-bold text-ink-soft">Conferir o RA</a>
		</div>
	</section>
{:else}
	<section class="blueprint faixa px-4 pt-7 pb-8 text-white sm:p-8">
		<a href="/conta/" class="inline-flex min-h-11 items-center gap-2 text-sm font-bold text-bar-fg hover:text-white">
			<ArrowLeft size={17} weight="bold" aria-hidden="true" /> Conta e turma
		</a>
		<p class="mt-2 text-sm font-semibold text-bar-fg">{atual.rotulo} · simulado em papel</p>
		<h1 class="mt-1 font-display text-3xl font-extrabold tracking-tight text-pretty">Seu resultado</h1>
		<p class="nums mt-4 font-display text-6xl leading-none font-black tracking-tight">
			{atual.acertos}<span class="text-2xl font-bold text-bar-fg">/{totalQuestoes || atual.total}</span>
		</p>
		<p class="mt-2 text-sm font-semibold text-bar-fg">
			{pctAtual}% de acerto
			{#if media !== null}· turma: média {media.toLocaleString('pt-BR', { maximumFractionDigits: 1 })}{/if}
			{#if mediana !== null}· mediana {mediana.toLocaleString('pt-BR', { maximumFractionDigits: 1 })}{/if}
		</p>
		{#if notas.length}
			<p class="mt-1 text-sm text-bar-fg">
				Dissertativas: {notas.map((n) => Number(n).toLocaleString('pt-BR', { minimumFractionDigits: 1, maximumFractionDigits: 1 })).join(' · ')}
			</p>
		{/if}
		<p class="mt-4 text-xs text-bar-fg">Importado do site do professor em {dia(atual.importado_em)}.</p>
		{#if foco[0]?.id}
			<a
				href="/treino/?materia={foco[0].id}"
				class="btn3d duo-accent mt-5 flex min-h-[52px] items-center justify-center gap-2 rounded-[14px] px-6 font-display text-base font-bold"
			>
				<Target size={20} weight="bold" aria-hidden="true" /> Treinar {foco[0].rotulo}
			</a>
		{/if}
	</section>

	{#if linhas.length > 1}
		<label class="mt-5 flex items-center gap-2 text-sm font-bold">
			Outro simulado
			<select bind:value={simuladoId} class="min-h-11 flex-1 rounded-xl border-2 border-line bg-paper px-3 text-base">
				{#each linhas as l (l.simulado_id)}
					<option value={l.simulado_id}>{l.rotulo}</option>
				{/each}
			</select>
		</label>
	{/if}

	<section class="mt-6" aria-labelledby="t-foco">
		<h2 id="t-foco" class="font-display text-title font-extrabold">Onde focar</h2>
		<p class="mt-1 text-sm text-pretty text-ink-soft">
			As áreas com menor acerto neste simulado, pior primeiro. A marca na barra é a média da
			turma.
		</p>

		{#if foco.length === 0}
			<p class="mt-4 rounded-3xl border border-line bg-card p-5 text-sm text-ink-soft">
				O site do professor não informou o desempenho por área deste simulado.
			</p>
		{:else}
			<ul class="mt-4 space-y-3">
				{#each foco as a (a.nome)}
					<li class="rounded-3xl border border-line bg-card p-4 sm:p-5">
						<div class="flex items-start justify-between gap-3">
							<div class="min-w-0">
								<p class="font-display text-[17px] font-bold text-pretty">{a.rotulo}</p>
								<p class="mt-0.5 flex flex-wrap items-center gap-x-2 text-xs text-ink-soft">
									<span>{a.total} {a.total === 1 ? 'questão' : 'questões'}</span>
									{#if a.turma !== null}<span>· turma {a.turma}%</span>{/if}
									{#if a.tendencia === 'piorou'}
										<span class="font-semibold text-bad-fg">· piorou desde o anterior</span>
									{:else if a.tendencia === 'melhorou'}
										<span class="font-semibold text-ok-fg">· melhorou</span>
									{:else if a.tendencia === 'estavel'}
										<span>· estável</span>
									{/if}
									{#if a.turma !== null && a.turma - a.percentual >= 10}
										<span class="font-semibold text-warn-fg">· {a.turma - a.percentual} pontos abaixo da turma</span>
									{/if}
								</p>
							</div>
							<p class="nums shrink-0 font-display text-2xl font-extrabold">{a.percentual}%</p>
						</div>
						<div class="relative mt-2 h-2 rounded-full bg-track" aria-hidden="true">
							<div class="h-full rounded-full bg-accent-bar" style="width: {a.percentual}%"></div>
							{#if a.turma !== null}
								<span class="absolute -top-1 h-4 w-0.5 rounded-full bg-ink ring-2 ring-card" style="left: calc({a.turma}% - 1px)"></span>
							{/if}
						</div>
						{#if a.id}
							<a href="/treino/?materia={a.id}" class="mt-2 inline-flex min-h-11 items-center gap-1.5 text-sm font-bold text-accent-ink">
								Treinar {nomeMateria(a.id)} <ArrowRight size={16} weight="bold" aria-hidden="true" />
							</a>
						{:else}
							<a href="/treino/" class="mt-2 inline-flex min-h-11 items-center gap-1.5 text-sm font-bold text-accent-ink">
								Treinar questões <ArrowRight size={16} weight="bold" aria-hidden="true" />
							</a>
						{/if}
					</li>
				{/each}
			</ul>
		{/if}

		{#if resto.length}
			<details class="mt-4 rounded-2xl border border-line bg-tile px-4 py-2">
				<summary class="flex min-h-11 cursor-pointer items-center text-sm font-bold">
					Ver as outras {resto.length} áreas
				</summary>
				<ul class="mt-1 mb-2 space-y-1.5">
					{#each resto as a (a.nome)}
						<li class="flex items-baseline justify-between gap-3 text-sm">
							<span class="min-w-0 text-pretty">{a.rotulo}</span>
							<span class="nums shrink-0 font-bold">{a.percentual}%{#if a.turma !== null}<span class="font-normal text-ink-soft"> (turma {a.turma}%)</span>{/if}</span>
						</li>
					{/each}
				</ul>
			</details>
		{/if}
	</section>

	<section class="mt-6 rounded-3xl border border-line bg-card p-5 sm:p-6" aria-labelledby="t-como">
		<h2 id="t-como" class="flex items-center gap-2 font-display text-heading font-extrabold">
			<Target size={20} weight="bold" aria-hidden="true" /> Como usar isso
		</h2>
		<p class="mt-2 text-sm leading-relaxed text-pretty">
			Comece pela primeira área: o botão abre o treino já filtrado por essa matéria. Se preferir uma
			sessão fechada, use o <a href="/estudo/" class="font-bold text-accent-ink underline">estudo por níveis</a>
			e escolha a mesma matéria.
		</p>
		<p class="mt-2 text-xs text-pretty text-ink-soft">
			Este resultado vem do simulado em papel do site do professor, não da sua nota oficial do ENADE.
			<a href="https://pilar.ia.br/enade2026/" target="_blank" rel="noopener" class="inline-flex items-center gap-1 font-bold text-accent-ink underline">
				Abrir o site do professor <ArrowSquareOut size={13} weight="bold" aria-hidden="true" />
			</a>
		</p>
	</section>
{/if}
