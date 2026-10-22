<script>
	// Privacidade (P2, obrigatória antes do lançamento para a turma em 01/11).
	// Texto curto e concreto: o que sai do aparelho, quem vê e como apagar.
	// Mudou o que o banco guarda (supabase/migrations/)? Mude esta página junto.
	import { ArrowLeft } from 'phosphor-svelte';

	const ATUALIZADA = '22 de outubro de 2026';
</script>

<svelte:head>
	<title>Privacidade · Simulado ENADE</title>
</svelte:head>

<article class="mx-auto max-w-[62ch] pb-8">
	<a href="/" class="inline-flex min-h-11 items-center gap-2 text-sm font-bold text-ink-soft hover:text-ink">
		<ArrowLeft size={17} weight="bold" aria-hidden="true" /> Início
	</a>

	<h1 class="mt-2 font-display text-title font-extrabold">Privacidade</h1>
	<p class="mt-1 text-sm text-ink-soft">Atualizada em {ATUALIZADA}.</p>

	<div class="mt-6 space-y-8 text-[15px] leading-relaxed text-pretty">
		<section aria-labelledby="p-sem-conta">
			<h2 id="p-sem-conta" class="font-display text-heading font-bold">Sem conta, seu progresso fica no aparelho</h2>
			<p class="mt-2">
				Para estudar não precisa de conta. Seu progresso (respostas, erros, questões marcadas e
				simulados) fica só no navegador deste aparelho. Ninguém mais vê, nem nós. A única coisa que sai
				é a contagem de visitas, explicada abaixo.
			</p>
		</section>

		<section aria-labelledby="p-conta">
			<h2 id="p-conta" class="font-display text-heading font-bold">Com conta e turma</h2>
			<p class="mt-2">A conta serve para entrar na turma do seu professor. Quando você entra, guardamos:</p>
			<ul class="mt-2 list-disc space-y-1.5 pl-5">
				<li><strong>Do login:</strong> seu nome e e-mail, que vêm do Google (ou só o e-mail, se entrar por link).</li>
				<li><strong>Da turma:</strong> o apelido que você escolher e o RA, se você informar. O RA é opcional.</li>
				<li>
					<strong>De cada resposta:</strong> qual questão, se acertou, a matéria, o modo (treino, estudo ou
					simulado), quanto tempo levou e quando respondeu. O texto que você escreve na discursiva
					<strong>não</strong> sai do aparelho.
				</li>
			</ul>
			<p class="mt-2">Respostas de antes de você entrar na conta não sobem.</p>
		</section>

		<section aria-labelledby="p-quem">
			<h2 id="p-quem" class="font-display text-heading font-bold">Quem vê o quê</h2>
			<ul class="mt-2 list-disc space-y-1.5 pl-5">
				<li>
					<strong>O professor da sua turma</strong> vê seu nome, apelido, RA (se houver) e seu desempenho:
					quantas questões respondeu, acertos por matéria e resultado nos simulados da turma.
				</li>
				<li>
					<strong>Os colegas da turma</strong> veem só o seu apelido e seus acertos no ranking. Se você
					desmarcar "Aparecer no ranking", nem isso.
				</li>
				<li><strong>Ninguém mais.</strong> Não vendemos nem passamos seus dados para ninguém, e o site não tem anúncios.</li>
			</ul>
		</section>

		<section aria-labelledby="p-onde">
			<h2 id="p-onde" class="font-display text-heading font-bold">Onde fica guardado</h2>
			<p class="mt-2">
				No Supabase, o serviço de banco de dados que o site usa. As regras de quem pode ler cada coisa
				ficam no próprio banco, e o código do site é aberto no
				<a href="https://github.com/Krydelmany/simulado-enade" class="font-bold text-accent-ink underline">GitHub</a>.
			</p>
		</section>

		<section aria-labelledby="p-apagar">
			<h2 id="p-apagar" class="font-display text-heading font-bold">Como sair ou apagar</h2>
			<ul class="mt-2 list-disc space-y-1.5 pl-5">
				<li>
					<strong>Sair da turma:</strong> em <a href="/conta/" class="font-bold text-accent-ink underline">Conta e turma</a>,
					"Sair desta turma". O professor deixa de ver você.
				</li>
				<li>
					<strong>Apagar tudo:</strong> na mesma tela, "Apagar minha conta". Apaga na hora sua conta, suas
					turmas e todas as respostas que subiram. O progresso no seu aparelho continua.
				</li>
			</ul>
		</section>

		<section aria-labelledby="p-visitas">
			<h2 id="p-visitas" class="font-display text-heading font-bold">Contagem de visitas</h2>
			<p class="mt-2">
				Para saber quantas pessoas usam o site, contamos cada página aberta: qual página, de que site
				você chegou (só o nome, como whatsapp.com), se é celular ou computador e se você estava na conta.
			</p>
			<p class="mt-2">
				Para contar pessoas e não cliques, o navegador guarda um código sorteado. Ele não tem ligação
				com seu nome nem com sua conta, e some se você limpar os dados do site. Não guardamos seu IP nas
				visitas. Com o "não rastrear" ligado no navegador, não contamos nada.
			</p>
		</section>

		<section aria-labelledby="p-reporte">
			<h2 id="p-reporte" class="font-display text-heading font-bold">Reportar erro numa questão</h2>
			<p class="mt-2">
				Quando você reporta um erro, guardamos a questão, o motivo e o texto que você escrever. Se você
				estiver na conta, o reporte fica ligado a ela; sem conta, ele é anônimo.
			</p>
		</section>

		<section aria-labelledby="p-duvidas">
			<h2 id="p-duvidas" class="font-display text-heading font-bold">Dúvidas</h2>
			<p class="mt-2">
				Fale com o professor da sua turma ou abra uma conversa no
				<a href="https://github.com/Krydelmany/simulado-enade/issues" class="font-bold text-accent-ink underline">GitHub do projeto</a>.
			</p>
		</section>
	</div>
</article>
