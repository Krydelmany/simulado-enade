<script>
	import { onMount } from 'svelte';
	import { fly } from 'svelte/transition';
	import { page } from '$app/stores';
	import Questao from '$lib/Questao.svelte';
	import SessaoTopo from '$lib/SessaoTopo.svelte';
	import BarraAcao from '$lib/BarraAcao.svelte';
	import BuscaQuestoes from '$lib/BuscaQuestoes.svelte';
	import Contador from '$lib/Contador.svelte';
	import DicaGestos from '$lib/DicaGestos.svelte';
	import { DUR } from '$lib/motion.js';
	import { deslizarQuestoes } from '$lib/gestos.js';
	import { ligarCamadas, sairDaRota } from '$lib/camadas.svelte.js';
	import { carregarBancoDetalhado, embaralhar } from '$lib/banco.js';
	import { remontarSessao } from '$lib/sessao.js';
	import { GRUPOS_MATERIA, materiaExiste, nomeMateria } from '$lib/materias.js';
	import {
		somarXP,
		getXP,
		getErros,
		registrarErro,
		removerErro,
		getRevisar,
		registrarResposta,
		registrarSessao,
		marcarRevisar,
		desmarcarRevisar,
		getParaRevisar,
		contarParaRevisar,
		salvarSessao,
		carregarSessao,
		limparSessao
	} from '$lib/stats.js';
	import { ArrowLeft, ArrowsClockwise, Flag, Lightning, Play, Tag, Target, Timer, Trophy } from 'phosphor-svelte';

	let banco = $state([]);
	let fila = $state([]);
	let i = $state(0);
	let volta = $state(0);
	let filtro = $state('todos');
	let filtroAnterior = $state('todos');
	// respostas[i] guarda a resposta da questão i da volta atual (para a navegação voltar e reexibir)
	let respostas = $state([]);
	// log acumula o histórico da sessão (todas as voltas) e alimenta os contadores
	let log = $state([]);
	let encerrada = $state(false);
	let fimVolta = $state(false);
	let inicio = $state(Date.now());
	let xp = $state(0);
	let xpGanho = $state(0);
	let xpPing = $state(0);
	let xpValor = $state(10);
	let carregou = $state(false);
	let falhou = $state(false);
	// banco veio inteiro? (com um JSON faltando, id ausente não é questão apagada)
	let bancoInteiro = $state(true);
	// treino pausado que não deu para remontar por causa do banco parcial
	let sessaoGuardada = $state(false);
	let escolha = $state(false);
	let salva = $state(null);
	let prontoModo = $state(null);
	let confirmaFiltro = $state(null);
	let confirmaSaida = $state(false);
	let zoomAberto = $state(false);
	// sentido da última troca de questão: a nova entra deslizando por ele
	// (1 = veio da direita, -1 = da esquerda, 0 = sem animação)
	let direcao = $state(0);

	// O quiz é a base da rota: o voltar do sistema fecha só o que está por
	// cima (fim da volta, modais, zoom) e, na base, sai da rota sem perda —
	// `persistir()` roda a cada resposta e navegação.
	ligarCamadas(
		() =>
			[fimVolta && 'fim', confirmaFiltro && 'filtro', confirmaSaida && 'saida', zoomAberto && 'zoom'].filter(
				Boolean
			),
		(n) => {
			if (n === 'fim') fimVolta = false;
			else if (n === 'filtro') confirmaFiltro = null;
			else if (n === 'saida') confirmaSaida = false;
			else if (n === 'zoom') zoomAberto = false;
		}
	);

	// a questão nova abria no meio da rolagem da anterior
	function topo() {
		window.scrollTo({ top: 0 });
	}
	let ultimoToque = $state(0);
	let refTema = $state(null);
	let refSaida = $state(null);

	$effect(() => {
		if (!carregou || !banco.length) return;
		const m = revisao ? 'rev' : 'nor';
		if (prontoModo === m) return;
		const primeira = prontoModo === null;
		prontoModo = m;
		// A montagem inicial é do onMount. Antes este efeito rodava logo depois
		// dele, remontava a fila e o `montar()` apagava a sessão salva: o
		// "Continuar de onde parou?" nunca aparecia e o "Sair e salvar" se
		// perdia ao voltar para /treino/.
		if (primeira) return;
		// Remonta nos DOIS sentidos. Antes só o modo revisão remontava: sair
		// dela pela aba "Treino" trocava o título e a URL mas mantinha a fila
		// de revisão — e, se ela estava vazia, deixava a tela num "nada por
		// aqui" sem o botão de sair. Era justamente o caminho de recuperação
		// que não funcionava.
		escolha = false;
		encerrada = false;
		filtro = 'todos';
		iniciar();
	});

	let revisao = $derived($page.url.searchParams.get('modo') === 'revisao');
	// O filtro é por MATÉRIA, não por tema. No banco cada questão tem um tema
	// próprio, então filtrar por tema devolvia sempre UMA questão — o controle
	// mais visível da tela não filtrava nada. As matérias são as 20 áreas da
	// Portaria + as de Formação Geral (`materias.json`), na ordem do inciso;
	// matéria sem questão nenhuma fica fora do select em vez de levar a uma
	// fila vazia.
	let gruposFiltro = $derived.by(() => {
		const n = new Map();
		for (const q of banco) n.set(materia(q), (n.get(materia(q)) || 0) + 1);
		return GRUPOS_MATERIA.map((g) => ({
			rotulo: g.rotulo,
			materias: g.materias.filter((m) => n.get(m.id)).map((m) => ({ ...m, n: n.get(m.id) }))
		})).filter((g) => g.materias.length);
	});

	// contadores derivados do log — assim navegar para frente/voltar nunca conta duas vezes
	let feitas = $derived(log.filter((r) => !r.pulada).length);
	let certas = $derived(log.filter((r) => r.certa).length);
	let ultima = $derived(i + 1 >= fila.length);
	let podeAvancar = $derived(!!respostas[i]);
	// estatísticas só da volta atual, para o aviso de fim de volta
	let resumoVolta = $derived.by(() => {
		const l = log.filter((r) => (r.volta ?? 0) === volta);
		return {
			feitas: l.filter((r) => !r.pulada).length,
			certas: l.filter((r) => r.certa).length,
			puladas: l.filter((r) => r.pulada).length
		};
	});

	onMount(async () => {
		try {
			({ questoes: banco, completo: bancoInteiro } = await carregarBancoDetalhado());
			xp = getXP();
		} catch {
			falhou = true;
		} finally {
			carregou = true;
		}
		iniciar();
	});

	// Com treino pausado, pergunta se continua; sem, monta uma fila nova.
	// Serve ao carregar a página e ao trocar entre treino e revisão.
	function iniciar() {
		sessaoGuardada = false;
		const s = carregarSessao();
		if (!revisao && s?.ids?.length) {
			const achadas = s.ids.map((id) => banco.find((q) => q.id === id));
			// Banco pela metade: a questão que falta pode estar no JSON que não
			// chegou. Antes a sessão voltava encurtada em silêncio, e a primeira
			// resposta regravava a versão curta por cima da inteira. Agora fica
			// guardada e a tela pede para recarregar — sem montar() nenhum, que
			// apagaria a sessão.
			if (!bancoInteiro && !achadas.every(Boolean)) {
				sessaoGuardada = true;
				return;
			}
			// banco inteiro: o que falta saiu do banco — remonta reindexando o
			// que é guardado por posição (ver `remontarSessao`)
			const r = remontarSessao(s.ids, banco, s);
			if (r.fila.length) {
				salva = {
					...s,
					...r,
					certas: r.log.filter((x) => x.certa).length,
					feitas: r.log.filter((x) => !x.pulada).length
				};
				escolha = true;
				return;
			}
		}
		montar();
	}

	$effect(() => {
		if (confirmaFiltro && refTema) refTema.focus();
	});
	$effect(() => {
		if (confirmaSaida && refSaida) refSaida.focus();
	});

	function materia(q) {
		return q.materia || 'formacao-geral';
	}

	function base() {
		let lista = revisao ? banco.filter((q) => getParaRevisar().includes(q.id)) : banco;
		if (filtro !== 'todos') lista = lista.filter((q) => materia(q) === filtro);
		return lista;
	}

	/**
	 * Poe a questao escolhida na busca na posicao ATUAL da fila, sem perder o
	 * resto: ela sai de onde estava (se estava) e entra em `i`. O resto da fila
	 * mantem a ordem relativa.
	 *
	 * `respostas` e indexado por posicao, entao inserir no meio desalinha tudo
	 * a frente — o que e seguro aqui porque `respostas` so serve para reexibir
	 * ao voltar; o que alimenta XP e historico e o `log`. Corta da posicao
	 * atual em diante para nao mostrar a resposta de outra questao.
	 */
	function pularPara(id) {
		if (revisao) {
			// em revisao a fila e so o que foi marcado: pular para fora dela
			// criaria uma questao que nao entrou no modo
			const q = banco.find((x) => x.id === id);
			if (q && !fila.some((x) => x.id === id)) {
				fila = [q, ...fila];
				i = 0;
				respostas = [];
			}
			return;
		}
		const q = banco.find((x) => x.id === id);
		if (!q) return;
		const novaFila = fila.filter((x) => x.id !== id);
		novaFila.splice(Math.min(i, novaFila.length), 0, q);
		fila = novaFila;
		respostas = respostas.slice(0, i);
		escolha = false;
		fimVolta = false;
		persistir();
	}

	function montar(nova = true) {
		if (nova) {
			// a revisão não grava sessão — e não pode apagar o treino pausado
			if (!revisao) limparSessao();
			fila = embaralhar(base());
			i = 0;
			volta = 0;
			respostas = [];
			log = [];
			xpGanho = 0;
			inicio = Date.now();
			direcao = 0;
		} else if (salva) {
			fila = salva.fila;
			i = Math.min(salva.i ?? 0, fila.length - 1);
			volta = salva.volta ?? 0;
			respostas = Array.isArray(salva.respostas) ? salva.respostas : [];
			log = salva.log || [];
			xpGanho = salva.xpGanho || 0;
			inicio = salva.inicio || Date.now();
			// restaura também o filtro com que a sessão foi montada
			// sessão salva antes da troca de matérias guarda o nome do AVA
			// ("TELECOMUNICACOES"), que não filtra mais nada — volta a "todos"
			if (salva.filtro && (salva.filtro === 'todos' || materiaExiste(salva.filtro))) {
				filtro = salva.filtro;
				filtroAnterior = salva.filtro;
			}
		}
		xpPing = 0;
		escolha = false;
		encerrada = false;
		fimVolta = false;
	}

	function persistir() {
		if (revisao || !fila.length) return;
		salvarSessao({
			v: 2,
			i,
			volta,
			certas,
			feitas,
			filtro,
			ids: fila.map((q) => q.id),
			respostas,
			log,
			inicio,
			xpGanho
		});
	}

	function sair() {
		// em revisão nada é salvo; no treino normal, avisa antes de sair com progresso
		if (revisao || feitas === 0) {
			sairDaRota('/');
			return;
		}
		confirmaSaida = true;
	}

	function sairAgora() {
		persistir();
		sairDaRota('/');
	}

	// registra/atualiza uma resposta para (idx, volta) — reescrever evita contar duas vezes
	// quando o aluno pula e depois volta para responder a mesma questão
	function registrar(idx, dados) {
		const chave = (r) => `${r.volta ?? 0}:${r.idx ?? -1}`;
		const k = `${volta}:${idx}`;
		log = [...log.filter((r) => chave(r) !== k), { idx, volta, ...dados }];
	}

	function aoResponder(r) {
		const q = fila[i];
		// histórico persistente — sem esta chamada o módulo de progresso
		// escrevia em vazio e a home mostrava zeros para sempre
		registrarResposta({
			id: r.id,
			certa: !!r.certa,
			parcial: !!r.parcial,
			anulada: !!r.anulada,
			materia: q?.materia,
			tema: q?.tema,
			duracaoMs: Date.now() - (ultimoToque || inicio)
		});
		ultimoToque = Date.now();
		// guarda também `respondida: true` para o Questao reexibir o veredito ao voltar
		respostas[i] = { ...r, respondida: true };
		registrar(i, {
			id: r.id,
			materia: q?.materia || '?',
			certa: !!r.certa,
			parcial: !!r.parcial,
			anulada: !!r.anulada,
			pulada: false
		});
		if (r.anulada) {
			// ponto para todos: conta como acerto, mas não rende XP (não houve mérito)
		} else if (r.certa) {
			somarXP(10);
			xp = getXP();
			xpGanho += 10;
			xpPing++;
			xpValor = 10;
			removerErro(r.id);
		} else if (r.parcial) {
			somarXP(5);
			xp = getXP();
			xpGanho += 5;
			xpPing++;
			xpValor = 5;
		} else {
			registrarErro(r.id);
		}
		persistir();
	}

	function aoPular(id) {
		const q = fila[i];
		// pular não é erro: só marca como vista e avança
		respostas[i] = { id, pulada: true };
		registrar(i, {
			id,
			materia: q?.materia || '?',
			certa: false,
			parcial: false,
			anulada: false,
			pulada: true
		});
		avancar();
	}

	function aoRevisar(id, marcado) {
		// Bucket próprio: "marcar para rever" e "errar" são fatos diferentes,
		// e guardar os dois na mesma lista fazia o aluno desmarcar uma questão
		// errada e ela sumir da revisão de erros.
		if (marcado) marcarRevisar(id);
		else desmarcarRevisar(id);
	}

	function avancar() {
		xpPing = 0;
		direcao = 1;
		topo();
		if (ultima) {
			// fim da fila: avisa em vez de dar a volta em silêncio
			fimVolta = true;
			persistir();
			return;
		}
		i++;
		persistir();
	}

	function voltar() {
		if (i === 0) return;
		xpPing = 0;
		direcao = -1;
		topo();
		i--;
		persistir();
	}

	function continuarVolta() {
		direcao = 1;
		topo();
		volta++;
		i = 0;
		respostas = [];
		fimVolta = false;
		persistir();
	}

	function encerrar() {
		// encerrar a revisão não encerra o treino pausado
		if (!revisao) limparSessao();
		encerrada = true;
		// fecha a sessão no histórico: sem isso a home nunca sabe que a
		// pessoa estudou, mesmo tendo respondido 40 questões
		if (feitas > 0) {
			registrarSessao({
				modo: revisao ? 'revisao' : 'treino',
				nivel: null,
				respondidas: feitas,
				certas,
				duracaoMs: Date.now() - inicio
			});
		}
	}

	// troca de filtro nunca descarta trabalho em silêncio: pede confirmação
	function aoTrocarFiltro() {
		if (feitas === 0) {
			filtroAnterior = filtro;
			montar();
			return;
		}
		confirmaFiltro = filtro;
		filtro = filtroAnterior; // devolve o select ao filtro em vigor até confirmar
	}

	function aplicarTema() {
		if (!confirmaFiltro) return;
		filtro = confirmaFiltro;
		filtroAnterior = confirmaFiltro;
		confirmaFiltro = null;
		montar();
	}

	function ehCampo(t) {
		return (
			t instanceof HTMLElement &&
			(t.isContentEditable || ['INPUT', 'TEXTAREA', 'SELECT'].includes(t.tagName))
		);
	}

	function aoTecla(e) {
		if (e.metaKey || e.ctrlKey || e.altKey) return;
		if (ehCampo(e.target)) return;
		if (e.key === 'Escape') {
			if (confirmaFiltro) {
				confirmaFiltro = null;
				return;
			}
			if (confirmaSaida) {
				confirmaSaida = false;
				return;
			}
			if (fimVolta) {
				fimVolta = false;
				return;
			}
			if (zoomAberto) return; // deixa o Esc fechar o zoom da figura
			if (escolha || encerrada) return; // fora da sessão não há o que encerrar
			sair();
			return;
		}
		if (confirmaSaida || confirmaFiltro || fimVolta || escolha || encerrada || zoomAberto) return;
		if (e.key === 'ArrowLeft') {
			e.preventDefault();
			voltar();
			return;
		}
		if (e.key === 'ArrowRight' || e.key === 'Enter') {
			// com foco num botão/link, deixa a ativação nativa cuidar (evita avançar 2x)
			if (e.key === 'Enter' && e.target instanceof HTMLElement && ['BUTTON', 'A'].includes(e.target.tagName))
				return;
			if (!podeAvancar) return;
			e.preventDefault();
			avancar();
		}
	}

	function mmss() {
		const s = Math.floor((Date.now() - inicio) / 1000);
		return `${String(Math.floor(s / 60)).padStart(2, '0')}:${String(s % 60).padStart(2, '0')}`;
	}

	function porMateria() {
		const mapa = new Map();
		for (const r of log) {
			if (r.pulada || !r.materia) continue;
			if (!mapa.has(r.materia)) mapa.set(r.materia, { n: 0, ok: 0 });
			const m = mapa.get(r.materia);
			m.n++;
			if (r.certa) m.ok++;
		}
		return [...mapa.entries()].sort((a, b) => b[1].n - a[1].n).slice(0, 3);
	}

	function bolinha(k) {
		if (k === i) return 'bg-accent';
		const r = respostas[k];
		if (r?.pulada) return 'bg-track';
		if (r?.certa) return 'bg-ok-solid';
		if (r) return 'bg-bad-solid';
		return 'bg-line';
	}
