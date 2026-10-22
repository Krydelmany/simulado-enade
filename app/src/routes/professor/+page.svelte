<script>
	// Painel do professor. Quem decide se a pessoa pode ver é o banco
	// (`painel_*` conferem o papel): para quem não é professor da turma, as
	// funções devolvem vazio e esta tela mostra "sem acesso".
	import { onMount } from 'svelte';
	import { page } from '$app/stores';
	import { ArrowLeft, CalendarPlus, Check, Copy, DownloadSimple, Trash } from 'phosphor-svelte';
	import {
		nuvemLigada,
		usuarioAtual,
		minhasTurmas,
		painel,
		simuladosDaTurma,
		criarSimulado,
		apagarSimulado,
		resultadoSimulado
	} from '$lib/nuvem.js';
	import { carregarBanco, rotuloQuestao } from '$lib/banco.js';
	import { nomeMateria } from '$lib/materias.js';
	import { FORMATO, montarProva } from '$lib/simulado.js';
	import { baixarCsv, dataCsv } from '$lib/csv.js';

	let carregando = $state(true);
	let erro = $state('');
	let turma = $state(null);
	let dados = $state(null);
	let banco = $state.raw([]);
	let porId = $state.raw(new Map());
	let aba = $state('alunos');
	let copiado = $state(false);

	// simulados da turma
	let simulados = $state([]);
	let titulo = $state('Simulado 1');
	let abre = $state('');
	let fecha = $state('');
	let agendando = $state(false);
	let erroAgenda = $state('');
	let avisoAgenda = $state('');
	let abertoId = $state(null);
	// id → {alunos, questoes} | {erro}; ausente = carregando
	let resultados = $state({});
	let confirmaApagar = $state(null);

	const abas = [
		['alunos', 'Alunos'],
		['simulados', 'Simulados'],
		['materias', 'Matérias'],
		['questoes', 'Questões'],
		['semanas', 'Semanas']
	];

	const OBJETIVAS = FORMATO.fg + FORMATO.ce;

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

	// "sex 31/10 às 23:59"
	function diaHora(iso) {
		const d = new Date(iso);
		if (Number.isNaN(d.getTime())) return '';
		const dia = d.toLocaleDateString('pt-BR', { weekday: 'short' }).replace('.', '');
		const data = d.toLocaleDateString('pt-BR', { day: '2-digit', month: '2-digit' });
		const hora = d.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' });
		return `${dia} ${data} às ${hora}`;
	}

	// Date → "2026-10-23T08:00" no fuso do aparelho (formato do datetime-local)
	function paraCampo(d) {
		const p = (n) => String(n).padStart(2, '0');
		return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())}T${p(d.getHours())}:${p(d.getMinutes())}`;
	}

	function estadoDe(s) {
		const t = Date.now();
		if (t < new Date(s.abre_em).getTime()) return 'agendado';
		if (t <= new Date(s.fecha_em).getTime()) return 'aberto';
		return 'encerrado';
	}

	const ROTULO_ESTADO = {
		agendado: ['Agendado', 'bg-tile text-ink-soft'],
		aberto: ['Aberto', 'bg-accent-soft text-accent-ink'],
		encerrado: ['Encerrado', 'border border-line text-ink-soft']
	};

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

	function prepararFormulario() {
		const a = new Date();
		a.setDate(a.getDate() + 1);
		a.setHours(8, 0, 0, 0);
		const f = new Date(a);
		f.setDate(f.getDate() + 7);
		f.setHours(23, 59, 0, 0);
		abre = paraCampo(a);
		fecha = paraCampo(f);
		titulo = `Simulado ${simulados.length + 1}`;
	}

	// Sorteia aqui, com o mesmo `montarProva` do simulado individual (D12):
	// o banco só guarda a lista, e todo aluno recebe exatamente essa prova.
	async function agendar(ev) {
		ev.preventDefault();
		erroAgenda = '';
		avisoAgenda = '';
		const inicio = new Date(abre);
		const fim = new Date(fecha);
		if (!(fim > inicio)) {
			erroAgenda = 'O fim precisa ser depois do início.';
			return;
		}
		const p = montarProva(banco);
		if (!p) {
			erroAgenda = 'As questões não carregaram inteiras. Recarregue a página e tente de novo.';
			return;
		}
		agendando = true;
		try {
			await criarSimulado({
				turmaId: turma.id,
				titulo,
				questoes: p.ids,
				objetivas: OBJETIVAS,
				abreEm: inicio,
				fechaEm: fim
			});
			simulados = await simuladosDaTurma(turma.id);
			avisoAgenda = `Agendado. A turma vê "${titulo.trim()}" na tela do Simulado a partir de ${diaHora(inicio)}.`;
			prepararFormulario();
		} catch (e) {
			erroAgenda = e.message;
		} finally {
			agendando = false;
		}
	}

	async function alternarResultado(s) {
		if (abertoId === s.id) {
			abertoId = null;
			return;
		}
		abertoId = s.id;
		delete resultados[s.id];
		try {
			resultados[s.id] = await resultadoSimulado(s.id);
		} catch (e) {
			resultados[s.id] = { erro: e.message };
		}
	}

	async function apagar(s) {
		try {
			await apagarSimulado(s.id);
			simulados = simulados.filter((x) => x.id !== s.id);
			confirmaApagar = null;
			if (abertoId === s.id) abertoId = null;
		} catch (e) {
			erroAgenda = e.message;
		}
	}

	// matérias do simulado, pior primeiro (o banco devolve por questão)
	function materiasDo(r) {
		const mapa = new Map();
		for (const q of r.questoes) {
			const k = q.materia || '';
			const m = mapa.get(k) ?? { materia: k, respondidas: 0, certas: 0 };
			m.respondidas += num(q.respondidas);
			m.certas += num(q.certas);
			mapa.set(k, m);
		}
		return [...mapa.values()].sort((x, y) => (pct(x.certas, x.respondidas) ?? 0) - (pct(y.certas, y.respondidas) ?? 0));
	}

	function csvAlunos() {
		baixarCsv(
			`${turma.nome} - alunos`,
			['Nome', 'Apelido', 'RA', 'Respondidas (7 dias)', 'Respondidas (total)', 'Acertos', 'Acerto (%)', 'Dias com estudo', 'Última vez'],
			dados.alunos.map((a) => [
				a.nome,
				a.apelido,
				a.ra ?? '',
				num(a.respondidas_7d),
				num(a.respondidas),
				num(a.certas),
				pct(a.certas, a.respondidas) ?? '',
				num(a.dias_ativos),
				dataCsv(a.ultima_em)
			])
		);
	}

	function csvSimulado(s, r) {
		baixarCsv(
			`${turma.nome} - ${s.titulo}`,
			['Nome', 'Apelido', 'RA', 'Acertos', `De (${s.objetivas} objetivas)`, 'Acerto (%)', 'Respondidas', 'Entregue em'],
			r.alunos.map((a) => [
				a.nome,
				a.apelido,
				a.ra ?? '',
				num(a.respondidas) ? num(a.certas) : '',
				s.objetivas,
				num(a.respondidas) ? pct(a.certas, s.objetivas) : '',
				num(a.respondidas),
				dataCsv(a.entregue_em)
			])
		);
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
			const [p, b, sims] = await Promise.all([
				painel(id),
				carregarBanco().catch(() => []),
				simuladosDaTurma(id).catch(() => [])
			]);
			dados = p;
			banco = b;
			porId = new Map(b.map((q) => [q.id, q]));
			simulados = sims;
			prepararFormulario();
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
	<header class="mt-2 flex flex-wrap items-end justify-between gap-x-6 gap-y-3">
		<div>
			<p class="text-sm font-semibold text-ink-soft">{turma.instituicao}</p>
			<h1 class="font-display text-2xl font-extrabold tracking-tight">{turma.nome}</h1>
			{#if dias !== null}
				<p class="mt-1 text-sm font-bold text-accent-ink">{dias} {dias === 1 ? 'dia' : 'dias'} até o ENADE</p>
			{/if}
		</div>
		<div class="flex items-center gap-2 text-sm">
			<span class="text-ink-soft">Código da turma <strong class="font-code text-ink">{turma.codigo}</strong></span>
			<button
				type="button"
				onclick={copiarLink}
				class="flex min-h-11 items-center gap-1.5 rounded-xl border-2 border-line px-3 font-bold"
			>
				{#if copiado}<Check size={16} weight="bold" aria-hidden="true" /> Copiado{:else}<Copy size={16} weight="bold" aria-hidden="true" /> Copiar convite{/if}
			</button>
		</div>
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
	{/if}

	<!-- 5 abas: em 390 px viram 2 linhas. Rolando de lado, "Semanas" ficava
	     escondida fora da tela, sem sinal de que existia. -->
	<div class="mt-6 grid grid-cols-3 gap-1 rounded-2xl bg-tile p-1 sm:grid-cols-5" role="tablist" aria-label="Partes do painel">
		{#each abas as [v, rotulo] (v)}
			<button
				type="button"
				role="tab"
				id="aba-{v}"
				aria-selected={aba === v}
				aria-controls="painel-{v}"
				onclick={() => (aba = v)}
				class="min-h-11 rounded-xl px-2 text-sm font-bold whitespace-nowrap {aba === v ? 'bg-card shadow-sm' : 'text-ink-soft'}"
			>
				{rotulo}
			</button>
		{/each}
	</div>

	<div id="painel-{aba}" role="tabpanel" tabindex="0" aria-labelledby="aba-{aba}" class="mt-4">
		{#if aba === 'alunos'}
			<div class="flex flex-wrap items-center justify-between gap-2">
				<p class="text-xs text-ink-soft">Mais ativos primeiro. "7 dias" mostra quem está estudando agora.</p>
				{#if dados.alunos.length}
					<button type="button" onclick={csvAlunos} class="flex min-h-11 items-center gap-1.5 rounded-xl px-2 text-sm font-bold text-accent-ink">
						<DownloadSimple size={17} weight="bold" aria-hidden="true" /> Baixar planilha
					</button>
				{/if}
			</div>
			{#if dados.alunos.length === 0}
				<p class="mt-3 text-sm text-ink-soft">Quando alguém entrar pelo convite, aparece aqui.</p>
			{:else}
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
			{/if}
		{:else if aba === 'simulados'}
			<form class="rounded-3xl border border-line bg-card p-5 sm:p-6" onsubmit={agendar} aria-labelledby="t-agendar">
				<h2 id="t-agendar" class="flex items-center gap-2 font-display text-heading font-extrabold">
					<CalendarPlus size={20} weight="bold" aria-hidden="true" /> Agendar simulado
				</h2>
				<p class="mt-1 text-sm text-pretty text-ink-soft">
					A prova é sorteada agora ({FORMATO.fg} de Formação Geral, {FORMATO.ce} específicas e
					{FORMATO.discursivas} discursiva, espalhadas pelas matérias) e toda a turma faz a mesma. Cada aluno
					tem 4 horas de relógio, dentro do período que você escolher.
				</p>
				<div class="mt-4 grid gap-4 sm:grid-cols-[1fr_auto_auto]">
					<div>
						<label for="sim-titulo" class="text-sm font-bold">Nome</label>
						<input
							id="sim-titulo"
							required
							minlength="2"
							maxlength="80"
							bind:value={titulo}
							class="mt-1.5 min-h-12 w-full rounded-xl border-2 border-line bg-paper px-3 text-base"
						/>
					</div>
					<div>
						<label for="sim-abre" class="text-sm font-bold">Abre em</label>
						<input id="sim-abre" type="datetime-local" required bind:value={abre} class="mt-1.5 min-h-12 w-full rounded-xl border-2 border-line bg-paper px-3 text-base" />
					</div>
					<div>
						<label for="sim-fecha" class="text-sm font-bold">Fecha em</label>
						<input id="sim-fecha" type="datetime-local" required bind:value={fecha} class="mt-1.5 min-h-12 w-full rounded-xl border-2 border-line bg-paper px-3 text-base" />
					</div>
				</div>
				{#if erroAgenda}
					<p role="alert" class="mt-4 rounded-2xl border border-bad-fg/30 bg-bad-bg p-3 text-sm font-semibold text-bad-fg">{erroAgenda}</p>
				{/if}
				{#if avisoAgenda}
					<p role="status" class="mt-4 rounded-2xl bg-ok-bg p-3 text-sm font-semibold text-ok-fg">{avisoAgenda}</p>
				{/if}
				<button
					type="submit"
					disabled={agendando}
					class="btn3d duo-accent mt-5 flex min-h-[52px] w-full items-center justify-center gap-2 rounded-[14px] px-6 font-display text-base font-bold disabled:opacity-60 sm:w-auto"
				>
					{agendando ? 'Agendando…' : 'Sortear a prova e agendar'}
				</button>
			</form>

			{#if simulados.length === 0}
				<p class="mt-4 text-sm text-ink-soft">Nenhum simulado agendado ainda.</p>
			{:else}
				<ul class="mt-4 space-y-3">
					{#each simulados as s (s.id)}
						{@const estado = estadoDe(s)}
						{@const r = resultados[s.id]}
						<li class="rounded-3xl border border-line bg-card p-4 sm:p-5">
							<div class="flex flex-wrap items-start justify-between gap-2">
								<div class="min-w-0">
									<h3 class="font-display text-heading font-bold text-pretty">{s.titulo}</h3>
									<p class="mt-0.5 text-sm text-ink-soft">De {diaHora(s.abre_em)} até {diaHora(s.fecha_em)}</p>
								</div>
								<span class="shrink-0 rounded-full px-2.5 py-0.5 text-xs font-bold {ROTULO_ESTADO[estado][1]}">{ROTULO_ESTADO[estado][0]}</span>
							</div>
							<div class="mt-3 flex flex-wrap gap-2">
								<button
									type="button"
									onclick={() => alternarResultado(s)}
									aria-expanded={abertoId === s.id}
									class="min-h-11 rounded-xl border-2 border-line px-4 text-sm font-bold"
								>
									{abertoId === s.id ? 'Fechar resultado' : 'Ver resultado'}
								</button>
								{#if confirmaApagar === s.id}
									<button type="button" onclick={() => apagar(s)} class="flex min-h-11 items-center gap-1.5 rounded-xl bg-bad-solid px-4 text-sm font-bold text-white">
										<Trash size={16} weight="bold" aria-hidden="true" /> Sim, apagar
									</button>
									<button type="button" onclick={() => (confirmaApagar = null)} class="min-h-11 px-3 text-sm font-bold text-ink-soft">Cancelar</button>
								{:else}
									<button type="button" onclick={() => (confirmaApagar = s.id)} class="flex min-h-11 items-center gap-1.5 rounded-xl px-3 text-sm font-bold text-ink-soft hover:text-bad-fg">
										<Trash size={16} weight="bold" aria-hidden="true" /> Apagar
									</button>
								{/if}
							</div>
							{#if confirmaApagar === s.id}
								<p class="mt-2 text-xs text-pretty text-bad-fg">Some da tela dos alunos. As respostas de quem já fez continuam no estudo de cada um.</p>
							{/if}

							{#if abertoId === s.id}
								<div class="mt-4 border-t border-line pt-4">
									{#if !r}
										<div class="h-32 animate-pulse rounded-2xl bg-skel" role="status" aria-label="Carregando o resultado"></div>
									{:else if r.erro}
										<p role="alert" class="text-sm font-semibold text-bad-fg">{r.erro}</p>
									{:else}
										{@const fizeram = r.alunos.filter((a) => num(a.respondidas) > 0)}
										{@const media = fizeram.length ? fizeram.reduce((t, a) => t + num(a.certas), 0) / fizeram.length : 0}
										<dl class="grid grid-cols-2 gap-2">
											<div class="rounded-2xl bg-tile p-3">
												<dd class="nums text-2xl font-extrabold">{fizeram.length} de {r.alunos.length}</dd>
												<dt class="mt-0.5 text-xs font-semibold text-ink-soft">Alunos que entregaram</dt>
											</div>
											<div class="rounded-2xl bg-tile p-3">
												<dd class="nums text-2xl font-extrabold">{fizeram.length ? `${media.toFixed(1).replace('.', ',')} de ${s.objetivas}` : '—'}</dd>
												<dt class="mt-0.5 text-xs font-semibold text-ink-soft">Média de acertos nas objetivas</dt>
											</div>
										</dl>

										<div class="mt-4 flex items-center justify-between gap-2">
											<h4 class="text-label font-bold text-ink-soft">Por aluno</h4>
											<button type="button" onclick={() => csvSimulado(s, r)} class="flex min-h-11 items-center gap-1.5 rounded-xl px-2 text-sm font-bold text-accent-ink">
												<DownloadSimple size={17} weight="bold" aria-hidden="true" /> Baixar planilha
											</button>
										</div>
										<div class="mt-1 overflow-x-auto rounded-2xl border border-line">
											<table class="w-full min-w-[440px] text-left text-sm">
												<thead class="bg-tile text-xs text-ink-soft">
													<tr>
														<th scope="col" class="px-3 py-2 font-bold">Aluno</th>
														<th scope="col" class="px-3 py-2 text-right font-bold">Acertos</th>
														<th scope="col" class="px-3 py-2 text-right font-bold">%</th>
														<th scope="col" class="px-3 py-2 font-bold">Entregou</th>
													</tr>
												</thead>
												<tbody>
													{#each r.alunos as a (a.usuario_id)}
														{@const fez = num(a.respondidas) > 0}
														<tr class="border-t border-line">
															<td class="px-3 py-2">
																<span class="font-semibold">{a.nome || a.apelido}</span>
																{#if a.ra}<span class="block font-code text-xs text-ink-soft">{a.ra}</span>{/if}
															</td>
															<td class="nums px-3 py-2 text-right font-bold">{fez ? `${num(a.certas)}/${s.objetivas}` : '—'}</td>
															<td class="nums px-3 py-2 text-right">{fez ? `${pct(a.certas, s.objetivas)}%` : '—'}</td>
															<td class="px-3 py-2 text-xs {fez ? '' : 'font-bold text-bad-fg'}">{fez ? quando(a.entregue_em) : 'não fez'}</td>
														</tr>
													{/each}
												</tbody>
											</table>
										</div>

										{#if r.questoes.length}
											<h4 class="mt-5 text-label font-bold text-ink-soft">Por matéria (pior primeiro)</h4>
											<ul class="mt-2 space-y-2.5">
												{#each materiasDo(r) as m (m.materia)}
													{@const p = pct(m.certas, m.respondidas) ?? 0}
													<li>
														<div class="flex items-baseline justify-between gap-3 text-sm">
															<span class="min-w-0 font-semibold text-pretty">{m.materia ? nomeMateria(m.materia) : 'Sem matéria'}</span>
															<span class="nums shrink-0 font-bold">{p}%</span>
														</div>
														<div class="mt-1 h-2 overflow-hidden rounded-full bg-track" aria-hidden="true">
															<div class="h-full rounded-full {p < 50 ? 'bg-bad-solid' : 'bg-ok-solid'}" style="width: {p}%"></div>
														</div>
													</li>
												{/each}
											</ul>

											<h4 class="mt-5 text-label font-bold text-ink-soft">Questões que a turma mais errou</h4>
											<ol class="mt-2 space-y-2">
												{#each r.questoes.slice(0, 5) as q (q.questao_id)}
													{@const b = porId.get(q.questao_id)}
													<li class="rounded-2xl bg-tile p-3">
														<div class="flex items-baseline justify-between gap-3">
															<span class="text-sm font-bold">{b ? rotuloQuestao(b) : q.questao_id}</span>
															<span class="nums shrink-0 text-sm font-bold">{fmtPct(q.certas, q.respondidas)} acertaram</span>
														</div>
														{#if b?.tema}<p class="mt-0.5 text-xs text-pretty text-ink-soft">{b.tema}</p>{/if}
													</li>
												{/each}
											</ol>
										{/if}
									{/if}
								</div>
							{/if}
						</li>
					{/each}
				</ul>
			{/if}
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
								{b?.tema ?? ''}{b?.tema && q.materia ? ', ' : ''}{q.materia ? nomeMateria(q.materia) : ''}
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
								<strong>{num(s.respondidas)}</strong>, {num(s.alunos_ativos)} {num(s.alunos_ativos) === 1 ? 'aluno' : 'alunos'}, {fmtPct(s.certas, s.respondidas)}
							</span>
						</li>
					{/each}
				</ul>
			{/if}
		{/if}
	</div>
{/if}
