<script>
	import { onMount } from 'svelte';
	import { fly } from 'svelte/transition';
	import Questao from '$lib/Questao.svelte';
	import BarraAcao from '$lib/BarraAcao.svelte';
	import Contador from '$lib/Contador.svelte';
	import DicaGestos from '$lib/DicaGestos.svelte';
	import { DUR } from '$lib/motion.js';
	import { arrastarParaFechar, deslizarQuestoes } from '$lib/gestos.js';
	import { ligarCamadas } from '$lib/camadas.svelte.js';
	import { carregarBancoDetalhado } from '$lib/banco.js';
	import { nomeMateria } from '$lib/materias.js';
	import { foco } from '$lib/foco.svelte.js';
	import {
		FORMATO,
		TOTAL_QUESTOES,
		NOME_BLOCO,
		blocoDe,
		bancoCompleto,
		disponiveis,
		montarProva,
		corrigir,
		lerProva,
		gravarProva,
		limparProva,
		lerUltimo,
		gravarUltimo,
		relogio
	} from '$lib/simulado.js';
	import {
		getRevisar,
		marcarRevisar,
		desmarcarRevisar,
		registrarResposta,
		registrarErro,
		removerErro,
		registrarSessao,
		somarXP,
		contarParaRevisar
	} from '$lib/stats.js';
	import {
		ArrowLeft,
		ArrowRight,
		ArrowsClockwise,
		CheckCircle,
		Hourglass,
		Infinity as InfinityIcon,
		Info,
		ListChecks,
		MinusCircle,
		PaperPlaneTilt,
		Pause,
		Play,
		SquaresFour,
		Stairs,
		Timer,
		Trophy,
		X,
		XCircle
	} from 'phosphor-svelte';

	// Formato oficial (Portaria INEP nº 161, de 14/04/2026).
	const FORMATO_TELA = [
		{ label: 'Formação Geral', valor: '15 objetivas' },
		{ label: 'Componente Específico', valor: '30 objetivas + 1 discursiva' },
		{ label: 'Tempo', valor: '4 horas' }
	];
	// o relógio fica laranja nos últimos 30 minutos
	const ALERTA_MS = 30 * 60 * 1000;

	let banco = $state([]);
	let carregou = $state(false);
	let falhou = $state(false);
	// banco carregou pela metade: algum JSON não chegou
	let bancoParcial = $state(false);
	// prova salva que não deu para remontar por causa do banco parcial
	let provaGuardada = $state(false);
	let prova = $state(null);
	let questoes = $state([]);
	// 'inicio' | 'prova' | 'resultado' | 'revisao'
	let tela = $state('inicio');
	let i = $state(0);
	let agora = $state(Date.now());
	// instante em que o relógio voltou a correr nesta abertura da prova
	let retomadoEm = $state(Date.now());
	let ultimo = $state(null);
	let cartaoAberto = $state(false);
	let confirmaEntrega = $state(false);
	let confirmaNova = $state(false);
	let zoomAberto = $state(false);
	// sentido da última troca de questão: a nova entra deslizando por ele
	let direcao = $state(0);

	// A tela inicial é a base da rota; prova, resultado e revisão são camadas
	// por cima. Antes, o voltar do sistema no meio da prova saía do simulado
	// e caía na home. Sem confirmação: voltar da prova só pausa (relógio
	// parado, prova salva), e o histórico nunca REABRE a prova.
	ligarCamadas(
		() => {
			const l = [];
			if (tela === 'prova') {
				l.push('prova');
				if (cartaoAberto) l.push('cartao');
				if (confirmaEntrega) l.push('entrega');
			} else if (tela === 'resultado') l.push('resultado');
			else if (tela === 'revisao') l.push('resultado', 'revisao');
			else if (confirmaNova) l.push('nova');
			if (zoomAberto) l.push('zoom');
			return l;
		},
		(n) => {
			if (n === 'prova') pausar();
			else if (n === 'cartao') cartaoAberto = false;
			else if (n === 'entrega') confirmaEntrega = false;
			else if (n === 'nova') confirmaNova = false;
			else if (n === 'resultado') {
				tela = 'inicio';
				topo();
			} else if (n === 'revisao') tela = 'resultado';
			else if (n === 'zoom') zoomAberto = false;
		}
	);

	// estável: trocar a referência refaria o attachment da BarraAcao
	function abrirCartao() {
		cartaoAberto = true;
	}
	let refEntrega = $state(null);

	let completo = $derived(bancoCompleto(banco));
	let disp = $derived(disponiveis(banco));
	let emAndamento = $derived(!!prova && !prova.entregue);
	let gasto = $derived(
		prova ? prova.gastoMs + (tela === 'prova' ? Math.max(0, agora - retomadoEm) : 0) : 0
	);
	let restante = $derived(Math.max(0, FORMATO.duracaoMs - gasto));
	let respondidas = $derived(
		prova
			? questoes.filter((q, k) =>
					q.tipo === 'discursiva' ? !!prova.rascunho?.trim() : !!prova.marcas?.[k]
				).length
			: 0
	);
	let brancos = $derived(questoes.length - respondidas);
	let res = $derived(prova?.entregue ? corrigir(prova, questoes) : null);
	let pct = $derived(res ? Math.round((res.objetivas.certas / res.objetivas.total) * 100) : 0);

	// a prova e a revisão ocupam a tela toda: sem tab bar, com barra de ação fixa
	$effect(() => {
		foco.quiz = tela === 'prova' || tela === 'revisao';
		return () => {
			foco.quiz = false;
		};
	});

	// relógio: só corre com a prova aberta na tela
	$effect(() => {
		if (tela !== 'prova') return;
		const tique = setInterval(() => {
			agora = Date.now();
		}, 1000);
		const grava = setInterval(salvar, 15000);
		return () => {
			clearInterval(tique);
			clearInterval(grava);
		};
	});

	$effect(() => {
		if (tela === 'prova' && prova && !prova.entregue && restante <= 0) entregar(true);
	});

	$effect(() => {
		if (confirmaEntrega && refEntrega) refEntrega.focus();
	});

	onMount(() => {
		(async () => {
			let completo = false;
			try {
				({ questoes: banco, completo } = await carregarBancoDetalhado());
			} catch {
				falhou = true;
			} finally {
				carregou = true;
			}
			bancoParcial = !completo;
			ultimo = lerUltimo();
			const p = lerProva();
			if (p) {
				const mapa = new Map(banco.map((q) => [q.id, q]));
				const lista = p.ids.map((id) => mapa.get(id));
				if (lista.every(Boolean)) {
					prova = p;
					questoes = lista;
					i = Math.min(p.i ?? 0, lista.length - 1);
				} else if (completo) {
					// banco inteiro e a questão não existe mais: a prova não fecha
					limparProva();
				} else {
					// Banco pela metade (offline, 404, deploy no meio): o id pode
					// estar no arquivo que não chegou. Antes a prova era apagada
					// aqui — inclusive a já entregue. Agora fica no aparelho, e a
					// tela pede para recarregar.
					provaGuardada = true;
				}
			}
		})();

		// fechar a aba ou trocar de app no celular: grava o tempo até aqui
		const aoSair = () => {
			if (document.visibilityState === 'hidden') salvar();
		};
		document.addEventListener('visibilitychange', aoSair);
		window.addEventListener('pagehide', salvar);
		return () => {
			salvar();
			document.removeEventListener('visibilitychange', aoSair);
			window.removeEventListener('pagehide', salvar);
		};
	});

	// grava a prova; com ela aberta, passa o tempo corrido para `gastoMs`
	function salvar() {
		if (!prova) return;
		if (tela === 'prova' && !prova.entregue) {
			const t = Date.now();
			prova.gastoMs = Math.min(FORMATO.duracaoMs, prova.gastoMs + Math.max(0, t - retomadoEm));
			retomadoEm = t;
			agora = t;
			prova.i = i;
		}
		gravarProva($state.snapshot(prova));
	}

	function topo() {
		window.scrollTo({ top: 0 });
	}

	function comecar() {
		const p = montarProva(banco);
		if (!p) return;
		const mapa = new Map(banco.map((q) => [q.id, q]));
		prova = p;
		questoes = p.ids.map((id) => mapa.get(id));
		i = 0;
		direcao = 0;
		retomadoEm = Date.now();
		agora = retomadoEm;
		confirmaNova = false;
		tela = 'prova';
		gravarProva($state.snapshot(prova));
		topo();
	}

	function continuar() {
		retomadoEm = Date.now();
		agora = retomadoEm;
		tela = 'prova';
		topo();
	}

	function pausar() {
		salvar();
		cartaoAberto = false;
		tela = 'inicio';
		topo();
	}

	function irPara(k) {
		if (k < 0 || k >= questoes.length) return;
		direcao = Math.sign(k - i);
		i = k;
		cartaoAberto = false;
		if (tela === 'prova') salvar();
		topo();
	}

	function marcar(_id, letra) {
		if (letra) prova.marcas[i] = letra;
		else delete prova.marcas[i];
		salvar();
	}

	function escrever(texto) {
		prova.rascunho = texto;
		salvar();
	}

	function alternarRevisar(id, marcado) {
		if (marcado) marcarRevisar(id);
		else desmarcarRevisar(id);
	}

	function avancar() {
		if (i + 1 < questoes.length) irPara(i + 1);
		else cartaoAberto = true;
	}

	function pedirEntrega() {
		cartaoAberto = false;
		confirmaEntrega = true;
	}

	function entregar(esgotado = false) {
		if (!prova || prova.entregue) return;
		salvar();
		prova.gastoMs = Math.min(FORMATO.duracaoMs, prova.gastoMs);
		prova.entregue = true;
		prova.entregueEm = Date.now();
		prova.tempoEsgotado = !!esgotado;
		const r = corrigir(prova, questoes);

		// o simulado alimenta o mesmo histórico dos outros modos: o que errou
		// vai para "Revisar erros". Branco fica de fora — quem abandona a prova
		// na questão 3 não quer 43 questões novas na revisão; elas continuam
		// a um toque no gabarito corrigido.
		for (const it of r.itens) {
			if (it.bloco === 'DISC' || it.status === 'branco') continue;
			const q = questoes[it.k];
			registrarResposta({
				id: q.id,
				certa: it.status === 'certa',
				anulada: q.gabarito === 'ANULADA',
				materia: q.materia,
				tema: q.tema
			});
			if (it.status === 'certa') removerErro(q.id);
			else registrarErro(q.id);
		}
		const xp = r.objetivas.certas * 10;
		if (xp) somarXP(xp);
		prova.xp = xp;
		registrarSessao({
			modo: 'simulado',
			respondidas: r.objetivas.total - r.objetivas.brancos,
			certas: r.objetivas.certas,
			duracaoMs: prova.gastoMs
		});
		ultimo = {
			em: prova.entregueEm,
			certas: r.objetivas.certas,
			total: r.objetivas.total,
			fg: r.fg,
			ce: r.ce,
			gastoMs: prova.gastoMs
		};
		gravarUltimo(ultimo);
		gravarProva($state.snapshot(prova));
		confirmaEntrega = false;
		cartaoAberto = false;
		tela = 'resultado';
		topo();
	}

	function revisar(k) {
		direcao = 0;
		i = k;
		tela = 'revisao';
		topo();
	}

	// autoavaliação da discursiva, feita na revisão contra o padrão do INEP
	function avaliarDiscursiva(r) {
		const q = questoes[i];
		if (q?.tipo !== 'discursiva') return;
		prova.discAuto = r.auto;
		registrarResposta({
			id: q.id,
			certa: !!r.certa,
			parcial: !!r.parcial,
			materia: q.materia,
			tema: q.tema
		});
		gravarProva($state.snapshot(prova));
	}

	function novaProva() {
		if (emAndamento) {
			confirmaNova = true;
			return;
		}
		comecar();
	}

	function inicialRevisao(k) {
		const q = questoes[k];
		if (q.tipo === 'discursiva') {
			return prova.discAuto ? { respondida: true, mostrouPadrao: true, auto: prova.discAuto } : null;
		}
		return { respondida: true, escolha: prova.marcas?.[k] ?? null };
	}

	function ehCampo(t) {
		return (
			t instanceof HTMLElement &&
			(t.isContentEditable || ['INPUT', 'TEXTAREA', 'SELECT'].includes(t.tagName))
		);
	}

	function aoTecla(e) {
		if (e.key === 'Escape') {
			if (confirmaEntrega) confirmaEntrega = false;
			else if (confirmaNova) confirmaNova = false;
			else if (cartaoAberto) cartaoAberto = false;
			return;
		}
		if (e.metaKey || e.ctrlKey || e.altKey || ehCampo(e.target)) return;
		if (tela !== 'prova' && tela !== 'revisao') return;
		if (cartaoAberto || confirmaEntrega || zoomAberto) return;
		if (e.key === 'ArrowLeft') {
			e.preventDefault();
			irPara(i - 1);
		} else if (e.key === 'ArrowRight') {
			e.preventDefault();
			if (tela === 'prova') avancar();
			else if (i + 1 < questoes.length) irPara(i + 1);
		}
	}

	function corCelula(k) {
		const q = questoes[k];
		const marcada = q.tipo === 'discursiva' ? !!prova.rascunho?.trim() : !!prova.marcas?.[k];
		const atual = k === i ? ' ring-2 ring-accent ring-offset-2 ring-offset-card' : '';
		return (marcada ? 'border-ink bg-ink text-paper' : 'border-line bg-card text-ink') + atual;
	}

	function corCorrigida(it) {
		if (it.status === 'certa') return 'border-ok-solid bg-ok-solid text-white';
		if (it.status === 'errada') return 'border-bad-solid bg-bad-solid text-white';
		if (it.status === 'parcial') return 'border-amber-600 bg-amber-500 text-white';
		if (it.status === 'pendente') return 'border-dashed border-ink-soft bg-card text-ink';
		return 'border-line bg-track text-ink-soft';
	}

	function dataCurta(ms) {
		try {
			return new Date(ms).toLocaleDateString('pt-BR', { day: '2-digit', month: 'short' });
		} catch {
			return '';
		}
	}

	const BLOCOS = [
		{ id: 'FG', de: 0, ate: FORMATO.fg },
		{ id: 'CE', de: FORMATO.fg, ate: FORMATO.fg + FORMATO.ce },
		{ id: 'DISC', de: FORMATO.fg + FORMATO.ce, ate: TOTAL_QUESTOES }
	];
