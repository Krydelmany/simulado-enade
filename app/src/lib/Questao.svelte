<script>
	import { fly } from 'svelte/transition';
	import { ehGerada, rotuloQuestao } from './banco.js';
	import { nomeMateria } from './materias.js';
	import { DUR, REDUCED } from './motion.js';
	import {
		ArrowRight,
		Atom,
		BookmarkSimple,
		CaretDown,
		Check,
		CheckCircle,
		Copy,
		Image as ImageIcon,
		Info,
		MagnifyingGlassPlus,
		MinusCircle,
		Robot,
		SealCheck,
		SkipForward,
		UserCircle,
		Warning,
		WarningCircle,
		X,
		XCircle
	} from 'phosphor-svelte';
	import { nuvemLigada, reportarQuestao, MOTIVOS_REPORTE } from './nuvem.js';
	import SeloSequencia from './SeloSequencia.svelte';
	import TextoRico from './TextoRico.svelte';
	import { copiarQuestao } from './copiar.js';
	import { carregarResolucoes, rotuloAutoria } from './resolucoes.js';

	/**
	 * `inicial` restaura o estado de uma questão já respondida quando o aluno volta
	 * a ela (navegação anterior/seguinte) — vem do mapa `respostas` da página.
	 *
	 * Contrato ÚNICO de resposta para os dois modos (treino e estudo):
	 *   { id, certa, parcial?, anulada? }   (+ escolha/mostrouPadrao/auto, para restaurar a UI)
	 *
	 * `prova` é o cartão-resposta do simulado: marcar não corrige — a letra
	 * fica marcada, pode ser trocada ou desmarcada (`onMarcar(id, letra|null)`),
	 * e a discursiva vira um campo de texto (`onRascunho`). A correção só
	 * aparece depois da entrega, com esta mesma questão fora do modo prova e
	 * `respostaAluno` mostrando o que o aluno escreveu.
	 *
	 * Fora do modo `prova`, objetivas seguem um botão principal único:
	 *   Selecionar alternativa → Verificar resposta → Veredito + Continuar (acima de "Como resolver").
	 *
	 * `atalhos`: `true` (padrão na questão única), `false` (quando há modal/camada
	 * aberta na rota — impede marcar/verificar por trás do overlay) ou `'foco'`
	 * (em listas com várias questões simultâneas, como o Guia — só reage quando o
	 * foco do teclado está dentro deste cartão).
	 */
	let {
		q,
		onResponder = null,
		onPular = null,
		onRevisar = null,
		revisarInicial = false,
		inicial = null,
		prova = false,
		onMarcar = null,
		rascunhoInicial = '',
		onRascunho = null,
		respostaAluno = '',
		// a resolução abre sozinha depois da resposta no treino e no estudo;
		// na correção do simulado ela vem fechada, a um toque
		resolucaoAberta = true,
		atalhos = true,
		// ação única de avanço/volta no Treino e no Estudo (perto do feedback,
		// acima de "Como resolver" — evita dois botões grandes na mesma tela)
		onContinuar = null,
		rotuloContinuar = 'Continuar',
		podeContinuarSemResponder = false,
		onAnterior = null,
		anteriorDesabilitado = false,
		mostrarXP = false,
		xpValor = 10,
		// acertos seguidos na sessão (Treino e Estudo); a partir de 3 vira selo
		sequencia = 0,
		selecaoPendente = $bindable(false),
		zoomAberto = $bindable(false),
		reporteAberto = $bindable(false)
	} = $props();

	// lê o estado inicial DENTRO de uma função: é intencional capturar uma vez
	// (o componente é remontado por questão via {#key}) e evita o aviso do compilador
	function estadoInicial() {
		return {
			escolha: inicial?.escolha ?? null,
			respondida: !!inicial?.respondida,
			mostrouPadrao: !!inicial?.mostrouPadrao,
			auto: inicial?.auto ?? null, // discursiva: 'certa' | 'parcial' | 'errada'
			revisar: !!revisarInicial,
			rascunho: rascunhoInicial || ''
		};
	}
	const ini = estadoInicial();
	let rascunho = $state(ini.rascunho);

	let escolha = $state(ini.escolha);
	let selecionada = $state(ini.respondida ? ini.escolha : null);
	let respondida = $state(ini.respondida);
	let mostrouPadrao = $state(ini.mostrouPadrao);
	let auto = $state(ini.auto);
	let revisar = $state(ini.revisar);
	// só rola/foca o veredito quando o aluno ACABOU de responder — nunca ao restaurar
	let avaliadaAgora = $state(false);
	let veredito = $state(null);
	let artigo = $state(null);

	// expõe seleção ainda não verificada para a rota bloquear Enter, Continuar
	// e deslize quando o aluno volta numa questão pulada e marca uma alternativa
	$effect(() => {
		selecaoPendente = !prova && q.tipo === 'objetiva' && !respondida && selecionada !== null;
		return () => {
			selecaoPendente = false;
		};
	});

	// "Como resolver": só depois da resposta (ou, na discursiva, depois de ver
	// o padrão) e nunca na prova do simulado
	const podeResolver = $derived(!prova && (respondida || mostrouPadrao));
	let resolucao = $state(null); // null = ainda não carregou, ou a questão não tem
	// lido uma vez, como `inicial`: a questão é remontada a cada troca ({#key})
	// svelte-ignore state_referenced_locally
	let resolucaoVisivel = $state(resolucaoAberta);
	$effect(() => {
		if (!podeResolver || resolucao) return;
		let vivo = true;
		carregarResolucoes().then((mapa) => {
			if (vivo) resolucao = mapa[q.id] ?? null;
		});
		return () => {
			vivo = false;
		};
	});

	const LETRAS = ['A', 'B', 'C', 'D', 'E'];
	const FAISCAS = [
		{ x: '-16px', y: '-14px', cor: 'bg-ok-solid' },
		{ x: '16px', y: '-14px', cor: 'bg-milestone' },
		{ x: '-20px', y: '4px', cor: 'bg-accent' },
		{ x: '20px', y: '4px', cor: 'bg-ok-solid' },
		{ x: '0px', y: '-20px', cor: 'bg-milestone' }
	];

	const anulada = $derived(q.gabarito === 'ANULADA');
	const acertou = $derived(respondida && !anulada && escolha === q.gabarito);

	// categoria do veredito — dirige cor e ícone num só lugar
	const categoria = $derived(
		!respondida
			? null
			: anulada
				? 'anulada'
				: auto
					? auto
					: acertou
						? 'certa'
						: q.tipo === 'objetiva' && !escolha
							? 'branco' // correção do simulado: questão sem marcação
							: 'errada'
	);

	function escolher(letra) {
		if (respondida) return;
		if (prova) {
			// cartão-resposta: marca, troca ou desmarca — nada de veredito
			escolha = escolha === letra ? null : letra;
			onMarcar?.(q.id, escolha);
			return;
		}
		selecionada = letra;
	}

	function verificar() {
		if (prova || respondida || !selecionada) return;
		escolha = selecionada;
		respondida = true;
		avaliadaAgora = true;
		// questão anulada = ponto para todos: qualquer alternativa conta como acerto
		const certa = anulada || escolha === q.gabarito;
		onResponder?.({ id: q.id, certa, anulada, escolha });
	}

	function autoavaliar(nivel) {
		if (respondida) return;
		respondida = true;
		avaliadaAgora = true;
		mostrouPadrao = true;
		auto = nivel === 1 ? 'certa' : nivel === 0.5 ? 'parcial' : 'errada';
		onResponder?.({
			id: q.id,
			certa: nivel === 1,
			parcial: nivel === 0.5,
			escolha: null,
			mostrouPadrao: true,
			auto
		});
	}

	function pular() {
		if (respondida) return;
		onPular?.(q.id);
	}

	// 'ok' | 'erro' por 2 s depois de copiar; o ícone e o aviso mudam juntos
	let copia = $state(null);
	let timerCopia;
	async function copiar() {
		const ok = await copiarQuestao(q);
		copia = ok ? 'ok' : 'erro';
		clearTimeout(timerCopia);
		timerCopia = setTimeout(() => (copia = null), 2000);
	}
	$effect(() => () => clearTimeout(timerCopia));

	function alternarRevisar() {
		revisar = !revisar;
		onRevisar?.(q.id, revisar);
	}

	// teclado nunca deve sequestrar quem está digitando num campo
	function ehCampo(t) {
		return (
			t instanceof HTMLElement &&
			(t.isContentEditable || ['INPUT', 'TEXTAREA', 'SELECT'].includes(t.tagName))
		);
	}

	function aoTecla(e) {
		if (e.defaultPrevented) return;
		// com a imagem ampliada, o Esc só fecha o zoom (a página ignora via `zoomAberto`)
		if (zoomAberto) {
			if (e.key === 'Escape') {
				e.preventDefault();
				zoomAberto = false;
			}
			return;
		}
		// com o formulário de reporte aberto, o primeiro Esc fora de campo fecha
		// só o painel (sem apagar o texto digitado nem encerrar a sessão)
		if (reporteAberto) {
			if (e.key === 'Escape' && !ehCampo(e.target)) {
				e.preventDefault();
				reporteAberto = false;
			}
			return;
		}
		// com camada/modal aberta na rota (ou atalho desligado), ignora o teclado
		if (!atalhos) return;
		if (atalhos === 'foco' && (!artigo || !artigo.contains(document.activeElement))) return;
		if (e.metaKey || e.ctrlKey || e.altKey || e.repeat) return;
		if (ehCampo(e.target)) return;
		if (q.tipo !== 'objetiva' || respondida) return;

		// Atalho silencioso: Enter verifica a alternativa selecionada (fora do modo prova).
		// Se o foco estiver na própria alternativa já selecionada (caso clique + Enter),
		// verifica imediatamente; em links, resumos ou outros botões, deixa o nativo agir.
		if (e.key === 'Enter' && !prova && selecionada) {
			const alvo = e.target instanceof Element ? e.target : null;
			const altFocada = alvo?.closest('button[data-alt-letra]');
			const naSelecionada = altFocada?.getAttribute('data-alt-letra') === selecionada;
			if (!naSelecionada && alvo?.closest('a, button, summary, [role="button"]')) return;
			e.preventDefault();
			verificar();
			return;
		}

		// atalhos de cartão-resposta: A–E ou 1–5
		const mapa = {
			a: 'A',
			b: 'B',
			c: 'C',
			d: 'D',
			e: 'E',
			'1': 'A',
			'2': 'B',
			'3': 'C',
			'4': 'D',
			'5': 'E'
		};
		const letra = mapa[String(e.key).toLowerCase()];
		// `alternativas_visuais` entra junto: as letras existem, só não têm
		// texto — sem isso o teclado não responderia essas questões.
		if (letra && (q.alternativas[letra] || q.alternativas_visuais)) {
			e.preventDefault();
			escolher(letra);
		}
	}

	// `zoomAberto` é a FONTE do zoom (não um espelho): a página precisa
	// fechá-lo pelo voltar do sistema (ver `camadas.svelte.js`), e lê o mesmo
	// valor para o Esc não encerrar a sessão junto. Ao desmontar, fecha ambos.
	$effect(() => () => {
		zoomAberto = false;
		reporteAberto = false;
	});

	$effect(() => {
		document.body.style.overflow = zoomAberto ? 'hidden' : '';
		return () => {
			document.body.style.overflow = '';
		};
	});

	// ao responder, garante que o veredito E o botão Continuar logo abaixo fiquem visíveis na tela
	$effect(() => {
		if (!avaliadaAgora || !veredito) return;
		const r = veredito.getBoundingClientRect();
		const barra = artigo?.querySelector('[data-barra-acao]');
		const rb = barra?.getBoundingClientRect();
		const h = window.innerHeight || 0;
		const baixo = Math.max(r.bottom, rb?.bottom ?? r.bottom);
		const fora = r.top < 8 || baixo > h - 12;
		veredito.focus({ preventScroll: true });
		if (fora) {
			(rb && rb.bottom > h - 12 ? barra : veredito).scrollIntoView({
				block: 'center',
				behavior: REDUCED ? 'auto' : 'smooth'
			});
		}
	});

	// leitor de tela: a alternativa sem as marcas de bloco de código
	const MARCA_BLOCO = new RegExp('\x60{3}\\w*\\n?', 'g');
	function rotuloAlt(letra) {
		const texto = q.alternativas[letra];
		if (!texto) return 'Alternativa ' + letra + ' (na imagem)';
		return 'Alternativa ' + letra + ': ' + texto.replace(MARCA_BLOCO, '');
	}

	// Reportar erro (D13): abre no próprio cartão, sem modal — um modal seria
	// mais uma camada para o voltar do sistema em três rotas. `reporteAberto`
	// é `$bindable` para o Esc da rota não sair da sessão enquanto está aberto.
	let motivo = $state('');
	let detalhe = $state('');
	let reporte = $state(''); // '' | 'enviando' | 'ok'
	let erroReporte = $state('');

	async function enviarReporte(ev) {
		ev.preventDefault();
		if (!motivo || reporte === 'enviando') return;
		erroReporte = '';
		reporte = 'enviando';
		try {
			await reportarQuestao({ questaoId: q.id, motivo, detalhe });
			reporte = 'ok';
			reporteAberto = false;
		} catch (e) {
			reporte = '';
			erroReporte = e.message;
		}
	}

	function classeAlt(letra) {
		const base =
			'flex w-full items-start gap-3.5 rounded-2xl border-2 px-4 py-3.5 text-left text-[15px] leading-relaxed transition-[border-color,background-color,color,transform,opacity] duration-150 active:scale-[0.992] disabled:cursor-default ';
		// marcação no acento do curso; verde/vermelho ficam só para a correção
		if (prova) {
			return (
				base +
				(letra === escolha
					? 'border-accent bg-accent-soft text-ink'
					: 'border-line bg-card text-ink hover:border-line-strong hover:bg-panel/60')
			);
		}
		if (!respondida) {
			return (
				base +
				(letra === selecionada
					? 'border-accent bg-accent-soft text-ink pop'
					: 'border-line bg-card text-ink hover:border-line-strong hover:bg-panel/60')
			);
		}
		if (anulada) return base + 'border-line bg-panel text-ink';
		if (letra === q.gabarito) return base + 'border-ok-solid bg-ok-bg text-ink pop';
		if (letra === escolha) return base + 'border-bad-solid bg-bad-bg text-ink';
		return base + 'border-line bg-card text-ink opacity-50';
	}

	function classeBolha(letra) {
		// bolha de cartão-resposta: preenche no acento ao marcar/selecionar
		const base =
			'flex h-8 w-8 shrink-0 items-center justify-center rounded-full border-2 font-display text-sm font-bold transition-colors duration-150 ';
		if (prova) {
			return (
				base +
				(letra === escolha
					? 'border-accent bg-accent text-accent-on'
					: 'border-line-strong bg-panel text-ink-soft')
			);
		}
		if (!respondida) {
			return (
				base +
				(letra === selecionada
					? 'border-accent bg-accent text-accent-on'
					: 'border-line-strong bg-panel text-ink-soft')
			);
		}
		if (anulada) {
			return letra === escolha
				? base + 'border-warn-line bg-warn-line text-white'
				: base + 'border-line bg-tile text-ink-soft';
		}
		if (letra === q.gabarito) return base + 'border-ok-solid bg-ok-solid text-white';
		if (letra === escolha) return base + 'border-bad-solid bg-bad-solid text-white';
		return base + 'border-line bg-panel text-ink-soft';
	}
