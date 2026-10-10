<script>
	import { onMount } from 'svelte';
	import Questao from '$lib/Questao.svelte';
	import { carregarBanco, embaralhar } from '$lib/banco.js';
	import { somarXP, registrarAtividade, registrarErro, removerErro } from '$lib/stats.js';

	let banco = $state([]);
	let fila = $state([]);
	let i = $state(0);
	let certas = $state(0);
	let feitas = $state(0);
	let tema = $state('todos');
	let encerrada = $state(false);
	let inicio = $state(Date.now());

	let temas = $derived([...new Set(banco.map((q) => q.tema))].sort());

	onMount(async () => {
		banco = await carregarBanco();
		fila = embaralhar(banco);
	});

	function aplicarTema() {
		fila = embaralhar(tema === 'todos' ? banco : banco.filter((q) => q.tema === tema));
		i = 0;
		certas = 0;
		feitas = 0;
		encerrada = false;
		inicio = Date.now();
	}

	function aoResponder(r) {
		feitas++;
		registrarAtividade();
		if (r.certa) {
			certas++;
			somarXP(10);
			removerErro(r.id);
		} else if (!r.anulada) {
			registrarErro(r.id);
		}
	}

	function minutos() {
		return Math.round((Date.now() - inicio) / 60000);
	}
</script>

{#if !banco.length}
	<p class="rounded-xl bg-white p-5 text-center text-slate-500">Carregando questões…</p>
{:else if encerrada}
	<div class="space-y-3 rounded-xl bg-white p-5 text-center shadow-sm">
		<h1 class="text-xl font-bold">Resumo da sessão</h1>
		<p class="text-4xl font-black text-blue-900">{certas}/{feitas}</p>
		<p class="text-sm text-slate-600">
			{feitas ? Math.round((certas / feitas) * 100) : 0}% de acerto · ~{minutos()} min
			{tema !== 'todos' ? ` · ${tema}` : ''}
		</p>
		<button type="button" onclick={aplicarTema} class="w-full rounded-lg bg-blue-900 p-3 font-semibold text-white">
			Nova sessão
		</button>
		<a href="/" class="block rounded-lg border border-slate-300 p-3 font-semibold">Início</a>
	</div>
{:else}
	<div class="mb-3 flex items-center gap-2">
		<select bind:value={tema} onchange={aplicarTema} class="flex-1 rounded-lg border border-slate-300 bg-white p-3 text-sm font-medium">
			<option value="todos">Todos os temas</option>
			{#each temas as t (t)}
				<option value={t}>{t}</option>
			{/each}
		</select>
		<button type="button" onclick={() => (encerrada = true)} class="rounded-lg bg-slate-700 px-4 py-3 text-sm font-semibold text-white">
			Parar
		</button>
	</div>

	<p class="mb-3 text-center text-sm font-semibold text-slate-600">
		{i + 1}ª questão · ✅ {certas}/{feitas}
	</p>

	{#if fila[i]}
		{#key fila[i].id + '-' + i}
			<Questao
				q={fila[i]}
				onResponder={(r) => {
					aoResponder(r);
				}}
			/>
		{/key}
		<div class="mt-3 grid grid-cols-2 gap-2">
			<button
				type="button"
				onclick={() => (i = (i + 1) % fila.length)}
				class="rounded-lg border border-slate-300 bg-white p-3 font-semibold"
			>
				Pular →
			</button>
			<button
				type="button"
				onclick={() => (i = (i + 1) % fila.length)}
				class="rounded-lg bg-blue-900 p-3 font-semibold text-white"
			>
				Próxima →
			</button>
		</div>
	{/if}
{/if}
