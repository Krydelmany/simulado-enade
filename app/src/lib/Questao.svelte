<script>
	import { fly } from 'svelte/transition';
	import { ehGerada, rotuloQuestao } from './banco.js';
	import { nomeMateria } from './materias.js';
	import { DUR, REDUCED } from './motion.js';
	import {
		Atom,
		BookmarkSimple,
		CheckCircle,
		Image as ImageIcon,
		Info,
		MagnifyingGlassPlus,
		MinusCircle,
		SealCheck,
		SkipForward,
		XCircle
	} from 'phosphor-svelte';
	import TextoRico from './TextoRico.svelte';

	/**
	 * `inicial` restaura o estado de uma questão já respondida quando o aluno volta
	 * a ela (navegação anterior/seguinte) — vem do mapa `respostas` da página.
	 *
	 * Contrato ÚNICO de resposta para os dois modos (treino e estudo):
	 *   { id, certa, parcial?, anulada? }   (+ escolha/mostrouPadrao/auto, para restaurar a UI)
	 */
	let {
		q,
		onResponder,
		onPular = null,
		onRevisar = null,
		revisarInicial = false,
		inicial = null,
		zoomAberto = $bindable(false)
	} = $props();

	// lê o estado inicial DENTRO de uma função: é intencional capturar uma vez
	// (o componente é remontado por questão via {#key}) e evita o aviso do compilador
	function estadoInicial() {
		return {
			escolha: inicial?.escolha ?? null,
			respondida: !!inicial?.respondida,
			mostrouPadrao: !!inicial?.mostrouPadrao,
			auto: inicial?.auto ?? null, // discursiva: 'certa' | 'parcial' | 'errada'
			revisar: !!revisarInicial
		};
	}
	const ini = estadoInicial();

	let escolha = $state(ini.escolha);
	let respondida = $state(ini.respondida);
	let mostrouPadrao = $state(ini.mostrouPadrao);
	let auto = $state(ini.auto);
	let revisar = $state(ini.revisar);
	let ampliada = $state(false);
	// só rola/foca o veredito quando o aluno ACABOU de responder — nunca ao restaurar
	let avaliadaAgora = $state(false);
	let veredito = $state(null);

	const LETRAS = ['A', 'B', 'C', 'D', 'E'];
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
						: 'errada'
	);

	function responder(letra) {
		if (respondida) return;
		escolha = letra;
		respondida = true;
		avaliadaAgora = true;
		// questão anulada = ponto para todos: qualquer alternativa conta como acerto
		const certa = anulada || letra === q.gabarito;
		onResponder?.({ id: q.id, certa, anulada, escolha: letra });
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
		// com a imagem ampliada, o Esc só fecha o zoom (a página ignora via `zoomAberto`)
		if (ampliada) {
			if (e.key === 'Escape') ampliada = false;
			return;
		}
		if (e.metaKey || e.ctrlKey || e.altKey) return;
		if (ehCampo(e.target)) return;
		if (q.tipo !== 'objetiva' || respondida) return;
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
			responder(letra);
		}
	}

	// avisa a página se há um modal (zoom) aberto, para o Esc não encerrar a sessão junto
	$effect(() => {
		zoomAberto = ampliada;
		return () => {
			zoomAberto = false;
		};
	});

	$effect(() => {
		document.body.style.overflow = ampliada ? 'hidden' : '';
		return () => {
			document.body.style.overflow = '';
		};
	});

	// ao responder, leva o veredito para a tela (mobile) e move o foco para ele
	$effect(() => {
		if (!avaliadaAgora || !veredito) return;
		const r = veredito.getBoundingClientRect();
		const h = window.innerHeight || 0;
		// A barra de ação é fixa no rodapé e a altura dela muda conforme a tela
		// (botão voltar + posição + CTA). Medir no DOM é mais confiável do que
		// chutar um valor: com o chute, o veredito "certa" ficava atrás da barra
		// — ou seja, o aluno respondia e não via o resultado.
		const barra = document.querySelector('[data-barra-acao]');
		const folga = (barra?.getBoundingClientRect().height || 0) + 12;
		const fora = r.top < 8 || r.bottom > h - folga;
		veredito.focus({ preventScroll: true });
		if (fora) veredito.scrollIntoView({ block: 'center', behavior: REDUCED ? 'auto' : 'smooth' });
	});

	// leitor de tela: a alternativa sem as marcas de bloco de código
	const MARCA_BLOCO = new RegExp('\x60{3}\\w*\\n?', 'g');
	function rotuloAlt(letra) {
		const texto = q.alternativas[letra];
		if (!texto) return 'Alternativa ' + letra + ' (na imagem)';
		return 'Alternativa ' + letra + ': ' + texto.replace(MARCA_BLOCO, '');
	}

	function classeAlt(letra) {
		const base =
			'flex w-full items-start gap-3 rounded-2xl border-2 p-3.5 text-left text-[15px] leading-relaxed transition-[border-color,background-color,color,transform] duration-150 active:scale-[0.99] disabled:cursor-default ';
		if (!respondida) return base + 'border-line bg-card hover:border-ink';
		if (anulada) return base + 'border-line bg-tile';
		if (letra === q.gabarito) return base + 'border-ok-solid bg-ok-solid text-white pop';
		if (letra === escolha) return base + 'border-bad-solid bg-bad-solid text-white';
		return base + 'border-line bg-card opacity-50';
	}

	function classeBolha(letra) {
		// bolha de cartão-resposta: preenche como caneta ao marcar
		const base =
			'flex h-8 w-8 shrink-0 items-center justify-center rounded-full border-[2.5px] text-sm font-extrabold transition-colors duration-150 ';
		if (!respondida) return base + 'border-ink/30 text-ink';
		if (anulada) return letra === escolha ? base + 'border-white bg-white/25 text-white' : base + 'border-line text-ink-soft';
		if (letra === q.gabarito) return base + 'border-white bg-white/25 text-white';
		if (letra === escolha) return base + 'border-white bg-white/25 text-white';
		return base + 'border-line text-ink-soft';
	}
