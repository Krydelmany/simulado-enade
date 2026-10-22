<script>
	// Primeira aba do painel: responde, nesta ordem, o que o professor quer
	// saber antes de entrar na sala — a turma está estudando? quem sumiu? onde
	// ela erra? está melhorando? Tudo sai das mesmas `painel_*`; nada novo no
	// banco.
	import { ArrowDown, ArrowUp, Check, Copy, Minus } from 'phosphor-svelte';
	import { MATERIAS_CE, nomeMateria } from '$lib/materias.js';
	import GraficoColunas from './GraficoColunas.svelte';
	import { diaMes, inicioDaSemana, isoDia, num, pct, plural, quando } from './formato.js';

	/** @type {{ dados: any, simulados: any[], onAbrirAluno: (id: string) => void, onIrPara: (aba: string) => void }} */
	// `dados.simulados` = painel_simulados_resumo (participação e média por prova)
	let { dados, simulados, onAbrirAluno, onIrPara } = $props();

	const SEMANAS = 8;
	// com menos respostas que isso, o acerto da matéria é sorte, não ponto fraco
	const MINIMO_MATERIA = 5;

	// as últimas 8 semanas, inclusive as sem resposta (o banco não as devolve)
	let semanas = $derived.by(() => {
		const porSemana = new Map(dados.semanas.map((s) => [String(s.semana).slice(0, 10), s]));
		const atual = inicioDaSemana();
		return Array.from({ length: SEMANAS }, (_, k) => {
			const d = new Date(atual);
			d.setDate(d.getDate() - 7 * (SEMANAS - 1 - k));
			const s = porSemana.get(isoDia(d));
			return {
				chave: isoDia(d),
				rotulo: diaMes(d),
				ativos: num(s?.alunos_ativos),
				respondidas: num(s?.respondidas),
				certas: num(s?.certas)
			};
		});
	});
	let estaSemana = $derived(semanas.at(-1));
	let semanaPassada = $derived(semanas.at(-2));

	let alunos = $derived(dados.alunos.length);

	// acerto nas questões oficiais do ENADE: é o número que prevê a prova
	let oficiais = $derived.by(() => {
		const o = dados.materias.filter((m) => m.oficial);
		return { respondidas: o.reduce((t, m) => t + num(m.respondidas), 0), certas: o.reduce((t, m) => t + num(m.certas), 0) };
	});

	// sem estudo nos últimos 7 dias, quem nunca entrou primeiro
	let parados = $derived(
		dados.alunos
			.filter((a) => num(a.respondidas_7d) === 0)
			.sort((x, y) => (x.ultima_em ? new Date(x.ultima_em).getTime() : 0) - (y.ultima_em ? new Date(y.ultima_em).getTime() : 0))
	);

	// matérias somando oficiais e revisão
	let porMateria = $derived.by(() => {
		const mapa = new Map();
		for (const m of dados.materias) {
			if (!m.materia) continue;
			const x = mapa.get(m.materia) ?? { materia: m.materia, respondidas: 0, certas: 0 };
			x.respondidas += num(m.respondidas);
			x.certas += num(m.certas);
			mapa.set(m.materia, x);
		}
		return [...mapa.values()];
	});
	let fracas = $derived(
		porMateria
			.filter((m) => m.respondidas >= MINIMO_MATERIA)
			.sort((x, y) => pct(x.certas, x.respondidas) - pct(y.certas, y.respondidas))
			.slice(0, 3)
	);
	let intocadas = $derived(MATERIAS_CE.filter((m) => !porMateria.some((x) => x.materia === m.id)));

	// simulados que alguém já fez, na ordem em que abriram
	let feitos = $derived((dados.simulados ?? []).filter((s) => num(s.alunos_fizeram) > 0));

	let proximo = $derived.by(() => {
		const agora = Date.now();
		return (
			simulados
				.filter((s) => new Date(s.fecha_em).getTime() >= agora)
				.sort((a, b) => new Date(a.abre_em) - new Date(b.abre_em))[0] ?? null
		);
	});

	let copiado = $state(false);
	async function copiarParados() {
		try {
			await navigator.clipboard.writeText(parados.map((a) => a.nome || a.apelido).join('\n'));
			copiado = true;
			setTimeout(() => (copiado = false), 2000);
		} catch {
			// sem permissão: a lista continua na tela
		}
	}

	/** delta com sinal e o ícone da direção; subir é bom nos três números daqui */
	function delta(agora, antes) {
		const d = agora - antes;
		return { d, icone: d > 0 ? ArrowUp : d < 0 ? ArrowDown : Minus, cor: d > 0 ? 'text-ok-fg' : d < 0 ? 'text-bad-fg' : 'text-ink-soft' };
	}
	let dA = $derived(delta(estaSemana.ativos, semanaPassada.ativos));
	let dR = $derived(delta(estaSemana.respondidas, semanaPassada.respondidas));
</script>

