<script>
	// Ficha de UM aluno, aberta a partir do painel (é uma camada: o voltar do
	// sistema fecha). Tudo vem de uma ida só ao banco (`painel_aluno`), que
	// confere se quem pede é professor da turma e se o aluno é dela.
	import { onMount } from 'svelte';
	import { ArrowLeft, CheckCircle, WarningCircle, XCircle } from 'phosphor-svelte';
	import { painelAluno } from '$lib/nuvem.js';
	import { rotuloQuestao } from '$lib/banco.js';
	import { MATERIAS_CE, nomeMateria } from '$lib/materias.js';
	import GraficoColunas from './GraficoColunas.svelte';
	import { diaMes, isoDia, num, pct, plural, quando } from './formato.js';

	/**
	 * @type {{
	 *   turmaId: string,
	 *   alunoId: string,
	 *   turmaPorMateria: Array<{ materia: string, respondidas: number, certas: number }>,
	 *   porId: Map<string, any>,
	 *   onFechar: () => void
	 * }}
	 */
	let { turmaId, alunoId, turmaPorMateria, porId, onFechar } = $props();

	const DIAS = 35;
	// diferença que vale apontar: abaixo disso é ruído de poucas questões
	const ABAIXO = 10;
	// com 1 ou 2 respostas, o percentual da matéria é sorte, não diagnóstico
	const MINIMO = 3;

	let f = $state(null);
	let erro = $state('');

	onMount(async () => {
		window.scrollTo({ top: 0 });
		try {
			f = await painelAluno(turmaId, alunoId);
			if (!f) erro = 'Este aluno não está mais na turma.';
		} catch (e) {
			erro = e.message;
		}
	});

	let totais = $derived.by(() => {
		if (!f) return null;
		const respondidas = num(f.total);
		// acerto na PRIMEIRA tentativa (D16): refazer até acertar não infla
		const certasObjetivas = f.materias.reduce((t, m) => t + num(m.certas), 0);
		const objetivas = f.materias.reduce((t, m) => t + num(m.respondidas), 0);
		const desde = isoDia(new Date(Date.now() - 6 * 86_400_000));
		const semana = f.dias.filter((d) => String(d.dia).slice(0, 10) >= desde).reduce((t, d) => t + num(d.respondidas), 0);
		return { respondidas, acerto: pct(certasObjetivas, objetivas), semana, diasAtivos: f.dias.length };
	});

	// um ponto por dia, inclusive os sem estudo (o banco só devolve os com)
	let dias = $derived.by(() => {
		if (!f) return [];
		const porDia = new Map(f.dias.map((d) => [String(d.dia).slice(0, 10), d]));
		return Array.from({ length: DIAS }, (_, k) => {
			const d = new Date();
			d.setHours(12, 0, 0, 0);
			d.setDate(d.getDate() - (DIAS - 1 - k));
			const x = porDia.get(isoDia(d));
			const n = num(x?.respondidas);
			return {
				chave: isoDia(d),
				rotulo: diaMes(d),
				valor: n,
				dica: n ? `${diaMes(d)}: ${plural(n, 'questão', 'questões')}` : `${diaMes(d)}: não estudou`
			};
		});
	});

	// matérias do aluno ao lado da média da turma, pior primeiro
	let materias = $derived.by(() => {
		if (!f) return [];
		const daTurma = new Map(turmaPorMateria.map((m) => [m.materia, m]));
		return f.materias
			.filter((m) => m.materia && num(m.respondidas))
			.map((m) => {
				const t = daTurma.get(m.materia);
				return {
					materia: m.materia,
					respondidas: num(m.respondidas),
					aluno: pct(m.certas, m.respondidas),
					turma: t ? pct(t.certas, t.respondidas) : null
				};
			})
			.sort((x, y) => x.aluno - y.aluno);
	});
	let materiasFirmes = $derived(materias.filter((m) => m.respondidas >= MINIMO));
	let materiasPoucas = $derived(materias.filter((m) => m.respondidas < MINIMO));
	let naoTreinou = $derived(f ? MATERIAS_CE.filter((m) => !f.materias.some((x) => x.materia === m.id)) : []);
</script>

<button type="button" onclick={onFechar} class="inline-flex min-h-11 items-center gap-2 text-sm font-bold text-ink-soft hover:text-ink">
	<ArrowLeft size={17} weight="bold" aria-hidden="true" /> Voltar para a turma
</button>

