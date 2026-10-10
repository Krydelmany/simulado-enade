<script>
	import { onMount } from 'svelte';
	import { page } from '$app/stores';
	import Questao from '$lib/Questao.svelte';
	import SessaoTopo from '$lib/SessaoTopo.svelte';
	import BarraAcao from '$lib/BarraAcao.svelte';
	import Contador from '$lib/Contador.svelte';
	import { carregarBanco, embaralhar } from '$lib/banco.js';
	import {
		somarXP,
		getXP,
		getErros,
		registrarErro,
		removerErro
	} from '$lib/stats.js';
	import { ArrowsClockwise, Flag, Lightning, Tag, Target, Timer, Trophy } from 'phosphor-svelte';

	let banco = $state([]);
	let fila = $state([]);
	let i = $state(0);
	let certas = $state(0);
	let feitas = $state(0);
	let log = $state([]);
	let tema = $state('todos');
	let encerrada = $state(false);
	let inicio = $state(Date.now());
	let xp = $state(0);
	let xpGanho = $state(0);
	let xpPing = $state(0);
	let carregou = $state(false);
	let falhou = $state(false);

	let revisao = $derived($page.url.searchParams.get('modo') === 'revisao');
	let temas = $derived([...new Set(banco.map((q) => q.tema))].sort());

	onMount(async () => {
		try {
			banco = await carregarBanco();
			xp = getXP();
		} catch {
			falhou = true;
		} finally {
			carregou = true;
		}
		montar();
	});

	function base() {
		let lista = revisao ? banco.filter((q) => getErros().includes(q.id)) : banco;
		if (tema !== 'todos') lista = lista.filter((q) => q.tema === tema);
		return lista;
	}

	function montar() {
		fila = embaralhar(base());
		i = 0;
		certas = 0;
		feitas = 0;
		log = [];
		xpGanho = 0;
		xpPing = 0;
		encerrada = false;
		inicio = Date.now();
	}

	function aoResponder(r) {
		feitas++;
		const q = fila.find((x) => x.id === r.id);
		log = [...log, { materia: q?.materia_ava || q?.tema || '?', certa: !!r.certa }];
		if (r.certa) {
			certas++;
			somarXP(10);
			xp = getXP();
			xpGanho += 10;
			xpPing++;
			removerErro(r.id);
		} else if (!r.anulada) {
			registrarErro(r.id);
		}
	}

	function mmss() {
		const s = Math.floor((Date.now() - inicio) / 1000);
		return `${String(Math.floor(s / 60)).padStart(2, '0')}:${String(s % 60).padStart(2, '0')}`;
	}

	function porMateria() {
		const mapa = new Map();
		for (const r of log) {
			if (!mapa.has(r.materia)) mapa.set(r.materia, { n: 0, ok: 0 });
			const m = mapa.get(r.materia);
			m.n++;
			if (r.certa) m.ok++;
		}
		return [...mapa.entries()].sort((a, b) => b[1].n - a[1].n).slice(0, 3);
	}
</script>