</script>

<svelte:window onkeydown={aoTecla} />

<article bind:this={artigo} class="folha rounded-3xl p-4 sm:p-6">
	<div class="flex flex-wrap items-center gap-2">
		<p class="text-label font-bold text-ink-soft">
			{rotuloQuestao(q)}
		</p>
		{#if q.materia}
			<p class="flex items-center gap-1 rounded-full bg-accent-soft px-2.5 py-0.5 text-xs font-bold text-accent-ink">
				<Atom size={12} weight="bold" aria-hidden="true" />
				{nomeMateria(q.materia)}
			</p>
		{/if}
		{#if ehGerada(q)}
			<!-- gerada não é prova: o que importa ao aluno é o nível, não a parte -->
			<p class="rounded-full border border-line bg-panel px-2.5 py-0.5 text-xs font-semibold text-ink-soft">
				Nível {q.dificuldade === 'Média' ? 'médio' : (q.dificuldade ?? '').toLowerCase()}
			</p>
		{:else if q.parte}
			<p class="rounded-full border border-line bg-panel px-2.5 py-0.5 text-xs font-semibold text-ink-soft">
				{q.parte === 'FG' ? 'Formação Geral' : q.parte}
			</p>
		{/if}
		<!-- os dois botões andam juntos: soltos, quando as etiquetas enchiam a
		     linha o de revisar caía sozinho para a esquerda da linha de baixo -->
		<div class="ml-auto flex items-center gap-1.5">
			<!-- copia enunciado, figura e alternativas (sem gabarito) para colar fora
			     do site. Fica fora da PROVA do simulado: lá ele facilitaria colar a
			     questão em outro lugar no meio do teste; na correção, depois da
			     entrega (a mesma questão sem `prova`), ele volta -->
			{#if !prova}
				<button
					type="button"
					onclick={copiar}
					aria-label="Copiar questão"
					title={copia === 'erro' ? 'O navegador não deixou copiar' : 'Copiar questão'}
					class="flex h-11 w-11 items-center justify-center rounded-full border border-line transition-colors active:scale-95 {copia ===
					'ok'
						? 'border-ok-border bg-ok-bg text-ok-fg'
						: copia === 'erro'
							? 'border-bad-border bg-bad-bg text-bad-fg'
							: 'bg-paper text-ink-soft hover:border-line-strong hover:text-ink'}"
				>
					{#if copia === 'ok'}
						<Check size={18} weight="bold" aria-hidden="true" />
					{:else if copia === 'erro'}
						<Warning size={18} weight="bold" aria-hidden="true" />
					{:else}
						<Copy size={18} weight="bold" aria-hidden="true" />
					{/if}
				</button>
				<span class="sr-only" role="status">
					{copia === 'ok' ? 'Questão copiada' : copia === 'erro' ? 'Não deu para copiar a questão' : ''}
				</span>
			{/if}
			<button
				type="button"
				onclick={alternarRevisar}
				aria-pressed={revisar}
				aria-label={revisar ? 'Remover marcação de revisar' : 'Marcar para revisar depois'}
				title={revisar ? 'Remover marcação de revisar' : 'Marcar para revisar depois'}
				class="flex h-11 w-11 items-center justify-center rounded-full border transition-colors active:scale-95 {revisar
					? 'border-milestone-border bg-milestone-soft text-milestone-ink'
					: 'border-line bg-paper text-ink-soft hover:border-line-strong hover:text-ink'}"
			>
				<BookmarkSimple size={18} weight={revisar ? 'fill' : 'bold'} aria-hidden="true" />
			</button>
		</div>
	</div>

	<h2 class="mt-2.5 font-display text-lg font-bold tracking-tight text-pretty text-ink">{q.tema}</h2>

	{#if q.imagem}
		<figure class="mt-4 overflow-hidden rounded-2xl border border-line bg-white">
			<button
				type="button"
				onclick={() => (zoomAberto = true)}
				aria-label="Ampliar figura: {q.imagem.alt}"
				class="block w-full cursor-zoom-in p-2"
			>
				<img
					src={q.imagem.src}
					alt={q.imagem.alt}
					loading="lazy"
					class="mx-auto h-auto max-h-[54vh] w-auto max-w-full"
				/>
			</button>
			<figcaption class="flex items-start gap-2 border-t border-line bg-panel px-3.5 py-2 text-xs text-ink-soft">
				<MagnifyingGlassPlus size={14} weight="bold" class="mt-0.5 shrink-0" aria-hidden="true" />
				<span>
					Toque para ampliar
					{#if q.imagem.legenda} · {q.imagem.legenda}{/if}
				</span>
			</figcaption>
		</figure>
		{#if zoomAberto}
			<div
				class="fixed inset-0 z-50 flex flex-col bg-black/90 p-4"
				style="padding-bottom: env(safe-area-inset-bottom);"
			>
				<button
					type="button"
					onclick={() => (zoomAberto = false)}
					aria-label="Fechar figura ampliada"
					class="absolute inset-0 cursor-zoom-out"
				></button>
				<div
					role="dialog"
					aria-modal="true"
					aria-label="Figura ampliada: {q.imagem.alt}"
					class="pointer-events-none relative flex min-h-0 flex-1 flex-col"
				>
					<img
						src={q.imagem.src}
						alt={q.imagem.alt}
						class="m-auto max-h-full max-w-full rounded-xl object-contain"
					/>
					<p class="pt-3 text-center text-sm font-semibold text-white/80">Toque para fechar</p>
				</div>
			</div>
		{/if}
	{:else if q.figura}
		<p class="mt-4 flex items-start gap-2 rounded-2xl border border-dashed border-warn-line bg-warn-bg p-3 text-sm text-warn-fg">
			<ImageIcon size={18} weight="bold" class="mt-0.5 shrink-0" aria-hidden="true" />
			<span>Figura: {q.figura.desc} <span class="italic">(imagem entra aqui)</span></span>
		</p>
	{/if}

	<div class="enunciado mt-4 max-w-[62ch] text-[15.5px] leading-[1.7] text-ink">
		<TextoRico texto={q.enunciado} />
	</div>

	{#if q.tipo === 'objetiva'}
		{#if anulada && !respondida}
			<p class="mt-4 flex items-start gap-2 rounded-2xl bg-warn-bg p-3.5 text-sm font-semibold text-warn-fg" role="note">
				<Info size={18} weight="bold" class="mt-0.5 shrink-0" aria-hidden="true" />
				<span>Questão anulada pelo INEP — qualquer alternativa marca o ponto.</span>
			</p>
		{/if}
		<div class="mt-5 space-y-2.5" role="group" aria-label="Alternativas">
			{#if q.alternativas_visuais}
				<!--
					Estas questões têm as opções A–E desenhadas dentro da figura
					(trecho de código, fórmula, diagrama): não há texto para cada
					alternativa. Sem um cartão por letra a questão ficava sem
					nenhum botão — o aluno via a imagem e não tinha como
					responder, e a sessão travava. Aqui cada letra vira um
					cartão-resposta sozinho, que é o que a prova pede.
				-->
				<p class="flex items-start gap-2 rounded-2xl border border-dashed border-line bg-panel p-3 text-sm text-ink-soft">
					<Info size={18} weight="bold" class="mt-0.5 shrink-0" aria-hidden="true" />
					<span>As alternativas estão na imagem. Marque a letra correspondente abaixo.</span>
				</p>
			{/if}
			{#each LETRAS as letra, k (letra)}
				{#if q.alternativas[letra] || q.alternativas_visuais}
					<div class="rise" style="animation-delay: {k * 30}ms">
						<button
							type="button"
							data-alt-letra={letra}
							onclick={() => escolher(letra)}
							disabled={respondida}
							aria-pressed={prova ? letra === escolha : !respondida ? letra === selecionada : undefined}
							aria-label={rotuloAlt(letra)}
							class={classeAlt(letra)}
						>
							<span class={classeBolha(letra)}>
								{#if respondida && !anulada && letra === q.gabarito}
									<Check size={16} weight="bold" aria-hidden="true" />
								{:else if respondida && !anulada && letra === escolha}
									<X size={16} weight="bold" aria-hidden="true" />
								{:else}
									{letra}
								{/if}
							</span>
							{#if q.alternativas[letra]?.includes('```')}
								<!-- alternativa que é código (2023-CE-Q15, Q30): bloco mono, como no enunciado -->
								<span class="min-w-0 flex-1"><TextoRico texto={q.alternativas[letra]} /></span>
							{:else if q.alternativas[letra]}
								<span class="enunciado min-w-0 flex-1">{q.alternativas[letra]}</span>
							{:else}
								<span class="text-sm font-semibold text-ink-soft">Alternativa {letra} da imagem</span>
							{/if}
						</button>
					</div>
				{/if}
			{/each}
		</div>

		<!-- Ação única antes da verificação (fora do modo prova): evita dois botões grandes na tela -->
		{#if !prova && !respondida}
			<div data-barra-acao class="mt-5 flex flex-col gap-2 sm:flex-row sm:items-center">
				{#if onAnterior}
					<button
						type="button"
						onclick={onAnterior}
						disabled={anteriorDesabilitado}
						class="btn-suave min-h-12 rounded-full px-5 font-display text-sm font-bold disabled:pointer-events-none disabled:opacity-40"
					>
						Anterior
					</button>
				{/if}
				{#if selecionada}
					<button
						type="button"
						onclick={verificar}
						class="btn-primario flex min-h-12 flex-1 items-center justify-center gap-2 rounded-full px-6 font-display text-base font-bold"
					>
						Verificar resposta ({selecionada})
					</button>
				{:else if podeContinuarSemResponder && onContinuar}
					<button
						type="button"
						onclick={onContinuar}
						class="btn-primario flex min-h-12 flex-1 items-center justify-center gap-2 rounded-full px-6 font-display text-base font-bold"
					>
						<span>{rotuloContinuar}</span>
						<ArrowRight size={17} weight="bold" aria-hidden="true" />
					</button>
				{:else}
					<button
						type="button"
						disabled
						class="flex min-h-12 flex-1 cursor-not-allowed items-center justify-center rounded-full border border-line bg-panel px-6 font-display text-base font-bold text-ink-soft"
					>
						Selecione uma alternativa
					</button>
				{/if}
				{#if onPular && !podeContinuarSemResponder}
					<button
						type="button"
						onclick={pular}
						class="btn-suave flex min-h-12 items-center justify-center gap-1.5 rounded-full px-5 text-sm font-bold text-ink-soft hover:text-ink"
					>
						<SkipForward size={16} weight="bold" aria-hidden="true" /> Pular
					</button>
				{/if}
			</div>
		{/if}
	{:else}
		<div class="mt-5">
			{#if prova}
				<!-- na prova o padrão não aparece: o aluno escreve, e a comparação vem na correção -->
				<label class="block">
					<span class="text-sm font-bold text-ink">Sua resposta</span>
					<span class="mt-0.5 block text-xs text-ink-soft">Fica só neste aparelho. Na correção, você compara com o padrão do INEP.</span>
					<textarea
						bind:value={rascunho}
						oninput={() => onRascunho?.(rascunho)}
						rows="12"
						class="mt-2 w-full rounded-2xl border-2 border-line bg-paper p-3.5 text-[15px] leading-relaxed text-ink focus:border-accent focus:outline-none"
					></textarea>
				</label>
			{:else}
				{#if respostaAluno}
					<div class="mb-3 rounded-2xl border border-line bg-panel p-4">
						<p class="text-label font-bold text-ink-soft">Sua resposta</p>
						<p class="enunciado mt-2 max-w-[60ch] text-sm leading-relaxed text-ink">{respostaAluno}</p>
					</div>
				{/if}
				{#if q.padrao_placeholder}
					<!--
						O gabarito desta discursiva é um desenho que o INEP publica
						como figura. Sem a figura, mostrar "padrão oficial" seria
						mostrar uma frase vazia — e pior, mandar o aluno se
						autoavaliar contra o vazio e dar nota de comparação com
						nada. Melhor dizer a verdade e deixar a autoavaliação de fora.
					-->
					<p class="flex items-start gap-2 rounded-2xl border border-dashed border-line bg-panel p-3.5 text-sm text-ink-soft">
						<Info size={18} weight="bold" class="mt-0.5 shrink-0" aria-hidden="true" />
						<span>
							O padrão oficial desta questão é um desenho que ainda não está no site. Escreva sua resposta no papel e confira com a apostila.
						</span>
					</p>
				{:else if !mostrouPadrao}
					<button
						type="button"
						onclick={() => (mostrouPadrao = true)}
						class="btn-primario flex min-h-12 w-full items-center justify-center rounded-full px-6 font-display text-base font-bold"
					>
						{q.fonte === 'guia' ? 'Escrevi minha resposta — ver modelo do guia' : 'Escrevi minha resposta — ver padrão oficial'}
					</button>
				{:else}
					<div in:fly={{ y: 8, duration: DUR }} class="rounded-2xl border border-line bg-panel p-4">
						<p class="flex items-center gap-1.5 text-label font-bold text-ink-soft">
							<SealCheck size={15} weight="bold" aria-hidden="true" />
							{q.fonte === 'guia' ? 'Modelo de resposta do guia' : 'Padrão de resposta do INEP'}
						</p>
						<p class="enunciado mt-2 max-w-[60ch] text-sm leading-relaxed text-ink"><TextoRico texto={q.padrao} /></p>
					</div>
					{#if !respondida}
						<p class="mt-4 text-sm font-bold text-ink">Compare com a sua. Como foi?</p>
						<div class="mt-2.5 grid grid-cols-3 gap-2">
							<button
								type="button"
								onclick={() => autoavaliar(1)}
								class="flex min-h-11 items-center justify-center gap-1.5 rounded-full bg-ok-solid px-3 py-2.5 text-sm font-bold text-white transition-transform active:scale-[0.98]"
							>
								<CheckCircle size={17} weight="bold" aria-hidden="true" /> Acertei
							</button>
							<button
								type="button"
								onclick={() => autoavaliar(0.5)}
								class="flex min-h-11 items-center justify-center gap-1.5 rounded-full border border-warn-line/50 bg-warn-bg px-3 py-2.5 text-sm font-bold text-warn-fg transition-transform active:scale-[0.98]"
							>
								<MinusCircle size={17} weight="bold" aria-hidden="true" /> Meio
							</button>
							<button
								type="button"
								onclick={() => autoavaliar(0)}
								class="flex min-h-11 items-center justify-center gap-1.5 rounded-full bg-bad-solid px-3 py-2.5 text-sm font-bold text-white transition-transform active:scale-[0.98]"
							>
								<XCircle size={17} weight="bold" aria-hidden="true" /> Errei
							</button>
						</div>
					{/if}
				{/if}

				{#if !respondida && (onAnterior || onPular || (podeContinuarSemResponder && onContinuar))}
					<div data-barra-acao class="mt-4 flex flex-col gap-2 sm:flex-row sm:items-center">
						{#if onAnterior}
							<button
								type="button"
								onclick={onAnterior}
								disabled={anteriorDesabilitado}
								class="btn-suave min-h-12 rounded-full px-5 font-display text-sm font-bold disabled:pointer-events-none disabled:opacity-40"
							>
								Anterior
							</button>
						{/if}
						{#if podeContinuarSemResponder && onContinuar}
							<button
								type="button"
								onclick={onContinuar}
								class="btn-primario flex min-h-12 flex-1 items-center justify-center gap-2 rounded-full px-6 font-display text-base font-bold"
							>
								<span>{rotuloContinuar}</span>
								<ArrowRight size={17} weight="bold" aria-hidden="true" />
							</button>
						{:else if onPular}
							<button
								type="button"
								onclick={pular}
								class="btn-suave flex min-h-12 flex-1 items-center justify-center gap-1.5 rounded-full px-5 text-sm font-bold text-ink-soft hover:text-ink"
							>
								<SkipForward size={16} weight="bold" aria-hidden="true" /> Pular questão
							</button>
						{/if}
					</div>
				{/if}
			{/if}
		</div>
	{/if}

	<!-- Gaveta de feedback: `gaveta-subir` no contêiner e `shake` no cartão interno
	     para que uma animação nunca sobrescreva a outra ao errar. O botão Continuar
	     fica colado aqui, acima de "Como resolver", sempre visível após verificar. -->
	{#if respondida}
		<div class="gaveta-subir mt-4">
			<div
				bind:this={veredito}
				tabindex="-1"
				class="relative rounded-2xl border p-4 {categoria === 'certa'
					? 'border-ok-border bg-ok-bg text-ok-fg'
					: categoria === 'errada'
						? (avaliadaAgora ? 'shake ' : '') + 'border-bad-border bg-bad-bg text-bad-fg'
						: 'border-warn-line/40 bg-warn-bg text-warn-fg'}"
				role="status"
				aria-live="polite"
			>
				{#if avaliadaAgora && categoria === 'certa' && sequencia >= 3}
					<SeloSequencia n={sequencia} />
				{/if}
				<div class="flex items-start gap-3">
					<span class="relative mt-0.5 flex h-6 w-6 shrink-0 items-center justify-center" aria-hidden="true">
						{#if categoria === 'certa' && avaliadaAgora}
							{#each FAISCAS as f, idx (idx)}
								<span
									class="faisca pointer-events-none absolute h-1.5 w-1.5 rounded-full {f.cor}"
									style="--fx: {f.x}; --fy: {f.y}"
								></span>
							{/each}
						{/if}
						{#if categoria === 'anulada'}
							<Info size={22} weight="fill" />
						{:else if categoria === 'certa'}
							<CheckCircle size={22} weight="fill" />
						{:else if categoria === 'parcial' || (q.tipo === 'objetiva' && !escolha)}
							<MinusCircle size={22} weight="fill" />
						{:else}
							<XCircle size={22} weight="fill" />
						{/if}
					</span>
					<div class="min-w-0 flex-1 text-sm leading-relaxed">
						{#if categoria === 'anulada'}
							<p class="font-display font-bold">Questão anulada pelo INEP</p>
							<p class="mt-0.5 opacity-90">Ponto garantido para todas as alternativas.</p>
						{:else if categoria === 'certa'}
							<p class="font-display font-bold">Resposta certa!</p>
							<p class="mt-0.5 opacity-90">
								{#if q.tipo === 'objetiva'}Gabarito: <strong>{q.gabarito}</strong>.{:else}Você marcou como certa na autoavaliação.{/if}
							</p>
						{:else if categoria === 'parcial'}
							<p class="font-display font-bold">Quase lá</p>
							<p class="mt-0.5 opacity-90">Você avaliou como parcial — vale conferir os detalhes do padrão.</p>
						{:else if q.tipo === 'objetiva' && !escolha}
							<!-- só acontece na correção do simulado: a questão ficou sem marcação -->
							<p class="font-display font-bold">Em branco</p>
							<p class="mt-0.5 opacity-90">Gabarito oficial: <strong>{q.gabarito}</strong>.</p>
						{:else if q.tipo === 'objetiva'}
							<p class="font-display font-bold">Não foi dessa vez</p>
							<p class="mt-0.5 opacity-90">Gabarito: <strong>{q.gabarito}</strong> · você marcou <strong>{escolha}</strong>.</p>
						{:else}
							<p class="font-display font-bold">Vale revisar o padrão</p>
							<p class="mt-0.5 opacity-90">Você avaliou como errada — releia o modelo oficial acima.</p>
						{/if}
					</div>
				</div>
			</div>

			{#if onContinuar}
				<div data-barra-acao class="relative mt-3 flex flex-col gap-2 sm:flex-row sm:items-center">
					{#if mostrarXP}
						<span
							class="xp-float nums pointer-events-none absolute -top-10 right-2 rounded-full border border-milestone-border bg-milestone-soft px-3 py-1 text-xs font-extrabold text-milestone-ink shadow-sm"
							role="status"
						>
							+{xpValor} XP
						</span>
					{/if}
					{#if onAnterior}
						<button
							type="button"
							onclick={onAnterior}
							disabled={anteriorDesabilitado}
							class="btn-suave min-h-12 rounded-full px-5 font-display text-sm font-bold disabled:pointer-events-none disabled:opacity-40"
						>
							Anterior
						</button>
					{/if}
					<button
						type="button"
						onclick={onContinuar}
						class="btn-primario flex min-h-12 flex-1 items-center justify-center gap-2 rounded-full px-6 font-display text-base font-bold"
					>
						<span>{rotuloContinuar}</span>
						<ArrowRight size={17} weight="bold" aria-hidden="true" />
					</button>
				</div>
			{/if}
		</div>
	{/if}

	{#if podeResolver && resolucao}
		<section in:fly={{ y: 8, duration: DUR }} class="mt-3 rounded-2xl border border-line bg-panel" aria-label="Como resolver">
			<button
				type="button"
				onclick={() => (resolucaoVisivel = !resolucaoVisivel)}
				aria-expanded={resolucaoVisivel}
				class="flex min-h-11 w-full flex-wrap items-center gap-2 px-4 py-3 text-left"
			>
				<!-- autoria no topo esquerdo: quem escreveu e se alguém conferiu -->
				<span
					class="flex items-center gap-1 rounded-full px-2.5 py-0.5 text-xs font-bold {resolucao.auditado
						? 'bg-ok-bg text-ok-fg'
						: 'bg-warn-bg text-warn-fg'}"
				>
					{#if (resolucao.autor || 'IA') === 'IA'}
						<Robot size={12} weight="bold" aria-hidden="true" />
					{:else}
						<UserCircle size={12} weight="bold" aria-hidden="true" />
					{/if}
					{rotuloAutoria(resolucao)}
				</span>
				<span class="font-display text-sm font-bold text-ink">Como resolver</span>
				<CaretDown
					size={16}
					weight="bold"
					class="ml-auto shrink-0 text-ink-soft transition-transform {resolucaoVisivel ? 'rotate-180' : ''}"
					aria-hidden="true"
				/>
			</button>
			{#if resolucaoVisivel}
				<div class="px-4 pb-4">
					<p class="enunciado max-w-[60ch] text-sm leading-relaxed text-ink"><TextoRico texto={resolucao.texto} /></p>
					{#if !resolucao.auditado}
						<p class="mt-3 text-xs text-ink-soft">
							Escrita por {resolucao.autor || 'IA'} e ainda não conferida por uma pessoa: pode ter erro.
							{q.tipo === 'objetiva' ? 'O gabarito acima é o oficial.' : 'O padrão de resposta acima é o oficial.'}
						</p>
					{/if}
				</div>
			{/if}
		</section>
	{/if}

	{#if nuvemLigada && !prova}
		<div class="mt-5 border-t border-line pt-2" data-sem-gesto>
			{#if reporte === 'ok'}
				<p class="flex min-h-11 items-center gap-2 text-sm font-semibold text-ok-fg" role="status">
					<CheckCircle size={18} weight="bold" aria-hidden="true" /> Obrigado! Vamos conferir esta questão.
				</p>
			{:else if !reporteAberto}
				<button
					type="button"
					onclick={() => (reporteAberto = true)}
					class="flex min-h-11 items-center gap-1.5 text-xs font-semibold text-ink-soft hover:text-ink"
				>
					<WarningCircle size={16} weight="bold" aria-hidden="true" /> Achou um erro nesta questão?
				</button>
			{:else}
				<form class="pt-2" onsubmit={enviarReporte}>
					<fieldset>
						<legend class="text-sm font-bold text-ink">O que está errado?</legend>
						<div class="mt-1.5 space-y-0.5">
							{#each MOTIVOS_REPORTE as [valor, rotulo] (valor)}
								<label class="flex min-h-11 cursor-pointer items-center gap-3 rounded-xl px-2 hover:bg-panel">
									<input
										type="radio"
										name="motivo-{q.id}"
										value={valor}
										required
										bind:group={motivo}
										class="h-5 w-5 shrink-0 accent-[var(--accent)]"
									/>
									<span class="text-sm text-ink">{rotulo}</span>
								</label>
							{/each}
						</div>
					</fieldset>
					<label class="mt-3 block">
						<span class="text-sm font-bold text-ink">Detalhes <span class="font-semibold text-ink-soft">(opcional)</span></span>
						<textarea
							bind:value={detalhe}
							maxlength="1000"
							rows="3"
							placeholder="Ex.: na folha oficial do INEP o gabarito é C."
							class="mt-1.5 w-full rounded-2xl border-2 border-line bg-paper p-3 text-sm leading-relaxed text-ink focus:border-accent focus:outline-none"
						></textarea>
					</label>
					{#if erroReporte}
						<p class="mt-2 text-sm font-semibold text-bad-fg" role="alert">{erroReporte}</p>
					{/if}
					<div class="mt-3 flex flex-wrap gap-2">
						<button
							type="submit"
							disabled={!motivo || reporte === 'enviando'}
							class="btn-escuro min-h-11 rounded-full px-5 text-sm font-bold disabled:opacity-50"
						>
							{reporte === 'enviando' ? 'Enviando…' : 'Enviar'}
						</button>
						<button
							type="button"
							onclick={() => (reporteAberto = false)}
							class="min-h-11 rounded-full px-3 text-sm font-bold text-ink-soft hover:text-ink"
						>
							Cancelar
						</button>
					</div>
				</form>
			{/if}
		</div>
	{/if}
</article>
