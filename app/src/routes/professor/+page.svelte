<script>
	// Painel do professor. Quem decide se a pessoa pode ver é o banco
	// (`painel_*` conferem o papel): para quem não é professor da turma, as
	// funções devolvem vazio e esta tela mostra "sem acesso".
	import { onMount } from 'svelte';
	import { page } from '$app/stores';
	import { ArrowLeft, Copy, Check } from 'phosphor-svelte';
	import { nuvemLigada, usuarioAtual, minhasTurmas, painel } from '$lib/nuvem.js';
	import { carregarBanco, rotuloQuestao } from '$lib/banco.js';
	import { nomeMateria } from '$lib/materias.js';

	let carregando = $state(true);
	let erro = $state('');
	let turma = $state(null);
	let dados = $state(null);
	let porId = $state(new Map());
	let aba = $state('alunos');
	let copiado = $state(false);

	const abas = [
		['alunos', 'Alunos'],
		['materias', 'Matérias'],
		['questoes', 'Questões'],
		['semanas', 'Semanas']
	];

	const num = (v) => Number(v) || 0;
	const pct = (c, t) => (num(t) ? Math.round((num(c) / num(t)) * 100) : null);
	const fmtPct = (c, t) => (pct(c, t) === null ? '—' : `${pct(c, t)}%`);

	function quando(iso) {
		if (!iso) return 'nunca';
		const dias = Math.floor((Date.now() - new Date(iso).getTime()) / 86_400_000);
		if (dias <= 0) return 'hoje';
		if (dias === 1) return 'ontem';
		return `há ${dias} dias`;
	}

	function diasAte(data) {
		if (!data) return null;
		return Math.max(0, Math.ceil((new Date(`${String(data).slice(0, 10)}T00:00:00-03:00`).getTime() - Date.now()) / 86_400_000));
	}

	let resumo = $derived.by(() => {
		if (!dados) return null;
		const a = dados.alunos;
		const respondidas = a.reduce((s, x) => s + num(x.respondidas), 0);
		const certas = a.reduce((s, x) => s + num(x.certas), 0);
		return {
			alunos: a.length,
			ativos: a.filter((x) => num(x.respondidas_7d) > 0).length,
			respondidas,
			acerto: fmtPct(certas, respondidas)
		};
	});

	// matéria pior primeiro: é onde a aula de revisão rende mais
	let materias = $derived(
		dados
			? [...dados.materias]
					.filter((m) => num(m.respondidas) > 0)
					.sort((x, y) => (pct(x.certas, x.respondidas) ?? 0) - (pct(y.certas, y.respondidas) ?? 0))
			: []
	);

	let link = $derived(turma ? `${$page.url.origin}/conta/?turma=${turma.codigo ?? ''}` : '');

	async function copiarLink() {
		try {
			await navigator.clipboard.writeText(link);
			copiado = true;
			setTimeout(() => (copiado = false), 2000);
		} catch {
			// sem permissão de área de transferência: o link continua visível
		}
	}

	onMount(async () => {
		if (!nuvemLigada) {
			carregando = false;
			return;
		}
		try {
			const id = $page.url.searchParams.get('turma');
			const u = await usuarioAtual();
			if (!u) {
				erro = 'Entre na sua conta para ver o painel.';
				return;
			}
			const m = (await minhasTurmas()).find((x) => x.turma.id === id && x.papel === 'professor');
			if (!m) {
				erro = 'Você não é professor desta turma.';
				return;
			}
			turma = m.turma;
			const [p, banco] = await Promise.all([painel(id), carregarBanco().catch(() => [])]);
			dados = p;
			porId = new Map(banco.map((q) => [q.id, q]));
		} catch (e) {
			erro = e.message;
		} finally {
			carregando = false;
		}
	});
</script>

<svelte:head>
	<title>Painel da turma · Simulado ENADE</title>
</svelte:head>

<a href="/conta/" class="inline-flex min-h-11 items-center gap-2 text-sm font-bold text-ink-soft hover:text-ink">
	<ArrowLeft size={17} weight="bold" aria-hidden="true" /> Conta e turma
</a>

