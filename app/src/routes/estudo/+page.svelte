<script>
	import { onMount } from 'svelte';
	import Questao from '$lib/Questao.svelte';
	import { carregarBanco, embaralhar, doNivel } from '$lib/banco.js';
	import { somarXP, registrarAtividade, registrarErro, removerErro } from '$lib/stats.js';

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

	onMount(async () => {
		banco = await carregarBanco();
	});

	function comecar(n) {
		nivel = n;
		sessao = embaralhar(banco.filter((q) => doNivel(q, n))).slice(0, TOTAL);
		i = 0;
		certas = 0;
		parciais = 0;
		fim = false;
	}

	function aoResponder(r) {
		registrarAtividade();
		if (r.certa) {
			certas++;
			somarXP(10);
			removerErro(r.id);
		} else if (r.parcial) {
			parciais++;
			somarXP(5);
		} else if (!r.anulada) {
			registrarErro(r.id);
		}
		if (i + 1 >= sessao.length) fim = true;
		else i++;
	}
</script>

{#if !banco.length}
	<p class="rounded-xl bg-white p-5 text-center text-slate-500">Carregando questões…</p>
{:else if nivel === null}
	<div class="space-y-3">
		<h1 class="text-xl font-bold">Sessão de estudo · 10 questões</h1>
		{#each Object.entries(NIVEIS) as [n, info] (n)}
			<button
				type="button"
				onclick={() => comecar(Number(n))}
				class="block w-full rounded-xl bg-white p-5 text-left shadow-sm active:bg-blue-50"
			>
				<p class="text-lg font-bold">{info.nome}</p>
				<p class="mt-1 text-sm text-slate-600">{info.desc}</p>
			</button>
		{/each}
	</div>
{:else if fim}
	<div class="space-y-3 rounded-xl bg-white p-5 text-center shadow-sm">
		<h1 class="text-xl font-bold">{NIVEIS[nivel].nome}</h1>
		<p class="text-4xl font-black text-blue-900">{certas}/{sessao.length}</p>
		<p class="text-sm text-slate-600">
			{Math.round((certas / sessao.length) * 100)}% de acerto
			{parciais ? ` · ${parciais} meia(s) na discursiva` : ''}
		</p>
		<button type="button" onclick={() => (nivel = null)} class="w-full rounded-lg bg-blue-900 p-3 font-semibold text-white">
			Outra sessão
		</button>
		<a href="/" class="block rounded-lg border border-slate-300 p-3 font-semibold">Início</a>
	</div>
{:else}
	<div class="mb-3">
		<div class="h-2 overflow-hidden rounded-full bg-slate-200">
			<div class="h-full bg-blue-800" style="width: {((i + 1) / sessao.length) * 100}%"></div>
		</div>
		<p class="mt-1 text-center text-sm font-semibold text-slate-600">
			{NIVEIS[nivel].nome} · {i + 1}/{sessao.length} · ✅ {certas}
		</p>
	</div>
	{#if sessao[i]}
		{#key sessao[i].id}
			<Questao q={sessao[i]} onResponder={aoResponder} />
		{/key}
	{/if}
{/if}