</script>

<svelte:window onkeydown={aoTecla} />

<div class="mx-auto w-full max-w-3xl" style="padding-bottom: calc(1rem + env(safe-area-inset-bottom));">
{#if !carregou}
	<div class="space-y-3" role="status" aria-label="Carregando o simulado">
		<div class="h-40 animate-pulse rounded-3xl bg-skel"></div>
		<div class="h-24 animate-pulse rounded-3xl bg-skel"></div>
	</div>
{:else if falhou || !banco.length}
	<div class="rounded-3xl bg-card p-6 text-center shadow-sm" role="alert">
		<p class="font-display text-lg font-bold">Não deu para carregar as questões</p>
		<p class="mt-1 text-sm text-ink-soft">Verifique sua conexão e tente de novo.</p>
		<button type="button" onclick={() => location.reload()} class="btn3d duo-accent mt-4 w-full rounded-2xl p-3.5 font-bold">
			Tentar de novo
		</button>
	</div>
{:else if provaGuardada}
	<!-- sem o início: "Começar simulado" aqui gravaria por cima da prova guardada -->
	<div class="rounded-3xl bg-card p-6 text-center shadow-sm" role="alert">
		<p class="font-display text-lg font-bold">Parte das questões não carregou</p>
		<p class="mt-1 text-sm text-ink-soft">
			Sua prova continua guardada neste aparelho. Verifique a conexão e tente de novo para abri-la.
		</p>
		<button type="button" onclick={() => location.reload()} class="btn3d duo-accent mt-4 w-full rounded-2xl p-3.5 font-bold">
			Tentar de novo
		</button>
	</div>
{:else if tela === 'prova' && prova}
	<!-- ===================== PROVA ===================== -->
	<div class="blueprint -mx-4 -mt-6 bg-bar px-4 pt-4 pb-5 text-white" style="border-radius: 0 0 26px 26px;">
		<div class="mx-auto max-w-3xl">
			<div class="flex items-center gap-3">
				<button
					type="button"
					onclick={pausar}
					aria-label="Pausar a prova"
					class="flex h-11 min-w-11 items-center justify-center gap-1.5 rounded-full bg-white/10 px-3 text-sm font-bold transition-transform active:scale-95"
				>
					<Pause size={18} weight="fill" aria-hidden="true" /> Pausar
				</button>
				<span class="flex-1"></span>
				<p
					class="nums flex items-center gap-1.5 rounded-full px-3.5 py-1.5 font-code text-sm font-extrabold {restante <=
					ALERTA_MS
						? 'bg-accent text-white'
						: 'bg-white/10 text-white'}"
					role="timer"
					aria-label="Tempo restante: {relogio(restante)}"
				>
					<Timer size={16} weight="bold" aria-hidden="true" />
					{relogio(restante)}
				</p>
			</div>
			<div class="mt-3 flex items-baseline justify-between gap-3">
				<p class="font-display text-[17px] font-bold">Questão {i + 1} de {questoes.length}</p>
				<p class="shrink-0 text-sm font-medium text-bar-fg">{NOME_BLOCO[blocoDe(i)]}</p>
			</div>
			<div
				class="mt-2 h-2.5 overflow-hidden rounded-full bg-white/15"
				role="progressbar"
				aria-label="Questões respondidas"
				aria-valuemin="0"
				aria-valuemax={questoes.length}
				aria-valuenow={respondidas}
			>
				<div
					class="h-full rounded-full bg-accent-bar transition-[width] duration-500 ease-out"
					style="width: {(respondidas / questoes.length) * 100}%"
				></div>
			</div>
			<p class="nums mt-1.5 font-code text-label font-bold text-white/55">{respondidas} de {questoes.length} respondidas</p>
		</div>
	</div>

	<div class="mt-4">
		<DicaGestos
			id="simulado"
			texto="Deslize a questão para os lados para passar ou voltar. Da borda da tela para o meio, você volta à tela anterior. Puxe a barra de baixo para cima para abrir o cartão-resposta."
		/>
		<!-- na última questão, deslizar abre o cartão-resposta, como o CTA -->
		<div
			{@attach deslizarQuestoes(() => ({
				anterior: i > 0,
				proxima: true,
				onAnterior: () => irPara(i - 1),
				onProxima: avancar
			}))}
		>
			{#key questoes[i].id}
				<div in:fly={{ x: 32 * direcao, duration: direcao ? DUR : 0 }}>
					<Questao
						q={questoes[i]}
						prova
						onMarcar={marcar}
						onRascunho={escrever}
						rascunhoInicial={prova.rascunho}
						onRevisar={alternarRevisar}
						revisarInicial={getRevisar().includes(questoes[i].id)}
						inicial={{ escolha: prova.marcas?.[i] ?? null }}
						bind:zoomAberto
					/>
				</div>
			{/key}
		</div>
		<BarraAcao
			rotulo={i + 1 < questoes.length ? 'Próxima' : 'Revisar e entregar'}
			onClick={avancar}
			onPuxar={abrirCartao}
		>
			<nav class="flex items-center gap-2" aria-label="Navegação da prova">
				<button
					type="button"
					onclick={() => irPara(i - 1)}
					disabled={i === 0}
					aria-label="Questão anterior"
					class="flex h-11 w-11 shrink-0 items-center justify-center rounded-full border border-line bg-card text-ink transition-transform active:scale-95 disabled:opacity-40"
				>
					<ArrowLeft size={20} weight="bold" aria-hidden="true" />
				</button>
				<button
					type="button"
					onclick={() => (cartaoAberto = true)}
					class="nums flex min-h-11 flex-1 items-center justify-center gap-2 rounded-full border border-line bg-card text-sm font-bold text-ink transition-transform active:scale-[0.98]"
				>
					<SquaresFour size={18} weight="bold" aria-hidden="true" />
					Cartão-resposta · {respondidas}/{questoes.length}
				</button>
				<button
					type="button"
					onclick={pedirEntrega}
					aria-label="Entregar a prova"
					class="flex h-11 w-11 shrink-0 items-center justify-center rounded-full border border-line bg-card text-ink transition-transform active:scale-95"
				>
					<PaperPlaneTilt size={20} weight="bold" aria-hidden="true" />
				</button>
			</nav>
		</BarraAcao>
	</div>
{:else if tela === 'revisao' && prova && res}
	<!-- ===================== REVISÃO (depois de entregar) ===================== -->
	<div class="mb-4 flex items-center gap-2">
		<button
			type="button"
			onclick={() => {
				tela = 'resultado';
				topo();
			}}
			class="flex min-h-11 items-center gap-1 rounded-lg px-2 text-sm font-bold text-ink-soft hover:text-ink"
		>
			<ArrowLeft size={18} weight="bold" aria-hidden="true" /> Resultado
		</button>
		<span class="flex-1"></span>
		<p class="nums font-code text-label font-bold text-ink-soft uppercase">
			{NOME_BLOCO[blocoDe(i)]} · {i + 1} de {questoes.length}
		</p>
	</div>
	<!-- na última questão o gesto só cede: não troca de tela -->
	<div
		{@attach deslizarQuestoes(() => ({
			anterior: i > 0,
			proxima: i + 1 < questoes.length,
			onAnterior: () => irPara(i - 1),
			onProxima: () => irPara(i + 1)
		}))}
	>
		{#key questoes[i].id}
			<div in:fly={{ x: 32 * direcao, duration: direcao ? DUR : 0 }}>
				<Questao
					q={questoes[i]}
					onResponder={avaliarDiscursiva}
					onRevisar={alternarRevisar}
					revisarInicial={getRevisar().includes(questoes[i].id)}
					inicial={inicialRevisao(i)}
					respostaAluno={questoes[i].tipo === 'discursiva' ? prova.rascunho || '(em branco)' : ''}
					resolucaoAberta={false}
					bind:zoomAberto
				/>
			</div>
		{/key}
	</div>
	<BarraAcao
		rotulo={i + 1 < questoes.length ? 'Próxima' : 'Voltar ao resultado'}
		onClick={() => {
			if (i + 1 < questoes.length) irPara(i + 1);
			else {
				tela = 'resultado';
				topo();
			}
		}}
	>
		<nav class="flex items-center gap-2" aria-label="Navegação da correção">
			<button
				type="button"
				onclick={() => irPara(i - 1)}
				disabled={i === 0}
				aria-label="Questão anterior"
				class="flex h-11 w-11 shrink-0 items-center justify-center rounded-full border border-line bg-card text-ink transition-transform active:scale-95 disabled:opacity-40"
			>
				<ArrowLeft size={20} weight="bold" aria-hidden="true" />
			</button>
			<p class="nums flex-1 text-center text-sm font-bold text-ink-soft" role="status" aria-live="polite">
				Questão {i + 1} de {questoes.length}
			</p>
			<span class="h-11 w-11 shrink-0" aria-hidden="true"></span>
		</nav>
	</BarraAcao>
{:else if tela === 'resultado' && prova && res}
	<!-- ===================== RESULTADO ===================== -->
	<div class="blueprint -mx-4 -mt-6 bg-bar px-4 pt-8 pb-10 text-center text-white" style="border-radius: 0 0 26px 26px;">
		<p class="text-sm font-medium text-bar-fg">Simulado · {dataCurta(prova.entregueEm)}</p>
		<h1 class="mt-1 font-display text-3xl font-extrabold tracking-tight">
			{prova.tempoEsgotado ? 'Tempo esgotado' : 'Prova entregue'}
		</h1>
		<p class="springin mx-auto mt-4 flex h-24 w-24 items-center justify-center rounded-full bg-accent-soft">
			<Trophy size={44} weight="fill" class="text-accent" aria-hidden="true" />
		</p>
		<p class="nums mt-3 font-display text-6xl font-extrabold tracking-tight">
			<Contador valor={res.objetivas.certas} />/{res.objetivas.total}
		</p>
		<p class="nums mt-1 text-sm text-bar-fg">acertos nas objetivas · {pct}%</p>
	</div>

	<div class="mx-auto grid max-w-md grid-cols-3 gap-2 pt-4 text-center">
		<div class="rounded-2xl bg-card p-3 shadow-sm">
			<p class="nums text-xl font-extrabold">{res.fg.certas}/{res.fg.total}</p>
			<p class="text-[11px] font-semibold text-ink-soft">Formação Geral</p>
		</div>
		<div class="rounded-2xl bg-card p-3 shadow-sm">
			<p class="nums text-xl font-extrabold">{res.ce.certas}/{res.ce.total}</p>
			<p class="text-[11px] font-semibold text-ink-soft">Específico</p>
		</div>
		<div class="rounded-2xl bg-card p-3 shadow-sm">
			<p class="nums flex items-center justify-center gap-1 text-xl font-extrabold">
				<Hourglass size={16} weight="bold" class="text-accent" aria-hidden="true" />{relogio(prova.gastoMs)}
			</p>
			<p class="text-[11px] font-semibold text-ink-soft">Tempo</p>
		</div>
	</div>
	{#if res.objetivas.brancos}
		<p class="nums mt-2 text-center text-xs font-semibold text-ink-soft">
			{res.objetivas.brancos} {res.objetivas.brancos === 1 ? 'objetiva ficou' : 'objetivas ficaram'} em branco
		</p>
	{/if}

	<!-- discursiva: o site não corrige texto; o aluno compara com o padrão do INEP -->
	<div class="mt-4 rounded-3xl bg-card p-5 shadow-sm">
		<p class="font-display text-lg font-bold">Discursiva</p>
		{#if res.disc === 'pendente'}
			<p class="mt-1 text-sm text-ink-soft">
				A discursiva não entra na contagem acima: compare sua resposta com o padrão do INEP e avalie.
			</p>
			<button
				type="button"
				onclick={() => revisar(questoes.length - 1)}
				class="btn3d duo-accent mt-3 w-full rounded-2xl p-3 font-bold"
			>
				Ver padrão e me avaliar
			</button>
		{:else}
			<p class="mt-1 flex items-center gap-2 text-sm font-semibold">
				{#if res.disc === 'certa'}
					<CheckCircle size={18} weight="bold" class="text-ok-fg" aria-hidden="true" /> Você avaliou como certa.
				{:else if res.disc === 'parcial'}
					<MinusCircle size={18} weight="bold" class="text-warn-fg" aria-hidden="true" /> Você avaliou como parcial.
				{:else}
					<XCircle size={18} weight="bold" class="text-bad-fg" aria-hidden="true" /> Você avaliou como errada.
				{/if}
			</p>
			<button
				type="button"
				onclick={() => revisar(questoes.length - 1)}
				class="mt-2 text-sm font-bold text-accent-ink underline"
			>
				Rever a discursiva
			</button>
		{/if}
	</div>

	{#if res.porMateria.length}
		<div class="mt-3 rounded-3xl bg-card p-5 shadow-sm">
			<p class="font-display text-lg font-bold">Por matéria</p>
			<p class="mt-0.5 text-xs text-ink-soft">Do pior para o melhor desempenho — comece o estudo pelo topo.</p>
			<div class="mt-3 space-y-3">
				{#each res.porMateria as m (m.materia)}
					<div>
						<div class="flex items-baseline justify-between gap-3 text-sm">
							<p class="truncate font-semibold">{nomeMateria(m.materia)}</p>
							<p class="nums shrink-0 font-bold">{m.certas}/{m.total}</p>
						</div>
						<div class="mt-1 h-2 overflow-hidden rounded-full bg-track">
							<div class="h-full rounded-full bg-accent" style="width: {(m.certas / m.total) * 100}%"></div>
						</div>
					</div>
				{/each}
			</div>
		</div>
	{/if}

	<div class="mt-3 rounded-3xl bg-card p-5 shadow-sm">
		<p class="font-display text-lg font-bold">Gabarito corrigido</p>
		<p class="mt-0.5 text-xs text-ink-soft">Toque numa questão para ver a correção.</p>
		{#each BLOCOS as b (b.id)}
			<p class="mt-4 mb-2 font-code text-[11px] font-bold tracking-[0.14em] text-ink-soft uppercase">{NOME_BLOCO[b.id]}</p>
			<div class="grid grid-cols-8 gap-1.5 sm:grid-cols-10">
				{#each res.itens.slice(b.de, b.ate) as it (it.k)}
					<button
						type="button"
						onclick={() => revisar(it.k)}
						aria-label="Questão {it.k + 1}: {it.status === 'certa' ? 'certa' : it.status === 'errada' ? 'errada' : it.status === 'branco' ? 'em branco' : it.status === 'pendente' ? 'discursiva a avaliar' : it.status}"
						class="nums flex h-10 items-center justify-center rounded-xl border-2 text-sm font-extrabold transition-transform active:scale-95 {corCorrigida(it)}"
					>
						{it.k + 1}
					</button>
				{/each}
			</div>
		{/each}
		<div class="mt-4 flex flex-wrap gap-x-4 gap-y-1 text-[11px] font-semibold text-ink-soft" aria-hidden="true">
			<span class="flex items-center gap-1.5"><span class="h-3 w-3 rounded bg-ok-solid"></span> certa</span>
			<span class="flex items-center gap-1.5"><span class="h-3 w-3 rounded bg-bad-solid"></span> errada</span>
			<span class="flex items-center gap-1.5"><span class="h-3 w-3 rounded border border-line bg-track"></span> em branco</span>
		</div>
	</div>

	<p class="mt-3 flex items-start gap-2 rounded-2xl border border-line bg-panel p-3 text-xs leading-relaxed text-ink-soft">
		<Info size={16} weight="bold" class="mt-0.5 shrink-0" aria-hidden="true" />
		<span>
			Para comparar: no simulado da turma com a prova de 2019 (35 questões), a média foi 41,5% e a maior
			nota, 54,3%.
		</span>
	</p>

	<div class="mt-4 space-y-2">
		<button type="button" onclick={comecar} class="btn3d duo-accent flex w-full items-center justify-center gap-2 rounded-[14px] p-3.5 font-display text-lg font-bold">
			<ArrowsClockwise size={20} weight="bold" aria-hidden="true" /> Novo simulado
		</button>
		{#if contarParaRevisar(banco)}
			<a href="/treino/?modo=revisao" class="flex w-full items-center justify-center rounded-[14px] border-2 border-line bg-card p-3.5 font-display text-lg font-bold">
				Revisar erros e marcadas ({contarParaRevisar(banco)})
			</a>
		{/if}
	</div>
{:else}
	<!-- ===================== INÍCIO ===================== -->
	<div class="mb-5">
		<h1 class="font-display text-2xl font-extrabold tracking-tight">Simulado ENADE 2026</h1>
		<p class="mt-1 text-sm text-ink-soft">A prova inteira, cronometrada, com correção só no final.</p>
	</div>

	{#if bancoParcial}
		<p class="mb-4 flex items-start gap-2 rounded-2xl bg-warn-bg p-3 text-sm font-semibold text-warn-fg" role="status">
			<Info size={18} weight="bold" class="mt-0.5 shrink-0" aria-hidden="true" />
			<span>
				Parte das questões não carregou: uma prova nova sairia sorteada só do que chegou.
				<button type="button" onclick={() => location.reload()} class="font-bold underline">Recarregar</button>
			</span>
		</p>
	{/if}

	<div class="space-y-4">
		<section
			class="blueprint rise rounded-3xl bg-bar p-5 text-white shadow-[0_10px_30px_-12px_rgba(20,33,61,0.45)] sm:p-6"
		>
			<p class="flex items-center gap-2 font-code text-label font-bold text-bar-fg uppercase">
				<Timer size={15} weight="bold" aria-hidden="true" /> Formato ENADE 2026
			</p>
			<dl class="nums mt-4 space-y-2 text-[15px] font-semibold">
				{#each FORMATO_TELA as f, k (f.label)}
					<div
						class="flex items-baseline justify-between gap-3 {k === FORMATO_TELA.length - 1
							? 'border-t border-white/20 pt-2'
							: ''}"
					>
						<dt>{f.label}</dt>
						<dd class="text-right">{f.valor}</dd>
					</div>
				{/each}
			</dl>
			<p class="mt-4 text-xs leading-relaxed text-pretty text-bar-fg">
				Fonte: Portaria INEP nº 161, de 14 de abril de 2026.
			</p>
		</section>

		{#if emAndamento}
			<section class="rise rounded-3xl border-2 border-accent bg-card p-5 shadow-sm sm:p-6" aria-label="Prova em andamento">
				<p class="font-code text-[11px] font-bold tracking-[0.14em] text-accent-ink uppercase">Prova em andamento</p>
				<p class="nums mt-1 font-display text-xl font-extrabold">
					{respondidas} de {questoes.length} respondidas · {relogio(restante)} restantes
				</p>
				<p class="mt-1 text-sm text-ink-soft">O relógio parou quando você pausou e volta a correr ao continuar.</p>
				<button type="button" onclick={continuar} class="btn3d duo-accent mt-4 flex w-full items-center justify-center gap-2 rounded-[14px] p-3.5 font-display text-lg font-bold">
					<Play size={20} weight="fill" aria-hidden="true" /> Continuar a prova
				</button>
				<button type="button" onclick={novaProva} class="mt-2 w-full rounded-[14px] border-2 border-line bg-card p-3 font-display text-base font-bold">
					Descartar e começar outra
				</button>
			</section>
		{:else}
			<section class="rise rounded-3xl border border-line bg-card p-5 shadow-sm sm:p-6" style="animation-delay: 80ms" aria-label="Como funciona">
				<div class="flex items-center gap-2">
					<ListChecks size={18} weight="bold" class="text-accent-ink" aria-hidden="true" />
					<h2 class="font-display text-heading font-bold">Como funciona</h2>
				</div>
				<ul class="mt-3 space-y-2 text-sm leading-relaxed text-pretty">
					<li>• {TOTAL_QUESTOES} questões sorteadas das provas de 2014 a 2023, espalhadas pelas matérias da Portaria.</li>
					<li>• Marque, troque e volte quando quiser — o cartão-resposta mostra o que falta.</li>
					<li>• O relógio de 4 horas só corre com a prova aberta: dá para pausar e continuar depois.</li>
					<li>• A correção aparece só quando você entregar. Na discursiva, você compara com o padrão do INEP.</li>
				</ul>
				{#if completo}
					<button type="button" onclick={novaProva} class="btn3d duo-accent mt-5 flex w-full items-center justify-center gap-2 rounded-[14px] p-3.5 font-display text-lg font-bold">
						<Play size={20} weight="fill" aria-hidden="true" /> Começar simulado
					</button>
				{:else}
					<p class="nums mt-4 rounded-2xl border border-dashed border-warn-line bg-warn-bg p-3 text-xs leading-relaxed text-warn-fg" role="status">
						O banco ainda não fecha uma prova: há {disp.fg} de {FORMATO.fg} objetivas de FG, {disp.ce} de
						{FORMATO.ce} de CE e {disp.discursivas} de {FORMATO.discursivas} discursiva.
					</p>
				{/if}
			</section>
		{/if}

		{#if ultimo}
			<section class="rise rounded-3xl border border-line bg-card p-5 shadow-sm" style="animation-delay: 120ms" aria-label="Último simulado">
				<p class="font-code text-[11px] font-bold tracking-[0.14em] text-ink-soft uppercase">Último simulado · {dataCurta(ultimo.em)}</p>
				<p class="nums mt-1 font-display text-xl font-extrabold">
					{ultimo.certas}/{ultimo.total} · {Math.round((ultimo.certas / ultimo.total) * 100)}%
				</p>
				<p class="nums text-sm text-ink-soft">
					FG {ultimo.fg.certas}/{ultimo.fg.total} · CE {ultimo.ce.certas}/{ultimo.ce.total} · {relogio(ultimo.gastoMs)}
				</p>
				{#if prova?.entregue}
					<button
						type="button"
						onclick={() => {
							tela = 'resultado';
							topo();
						}}
						class="mt-3 text-sm font-bold text-accent-ink underline"
					>
						Ver a correção
					</button>
				{/if}
			</section>
		{/if}

		<section aria-label="Outras formas de treinar" class="space-y-3 pt-2">
			<h2 class="font-display text-heading font-bold">Sem tempo para a prova inteira?</h2>
			<a
				href="/treino/"
				class="rise group flex items-center gap-4 rounded-3xl border border-line bg-card p-4 shadow-sm transition-all hover:-translate-y-0.5 hover:border-ink/25 active:scale-[0.99]"
			>
				<span class="flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl bg-accent-soft" aria-hidden="true">
					<InfinityIcon size={24} weight="bold" class="text-accent-ink" aria-hidden="true" />
				</span>
				<span class="min-w-0 flex-1">
					<span class="block font-display text-base font-bold">Treino livre</span>
					<span class="block text-sm text-ink-soft">Questões em sequência, com correção na hora.</span>
				</span>
				<ArrowRight size={20} weight="bold" class="shrink-0 text-ink-soft opacity-60 transition-transform group-hover:translate-x-1 group-hover:text-accent-ink group-hover:opacity-100" aria-hidden="true" />
			</a>
			<a
				href="/estudo/"
				class="rise group flex items-center gap-4 rounded-3xl border border-line bg-card p-4 shadow-sm transition-all hover:-translate-y-0.5 hover:border-ink/25 active:scale-[0.99]"
			>
				<span class="flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl bg-accent-soft" aria-hidden="true">
					<Stairs size={24} weight="bold" class="text-accent-ink" aria-hidden="true" />
				</span>
				<span class="min-w-0 flex-1">
					<span class="block font-display text-base font-bold">Estudo por níveis</span>
					<span class="block text-sm text-ink-soft">Sessões de 10 por matéria.</span>
				</span>
				<ArrowRight size={20} weight="bold" class="shrink-0 text-ink-soft opacity-60 transition-transform group-hover:translate-x-1 group-hover:text-accent-ink group-hover:opacity-100" aria-hidden="true" />
			</a>
		</section>
	</div>
{/if}

	<!-- cartão-resposta -->
	{#if cartaoAberto && prova && tela === 'prova'}
		<div class="fixed inset-0 z-50 flex items-end justify-center p-0 sm:items-center sm:p-4">
			<button type="button" onclick={() => (cartaoAberto = false)} aria-label="Fechar o cartão-resposta" class="absolute inset-0 cursor-default bg-black/50"></button>
			<div
				role="dialog"
				aria-modal="true"
				aria-labelledby="cartao-titulo"
				class="relative max-h-[88vh] w-full max-w-lg overflow-y-auto overscroll-none rounded-t-3xl bg-card p-5 shadow sm:rounded-3xl"
				style="padding-bottom: calc(1.25rem + env(safe-area-inset-bottom));"
				in:fly={{ y: 40, duration: DUR }}
				{@attach arrastarParaFechar(() => (cartaoAberto = false))}
			>
				<span aria-hidden="true" class="mx-auto mb-3 block h-1 w-9 rounded-full bg-line sm:hidden"></span>
				<div class="flex items-center gap-2">
					<h2 id="cartao-titulo" class="font-display text-xl font-extrabold tracking-tight">Cartão-resposta</h2>
					<span class="flex-1"></span>
					<button type="button" onclick={() => (cartaoAberto = false)} aria-label="Fechar" class="flex h-11 w-11 items-center justify-center rounded-full border border-line">
						<X size={18} weight="bold" aria-hidden="true" />
					</button>
				</div>
				<p class="nums mt-1 text-sm text-ink-soft">{respondidas} respondidas · {brancos} em branco · {relogio(restante)} restantes</p>
				{#each BLOCOS as b (b.id)}
					<p class="mt-4 mb-2 font-code text-[11px] font-bold tracking-[0.14em] text-ink-soft uppercase">{NOME_BLOCO[b.id]}</p>
					<div class="grid grid-cols-8 gap-1.5 sm:grid-cols-10">
						{#each questoes.slice(b.de, b.ate) as q, j (q.id)}
							{@const k = b.de + j}
							<button
								type="button"
								onclick={() => irPara(k)}
								aria-label="Questão {k + 1}{q.tipo === 'discursiva' ? (prova.rascunho?.trim() ? ', escrita' : ', em branco') : prova.marcas?.[k] ? `, marcada ${prova.marcas[k]}` : ', em branco'}"
								aria-current={k === i ? 'true' : undefined}
								class="nums flex h-10 flex-col items-center justify-center rounded-xl border-2 text-sm leading-none font-extrabold transition-transform active:scale-95 {corCelula(k)}"
							>
								{k + 1}
								{#if q.tipo !== 'discursiva' && prova.marcas?.[k]}
									<span class="mt-0.5 text-[10px] font-bold opacity-80">{prova.marcas[k]}</span>
								{/if}
							</button>
						{/each}
					</div>
				{/each}
				<button type="button" onclick={pedirEntrega} class="btn3d duo-accent mt-5 flex w-full items-center justify-center gap-2 rounded-[14px] p-3.5 font-display text-lg font-bold">
					<PaperPlaneTilt size={20} weight="bold" aria-hidden="true" /> Entregar a prova
				</button>
			</div>
		</div>
	{/if}

	<!-- confirmação da entrega -->
	{#if confirmaEntrega}
		<div class="fixed inset-0 z-50 flex items-end justify-center p-4 sm:items-center">
			<button type="button" onclick={() => (confirmaEntrega = false)} aria-label="Voltar à prova" class="absolute inset-0 cursor-default bg-black/50"></button>
			<div role="dialog" aria-modal="true" aria-labelledby="entrega-titulo" class="relative w-full max-w-sm rounded-3xl bg-card p-5 shadow">
				<h2 id="entrega-titulo" class="font-display text-xl font-extrabold tracking-tight">Entregar a prova?</h2>
				<p class="nums mt-1 text-sm text-ink-soft">
					{#if brancos}
						{brancos} {brancos === 1 ? 'questão está' : 'questões estão'} em branco.
					{:else}
						Todas as questões estão respondidas.
					{/if}
					Depois de entregar, as respostas não mudam mais e a correção aparece.
				</p>
				<div class="mt-4 space-y-2">
					<button type="button" onclick={() => entregar(false)} class="btn3d duo-accent w-full rounded-[14px] p-3.5 font-display text-base font-bold">
						Entregar
					</button>
					<!-- o foco abre aqui: entregar não tem volta, e um Enter distraído não pode decidir isso -->
					<button type="button" bind:this={refEntrega} onclick={() => (confirmaEntrega = false)} class="w-full rounded-[14px] border-2 border-line bg-card p-3 font-display text-base font-bold">
						Voltar à prova
					</button>
				</div>
			</div>
		</div>
	{/if}

	<!-- descartar prova em andamento -->
	{#if confirmaNova}
		<div class="fixed inset-0 z-50 flex items-end justify-center p-4 sm:items-center">
			<button type="button" onclick={() => (confirmaNova = false)} aria-label="Manter a prova em andamento" class="absolute inset-0 cursor-default bg-black/50"></button>
			<div role="dialog" aria-modal="true" aria-labelledby="nova-titulo" class="relative w-full max-w-sm rounded-3xl bg-card p-5 shadow">
				<h2 id="nova-titulo" class="font-display text-xl font-extrabold tracking-tight">Descartar a prova em andamento?</h2>
				<p class="nums mt-1 text-sm text-ink-soft">
					As {respondidas} respostas dela se perdem e uma prova nova é sorteada.
				</p>
				<div class="mt-4 space-y-2">
					<button type="button" onclick={comecar} class="w-full rounded-[14px] border-2 border-bad-solid bg-bad-solid p-3.5 font-display text-base font-bold text-white">
						Descartar e começar outra
					</button>
					<button type="button" onclick={() => (confirmaNova = false)} class="w-full rounded-[14px] border-2 border-line bg-card p-3 font-display text-base font-bold">
						Manter a prova
					</button>
				</div>
			</div>
		</div>
	{/if}
</div>