{#if carregando}
	<div class="mt-4 space-y-3" role="status" aria-label="Carregando o painel">
		<div class="h-28 animate-pulse rounded-3xl bg-skel"></div>
		<div class="h-64 animate-pulse rounded-3xl bg-skel"></div>
	</div>
{:else if !nuvemLigada}
	<p class="mt-4 text-[15px] text-ink-soft">A conta ainda não está ligada neste site.</p>
{:else if erro}
	<p role="alert" class="mt-4 rounded-2xl border border-bad-fg/30 bg-bad-bg p-3 text-sm font-semibold text-bad-fg">{erro}</p>
{:else if dados && resumo}
	{@const dias = diasAte(turma.data_prova)}
	<header class="mt-2">
		<p class="text-sm font-semibold text-ink-soft">{turma.instituicao}</p>
		<h1 class="font-display text-2xl font-extrabold tracking-tight">{turma.nome}</h1>
		{#if dias !== null}
			<p class="mt-1 text-sm font-bold text-accent-ink">{dias} {dias === 1 ? 'dia' : 'dias'} até o ENADE</p>
		{/if}
	</header>

	<dl class="mt-5 grid grid-cols-2 gap-2 sm:grid-cols-4">
		<div class="rounded-2xl bg-tile p-3">
			<dd class="nums text-2xl font-extrabold">{resumo.alunos}</dd>
			<dt class="mt-0.5 text-xs font-semibold text-ink-soft">Alunos na turma</dt>
		</div>
		<div class="rounded-2xl bg-tile p-3">
			<dd class="nums text-2xl font-extrabold">{resumo.ativos}</dd>
			<dt class="mt-0.5 text-xs font-semibold text-ink-soft">Estudaram nos últimos 7 dias</dt>
		</div>
		<div class="rounded-2xl bg-tile p-3">
			<dd class="nums text-2xl font-extrabold">{resumo.respondidas.toLocaleString('pt-BR')}</dd>
			<dt class="mt-0.5 text-xs font-semibold text-ink-soft">Questões respondidas</dt>
		</div>
		<div class="rounded-2xl bg-tile p-3">
			<dd class="nums text-2xl font-extrabold">{resumo.acerto}</dd>
			<dt class="mt-0.5 text-xs font-semibold text-ink-soft">Acerto da turma</dt>
		</div>
	</dl>

	{#if resumo.alunos === 0}
		<section class="mt-6 rounded-3xl border border-line bg-card p-5 sm:p-6">
			<h2 class="font-display text-heading font-extrabold">Ninguém entrou ainda</h2>
			<p class="mt-2 text-sm text-pretty text-ink-soft">Mande este link para a turma (ou passe o código {turma.codigo}):</p>
			<div class="mt-3 flex flex-col gap-2 sm:flex-row">
				<code class="min-w-0 flex-1 truncate rounded-xl bg-tile px-3 py-3 text-sm">{link}</code>
				<button type="button" onclick={copiarLink} class="btn3d duo-btn flex min-h-11 items-center justify-center gap-2 rounded-xl px-4 text-sm font-bold">
					{#if copiado}<Check size={17} weight="bold" aria-hidden="true" /> Copiado{:else}<Copy size={17} weight="bold" aria-hidden="true" /> Copiar link{/if}
				</button>
			</div>
		</section>
	{:else}
		<div class="mt-6 flex gap-1 overflow-x-auto rounded-2xl bg-tile p-1" role="tablist" aria-label="Partes do painel">
			{#each abas as [v, rotulo] (v)}
				<button
					type="button"
					role="tab"
					id="aba-{v}"
					aria-selected={aba === v}
					aria-controls="painel-{v}"
					onclick={() => (aba = v)}
					class="min-h-11 flex-1 shrink-0 rounded-xl px-3 text-sm font-bold {aba === v ? 'bg-card shadow-sm' : 'text-ink-soft'}"
				>
					{rotulo}
				</button>
			{/each}
		</div>

		<div id="painel-{aba}" role="tabpanel" tabindex="0" aria-labelledby="aba-{aba}" class="mt-4">
			{#if aba === 'alunos'}
				<p class="text-xs text-ink-soft">Mais ativos primeiro. "7 dias" mostra quem está estudando agora.</p>
				<div class="mt-3 overflow-x-auto rounded-2xl border border-line">
					<table class="w-full min-w-[560px] text-left text-sm">
						<thead class="bg-tile text-xs text-ink-soft">
							<tr>
								<th scope="col" class="px-3 py-2 font-bold">Aluno</th>
								<th scope="col" class="px-3 py-2 font-bold">RA</th>
								<th scope="col" class="px-3 py-2 text-right font-bold">7 dias</th>
								<th scope="col" class="px-3 py-2 text-right font-bold">Total</th>
								<th scope="col" class="px-3 py-2 text-right font-bold">Acerto</th>
								<th scope="col" class="px-3 py-2 font-bold">Última vez</th>
							</tr>
						</thead>
						<tbody>
							{#each dados.alunos as a (a.usuario_id)}
								<tr class="border-t border-line">
									<td class="px-3 py-2">
										<span class="font-semibold">{a.nome || a.apelido}</span>
										{#if a.nome && a.apelido}<span class="block text-xs text-ink-soft">{a.apelido}</span>{/if}
									</td>
									<td class="px-3 py-2 font-code text-xs">{a.ra ?? '—'}</td>
									<td class="nums px-3 py-2 text-right font-bold">{num(a.respondidas_7d)}</td>
									<td class="nums px-3 py-2 text-right">{num(a.respondidas)}</td>
									<td class="nums px-3 py-2 text-right">{fmtPct(a.certas, a.respondidas)}</td>
									<td class="px-3 py-2 text-xs {a.ultima_em ? '' : 'font-bold text-bad-fg'}">{quando(a.ultima_em)}</td>
								</tr>
							{/each}
						</tbody>
					</table>
				</div>
			{:else if aba === 'materias'}
				<p class="text-xs text-ink-soft">Pior acerto primeiro: é onde uma aula de revisão rende mais.</p>
				{#if materias.length === 0}
					<p class="mt-3 text-sm text-ink-soft">Sem respostas ainda.</p>
				{:else}
					<ul class="mt-3 space-y-3">
						{#each materias as m (m.materia + String(m.oficial))}
							{@const p = pct(m.certas, m.respondidas) ?? 0}
							<li class="rounded-2xl border border-line bg-card p-3">
								<div class="flex items-baseline justify-between gap-3">
									<span class="min-w-0 text-sm font-semibold text-pretty">
										{m.materia ? nomeMateria(m.materia) : 'Sem matéria'}
										<span class="ml-1 text-xs font-semibold text-ink-soft">{m.oficial ? 'ENADE' : 'revisão'}</span>
									</span>
									<span class="nums shrink-0 font-display font-black">{p}%</span>
								</div>
								<div class="mt-2 h-2.5 overflow-hidden rounded-full bg-track" aria-hidden="true">
									<div class="h-full rounded-full {p < 50 ? 'bg-bad-solid' : 'bg-ok-solid'}" style="width: {p}%"></div>
								</div>
								<p class="nums mt-1.5 text-xs text-ink-soft">{num(m.respondidas)} {num(m.respondidas) === 1 ? 'resposta' : 'respostas'} de {num(m.alunos)} {num(m.alunos) === 1 ? 'aluno' : 'alunos'}</p>
							</li>
						{/each}
					</ul>
				{/if}
			{:else if aba === 'questoes'}
				<p class="text-xs text-ink-soft">As que a turma mais erra (só entram questões com 3 ou mais tentativas).</p>
				{#if dados.questoes.length === 0}
					<p class="mt-3 text-sm text-ink-soft">Ainda não há tentativas suficientes.</p>
				{:else}
					<ol class="mt-3 space-y-2">
						{#each dados.questoes as q (q.questao_id)}
							{@const b = porId.get(q.questao_id)}
							<li class="rounded-2xl border border-line bg-card p-3">
								<div class="flex items-baseline justify-between gap-3">
									<span class="text-sm font-bold">{b ? rotuloQuestao(b) : q.questao_id}</span>
									<span class="nums shrink-0 font-display font-black text-bad-fg">{fmtPct(q.erros, q.tentativas)} erram</span>
								</div>
								<p class="mt-1 text-xs text-pretty text-ink-soft">
									{b?.tema ?? ''}{b?.tema && q.materia ? ' · ' : ''}{q.materia ? nomeMateria(q.materia) : ''}
								</p>
								<p class="nums mt-1 text-xs text-ink-soft">{num(q.tentativas)} tentativas de {num(q.alunos)} {num(q.alunos) === 1 ? 'aluno' : 'alunos'}</p>
							</li>
						{/each}
					</ol>
				{/if}
			{:else}
				<p class="text-xs text-ink-soft">Quantos estudaram em cada semana e como foram.</p>
				{#if dados.semanas.length === 0}
					<p class="mt-3 text-sm text-ink-soft">Sem respostas ainda.</p>
				{:else}
					{@const maximo = Math.max(...dados.semanas.map((s) => num(s.respondidas)), 1)}
					<ul class="mt-3 space-y-2">
						{#each dados.semanas as s (s.semana)}
							<li class="grid grid-cols-[3rem_1fr_8.5rem] items-center gap-3 text-sm">
								<span class="nums text-xs font-semibold text-ink-soft">
									{new Date(`${String(s.semana).slice(0, 10)}T12:00:00`).toLocaleDateString('pt-BR', { day: '2-digit', month: '2-digit' })}
								</span>
								<div class="h-6 overflow-hidden rounded-lg bg-track" aria-hidden="true">
									<div class="h-full rounded-lg bg-accent-bar" style="width: {(num(s.respondidas) / maximo) * 100}%"></div>
								</div>
								<span class="nums text-right text-xs">
									<strong>{num(s.respondidas)}</strong> · {num(s.alunos_ativos)} {num(s.alunos_ativos) === 1 ? 'aluno' : 'alunos'} · {fmtPct(s.certas, s.respondidas)}
								</span>
							</li>
						{/each}
					</ul>
				{/if}
			{/if}
		</div>
	{/if}
{/if}
