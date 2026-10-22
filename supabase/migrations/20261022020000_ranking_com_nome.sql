-- O ranking mostra o NOME do aluno, e não mais um apelido à parte (D15).
--
-- Roda DEPOIS de 20261022010000_visitas.sql. O site funciona antes dela: o
-- app já manda o nome como apelido, e o ranking só passa a refletir na hora
-- uma troca de nome ("Mudar nome") depois que esta migração rodar.
--
-- Por quê: o formulário da turma pedia nome E apelido, e ficou repetido. O
-- nome vem de `perfis.nome` (Google ou digitado). `membros.apelido`
-- continua existindo, preenchido pelo app com o começo do nome, só como
-- reserva para quem tiver o perfil sem nome.

-- Dois alunos com o mesmo começo de nome não podem ser barrados na entrada.
drop index if exists public.membros_apelido_unico;

-- Mesma assinatura e mesmas colunas (a coluna continua se chamando `apelido`
-- para o app não mudar); `create or replace` mantém os grants.
create or replace function public.ranking_turma(p_turma uuid, p_desde timestamptz default null)
returns table (apelido text, eu boolean, respondidas bigint, certas bigint, dias_ativos bigint)
language sql
stable
security definer
set search_path = ''
as $$
	select
		coalesce(nullif(btrim(p.nome), ''), m.apelido),
		m.usuario_id = auth.uid(),
		count(r.id),
		count(r.id) filter (where r.resultado = 'certa'),
		count(distinct (r.respondida_em at time zone 'America/Sao_Paulo')::date)
	from public.membros m
	join public.turmas t on t.id = m.turma_id
	join public.perfis p on p.id = m.usuario_id
	left join public.respostas r
		on r.usuario_id = m.usuario_id
		and r.curso = t.curso
		and (p_desde is null or r.respondida_em >= p_desde)
	where m.turma_id = p_turma
		and m.papel = 'aluno'
		and (m.no_ranking or m.usuario_id = auth.uid())
		and t.ranking_ativo
		and public.eh_membro(p_turma)
	group by m.usuario_id, p.nome, m.apelido
	order by 4 desc, 3 desc, 1;
$$;