<div class="mx-auto w-full max-w-3xl">
{#if !carregou}
	<div class="space-y-3" role="status" aria-label="Carregando questões">
		<div class="h-40 animate-pulse rounded-3xl bg-skel"></div>
		<div class="h-14 animate-pulse rounded-2xl bg-skel"></div>
		<div class="h-14 animate-pulse rounded-2xl bg-skel"></div>
	</div>
{:else if falhou || !banco.length}
	<div class="rounded-3xl bg-card p-6 text-center shadow-sm" role="alert">
		<p class="font-display text-lg font-bold">Não deu para carregar as questões</p>
		<p class="mt-1 text-sm text-ink-soft">Verifique sua conexão e tente de novo.</p>
		<button type="button" onclick={() => location.reload()} class="btn3d duo-accent mt-4 w-full rounded-2xl p-3.5 font-bold">
			Tentar de novo
		</button>
	</div>
{:else if encerrada}
	<div class="-mx-4 -mt-6 bg-bar px-4 pt-8 pb-10 text-center text-white" style="border-radius: 0 0 26px 26px;">
		<p class="text-sm font-medium text-bar-fg">{revisao ? 'Revisão de erros' : 'Treino livre'}</p>
		<h2 class="mt-1 font-display text-3xl font-extrabold tracking-tight">Sessão concluída</h2>
		<p class="springin mx-auto mt-4 flex h-24 w-24 items-center justify-center rounded-full bg-accent-soft">
			<Trophy size={44} weight="fill" class="text-accent" aria-hidden="true" />
		</p>
		<p class="nums mt-3 font-display text-6xl font-extrabold tracking-tight">
			<Contador valor={certas} />/{feitas}
		</p>
		<p class="mt-1 text-sm text-bar-fg">acertos nesta sessão</p>
	</div>
	<div class="mx-auto -mt-0 grid max-w-xs grid-cols-3 gap-2 pt-4 text-center">
		<div class="rounded-2xl bg-card p-3 shadow-sm">
			<p class="nums flex items-center justify-center gap-1 text-xl font-extrabold"><Target size={17} weight="bold" class="text-accent" aria-hidden="true" />{feitas ? Math.round((certas / feitas) * 100) : 0}%</p>
			<p class="text-[11px] font-semibold text-ink-soft">Precisão</p>
		</div>
		<div class="rounded-2xl bg-card p-3 shadow-sm">
			<p class="nums flex items-center justify-center gap-1 text-xl font-extrabold"><Timer size={17} weight="bold" class="text-accent" aria-hidden="true" />{mmss()}</p>
			<p class="text-[11px] font-semibold text-ink-soft">Tempo</p>
		</div>
		<div class="rounded-2xl bg-card p-3 shadow-sm">
			<p class="nums flex items-center justify-center gap-1 text-xl font-extrabold"><Lightning size={17} weight="fill" class="text-accent" aria-hidden="true" />+{xpGanho}</p>
			<p class="text-[11px] font-semibold text-ink-soft">XP ganho</p>
		</div>
	</div>
	{#if porMateria().length}
		<div class="mt-3 rounded-3xl bg-card p-5 shadow-sm">
			<p class="font-display text-lg font-bold">Desempenho por matéria</p>
			<div class="mt-3 space-y-3">
				{#each porMateria() as [m, d] (m)}
					<div>
						<div class="flex items-baseline justify-between gap-3 text-sm">
							<p class="truncate font-semibold">{m}</p>
							<p class="nums shrink-0 font-bold">{d.ok}/{d.n}</p>
						</div>
						<div class="mt-1 h-2 overflow-hidden rounded-full bg-track">
							<div class="h-full rounded-full bg-accent" style="width: {(d.ok / d.n) * 100}%"></div>
						</div>
					</div>
				{/each}
			</div>
		</div>
	{/if}
	<div class="mt-4 space-y-2">
		<button type="button" onclick={montar} class="btn3d duo-accent flex w-full items-center justify-center gap-2 rounded-[14px] p-3.5 font-display text-lg font-bold">
			<ArrowsClockwise size={20} weight="bold" aria-hidden="true" /> Nova sessão
		</button>
		{#if getErros().length}
			<a href="/treino/?modo=revisao" class="flex w-full items-center justify-center rounded-[14px] border-2 border-line bg-card p-3.5 font-display text-lg font-bold">
				Revisar erros ({getErros().length})
			</a>
		{/if}
	</div>
{:else}
	<SessaoTopo
		titulo={revisao ? 'Revisar erros' : `${i + 1}ª questão`}
		detalhe={revisao ? `${certas}/${feitas}` : `${certas}/${feitas} certas`}
		progresso={fila.length ? (i + 1) / fila.length : 0}
		{xp}
		aoFechar={() => (encerrada = true)}
	/>
	{#if !fila.length}
		<div class="mt-6 rounded-3xl bg-card p-6 text-center shadow-sm">
			<p class="font-display text-lg font-bold">Nada por aqui</p>
			<p class="mt-1 text-sm text-ink-soft">
				{revisao ? 'Sem erros acumulados — quando errar, a questão aparece aqui.' : 'Nenhuma questão neste filtro.'}
			</p>
			{#if revisao}
				<a href="/treino/" class="btn3d duo-accent mt-4 flex w-full items-center justify-center rounded-[14px] p-3.5 font-display text-lg font-bold">
					Treinar tudo
				</a>
			{/if}
		</div>
	{:else}
		<div class="mt-4 mb-3 flex items-center gap-2">
			<label class="flex flex-1 items-center gap-2 rounded-2xl border border-line bg-card px-3">
				<Tag size={17} weight="bold" class="shrink-0 text-ink-soft" aria-hidden="true" />
				<span class="sr-only">Filtrar por tema</span>
				<select bind:value={tema} onchange={montar} class="w-full bg-transparent py-3 text-sm font-semibold text-ink">
					<option value="todos">Todos os temas</option>
					{#each temas as t (t)}
						<option value={t}>{t}</option>
					{/each}
				</select>
			</label>
			<p class="nums flex items-center gap-1.5 rounded-2xl bg-card px-3 py-3 text-sm font-bold" role="status">
				<Flag size={16} weight="bold" class="text-accent" aria-hidden="true" />{certas}/{feitas}
			</p>
		</div>
		{#if fila[i]}
			{#key fila[i].id + '-' + i}
				<Questao q={fila[i]} onResponder={aoResponder} />
			{/key}
			<BarraAcao rotulo="Próxima" mostrarXP={xpPing > 0} onClick={() => { xpPing = 0; i = (i + 1) % fila.length; }} />
		{/if}
	{/if}
{/if}

</div>