</script>

<svelte:window onkeydown={aoTecla} />

<div class="mx-auto w-full max-w-3xl" style="padding-bottom: calc(1rem + env(safe-area-inset-bottom));">
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
{:else if sessaoGuardada}
	<div class="rounded-3xl bg-card p-6 text-center shadow-sm" role="alert">
		<p class="font-display text-lg font-bold">Parte das questões não carregou</p>
		<p class="mt-1 text-sm text-ink-soft">
			Seu treino pausado continua guardado neste aparelho. Verifique a conexão e tente de novo para continuar.
		</p>
		<button type="button" onclick={() => location.reload()} class="btn3d duo-accent mt-4 w-full rounded-2xl p-3.5 font-bold">
			Tentar de novo
		</button>
	</div>
{:else if escolha && salva}
	<div class="rise rounded-3xl bg-card p-6 text-center shadow-[0_10px_30px_-12px_rgba(20,33,61,0.25)]">
		<p class="text-label font-bold text-ink-soft">Sessão pausada</p>
		<h2 class="mt-1 font-display text-2xl font-extrabold tracking-tight">Continuar de onde parou?</h2>
		<p class="nums mt-2 text-sm text-ink-soft">
			Questão {salva.i + 1} · {salva.certas}/{salva.feitas} certas{salva.filtro && salva.filtro !== 'todos' ? ` · ${nomeMateria(salva.filtro)}` : ''}
		</p>
		{#if salva.removidas}
			<p class="nums mt-1 text-xs font-semibold text-ink-soft">
				{salva.removidas} {salva.removidas === 1 ? 'questão saiu' : 'questões saíram'} do banco desde a pausa.
			</p>
		{/if}
		<button type="button" onclick={() => montar(false)} class="btn3d duo-accent mt-4 flex w-full items-center justify-center gap-2 rounded-[14px] p-3.5 font-display text-lg font-bold">
			<Play size={20} weight="fill" aria-hidden="true" /> Continuar sessão
		</button>
		<button type="button" onclick={() => montar()} class="mt-2 w-full rounded-[14px] border-2 border-line bg-card p-3.5 font-display text-lg font-bold">
			Nova sessão
		</button>
	</div>
{:else if encerrada}
	<div class="blueprint faixa px-4 pt-8 pb-10 text-center text-white">
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
			<p class="text-xs font-semibold text-ink-soft">Precisão</p>
		</div>
		<div class="rounded-2xl bg-card p-3 shadow-sm">
			<p class="nums flex items-center justify-center gap-1 text-xl font-extrabold"><Timer size={17} weight="bold" class="text-accent" aria-hidden="true" />{mmss()}</p>
			<p class="text-xs font-semibold text-ink-soft">Tempo</p>
		</div>
		<div class="rounded-2xl bg-card p-3 shadow-sm">
			<p class="nums flex items-center justify-center gap-1 text-xl font-extrabold"><Lightning size={17} weight="fill" class="text-accent" aria-hidden="true" />+{xpGanho}</p>
			<p class="text-xs font-semibold text-ink-soft">XP ganho</p>
		</div>
	</div>
	{#if porMateria().length}
		<div class="mt-3 rounded-3xl bg-card p-5 shadow-sm">
			<p class="font-display text-lg font-bold">Desempenho por matéria</p>
			<div class="mt-3 space-y-3">
				{#each porMateria() as [m, d] (m)}
					<div>
						<div class="flex items-baseline justify-between gap-3 text-sm">
							<p class="truncate font-semibold">{nomeMateria(m)}</p>
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
				Revisar erros e marcadas ({contarParaRevisar(banco)})
			</a>
		{/if}
	</div>
{:else}
	<SessaoTopo
		titulo={revisao ? 'Revisar erros' : `${i + 1}ª questão`}
		detalhe={revisao
			? `${certas}/${feitas}`
			: `${certas}/${feitas} certas${volta > 0 ? ` · volta ${volta + 1}` : ''}`}
		progresso={fila.length ? (i + 1) / fila.length : 0}
		{xp}
		aoFechar={sair}
	/>
	{#if !fila.length}
		<div class="mt-6 rounded-3xl bg-card p-6 text-center shadow-sm">
			<p class="font-display text-lg font-bold">Nada por aqui</p>
			<p class="mt-1 text-sm text-ink-soft">
				{revisao ? 'Sem erros acumulados — quando errar, a questão aparece aqui.' : 'Nenhuma questão nesta matéria.'}
			</p>
			<div class="mt-4 flex w-full flex-col gap-2">
				{#if revisao}
					<a href="/treino/" class="btn3d duo-accent flex w-full items-center justify-center rounded-[14px] p-3.5 font-display text-lg font-bold">
						Treinar tudo
					</a>
				{:else if filtro !== 'todos'}
					<button
						type="button"
						onclick={() => {
							confirmaFiltro = null;
							filtro = 'todos';
							montar();
						}}
						class="flex w-full items-center justify-center rounded-[14px] border-2 border-line bg-card p-3.5 font-display text-lg font-bold"
					>
						Ver todas as matérias
					</button>
				{/if}
				<a href="/estudo/" class="flex w-full items-center justify-center rounded-[14px] p-3 text-sm font-bold text-ink-soft">
					Estudo por níveis
				</a>
			</div>
		</div>
	{:else}
		<!-- Busca: campo fixo no topo, acima do filtro de materia. Some quando a
		     sessao acabou ou esta pausada — nesses estados nao ha fila para pular. -->
		<div class="relative mt-4 mb-3">
			<BuscaQuestoes {banco} aoPular={pularPara} />
		</div>
		<div class="mt-4 mb-3 flex items-center gap-2">
			<label class="flex flex-1 items-center gap-2 rounded-2xl border border-line bg-card px-3">
				<Tag size={17} weight="bold" class="shrink-0 text-ink-soft" aria-hidden="true" />
				<span class="sr-only">Filtrar por matéria</span>
				<select bind:value={filtro} onchange={aoTrocarFiltro} class="w-full bg-transparent py-3 text-sm font-semibold text-ink">
					<option value="todos">Todas as matérias</option>
					{#each gruposFiltro as g (g.rotulo)}
						<optgroup label={g.rotulo}>
							{#each g.materias as m (m.id)}
								<option value={m.id}>{m.nome} ({m.n})</option>
							{/each}
						</optgroup>
					{/each}
				</select>
			</label>
			<button
				type="button"
				onclick={encerrar}
				title="Encerrar sessão e ver o resumo"
				aria-label="Encerrar sessão e ver o resumo"
				class="nums flex min-h-11 items-center gap-1.5 rounded-2xl bg-card px-3 py-3 text-sm font-bold transition-transform active:scale-95"
			>
				<Flag size={16} weight="bold" class="text-accent" aria-hidden="true" />{certas}/{feitas}
			</button>
		</div>
		{#if fimVolta}
			<div class="rise rounded-3xl bg-card p-5 shadow-[0_10px_30px_-12px_rgba(20,33,61,0.25)]">
				<p class="text-label font-bold text-accent-ink">Volta {volta + 1} concluída</p>
				<h2 class="mt-1 font-display text-2xl font-extrabold tracking-tight">Você deu a volta na fila</h2>
				<p class="nums mt-2 text-sm text-ink-soft">
					Nesta volta: {resumoVolta.feitas} respondidas · {resumoVolta.certas} certas · {resumoVolta.puladas} puladas
				</p>
				{#if getErros().length}
					<p class="mt-2 text-sm text-ink-soft">Vale revisar os erros antes de encarar a fila de novo.</p>
				{/if}
				<div class="mt-4 space-y-2">
					<button
						type="button"
						onclick={continuarVolta}
						class="btn3d duo-accent flex w-full items-center justify-center gap-2 rounded-[14px] p-3.5 font-display text-lg font-bold"
					>
						<Play size={20} weight="fill" aria-hidden="true" /> Começar a volta {volta + 2}
					</button>
					{#if getErros().length}
						<a href="/treino/?modo=revisao" class="flex w-full items-center justify-center rounded-[14px] border-2 border-line bg-card p-3.5 font-display text-lg font-bold">
							Revisar erros e marcadas ({contarParaRevisar(banco)})
						</a>
					{/if}
					<button type="button" onclick={() => montar()} class="flex w-full items-center justify-center rounded-[14px] border-2 border-line bg-card p-3.5 font-display text-lg font-bold">
						Nova sessão embaralhada
					</button>
					<button type="button" onclick={() => (fimVolta = false)} class="w-full rounded-[14px] p-3 text-sm font-bold text-ink-soft">
						Voltar à última questão
					</button>
				</div>
			</div>
		{:else if fila[i]}
			<DicaGestos
				id="questoes"
				texto="Deslize a questão para os lados para passar ou voltar. Da borda da tela para o meio, você volta à tela anterior."
			/>
			<div
				{@attach deslizarQuestoes(() => ({
					anterior: i > 0,
					proxima: podeAvancar,
					onAnterior: voltar,
					onProxima: avancar
				}))}
			>
				{#key fila[i].id + '-' + volta + '-' + i}
					<div in:fly={{ x: 32 * direcao, duration: direcao ? DUR : 0 }}>
						<Questao
							q={fila[i]}
							onResponder={aoResponder}
							onPular={aoPular}
							onRevisar={aoRevisar}
							revisarInicial={getRevisar().includes(fila[i].id)}
							inicial={respostas[i]?.pulada ? null : (respostas[i] ?? null)}
							bind:zoomAberto
						/>
					</div>
				{/key}
			</div>
			<BarraAcao
				rotulo={ultima ? 'Concluir volta' : 'Próxima'}
				mostrarXP={xpPing > 0}
				xpValor={xpValor}
				desabilitado={!podeAvancar}
				aviso="Escolha uma alternativa para continuar — ou use Pular questão."
				onClick={avancar}
			>
				<nav class="flex items-center gap-2" aria-label="Navegação da sessão">
					<button
						type="button"
						onclick={voltar}
						disabled={i === 0}
						aria-label="Questão anterior"
						class="flex h-11 w-11 shrink-0 items-center justify-center rounded-full border border-line bg-card text-ink transition-transform active:scale-95 disabled:opacity-40"
					>
						<ArrowLeft size={20} weight="bold" aria-hidden="true" />
					</button>
					<p class="nums flex-1 text-center text-sm font-bold text-ink-soft" role="status" aria-live="polite">
						Questão {i + 1} de {fila.length}{volta > 0 ? ` · volta ${volta + 1}` : ''}
					</p>
					<span class="h-11 w-11 shrink-0" aria-hidden="true"></span>
				</nav>
				{#if fila.length <= 12}
					<div class="mt-1.5 flex justify-center gap-1" aria-hidden="true">
						{#each fila as _q, k (k)}
							<span class="h-1.5 w-2.5 rounded-full {bolinha(k)}"></span>
						{/each}
					</div>
				{/if}
			</BarraAcao>
		{/if}
	{/if}
{/if}

	{#if confirmaFiltro}
		<div class="fixed inset-0 z-50 flex items-end justify-center p-4 sm:items-center">
			<button
				type="button"
				onclick={() => (confirmaFiltro = null)}
				aria-label="Fechar e manter a matéria atual"
				class="absolute inset-0 cursor-default bg-black/50"
			></button>
			<div
				role="dialog"
				aria-modal="true"
				aria-labelledby="confirma-filtro-titulo"
				class="relative w-full max-w-sm rounded-3xl bg-card p-5 shadow"
			>
				<h2 id="confirma-filtro-titulo" class="font-display text-xl font-extrabold tracking-tight">Trocar de filtro?</h2>
				<p class="mt-1 text-sm text-ink-soft">
					Você já respondeu {feitas} {feitas === 1 ? 'questão' : 'questões'}. Trocar a matéria reinicia a fila e o placar.
				</p>
				<div class="mt-4 space-y-2">
					<button
						type="button"
						bind:this={refTema}
						onclick={aplicarTema}
						class="btn3d duo-accent w-full rounded-[14px] p-3.5 font-display text-base font-bold"
					>
						Trocar e reiniciar
					</button>
					<button
						type="button"
						onclick={() => (confirmaFiltro = null)}
						class="w-full rounded-[14px] border-2 border-line bg-card p-3 font-display text-base font-bold"
					>
						Manter o filtro atual
					</button>
				</div>
			</div>
		</div>
	{/if}

	{#if confirmaSaida}
		<div class="fixed inset-0 z-50 flex items-end justify-center p-4 sm:items-center">
			<button
				type="button"
				onclick={() => (confirmaSaida = false)}
				aria-label="Fechar e continuar treinando"
				class="absolute inset-0 cursor-default bg-black/50"
			></button>
			<div
				role="dialog"
				aria-modal="true"
				aria-labelledby="confirma-saida-titulo"
				class="relative w-full max-w-sm rounded-3xl bg-card p-5 shadow"
			>
				<h2 id="confirma-saida-titulo" class="font-display text-xl font-extrabold tracking-tight">Sair da sessão?</h2>
				<p class="mt-1 text-sm text-ink-soft">
					Seu progresso ({feitas} respondidas) fica salvo para continuar depois.
				</p>
				<div class="mt-4 space-y-2">
					<button
						type="button"
						bind:this={refSaida}
						onclick={sairAgora}
						class="btn3d duo-accent w-full rounded-[14px] p-3.5 font-display text-base font-bold"
					>
						Sair e salvar
					</button>
					<button
						type="button"
						onclick={() => (confirmaSaida = false)}
						class="w-full rounded-[14px] border-2 border-line bg-card p-3 font-display text-base font-bold"
					>
						Continuar treinando
					</button>
				</div>
			</div>
		</div>
	{/if}
</div>
