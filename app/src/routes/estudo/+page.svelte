<script>
	import { onMount } from 'svelte';
	import Questao from '$lib/Questao.svelte';
	import SessaoTopo from '$lib/SessaoTopo.svelte';
	import BarraAcao from '$lib/BarraAcao.svelte';
	import Contador from '$lib/Contador.svelte';
	import { carregarBanco, embaralhar, doNivel } from '$lib/banco.js';
	import {
		somarXP,
		getXP,
		getErros,
		registrarErro,
		removerErro
	} from '$lib/stats.js';
	import { ArrowsClockwise, Lightning, Target, Timer, Trophy } from 'phosphor-svelte';

	const TOTAL = 10;
	const NIVEIS = {
		1: { nome: 'N1 · Fundamentos', desc: 'Objetivas de base, sem pressa.' },
		2: { nome: 'N2 · Intermediário', desc: 'Misto, ritmo de prova.' },
		3: { nome: 'N3 · Avançado', desc: 'Misto + discursiva com autoavaliação.' }
	};

	let banco = $state([]);
	let nivel = $state(null);
	let sessao = $state([]);
	let i = $state(0);
	let certas = $state(0);
	let parciais = $state(0);
	let fim = $state(false);
	let pronto = $state(false);
	let respondidaAqui = $state(false);
	let log = $state([]);
	let inicio = $state(Date.now());
	let xp = $state(0);
	let xpGanho = $state(0);
	let xpPing = $state(0);
	let carregou = $state(false);
	let falhou = $state(false);

	onMount(async () => {
		try {
			banco = await carregarBanco();
			xp = getXP();
		} catch {
			falhou = true;
		} finally {
			carregou = true;
		}
	});

	function comecar(n) {
		nivel = n;
		sessao = embaralhar(banco.filter((q) => doNivel(q, n))).slice(0, TOTAL);
		i = 0;
		certas = 0;
		parciais = 0;
		log = [];
		fim = false;
		pronto = false;
		respondidaAqui = false;
		xpGanho = 0;
		xpPing = 0;
		inicio = Date.now();
	}

	function aoResponder(r) {
		respondidaAqui = true;
		const q = sessao.find((x) => x.id === r.id);
		log = [...log, { materia: q?.materia_ava || q?.tema || '?', certa: !!r.certa }];
		if (r.certa) {
			certas++;
			somarXP(10);
			xp = getXP();
			xpGanho += 10;
			xpPing++;
			removerErro(r.id);
		} else if (r.parcial) {
			parciais++;
			somarXP(5);
			xp = getXP();
			xpGanho += 5;
		} else if (!r.anulada) {
			registrarErro(r.id);
		}
		if (i + 1 >= sessao.length) pronto = true;
	}

	function avancar() {
		xpPing = 0;
		respondidaAqui = false;
		if (i + 1 >= sessao.length) fim = true;
		else i++;
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
{:else if nivel === null}
	<div class="mb-4">
		<h1 class="font-display text-2xl font-extrabold tracking-tight">Sessão de estudo</h1>
		<p class="mt-1 text-sm text-ink-soft">10 questões. Escolha o nível e comece.</p>
	</div>
	<div class="space-y-3">
		{#each Object.entries(NIVEIS) as [n, info], k (n)}
			<button
				type="button"
				onclick={() => comecar(Number(n))}
				class="rise flex w-full items-center gap-4 rounded-3xl bg-card p-5 text-left shadow-[0_10px_30px_-12px_rgba(20,33,61,0.25)] transition-transform hover:-translate-y-0.5 active:scale-[0.99]"
				style="animation-delay: {k * 70}ms"
			>
				<span class="nums flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl bg-bar font-display text-xl font-extrabold text-white" aria-hidden="true">
					{n}
				</span>
				<span class="min-w-0 flex-1">
					<span class="block font-display text-[17px] font-bold tracking-tight">{info.nome}</span>
					<span class="block text-sm text-ink-soft">{info.desc}</span>
				</span>
				<span class="flex shrink-0 gap-1" aria-hidden="true">
					{#each [1, 2, 3] as d (d)}
						<span class="h-2 w-2 rounded-full {d <= Number(n) ? 'bg-accent' : 'bg-track'}"></span>
					{/each}
				</span>
			</button>
		{/each}
	</div>
{:else if fim}
	<div class="blueprint -mx-4 -mt-6 bg-bar px-4 pt-8 pb-10 text-center text-white" style="border-radius: 0 0 26px 26px;">
		<p class="text-sm font-medium text-bar-fg">Estudo · {NIVEIS[nivel].nome}</p>
		<h2 class="mt-1 font-display text-3xl font-extrabold tracking-tight">Sessão concluída</h2>
		<p class="springin mx-auto mt-4 flex h-24 w-24 items-center justify-center rounded-full bg-accent-soft">
			<Trophy size={44} weight="fill" class="text-accent" aria-hidden="true" />
		</p>
		<p class="nums mt-3 font-display text-6xl font-extrabold tracking-tight">
			<Contador valor={certas} />/{sessao.length}
		</p>
		<p class="mt-1 text-sm text-bar-fg">acertos nesta sessão</p>
	</div>
	<div class="mx-auto -mt-0 grid max-w-xs grid-cols-3 gap-2 pt-4 text-center">
		<div class="rounded-2xl bg-card p-3 shadow-sm">
			<p class="nums flex items-center justify-center gap-1 text-xl font-extrabold"><Target size={17} weight="bold" class="text-accent" aria-hidden="true" />{Math.round((certas / sessao.length) * 100)}%</p>
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
		<button type="button" onclick={() => (nivel = null)} class="btn3d duo-accent flex w-full items-center justify-center gap-2 rounded-[14px] p-3.5 font-display text-lg font-bold">
			<ArrowsClockwise size={20} weight="bold" aria-hidden="true" /> Outra sessão
		</button>
		{#if getErros().length}
			<a href="/treino/?modo=revisao" class="flex w-full items-center justify-center rounded-[14px] border-2 border-line bg-card p-3.5 font-display text-lg font-bold">
				Revisar erros ({getErros().length})
			</a>
		{/if}
	</div>
{:else}
	<SessaoTopo
		titulo={`Questão ${i + 1} de ${sessao.length}`}
		detalhe={NIVEIS[nivel].nome.split(' · ')[0]}
		progresso={(i + 1) / sessao.length}
		{xp}
		aoFechar={() => (nivel = null)}
	/>
	<div class="mt-4">
		{#if sessao[i]}
			{#key sessao[i].id}
				<Questao q={sessao[i]} onResponder={aoResponder} />
			{/key}
			{#if respondidaAqui && !pronto}
				<BarraAcao rotulo="Continuar" mostrarXP={xpPing > 0} onClick={avancar} />
			{:else if pronto}
				<BarraAcao rotulo="Ver resultado" mostrarXP={false} onClick={() => (fim = true)} />
			{/if}
		{/if}
	</div>
{/if}

</div>
