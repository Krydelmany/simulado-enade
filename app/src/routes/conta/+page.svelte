<script>
	// Conta e turma. Uma etapa por vez: entrar → entrar na turma → turma.
	// Tudo aqui é opcional: sem conta o site funciona igual (progresso no
	// aparelho). A conta só serve para entrar numa turma — painel do professor,
	// ranking e progresso em mais de um aparelho.
	import { onMount } from 'svelte';
	import { page } from '$app/stores';
	import { GoogleLogo, EnvelopeSimple, Trophy, ChartBar, SignOut, Trash, UsersThree, Timer } from 'phosphor-svelte';
	import { lerFeitosDaTurma } from '$lib/simulado.js';
	import {
		nuvemLigada,
		usuarioAtual,
		entrarComGoogle,
		entrarComEmail,
		minhasTurmas,
		entrarTurma,
		sairDaTurma,
		ranking,
		sair,
		apagarConta,
		pendentes,
		enviarFila,
		simuladosDaTurma,
		salvarNome
	} from '$lib/nuvem.js';

	let carregando = $state(true);
	let usuario = $state(null);
	let turmas = $state([]);
	let erro = $state('');
	let ocupado = $state(false);

	// login por e-mail
	let mostrarEmail = $state(false);
	let email = $state('');
	let linkEnviado = $state(false);

	// entrar na turma
	let nome = $state('');
	let codigo = $state('');
	let apelido = $state('');
	let ra = $state('');
	let noRanking = $state(true);
	let consentiu = $state(false);
	let mostrarFormTurma = $state(false);

	// turma aberta + ranking
	let turmaAberta = $state(null);
	let periodo = $state('semana');
	let linhasRanking = $state([]);
	let carregandoRanking = $state(false);

	let fila = $state(0);
	let confirmarApagar = $state(false);
	let confirmarSair = $state(false);
	// mudar o nome em "Sua conta"
	let editandoNome = $state(false);
	let novoNome = $state('');

	// o próximo simulado da turma que a pessoa ainda pode fazer
	let proximoSimulado = $state(null);

	let precisaTurma = $derived(usuario && (turmas.length === 0 || mostrarFormTurma));

	function diasAte(data) {
		if (!data) return null;
		const alvo = new Date(`${String(data).slice(0, 10)}T00:00:00-03:00`).getTime();
		return Math.max(0, Math.ceil((alvo - Date.now()) / 86_400_000));
	}

	function inicioDaSemana() {
		const d = new Date();
		d.setHours(0, 0, 0, 0);
		d.setDate(d.getDate() - ((d.getDay() + 6) % 7)); // segunda-feira
		return d;
	}

	function pct(certas, total) {
		return total ? `${Math.round((Number(certas) / Number(total)) * 100)}%` : '—';
	}

	async function recarregar() {
		erro = '';
		try {
			usuario = await usuarioAtual();
			turmas = usuario ? await minhasTurmas() : [];
			if (!nome && usuario?.nome) nome = usuario.nome;
			if (!apelido && usuario?.nome) apelido = usuario.nome.split(/\s+/)[0].slice(0, 24);
			if (turmas.length && !turmaAberta) abrirTurma(turmas[0].turma);
			fila = pendentes();
		} catch (e) {
			erro = e.message;
		} finally {
			carregando = false;
		}
	}

	// o ranking é carregado pelo $effect lá embaixo (turma ou período mudou)
	function abrirTurma(t) {
		turmaAberta = t;
	}

	async function carregarRanking() {
		if (!turmaAberta?.ranking_ativo) {
			linhasRanking = [];
			return;
		}
		carregandoRanking = true;
		try {
			linhasRanking = await ranking(turmaAberta.id, periodo === 'semana' ? inicioDaSemana() : null);
		} catch (e) {
			erro = e.message;
		} finally {
			carregandoRanking = false;
		}
	}

	async function acao(fn) {
		erro = '';
		ocupado = true;
		try {
			await fn();
		} catch (e) {
			erro = e.message;
		} finally {
			ocupado = false;
		}
	}

	const google = () => acao(() => entrarComGoogle());
	const porEmail = (ev) => {
		ev.preventDefault();
		acao(async () => {
			await entrarComEmail(email);
			linkEnviado = true;
		});
	};

	function enviarTurma(ev) {
		ev.preventDefault();
		acao(async () => {
			// quem entrou por link de e-mail não tem nome: sem ele, o professor
			// só via o apelido no painel e não sabia quem era
			if (nome.trim() !== (usuario?.nome ?? '')) usuario.nome = await salvarNome(nome);
			const t = await entrarTurma({ codigo, apelido, ra, noRanking, consentiu });
			mostrarFormTurma = false;
			turmaAberta = null;
			await recarregar();
			if (t) abrirTurma(t);
			// a URL do convite já cumpriu o papel
			history.replaceState(history.state, '', '/conta/');
		});
	}

	const sairTurma = (t) =>
		acao(async () => {
			await sairDaTurma(t.id);
			confirmarSair = false;
			turmaAberta = null;
			await recarregar();
		});

	const guardarNome = (ev) => {
		ev.preventDefault();
		acao(async () => {
			usuario.nome = await salvarNome(novoNome);
			nome = usuario.nome;
			editandoNome = false;
		});
	};

	const sairConta = () =>
		acao(async () => {
			await sair();
			usuario = null;
			turmas = [];
		});

	const apagar = () =>
		acao(async () => {
			await apagarConta();
			usuario = null;
			turmas = [];
			confirmarApagar = false;
		});

	const sincronizar = () =>
		acao(async () => {
			await enviarFila();
			fila = pendentes();
		});

	onMount(() => {
		codigo = ($page.url.searchParams.get('turma') || '').toUpperCase();
		if (codigo) mostrarFormTurma = true;
		if (!nuvemLigada) {
			carregando = false;
			return;
		}
		recarregar();
		const t = setInterval(() => (fila = pendentes()), 5000);
		return () => clearInterval(t);
	});

	$effect(() => {
		if (turmaAberta && periodo) carregarRanking();
	});

	$effect(() => {
		const t = turmaAberta;
		proximoSimulado = null;
		if (!t) return;
		simuladosDaTurma(t.id)
			.then((l) => {
				const agora = Date.now();
				const feitos = lerFeitosDaTurma();
				proximoSimulado =
					l
						.filter((x) => !feitos[x.id] && new Date(x.fecha_em).getTime() >= agora)
						.sort((a, b) => new Date(a.abre_em) - new Date(b.abre_em))
						.map((x) => ({ ...x, aberto: new Date(x.abre_em).getTime() <= agora }))[0] ?? null;
			})
			.catch(() => {});
	});

	// "sex 31/10 às 23:59"
	function diaHora(iso) {
		const d = new Date(iso);
		if (Number.isNaN(d.getTime())) return '';
		const dia = d.toLocaleDateString('pt-BR', { weekday: 'short' }).replace('.', '');
		const data = d.toLocaleDateString('pt-BR', { day: '2-digit', month: '2-digit' });
		const hora = d.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' });
		return `${dia} ${data} às ${hora}`;
	}