</script>

<svelte:window onkeydown={aoTecla} />

<article class="rounded-3xl bg-card p-4 shadow-[0_10px_30px_-12px_rgba(20,33,61,0.25)] sm:p-6">
	<div class="flex flex-wrap items-center gap-2">
		<p class="font-code text-[11px] font-bold tracking-[0.14em] text-accent-ink uppercase">
			{rotuloQuestao(q)}
		</p>
		{#if q.materia}
			<p class="flex items-center gap-1 rounded-full bg-accent-soft px-2.5 py-0.5 text-[11px] font-bold text-accent-ink">
				<Atom size={12} weight="bold" aria-hidden="true" />
				{nomeMateria(q.materia)}
			</p>
		{/if}
		{#if ehGerada(q)}
			<!-- gerada não é prova: o que importa ao aluno é o nível, não a parte -->
			<p class="rounded-full border border-line px-2.5 py-0.5 text-[11px] font-bold text-ink-soft">
				Revisão · {q.dificuldade === 'Média' ? 'Médio' : q.dificuldade}
			</p>
		{:else if q.parte}
			<p class="rounded-full border border-line px-2.5 py-0.5 text-[11px] font-bold text-ink-soft">
				{q.parte === 'FG' ? 'Formação Geral' : q.parte}
			</p>
		{/if}
		<button
			type="button"
			onclick={alternarRevisar}
			aria-pressed={revisar}
			aria-label={revisar ? 'Remover marcação de revisar' : 'Marcar para revisar depois'}
			title={revisar ? 'Remover marcação de revisar' : 'Marcar para revisar depois'}
			class="ml-auto flex h-11 min-w-11 items-center justify-center rounded-full border transition-transform active:scale-95 {revisar
				? 'border-line bg-accent-soft text-accent-ink'
				: 'border-line bg-card text-ink-soft'}"
		>
			<BookmarkSimple size={20} weight={revisar ? 'fill' : 'bold'} aria-hidden="true" />
		</button>
	</div>
	<h2 class="mt-1 text-base font-bold tracking-tight">{q.tema}</h2>

	{#if q.imagem}
		<figure class="mt-3 overflow-hidden rounded-2xl border border-line bg-white">
			<button
				type="button"
				onclick={() => (ampliada = true)}
				aria-label="Ampliar figura: {q.imagem.alt}"
				class="block w-full cursor-zoom-in"
			>
				<img
					src={q.imagem.src}
					alt={q.imagem.alt}
					loading="lazy"
					class="mx-auto h-auto max-h-[54vh] w-auto max-w-full"
				/>
			</button>
			<figcaption class="flex items-start gap-2 px-3 py-2 text-xs text-ink-soft">
				<MagnifyingGlassPlus size={14} weight="bold" class="mt-0.5 shrink-0" aria-hidden="true" />
				<span>
					Toque para ampliar
					{#if q.imagem.legenda} · {q.imagem.legenda}{/if}
				</span>
			</figcaption>
		</figure>
		{#if ampliada}
			<div
				class="fixed inset-0 z-50 flex flex-col bg-black/90 p-4"
				style="padding-bottom: env(safe-area-inset-bottom);"
			>
				<button
					type="button"
					onclick={() => (ampliada = false)}
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
						class="m-auto max-h-full max-w-full rounded-lg object-contain"
					/>
					<p class="pt-3 text-center text-sm font-semibold text-white/80">Toque para fechar</p>
				</div>
			</div>
		{/if}
	{:else if q.figura}
		<p class="mt-3 flex items-start gap-2 rounded-2xl border border-dashed border-warn-line bg-warn-bg p-3 text-sm text-warn-fg">
			<ImageIcon size={18} weight="bold" class="mt-0.5 shrink-0" aria-hidden="true" />
			<span>Figura: {q.figura.desc} <span class="italic">(imagem entra aqui)</span></span>
		</p>
	{/if}

	<div class="enunciado mt-3 max-w-[65ch] text-[15px] leading-relaxed"><TextoRico texto={q.enunciado} /></div>

	{#if q.tipo === 'objetiva'}
		{#if anulada && !respondida}
			<p class="mt-4 flex items-start gap-2 rounded-2xl bg-warn-bg p-3 text-sm font-semibold text-warn-fg" role="note">
				<Info size={18} weight="bold" class="mt-0.5 shrink-0" aria-hidden="true" />
				<span>Questão anulada pelo INEP — qualquer alternativa marca o ponto.</span>
			</p>
		{/if}
		<div class="mt-4 space-y-2" role="group" aria-label="Alternativas">
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
					<div class="rise" style="animation-delay: {k * 45}ms">
						<button
							type="button"
							onclick={() => responder(letra)}
							disabled={respondida}
							aria-label={rotuloAlt(letra)}
							class={classeAlt(letra)}
						>
							<span class={classeBolha(letra)}>
								{letra}
							</span>
							{#if q.alternativas[letra]?.includes('```')}
								<!-- alternativa que é código (2023-CE-Q15, Q30): bloco mono, como no enunciado -->
								<span class="min-w-0 flex-1"><TextoRico texto={q.alternativas[letra]} /></span>
							{:else if q.alternativas[letra]}
								<span class="enunciado">{q.alternativas[letra]}</span>
							{:else}
								<span class="text-sm font-semibold text-ink-soft">Alternativa {letra} da imagem</span>
							{/if}
						</button>
					</div>
				{/if}
			{/each}
		</div>
	{:else}
		<div class="mt-4">
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
						O padrão oficial desta questão é um desenho que ainda não está
						no site. Escreva sua resposta no papel e confira com a
						apostila.
					</span>
				</p>
			{:else if !mostrouPadrao}
				<button
					type="button"
					onclick={() => (mostrouPadrao = true)}
					class="btn3d duo-accent w-full rounded-2xl p-3.5 font-bold"
				>
					Escrevi minha resposta — ver padrão oficial
				</button>
			{:else}
				<div in:fly={{ y: 8, duration: DUR }} class="rounded-2xl border border-line bg-panel p-4">
					<p class="flex items-center gap-1.5 text-[11px] font-bold tracking-[0.14em] text-ink-soft uppercase">
						<SealCheck size={15} weight="bold" aria-hidden="true" />
						Padrão de resposta · INEP
					</p>
					<p class="enunciado mt-2 max-w-[65ch] text-sm leading-relaxed"><TextoRico texto={q.padrao} /></p>
				</div>
				{#if !respondida}
					<p class="mt-3 text-sm font-bold">Compare com a sua. Como foi?</p>
					<div class="mt-2 grid grid-cols-3 gap-2">
						<button
							type="button"
							onclick={() => autoavaliar(1)}
							class="btn3d flex min-h-11 items-center justify-center gap-1.5 rounded-2xl border-ok-solid bg-ok-solid p-3 text-sm font-bold text-white"
						>
							<CheckCircle size={17} weight="bold" aria-hidden="true" /> Acertei
						</button>
						<button
							type="button"
							onclick={() => autoavaliar(0.5)}
							class="btn3d flex min-h-11 items-center justify-center gap-1.5 rounded-2xl border-amber-600 bg-amber-500 p-3 text-sm font-bold text-white"
						>
							<MinusCircle size={17} weight="bold" aria-hidden="true" /> Meio
						</button>
						<button
							type="button"
							onclick={() => autoavaliar(0)}
							class="btn3d flex min-h-11 items-center justify-center gap-1.5 rounded-2xl border-bad-solid bg-bad-solid p-3 text-sm font-bold text-white"
						>
							<XCircle size={17} weight="bold" aria-hidden="true" /> Errei
						</button>
					</div>
				{/if}
			{/if}
		</div>
	{/if}

	{#if onPular && !respondida}
		<button
			type="button"
			onclick={pular}
			class="mt-4 flex min-h-11 w-full items-center justify-center gap-1.5 rounded-2xl border border-line bg-card py-2.5 text-sm font-bold text-ink-soft transition-transform active:scale-[0.99]"
		>
			<SkipForward size={17} weight="bold" aria-hidden="true" /> Pular questão
		</button>
	{/if}

	{#if respondida}
		<p
			bind:this={veredito}
			tabindex="-1"
			in:fly={{ y: 8, duration: DUR }}
			class="mt-3 flex items-start gap-2 rounded-2xl p-3.5 text-sm font-semibold {categoria ===
			'certa'
				? 'bg-ok-bg text-ok-fg'
				: categoria === 'errada'
					? 'shake bg-bad-bg text-bad-fg'
					: 'bg-warn-bg text-warn-fg'}"
			role="status"
			aria-live="polite"
		>
			{#if categoria === 'anulada'}
				<Info size={19} weight="bold" class="mt-0.5 shrink-0" aria-hidden="true" />
				<span>Questão anulada pelo INEP — ponto para todos.</span>
			{:else if categoria === 'certa'}
				<CheckCircle size={19} weight="bold" class="mt-0.5 shrink-0" aria-hidden="true" />
				<span>Certa. Gabarito: {q.gabarito}</span>
			{:else if categoria === 'parcial'}
				<MinusCircle size={19} weight="bold" class="mt-0.5 shrink-0" aria-hidden="true" />
				<span>Quase. Você avaliou como parcial — vale conferir o padrão.</span>
			{:else if q.tipo === 'objetiva'}
				<XCircle size={19} weight="bold" class="mt-0.5 shrink-0" aria-hidden="true" />
				<span>Não foi dessa vez. Gabarito: {q.gabarito} — você marcou {escolha}.</span>
			{:else}
				<XCircle size={19} weight="bold" class="mt-0.5 shrink-0" aria-hidden="true" />
				<span>Você avaliou como errada. Vale reler o padrão acima.</span>
			{/if}
		</p>
	{/if}
</article>
