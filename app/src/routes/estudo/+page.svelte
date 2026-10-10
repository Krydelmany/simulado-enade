<script>
	import { onMount } from 'svelte';
	import Questao from '$lib/Questao.svelte';
	import Contador from '$lib/Contador.svelte';
	import { carregarBanco, embaralhar, doNivel } from '$lib/banco.js';
	import { somarXP, registrarAtividade, registrarErro, removerErro } from '$lib/stats.js';
	import { ArrowLeft, CheckCircle, Target, Trophy } from 'phosphor-svelte';
	import XpToast from '$lib/XpToast.svelte';

	const TOTAL = 10;
	const NIVEIS = {
		1: { nome: 'N1 · Fundamentos', desc: 'Objetivas de base, sem pressa.' },
		2: { nome: 'N2 · Intermediário', desc: 'Misto, ritmo de prova.' },
		3: { nome: 'N3 · Avançado', desc: 'Misto + discursiva com autoavaliação.' }
	};

	let banco = $state([]);
	let carregou = $state(false);
	let falhou = $state(false);
	let nivel = $state(null);
	let sessao = $state([]);
	let i = $state(0);
	let certas = $state(0);
	let parciais = $state(0);
	let fim = $state(false);
	let pronto = $state(false);
	let xpPing = $state(0);

	onMount(async () => {
		try {
			banco = await carregarBanco();
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
		fim = false;
		pronto = false;
	}

	function aoResponder(r) {
		registrarAtividade();
		if (r.certa) {
			certas++;
			somarXP(10);
			xpPing++;
			removerErro(r.id);
		} else if (r.parcial) {
			parciais++;
			somarXP(5);
		} else if (!r.anulada) {
			registrarErro(r.id);
		}
		if (i + 1 >= sessao.length) pronto = true;
		else i++;
	}
</script>

<div class="mb-4 flex items-center gap-2">
	<a href="/" class="flex items-center gap-1 rounded-lg px-2 py-2 text-sm font-bold text-ink-soft" aria-label="Voltar ao início">
		<ArrowLeft size={18} weight="bold" aria-hidden="true" /> Início
	</a>
	<span class="flex-1"></span>
	<h1 class="text-sm font-bold tracking-wide text-ink-soft uppercase">Estudo · 10 questões</h1>
</div>

{#if !carregou}
	<div class="space-y-3" role="status" aria-label="Carregando questões">
		<div class="h-40 animate-pulse rounded-3xl bg-skel"></div>
		<div class="h-14 animate-pulse rounded-2xl bg-skel"></div>
		<div class="h-14 animate-pulse rounded-2xl bg-skel"></div>
	</div>
{:else if falhou || !banco.length}
	<div class="rounded-3xl bg-card p-6 text-center shadow-sm" role="alert">
		<p class="text-lg font-bold">Não deu para carregar as questões</p>
		<p class="mt-1 text-sm text-ink-soft">Verifique sua conexão e tente de novo.</p>
		<button type="button" onclick={() => location.reload()} class="btn3d duo-accent mt-4 w-full rounded-2xl p-3.5 font-bold">
			Tentar de novo
		</button>
	</div>
{:else if nivel === null}
	<div class="space-y-3">
		{#each Object.entries(NIVEIS) as [n, info], k (n)}
			<button
				type="button"
				onclick={() => comecar(Number(n))}
				class="rise flex w-full items-center gap-4 rounded-3xl bg-card p-5 text-left shadow-[0_10px_30px_-12px_rgba(20,33,61,0.25)] transition-transform hover:-translate-y-0.5 active:scale-[0.99]"
				style="animation-delay: {k * 70}ms"
			>
				<span class="nums flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl bg-bar text-xl font-extrabold text-white">
					{n}
				</span>
				<span>
					<span class="block text-[17px] font-bold tracking-tight">{info.nome}</span>
					<span class="block text-sm text-ink-soft">{info.desc}</span>
				</span>
			</button>
		{/each}
	</div>
{:else if fim}
	<div class="rise space-y-4 rounded-3xl bg-card p-6 text-center shadow-[0_10px_30px_-12px_rgba(20,33,61,0.25)]">
		<p class="springin mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-accent-soft">
			<Trophy size={28} weight="bold" aria-hidden="true" class="text-accent-ink" />
		</p>
		<h2 class="text-lg font-bold">{NIVEIS[nivel].nome}</h2>
		<p class="text-6xl font-extrabold tracking-tight text-ink nums">
			<Contador valor={certas} />/{sessao.length}
		</p>
		<div class="mx-auto grid max-w-xs grid-cols-2 gap-2 text-center">
			<div class="rounded-2xl bg-tile p-3">
				<p class="nums flex items-center justify-center gap-1 text-xl font-extrabold">
					<Target size={17} weight="bold" aria-hidden="true" />{Math.round((certas / sessao.length) * 100)}%
				</p>
				<p class="text-[11px] font-semibold text-ink-soft">acerto</p>
			</div>
			<div class="rounded-2xl bg-tile p-3">
				<p class="nums flex items-center justify-center gap-1 text-xl font-extrabold">
					<CheckCircle size={17} weight="bold" aria-hidden="true" />{parciais}
				</p>
				<p class="text-[11px] font-semibold text-ink-soft">meias</p>
			</div>
		</div>
		<button type="button" onclick={() => (nivel = null)} class="btn3d duo-accent w-full rounded-2xl p-3.5 font-bold">
			Outra sessão
		</button>
	</div>
{:else}
	<div class="mb-3">
		<div class="h-2.5 overflow-hidden rounded-full bg-track" role="progressbar" aria-valuenow={i + 1} aria-valuemin="1" aria-valuemax={sessao.length} aria-label="Progresso da sessão">
			<div class="h-full rounded-full bg-accent transition-[width] duration-500 ease-out" style="width: {((i + 1) / sessao.length) * 100}%"></div>
		</div>
		<p class="nums mt-1.5 text-center text-sm font-bold text-ink-soft">
			{NIVEIS[nivel].nome} · {i + 1}/{sessao.length} · {certas} certas
		</p>
	</div>
	{#if sessao[i]}
		{#key sessao[i].id}
			<Questao q={sessao[i]} onResponder={aoResponder} />
		{/key}
		{#if pronto}
			<button
				type="button"
				onclick={() => (fim = true)}
				class="btn3d duo-accent mt-3 w-full rounded-2xl p-3.5 font-bold"
			>
				Ver resultado
			</button>
		{/if}
	{/if}
	{#if xpPing > 0}
		<XpToast n={xpPing} />
	{/if}
{/if}