</script>

<svelte:head>
	<title>Conta e turma · Simulado ENADE</title>
</svelte:head>

<div class="mx-auto max-w-xl">
	<h1 class="font-display text-2xl font-extrabold tracking-tight">Conta e turma</h1>

	{#if erro}
		<p role="alert" class="mt-4 rounded-2xl border border-bad-fg/30 bg-bad-bg p-3 text-sm font-semibold text-bad-fg">
			{erro}
		</p>
	{/if}

	{#if carregando}
		<div class="mt-6 space-y-3" role="status" aria-label="Carregando a conta">
			<div class="h-24 animate-pulse rounded-3xl bg-skel"></div>
			<div class="h-12 animate-pulse rounded-2xl bg-skel"></div>
		</div>
	{:else if !nuvemLigada}
		<section class="mt-6 rounded-3xl border border-line bg-card p-5 sm:p-6">
			<p class="text-[15px] leading-relaxed text-pretty">
				A conta ainda não está ligada neste site. Seu progresso continua salvo neste aparelho, como sempre.
			</p>
		</section>
	{:else if !usuario}
		<!-- Etapa 1: entrar -->
		<section class="mt-6 rounded-3xl border border-line bg-card p-5 sm:p-6" aria-labelledby="t-entrar">
			<h2 id="t-entrar" class="font-display text-heading font-extrabold">Entrar</h2>
			<p class="mt-2 text-[15px] leading-relaxed text-pretty text-ink-soft">
				{#if codigo}
					Para entrar na turma <strong class="font-code text-ink">{codigo}</strong>, primeiro entre na sua conta.
				{:else}
					A conta serve para entrar na turma do seu professor e levar o progresso para outro aparelho.
					Para só estudar, não precisa.
				{/if}
			</p>

			{#if linkEnviado}
				<p class="mt-5 rounded-2xl bg-ok-bg p-4 text-sm font-semibold text-ok-fg" role="status">
					Link enviado para {email}. Abra o e-mail neste aparelho e toque no link.
				</p>
			{:else}
				<button
					type="button"
					onclick={google}
					disabled={ocupado}
					class="btn3d duo-accent mt-5 flex min-h-[52px] w-full items-center justify-center gap-2 rounded-[14px] px-6 font-display text-base font-bold disabled:opacity-60"
				>
					<GoogleLogo size={20} weight="bold" aria-hidden="true" /> Entrar com Google
				</button>

				{#if mostrarEmail}
					<form class="mt-4 flex flex-col gap-2 sm:flex-row" onsubmit={porEmail}>
						<label class="sr-only" for="email">E-mail</label>
						<input
							id="email"
							type="email"
							required
							autocomplete="email"
							bind:value={email}
							placeholder="seu@email.com"
							class="min-h-11 flex-1 rounded-xl border-2 border-line bg-paper px-3 text-base"
						/>
						<button
							type="submit"
							disabled={ocupado}
							class="btn3d duo-btn min-h-11 rounded-xl px-4 text-sm font-bold disabled:opacity-60"
						>
							Mandar link
						</button>
					</form>
				{:else}
					<button
						type="button"
						onclick={() => (mostrarEmail = true)}
						class="mt-3 flex min-h-11 w-full items-center justify-center gap-2 rounded-xl text-sm font-bold text-ink-soft hover:text-ink"
					>
						<EnvelopeSimple size={18} weight="bold" aria-hidden="true" /> Prefiro receber um link por e-mail
					</button>
				{/if}
			{/if}
		</section>
	{:else if precisaTurma}
		<!-- Etapa 2: entrar na turma -->
		<section class="mt-6 rounded-3xl border border-line bg-card p-5 sm:p-6" aria-labelledby="t-turma">
			<h2 id="t-turma" class="font-display text-heading font-extrabold">Entrar na turma</h2>
			<p class="mt-2 text-[15px] leading-relaxed text-pretty text-ink-soft">
				O professor passa o código (ou o link) da turma.
			</p>

			<form class="mt-5 space-y-5" onsubmit={enviarTurma}>
				<div>
					<label for="codigo" class="text-sm font-bold">Código da turma</label>
					<input
						id="codigo"
						required
						autocomplete="off"
						autocapitalize="characters"
						spellcheck="false"
						bind:value={codigo}
						oninput={() => (codigo = codigo.toUpperCase())}
						class="mt-1.5 min-h-12 w-full rounded-xl border-2 border-line bg-paper px-3 font-code text-lg tracking-[0.2em] uppercase"
					/>
				</div>

				<div>
					<label for="nome" class="text-sm font-bold">Seu nome</label>
					<input
						id="nome"
						required
						minlength="2"
						maxlength="120"
						autocomplete="name"
						bind:value={nome}
						class="mt-1.5 min-h-12 w-full rounded-xl border-2 border-line bg-paper px-3 text-base"
					/>
					<p class="mt-1 text-xs text-ink-soft">Só o professor vê. É como ele acha você na lista da turma.</p>
				</div>

				<div>
					<label for="apelido" class="text-sm font-bold">Apelido no ranking</label>
					<input
						id="apelido"
						required
						minlength="2"
						maxlength="24"
						bind:value={apelido}
						class="mt-1.5 min-h-12 w-full rounded-xl border-2 border-line bg-paper px-3 text-base"
					/>
					<p class="mt-1 text-xs text-ink-soft">É o que a turma vê. Seu nome só o professor vê.</p>
				</div>

				<div>
					<label for="ra" class="text-sm font-bold">RA <span class="font-semibold text-ink-soft">(opcional)</span></label>
					<input
						id="ra"
						inputmode="numeric"
						autocomplete="off"
						maxlength="20"
						bind:value={ra}
						class="mt-1.5 min-h-12 w-full rounded-xl border-2 border-line bg-paper px-3 text-base"
					/>
					<p class="mt-1 text-xs text-ink-soft">Ajuda o professor a achar você na lista de chamada.</p>
				</div>

				<label class="flex min-h-11 cursor-pointer items-start gap-3">
					<input type="checkbox" bind:checked={noRanking} class="mt-1 h-5 w-5 shrink-0 accent-[var(--accent)]" />
					<span class="text-sm leading-relaxed">Aparecer no ranking da turma</span>
				</label>

				<label class="flex cursor-pointer items-start gap-3 rounded-2xl bg-tile p-3">
					<input type="checkbox" required bind:checked={consentiu} class="mt-1 h-5 w-5 shrink-0 accent-[var(--accent)]" />
					<span class="text-sm leading-relaxed text-pretty">
						Concordo que o professor desta turma veja meu nome, RA (se eu informar) e meu desempenho no
						site: quantas questões respondi, acertos por matéria e simulados. Posso sair da turma ou apagar a
						conta quando quiser. <a href="/privacidade/" target="_blank" class="font-bold underline">Como seus dados são usados</a>
					</span>
				</label>

				<div class="flex flex-col gap-2 sm:flex-row">
					<button
						type="submit"
						disabled={ocupado}
						class="btn3d duo-accent flex min-h-[52px] flex-1 items-center justify-center rounded-[14px] px-6 font-display text-base font-bold disabled:opacity-60"
					>
						Entrar na turma
					</button>
					{#if turmas.length}
						<button
							type="button"
							onclick={() => (mostrarFormTurma = false)}
							class="min-h-11 rounded-xl px-4 text-sm font-bold text-ink-soft hover:text-ink"
						>
							Cancelar
						</button>
					{/if}
				</div>
			</form>
		</section>
	{:else}
		<!-- Etapa 3: a turma -->
		{#if turmas.length > 1}
			<div class="mt-6 flex gap-2 overflow-x-auto pb-1" role="tablist" aria-label="Suas turmas">
				{#each turmas as m (m.turma.id)}
					<button
						type="button"
						role="tab"
						aria-selected={turmaAberta?.id === m.turma.id}
						onclick={() => abrirTurma(m.turma)}
						class="min-h-11 shrink-0 rounded-xl px-4 text-sm font-bold {turmaAberta?.id === m.turma.id
							? 'bg-bar text-white'
							: 'bg-tile text-ink-soft'}"
					>
						{m.turma.nome}
					</button>
				{/each}
			</div>
		{/if}

		{#if turmaAberta}
			{@const m = turmas.find((x) => x.turma.id === turmaAberta.id)}
			{@const dias = diasAte(turmaAberta.data_prova)}
			<section class="mt-6 rounded-3xl bg-bar p-5 text-white sm:p-6" aria-labelledby="t-nome">
				<p class="flex items-center gap-2 text-sm font-semibold text-bar-fg">
					<UsersThree size={18} weight="bold" aria-hidden="true" />
					{turmaAberta.instituicao}
				</p>
				<h2 id="t-nome" class="mt-1 font-display text-title font-extrabold">{turmaAberta.nome}</h2>
				{#if dias !== null}
					<p class="mt-4 flex items-baseline gap-2 font-display">
						<span class="nums text-5xl leading-none font-black">{dias}</span>
						<span class="text-base font-bold text-bar-fg">{dias === 1 ? 'dia' : 'dias'} até o ENADE</span>
					</p>
				{/if}
				{#if m?.papel === 'professor'}
					<a
						href="/professor/?turma={turmaAberta.id}"
						class="btn3d duo-accent mt-5 flex min-h-[52px] items-center justify-center gap-2 rounded-[14px] px-6 font-display text-base font-bold"
					>
						<ChartBar size={20} weight="bold" aria-hidden="true" /> Abrir painel da turma
					</a>
				{/if}
			</section>

			{#if proximoSimulado && m?.papel !== 'professor'}
				<section class="mt-6 rounded-3xl border-2 border-accent bg-card p-5 sm:p-6" aria-labelledby="t-proximo">
					<p class="flex items-center gap-2 text-label font-bold text-accent-ink">
						<Timer size={16} weight="bold" aria-hidden="true" />
						{proximoSimulado.aberto ? 'Simulado aberto agora' : 'Próximo simulado da turma'}
					</p>
					<h2 id="t-proximo" class="mt-1 font-display text-heading font-extrabold text-pretty">{proximoSimulado.titulo}</h2>
					<p class="mt-1 text-sm text-ink-soft">
						{proximoSimulado.aberto
							? `Faça até ${diaHora(proximoSimulado.fecha_em)}.`
							: `Abre ${diaHora(proximoSimulado.abre_em)} e fica aberto até ${diaHora(proximoSimulado.fecha_em)}.`}
					</p>
					{#if proximoSimulado.aberto}
						<a
							href="/simulado/"
							class="btn3d duo-accent mt-4 flex min-h-[52px] items-center justify-center gap-2 rounded-[14px] px-6 font-display text-base font-bold"
						>
							Ir para o simulado
						</a>
					{/if}
				</section>
			{/if}

			{#if turmaAberta.ranking_ativo}
				<section class="mt-6 rounded-3xl border border-line bg-card p-5 sm:p-6" aria-labelledby="t-ranking">
					<div class="flex items-center justify-between gap-3">
						<h2 id="t-ranking" class="flex items-center gap-2 font-display text-heading font-extrabold">
							<Trophy size={20} weight="bold" aria-hidden="true" /> Ranking
						</h2>
						<div class="flex rounded-xl bg-tile p-1" role="group" aria-label="Período do ranking">
							{#each [['semana', 'Semana'], ['geral', 'Geral']] as [v, rotulo] (v)}
								<button
									type="button"
									aria-pressed={periodo === v}
									onclick={() => (periodo = v)}
									class="min-h-9 rounded-lg px-3 text-xs font-bold {periodo === v ? 'bg-card shadow-sm' : 'text-ink-soft'}"
								>
									{rotulo}
								</button>
							{/each}
						</div>
					</div>
					<p class="mt-1 text-xs text-ink-soft">Por acertos. Conta treino, estudo e simulado.</p>

					{#if carregandoRanking}
						<div class="mt-4 h-32 animate-pulse rounded-2xl bg-skel" role="status" aria-label="Carregando o ranking"></div>
					{:else if linhasRanking.length === 0}
						<p class="mt-4 text-sm text-ink-soft">Ninguém respondeu nada nesse período ainda.</p>
					{:else}
						<ol class="mt-4 space-y-1.5">
							{#each linhasRanking as l, i (l.apelido + i)}
								<li
									class="flex min-h-11 items-center gap-3 rounded-xl px-3 {l.eu ? 'bg-accent-soft font-bold text-accent-ink' : 'bg-tile'}"
								>
									<span class="nums w-6 text-right font-display font-black">{i + 1}</span>
									<span class="min-w-0 flex-1 truncate">{l.apelido}{l.eu ? ' (você)' : ''}</span>
									<span class="nums text-sm font-bold">{l.certas}</span>
									<span class="nums w-12 text-right text-xs text-ink-soft">{pct(l.certas, l.respondidas)}</span>
								</li>
							{/each}
						</ol>
					{/if}
				</section>
			{/if}

			<div class="mt-4 flex flex-wrap items-center gap-x-4 gap-y-1 text-sm">
				<button type="button" onclick={() => (mostrarFormTurma = true)} class="min-h-11 font-bold text-ink-soft hover:text-ink">
					Entrar em outra turma
				</button>
				<!-- Professor não sai pelo site: voltar exige o admin (SQL), e um toque
				     sem querer tirava o painel dele. Aluno sai, mas confirmando. -->
				{#if m?.papel !== 'professor'}
					{#if confirmarSair}
						<button
							type="button"
							onclick={() => sairTurma(turmaAberta)}
							disabled={ocupado}
							class="min-h-11 rounded-xl bg-bad-solid px-4 font-bold text-white"
						>
							Sim, sair da turma
						</button>
						<button type="button" onclick={() => (confirmarSair = false)} class="min-h-11 px-2 font-bold text-ink-soft">
							Cancelar
						</button>
					{:else}
						<button type="button" onclick={() => (confirmarSair = true)} class="min-h-11 font-bold text-ink-soft hover:text-bad-fg">
							Sair desta turma
						</button>
					{/if}
				{/if}
			</div>
			{#if confirmarSair}
				<p class="text-xs text-pretty text-bad-fg">
					O professor deixa de ver você e você sai do ranking. Para voltar, use o código da turma de novo.
				</p>
			{/if}
		{/if}
	{/if}

	{#if usuario}
		<section class="mt-8 border-t border-line pt-5" aria-labelledby="t-conta">
			<h2 id="t-conta" class="text-label font-bold text-ink-soft">Sua conta</h2>
			{#if editandoNome}
				<form class="mt-2 flex flex-col gap-2 sm:flex-row" onsubmit={guardarNome}>
					<label class="sr-only" for="novo-nome">Seu nome</label>
					<input
						id="novo-nome"
						required
						minlength="2"
						maxlength="120"
						autocomplete="name"
						bind:value={novoNome}
						class="min-h-11 flex-1 rounded-xl border-2 border-line bg-paper px-3 text-base"
					/>
					<div class="flex gap-2">
						<button type="submit" disabled={ocupado} class="btn3d duo-btn min-h-11 rounded-xl px-4 text-sm font-bold disabled:opacity-60">Salvar</button>
						<button type="button" onclick={() => (editandoNome = false)} class="min-h-11 px-3 text-sm font-bold text-ink-soft">Cancelar</button>
					</div>
				</form>
			{:else}
				<p class="mt-2 text-sm">
					<strong class="font-semibold">{usuario.nome || 'Sem nome'}</strong>
					{#if usuario.email}<span class="block text-ink-soft">{usuario.email}</span>{/if}
				</p>
				<button
					type="button"
					onclick={() => {
						novoNome = usuario.nome;
						editandoNome = true;
					}}
					class="min-h-11 text-sm font-bold text-accent-ink"
				>
					Mudar nome
				</button>
			{/if}
			<p class="mt-1 text-xs text-ink-soft" role="status">
				{#if fila}
					{fila} {fila === 1 ? 'resposta esperando' : 'respostas esperando'} internet para subir.
					<button type="button" onclick={sincronizar} disabled={ocupado} class="font-bold underline">Enviar agora</button>
				{:else}
					Tudo sincronizado.
				{/if}
			</p>

			<div class="mt-4 flex flex-wrap gap-2">
				<button
					type="button"
					onclick={sairConta}
					disabled={ocupado}
					class="flex min-h-11 items-center gap-2 rounded-xl border-2 border-line px-4 text-sm font-bold"
				>
					<SignOut size={18} weight="bold" aria-hidden="true" /> Sair
				</button>
				{#if confirmarApagar}
					<button
						type="button"
						onclick={apagar}
						disabled={ocupado}
						class="flex min-h-11 items-center gap-2 rounded-xl bg-bad-solid px-4 text-sm font-bold text-white"
					>
						<Trash size={18} weight="bold" aria-hidden="true" /> Sim, apagar tudo
					</button>
					<button type="button" onclick={() => (confirmarApagar = false)} class="min-h-11 px-3 text-sm font-bold text-ink-soft">
						Cancelar
					</button>
				{:else}
					<button
						type="button"
						onclick={() => (confirmarApagar = true)}
						class="flex min-h-11 items-center gap-2 rounded-xl px-4 text-sm font-bold text-ink-soft hover:text-bad-fg"
					>
						<Trash size={18} weight="bold" aria-hidden="true" /> Apagar minha conta
					</button>
				{/if}
			</div>
			{#if confirmarApagar}
				<p class="mt-2 text-xs text-pretty text-bad-fg">
					Apaga sua conta, suas turmas e tudo que subiu para o servidor. O progresso neste aparelho continua.
				</p>
			{/if}
		</section>
	{/if}
</div>