{#if erro}
	<p role="alert" class="mt-4 rounded-2xl border border-bad-fg/30 bg-bad-bg p-3 text-sm font-semibold text-bad-fg">{erro}</p>
{:else if !f || !totais}
	<div class="mt-4 space-y-3" role="status" aria-label="Carregando a ficha do aluno">
		<div class="h-20 animate-pulse rounded-3xl bg-skel"></div>
		<div class="h-48 animate-pulse rounded-3xl bg-skel"></div>
	</div>
{:else}
	<header class="mt-2">
		<h1 class="font-display text-title font-extrabold text-pretty">{f.perfil.nome || f.perfil.apelido}</h1>
		<p class="mt-1 text-sm text-ink-soft">
			{f.perfil.ra ? `RA ${f.perfil.ra}. ` : 'Sem RA. '}Entrou na turma em {diaMes(f.perfil.entrou_em)}.
			{f.perfil.no_ranking ? '' : 'Pediu para não aparecer no ranking.'}
		</p>
	</header>

	<dl class="mt-4 grid grid-cols-2 gap-2 lg:grid-cols-4">
		<div class="rounded-2xl bg-tile p-3">
			<dt class="text-xs font-semibold text-ink-soft">Questões respondidas</dt>
			<dd class="mt-1 font-display text-2xl font-extrabold">{totais.respondidas.toLocaleString('pt-BR')}</dd>
		</div>
		<div class="rounded-2xl bg-tile p-3">
			<dt class="text-xs font-semibold text-ink-soft">Nos últimos 7 dias</dt>
			<dd class="mt-1 font-display text-2xl font-extrabold">{totais.semana.toLocaleString('pt-BR')}</dd>
		</div>
		<div class="rounded-2xl bg-tile p-3">
			<dt class="text-xs font-semibold text-ink-soft">Acerto na primeira tentativa</dt>
			<dd class="mt-1 font-display text-2xl font-extrabold">{totais.acerto ?? '—'}{totais.acerto === null ? '' : '%'}</dd>
		</div>
		<div class="rounded-2xl bg-tile p-3">
			<dt class="text-xs font-semibold text-ink-soft">Dias com estudo ({DIAS} dias)</dt>
			<dd class="mt-1 font-display text-2xl font-extrabold">{totais.diasAtivos}</dd>
		</div>
	</dl>

	<section class="mt-4 rounded-3xl border border-line bg-card p-4 sm:p-5" aria-label="Atividade">
		<GraficoColunas titulo="Questões por dia, nos últimos {DIAS} dias" itens={dias} cadaRotulo={7} altura={112} />
	</section>

	<div class="mt-4 grid items-start gap-4 lg:grid-cols-[1.3fr_1fr]">
		<section class="rounded-3xl border border-line bg-card p-4 sm:p-5" aria-labelledby="t-aluno-materias">
			<h2 id="t-aluno-materias" class="font-display text-heading font-bold">Por matéria</h2>
			<p class="text-sm text-ink-soft">Acerto na primeira tentativa, pior primeiro, com a média da turma marcada.</p>
			<!-- duas séries: a legenda é obrigatória (a cor sozinha não identifica) -->
			<p class="mt-2 flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-ink-soft" aria-hidden="true">
				<span class="flex items-center gap-1.5"><span class="h-2 w-4 rounded-full bg-accent-bar"></span> Este aluno</span>
				<span class="flex items-center gap-1.5"><span class="h-3 w-0.5 rounded-full bg-ink"></span> Média da turma</span>
			</p>
			{#if materias.length === 0}
				<p class="mt-3 text-sm text-ink-soft">Ainda não respondeu questões objetivas.</p>
			{:else if materiasFirmes.length === 0}
				<p class="mt-3 text-sm text-ink-soft">Nenhuma matéria tem {MINIMO} respostas ainda: é cedo para dizer onde ele erra.</p>
			{:else}
				<ul class="mt-3 space-y-3">
					{#each materiasFirmes as m (m.materia)}
						<li>
							<div class="flex items-baseline justify-between gap-3 text-sm">
								<span class="min-w-0 font-semibold text-pretty">{nomeMateria(m.materia)}</span>
								<span class="nums shrink-0"><strong>{m.aluno}%</strong>{#if m.turma !== null}<span class="text-ink-soft"> (turma {m.turma}%)</span>{/if}</span>
							</div>
							<div class="relative mt-1 h-2 rounded-full bg-track" aria-hidden="true">
								<div class="h-full rounded-full bg-accent-bar" style="width: {m.aluno}%"></div>
								{#if m.turma !== null}
									<span class="absolute -top-1 h-4 w-0.5 rounded-full bg-ink ring-2 ring-card" style="left: calc({m.turma}% - 1px)"></span>
								{/if}
							</div>
							<p class="mt-0.5 flex items-center gap-1 text-xs text-ink-soft">
								{plural(m.respondidas, 'resposta', 'respostas')}
								{#if m.turma !== null && m.turma - m.aluno >= ABAIXO}
									<span class="flex items-center gap-1 font-semibold text-warn-fg">
										<WarningCircle size={13} weight="bold" aria-hidden="true" /> {m.turma - m.aluno} pontos abaixo da turma
									</span>
								{/if}
							</p>
						</li>
					{/each}
				</ul>
			{/if}
			{#if materiasPoucas.length}
				<p class="mt-3 text-xs text-pretty text-ink-soft">
					Com menos de {MINIMO} respostas, ainda sem como dizer: {materiasPoucas.map((m) => nomeMateria(m.materia)).join(', ')}.
				</p>
			{/if}
			{#if naoTreinou.length}
				<details class="mt-4 rounded-2xl bg-tile px-3 py-2">
					<summary class="flex min-h-9 cursor-pointer items-center text-sm font-semibold">
						Ainda não treinou {naoTreinou.length} de {MATERIAS_CE.length} áreas da prova
					</summary>
					<ul class="mt-1 mb-1 flex flex-wrap gap-1.5">
						{#each naoTreinou as m (m.id)}
							<li class="rounded-full border border-line bg-card px-2.5 py-1 text-xs font-semibold text-ink-soft">{m.nome}</li>
						{/each}
					</ul>
				</details>
			{/if}
		</section>

		<div class="space-y-4">
			<section class="rounded-3xl border border-line bg-card p-4 sm:p-5" aria-labelledby="t-aluno-sim">
				<h2 id="t-aluno-sim" class="font-display text-heading font-bold">Simulados da turma</h2>
				{#if f.simulados.length === 0}
					<p class="mt-2 text-sm text-ink-soft">A turma ainda não teve simulado.</p>
				{:else}
					<ul class="mt-2 divide-y divide-line">
						{#each f.simulados as s (s.id)}
							{@const fez = num(s.respondidas) > 0}
							{@const futuro = new Date(s.abre_em).getTime() > Date.now()}
							<li class="flex items-baseline justify-between gap-3 py-2 text-sm">
								<span class="min-w-0 font-semibold text-pretty">{s.titulo}</span>
								{#if fez}
									<span class="nums shrink-0"><strong>{num(s.certas)}/{s.objetivas}</strong> <span class="text-ink-soft">({pct(s.certas, s.objetivas)}%)</span></span>
								{:else if futuro}
									<span class="shrink-0 text-xs text-ink-soft">ainda não abriu</span>
								{:else}
									<span class="flex shrink-0 items-center gap-1 text-xs font-bold text-bad-fg"><XCircle size={13} weight="bold" aria-hidden="true" /> não fez</span>
								{/if}
							</li>
						{/each}
					</ul>
				{/if}
			</section>
		</div>
	</div>

	<section class="mt-4 rounded-3xl border border-line bg-card p-4 sm:p-5" aria-labelledby="t-aluno-erradas">
		<h2 id="t-aluno-erradas" class="font-display text-heading font-bold">Questões que mais erra</h2>
		{#if f.erradas.length === 0}
			<p class="mt-2 text-sm text-ink-soft">Nenhum erro até agora.</p>
		{:else}
			<ul class="mt-2 grid gap-2 sm:grid-cols-2">
				{#each f.erradas as q (q.questao_id)}
					{@const b = porId.get(q.questao_id)}
					<li class="rounded-2xl bg-tile p-3">
						<p class="text-sm font-bold">{b ? rotuloQuestao(b) : q.questao_id}</p>
						<p class="text-xs text-pretty text-ink-soft">{b?.tema ?? ''}{b?.tema && q.materia ? ', ' : ''}{q.materia ? nomeMateria(q.materia) : ''}</p>
						{#if b?.gabarito && q.ultima_errada}
							<p class="mt-1 text-xs">Gabarito <strong>{b.gabarito}</strong>; quando errou, marcou <strong>{q.ultima_errada}</strong>.</p>
						{/if}
						<p class="mt-1 flex flex-wrap items-center gap-x-3 gap-y-0.5 text-xs">
							<span class="nums">{num(q.tentativas) === 1 ? 'Errou na única tentativa' : `Errou ${num(q.erros)} de ${num(q.tentativas)} tentativas`}</span>
							{#if q.ultima_certa}
								<span class="flex items-center gap-1 font-semibold text-ok-fg"><CheckCircle size={13} weight="bold" aria-hidden="true" /> acertou na última</span>
							{:else}
								<span class="flex items-center gap-1 font-semibold text-bad-fg"><XCircle size={13} weight="bold" aria-hidden="true" /> ainda erra</span>
							{/if}
							<span class="text-ink-soft">{quando(q.ultima_em)}</span>
						</p>
					</li>
				{/each}
			</ul>
		{/if}
	</section>
{/if}