<!-- 1. A turma está estudando? -->
<dl class="grid grid-cols-2 gap-2 lg:grid-cols-4">
	<div class="rounded-2xl bg-tile p-3">
		<dt class="text-xs font-semibold text-ink-soft">Estudaram nesta semana</dt>
		<dd class="mt-1 font-display text-2xl font-extrabold">{estaSemana.ativos} <span class="text-base font-bold text-ink-soft">de {alunos}</span></dd>
		<dd class="mt-0.5 flex items-center gap-1 text-xs font-semibold {dA.cor}">
			<dA.icone size={12} weight="bold" aria-hidden="true" />
			{dA.d === 0 ? 'igual à' : `${dA.d > 0 ? '+' : ''}${dA.d} que a`} semana passada
		</dd>
	</div>
	<div class="rounded-2xl bg-tile p-3">
		<dt class="text-xs font-semibold text-ink-soft">Questões nesta semana</dt>
		<dd class="mt-1 font-display text-2xl font-extrabold">{estaSemana.respondidas.toLocaleString('pt-BR')}</dd>
		<dd class="mt-0.5 flex items-center gap-1 text-xs font-semibold {dR.cor}">
			<dR.icone size={12} weight="bold" aria-hidden="true" />
			{dR.d === 0 ? 'igual à' : `${dR.d > 0 ? '+' : ''}${dR.d.toLocaleString('pt-BR')} que a`} semana passada
		</dd>
	</div>
	<div class="rounded-2xl bg-tile p-3">
		<dt class="text-xs font-semibold text-ink-soft">Acerto nas questões do ENADE</dt>
		<dd class="mt-1 font-display text-2xl font-extrabold">{pct(oficiais.certas, oficiais.respondidas) ?? '—'}{oficiais.respondidas ? '%' : ''}</dd>
		<dd class="mt-0.5 text-xs text-ink-soft">primeira tentativa, {plural(oficiais.respondidas, 'resposta', 'respostas')}</dd>
	</div>
	<div class="rounded-2xl bg-tile p-3">
		<dt class="text-xs font-semibold text-ink-soft">Nunca estudaram</dt>
		<dd class="mt-1 font-display text-2xl font-extrabold">{dados.alunos.filter((a) => !a.ultima_em).length}</dd>
		<dd class="mt-0.5 text-xs text-ink-soft">entraram na turma e não responderam nada</dd>
	</div>
</dl>

<div class="mt-4 grid items-start gap-4 lg:grid-cols-2">
	<!-- 2. Quem sumiu: a lista que vira mensagem no grupo -->
	<section class="rounded-3xl border border-line bg-card p-4 sm:p-5" aria-labelledby="t-parados">
		<div class="flex items-start justify-between gap-2">
			<div>
				<h2 id="t-parados" class="font-display text-heading font-bold">Precisam de um empurrão</h2>
				<p class="text-sm text-ink-soft">Sem estudar nos últimos 7 dias.</p>
			</div>
			{#if parados.length}
				<button type="button" onclick={copiarParados} class="flex min-h-11 shrink-0 items-center gap-1.5 rounded-xl px-2 text-sm font-bold text-accent-ink">
					{#if copiado}<Check size={16} weight="bold" aria-hidden="true" /> Copiado{:else}<Copy size={16} weight="bold" aria-hidden="true" /> Copiar nomes{/if}
				</button>
			{/if}
		</div>
		{#if parados.length === 0}
			<p class="mt-3 flex items-center gap-2 rounded-2xl bg-ok-bg p-3 text-sm font-semibold text-ok-fg">
				<Check size={18} weight="bold" aria-hidden="true" /> Todo mundo estudou nesta última semana.
			</p>
		{:else}
			<ul class="mt-2 divide-y divide-line">
				{#each parados.slice(0, 6) as a (a.usuario_id)}
					<li>
						<button type="button" onclick={() => onAbrirAluno(a.usuario_id)} class="flex min-h-11 w-full items-center justify-between gap-3 py-1.5 text-left hover:text-accent-ink">
							<span class="min-w-0 truncate text-sm font-semibold">{a.nome || a.apelido}</span>
							<span class="shrink-0 text-xs {a.ultima_em ? 'text-ink-soft' : 'font-bold text-bad-fg'}">
								{a.ultima_em ? `última vez ${quando(a.ultima_em)}` : 'nunca estudou'}
							</span>
						</button>
					</li>
				{/each}
			</ul>
			{#if parados.length > 6}
				<button type="button" onclick={() => onIrPara('alunos')} class="mt-1 min-h-11 text-sm font-bold text-accent-ink">
					Ver os outros {parados.length - 6}
				</button>
			{/if}
		{/if}
	</section>

	<!-- 3. Onde a turma erra e o que ninguém viu -->
	<section class="rounded-3xl border border-line bg-card p-4 sm:p-5" aria-labelledby="t-fracas">
		<h2 id="t-fracas" class="font-display text-heading font-bold">Onde a turma mais erra</h2>
		<p class="text-sm text-ink-soft">Matérias com pelo menos {MINIMO_MATERIA} respostas, pior acerto primeiro.</p>
		{#if fracas.length === 0}
			<p class="mt-3 text-sm text-ink-soft">Ainda há poucas respostas por matéria para dizer.</p>
		{:else}
			<ul class="mt-3 space-y-3">
				{#each fracas as m (m.materia)}
					{@const p = pct(m.certas, m.respondidas)}
					<li>
						<div class="flex items-baseline justify-between gap-3 text-sm">
							<span class="min-w-0 font-semibold text-pretty">{nomeMateria(m.materia)}</span>
							<span class="nums shrink-0 font-bold">{p}%</span>
						</div>
						<div class="mt-1 h-2 overflow-hidden rounded-full bg-track" aria-hidden="true">
							<div class="h-full rounded-full bg-accent-bar" style="width: {p}%"></div>
						</div>
						<p class="mt-0.5 text-xs text-ink-soft">{plural(m.respondidas, 'resposta', 'respostas')}</p>
					</li>
				{/each}
			</ul>
		{/if}
		{#if intocadas.length}
			<details class="mt-4 rounded-2xl bg-tile px-3 py-2">
				<summary class="flex min-h-9 cursor-pointer items-center text-sm font-semibold">
					Ninguém treinou ainda {intocadas.length} de {MATERIAS_CE.length} áreas da prova
				</summary>
				<ul class="mt-1 mb-1 flex flex-wrap gap-1.5">
					{#each intocadas as m (m.id)}
						<li class="rounded-full border border-line bg-card px-2.5 py-1 text-xs font-semibold text-ink-soft">{m.nome}</li>
					{/each}
				</ul>
			</details>
		{:else}
			<p class="mt-4 text-sm font-semibold text-ok-fg">Todas as {MATERIAS_CE.length} áreas da prova já foram treinadas.</p>
		{/if}
		<button type="button" onclick={() => onIrPara('materias')} class="mt-2 min-h-11 text-sm font-bold text-accent-ink">Ver todas as matérias</button>
	</section>
</div>

<!-- 4. Está melhorando? A medida justa é simulado contra simulado: mesma
     prova para a turma toda. O acerto semanal muda com a dificuldade das
     questões que caíram na semana, então não serve de evolução (D16). -->
<section class="mt-4 rounded-3xl border border-line bg-card p-4 sm:p-5" aria-labelledby="t-evolucao">
	<h2 id="t-evolucao" class="font-display text-heading font-bold">Evolução</h2>
	<div class="mt-3 grid gap-6 sm:grid-cols-2">
		<GraficoColunas
			titulo="Alunos que estudaram, por semana"
			cadaRotulo={2}
			itens={semanas.map((s) => ({ chave: s.chave, rotulo: s.rotulo, valor: s.ativos, dica: `Semana de ${s.rotulo}: ${plural(s.ativos, 'aluno', 'alunos')}` }))}
		/>
		{#if feitos.length >= 2}
			<GraficoColunas
				titulo="Média nos simulados da turma"
				maximo={100}
				formatar={(v) => `${v}%`}
				itens={feitos.map((s, k) => ({
					chave: s.id,
					rotulo: `${k + 1}º`,
					valor: Math.round((Number(s.media_certas) / s.objetivas) * 100),
					dica: `${s.titulo}: média ${String(s.media_certas).replace('.', ',')} de ${s.objetivas}, ${plural(s.alunos_fizeram, 'aluno fez', 'alunos fizeram')}`
				}))}
			/>
		{:else}
			<div class="min-w-0">
				<p class="text-sm font-bold">Média nos simulados da turma</p>
				{#if feitos.length === 1}
					{@const s = feitos[0]}
					<p class="mt-3 font-display text-2xl font-extrabold">
						{String(s.media_certas).replace('.', ',')} <span class="text-base font-bold text-ink-soft">de {s.objetivas}</span>
					</p>
					<p class="text-sm text-ink-soft">{s.titulo}, {plural(s.alunos_fizeram, 'aluno fez', 'alunos fizeram')}.</p>
				{/if}
				<p class="mt-2 text-sm text-pretty text-ink-soft">
					A evolução aparece a partir do {feitos.length === 1 ? 'segundo' : 'primeiro'} simulado da turma: é a mesma prova para
					todos, então dá para comparar uma rodada com a outra.
				</p>
				{#if feitos.length === 0}
					<button type="button" onclick={() => onIrPara('simulados')} class="mt-1 min-h-11 text-sm font-bold text-accent-ink">Agendar um simulado</button>
				{/if}
			</div>
		{/if}
	</div>
</section>

{#if proximo}
	{@const aberto = new Date(proximo.abre_em).getTime() <= Date.now()}
	<button
		type="button"
		onclick={() => onIrPara('simulados')}
		class="mt-4 flex w-full items-center justify-between gap-3 rounded-3xl border-2 border-accent bg-card p-4 text-left sm:p-5"
	>
		<span class="min-w-0">
			<span class="block text-label font-bold text-accent-ink">{aberto ? 'Simulado aberto agora' : 'Próximo simulado'}</span>
			<span class="block font-display text-heading font-bold text-pretty">{proximo.titulo}</span>
		</span>
		<span class="shrink-0 text-sm font-bold text-accent-ink">Ver resultado</span>
	</button>
{/if}
