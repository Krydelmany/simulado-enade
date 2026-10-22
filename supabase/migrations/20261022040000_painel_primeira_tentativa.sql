-- Painel do professor medido do jeito certo (D16). Roda DEPOIS de
-- 20261022030000_apelido_sem_email.sql.
--
-- 1. PRIMEIRA TENTATIVA. Acerto conta só a primeira resposta de cada aluno
--    a cada questão (a convenção do ASSISTments e da análise de itens). Antes
--    o painel contava toda tentativa: quem refazia a revisão até acertar
--    inflava o próprio acerto, o da matéria e o da turma.
-- 2. ALTERNATIVA MARCADA. `respostas.escolha` guarda a letra. Por questão, o
--    painel mostra a alternativa errada mais marcada, como o relatório de
--    questionário do Moodle e o do ASSISTments: "40% marcaram C" diz qual é o
--    engano, e é o que vira aula. Respostas de antes desta migração não têm a
--    letra.
-- 3. RANKING sem farm: conta questões DIFERENTES (respondidas e acertadas),
--    então repetir a mesma questão não sobe ninguém.
-- 4. EVOLUÇÃO pelos simulados (mesma prova para a turma toda), e não pelo
--    acerto semanal, que muda com a dificuldade das questões da semana.
-- 5. FICHA DO ALUNO numa função só.

alter table public.respostas
	add column escolha text check (escolha in ('A', 'B', 'C', 'D', 'E'));

grant insert (escolha) on public.respostas to authenticated;

-- A primeira resposta de cada aluno a cada questão OBJETIVA. A discursiva
-- fica fora de todo acerto: é autoavaliada (o próprio aluno diz se acertou).
-- Só as funções do painel leem (security_invoker + sem grant); empate no
-- mesmo instante cai no que chegou primeiro ao servidor.
create view public.primeiras_objetivas with (security_invoker = true) as
select distinct on (r.usuario_id, r.curso, r.questao_id) r.*
from public.respostas r
where r.questao_id !~ '-D[0-9]+$'
order by r.usuario_id, r.curso, r.questao_id, r.respondida_em, r.recebida_em;

revoke all on public.primeiras_objetivas from anon, authenticated;

-- ---------------------------------------------------------------------------
-- Matérias e questões da turma: primeira tentativa, só objetivas
-- ---------------------------------------------------------------------------

create or replace function public.painel_materias(p_turma uuid)
returns table (materia text, oficial boolean, alunos bigint, respondidas bigint, certas bigint)
language sql
stable
security definer
set search_path = ''
as $$
	select r.materia, r.oficial, count(distinct r.usuario_id), count(*),
		count(*) filter (where r.resultado = 'certa')
	from public.primeiras_objetivas r
	join public.membros m on m.usuario_id = r.usuario_id and m.turma_id = p_turma and m.papel = 'aluno'
	join public.turmas t on t.id = p_turma and t.curso = r.curso
	where public.eh_professor(p_turma) and r.resultado in ('certa', 'errada')
	group by r.materia, r.oficial
	order by 4 desc;
$$;

drop function public.painel_questoes(uuid, integer, integer);

-- `tentativas` = alunos que responderam (uma primeira tentativa por aluno).
-- `escolha_comum`: a alternativa errada mais marcada; `erros_com_escolha` é
-- a base dela (erros que têm a letra gravada).
create function public.painel_questoes(p_turma uuid, p_minimo integer default 3, p_limite integer default 20)
returns table (
	questao_id text,
	materia text,
	alunos bigint,
	tentativas bigint,
	erros bigint,
	escolha_comum text,
	escolha_comum_n bigint,
	erros_com_escolha bigint
)
language sql
stable
security definer
set search_path = ''
as $$
	with base as (
		select r.* from public.primeiras_objetivas r
		join public.membros m on m.usuario_id = r.usuario_id and m.turma_id = p_turma and m.papel = 'aluno'
		join public.turmas t on t.id = p_turma and t.curso = r.curso
		where public.eh_professor(p_turma) and r.resultado in ('certa', 'errada')
	),
	letras as (
		select b.questao_id, b.escolha, count(*) as n,
			row_number() over (partition by b.questao_id order by count(*) desc, b.escolha) as k
		from base b
		where b.resultado = 'errada' and b.escolha is not null
		group by b.questao_id, b.escolha
	)
	select b.questao_id, max(b.materia), count(distinct b.usuario_id), count(*),
		count(*) filter (where b.resultado = 'errada'),
		(select l.escolha from letras l where l.questao_id = b.questao_id and l.k = 1),
		(select l.n from letras l where l.questao_id = b.questao_id and l.k = 1),
		count(*) filter (where b.resultado = 'errada' and b.escolha is not null)
	from base b
	group by b.questao_id
	having count(*) >= greatest(p_minimo, 1)
	order by (count(*) filter (where b.resultado = 'errada'))::numeric / count(*) desc, 4 desc
	limit least(greatest(p_limite, 1), 100);
$$;

-- ---------------------------------------------------------------------------
-- Alunos: volume (toda resposta) + acerto na primeira tentativa
-- ---------------------------------------------------------------------------

drop function public.painel_alunos(uuid);

create function public.painel_alunos(p_turma uuid)
returns table (
	usuario_id uuid,
	nome text,
	apelido text,
	ra text,
	respondidas bigint,
	certas bigint,
	respondidas_7d bigint,
	dias_ativos bigint,
	simulados bigint,
	ultima_em timestamptz,
	primeiras bigint,
	primeiras_certas bigint
)
language sql
stable
security definer
set search_path = ''
as $$
	with p1 as (
		select r.usuario_id, count(*) as n, count(*) filter (where r.resultado = 'certa') as c
		from public.primeiras_objetivas r
		join public.turmas t on t.id = p_turma and t.curso = r.curso
		where r.resultado in ('certa', 'errada')
		group by r.usuario_id
	)
	select
		m.usuario_id,
		p.nome,
		m.apelido,
		m.ra,
		count(r.id),
		count(r.id) filter (where r.resultado = 'certa'),
		count(r.id) filter (where r.respondida_em >= now() - interval '7 days'),
		count(distinct (r.respondida_em at time zone 'America/Sao_Paulo')::date),
		count(r.id) filter (where r.modo = 'simulado'),
		max(r.respondida_em),
		coalesce(max(p1.n), 0),
		coalesce(max(p1.c), 0)
	from public.membros m
	join public.turmas t on t.id = m.turma_id
	join public.perfis p on p.id = m.usuario_id
	left join public.respostas r on r.usuario_id = m.usuario_id and r.curso = t.curso
	left join p1 on p1.usuario_id = m.usuario_id
	where m.turma_id = p_turma and m.papel = 'aluno' and public.eh_professor(p_turma)
	group by m.usuario_id, p.nome, m.apelido, m.ra
	order by 5 desc, 3;
$$;

-- ---------------------------------------------------------------------------
-- Ranking: questões diferentes, não tentativas
-- ---------------------------------------------------------------------------

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
		count(distinct r.questao_id),
		count(distinct r.questao_id) filter (where r.resultado = 'certa'),
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

-- ---------------------------------------------------------------------------
-- Simulados: questões com a alternativa errada mais marcada + resumo por prova
-- ---------------------------------------------------------------------------

drop function public.painel_simulado_questoes(uuid);

create function public.painel_simulado_questoes(p_simulado uuid)
returns table (
	questao_id text,
	materia text,
	respondidas bigint,
	certas bigint,
	escolha_comum text,
	escolha_comum_n bigint,
	erros_com_escolha bigint
)
language sql
stable
security definer
set search_path = ''
as $$
	with s as (
		select * from public.simulados x
		where x.id = p_simulado and public.eh_professor(x.turma_id)
	),
	primeira as (
		select distinct on (r.usuario_id, r.questao_id) r.questao_id, r.materia, r.resultado, r.escolha
		from public.respostas r
		join s on r.simulado_id = s.id
		join public.membros m on m.turma_id = s.turma_id and m.usuario_id = r.usuario_id and m.papel = 'aluno'
		where r.questao_id !~ '-D[0-9]+$'
		order by r.usuario_id, r.questao_id, r.respondida_em
	),
	letras as (
		select f.questao_id, f.escolha, count(*) as n,
			row_number() over (partition by f.questao_id order by count(*) desc, f.escolha) as k
		from primeira f
		where f.resultado = 'errada' and f.escolha is not null
		group by f.questao_id, f.escolha
	)
	select f.questao_id, max(f.materia), count(*),
		count(*) filter (where f.resultado in ('certa', 'anulada')),
		(select l.escolha from letras l where l.questao_id = f.questao_id and l.k = 1),
		(select l.n from letras l where l.questao_id = f.questao_id and l.k = 1),
		count(*) filter (where f.resultado = 'errada' and f.escolha is not null)
	from primeira f
	group by f.questao_id
	order by (count(*) filter (where f.resultado in ('certa', 'anulada')))::numeric / count(*), 1;
$$;

-- Um por simulado: quantos fizeram e a média de acertos de quem fez. É a
-- linha de evolução da turma (D16): mesma prova, mesmo formato.
create function public.painel_simulados_resumo(p_turma uuid)
returns table (
	id uuid,
	titulo text,
	objetivas smallint,
	abre_em timestamptz,
	fecha_em timestamptz,
	alunos_fizeram bigint,
	media_certas numeric
)
language sql
stable
security definer
set search_path = ''
as $$
	with primeira as (
		select distinct on (r.simulado_id, r.usuario_id, r.questao_id) r.simulado_id, r.usuario_id, r.resultado
		from public.respostas r
		join public.simulados s on s.id = r.simulado_id and s.turma_id = p_turma
		join public.membros m on m.turma_id = p_turma and m.usuario_id = r.usuario_id and m.papel = 'aluno'
		where r.questao_id !~ '-D[0-9]+$'
		order by r.simulado_id, r.usuario_id, r.questao_id, r.respondida_em
	),
	por_aluno as (
		select f.simulado_id, f.usuario_id, count(*) filter (where f.resultado in ('certa', 'anulada')) as certas
		from primeira f
		group by f.simulado_id, f.usuario_id
	)
	select s.id, s.titulo, s.objetivas, s.abre_em, s.fecha_em,
		count(a.usuario_id), round(avg(a.certas), 1)
	from public.simulados s
	left join por_aluno a on a.simulado_id = s.id
	where s.turma_id = p_turma and public.eh_professor(p_turma)
	group by s.id
	order by s.abre_em;
$$;

-- ---------------------------------------------------------------------------
-- Ficha do aluno
-- ---------------------------------------------------------------------------

-- Tudo de UM aluno em JSON, numa ida só. Quem não é professor da turma, ou
-- pede um aluno que não é dela, recebe `null` (como as `painel_*`).
create function public.painel_aluno(p_turma uuid, p_aluno uuid)
returns jsonb
language plpgsql
stable
security definer
set search_path = ''
as $$
declare
	v_curso text;
begin
	if not public.eh_professor(p_turma) then
		return null;
	end if;
	if not exists (
		select 1 from public.membros m
		where m.turma_id = p_turma and m.usuario_id = p_aluno and m.papel = 'aluno'
	) then
		return null;
	end if;
	select t.curso into v_curso from public.turmas t where t.id = p_turma;

	return jsonb_build_object(
		'perfil', (
			select jsonb_build_object(
				'nome', p.nome, 'apelido', m.apelido, 'ra', m.ra,
				'entrou_em', m.entrou_em, 'no_ranking', m.no_ranking
			)
			from public.membros m join public.perfis p on p.id = m.usuario_id
			where m.turma_id = p_turma and m.usuario_id = p_aluno
		),
		'total', (
			select count(*) from public.respostas r where r.usuario_id = p_aluno and r.curso = v_curso
		),
		-- os últimos 35 dias, no fuso de São Paulo (só os dias com resposta)
		'dias', coalesce((
			select jsonb_agg(x order by x.dia) from (
				select (r.respondida_em at time zone 'America/Sao_Paulo')::date as dia,
					count(*) as respondidas
				from public.respostas r
				where r.usuario_id = p_aluno and r.curso = v_curso
					and r.respondida_em >= now() - interval '35 days'
				group by 1
			) x
		), '[]'::jsonb),
		-- acerto por matéria na primeira tentativa (o mesmo critério da turma)
		'materias', coalesce((
			select jsonb_agg(x) from (
				select r.materia, count(*) as respondidas,
					count(*) filter (where r.resultado = 'certa') as certas
				from public.primeiras_objetivas r
				where r.usuario_id = p_aluno and r.curso = v_curso and r.resultado in ('certa', 'errada')
				group by r.materia
			) x
		), '[]'::jsonb),
		-- as que ele mais erra (todas as tentativas) e se a última já foi certa
		'erradas', coalesce((
			select jsonb_agg(x order by x.erros desc, x.ultima_em desc) from (
				select r.questao_id, max(r.materia) as materia, count(*) as tentativas,
					count(*) filter (where r.resultado = 'errada') as erros,
					max(r.respondida_em) as ultima_em,
					(array_agg(r.resultado order by r.respondida_em desc))[1] = 'certa' as ultima_certa,
					(array_agg(r.escolha order by r.respondida_em desc) filter (where r.resultado = 'errada'))[1] as ultima_errada
				from public.respostas r
				where r.usuario_id = p_aluno and r.curso = v_curso and r.resultado in ('certa', 'errada')
				group by r.questao_id
				having count(*) filter (where r.resultado = 'errada') > 0
				order by 4 desc, 5 desc
				limit 12
			) x
		), '[]'::jsonb),
		-- os simulados da turma, com a primeira resposta de cada questão (D12)
		'simulados', coalesce((
			select jsonb_agg(x order by x.abre_em desc) from (
				select s.id, s.titulo, s.objetivas, s.abre_em, s.fecha_em,
					count(f.questao_id) as respondidas,
					count(f.questao_id) filter (where f.resultado in ('certa', 'anulada')) as certas,
					max(f.respondida_em) as entregue_em
				from public.simulados s
				left join lateral (
					select distinct on (r.questao_id) r.questao_id, r.resultado, r.respondida_em
					from public.respostas r
					where r.simulado_id = s.id and r.usuario_id = p_aluno and r.questao_id !~ '-D[0-9]+$'
					order by r.questao_id, r.respondida_em
				) f on true
				where s.turma_id = p_turma
				group by s.id
			) x
		), '[]'::jsonb)
	);
end;
$$;

-- ---------------------------------------------------------------------------
-- Permissões (as recriadas com drop perdem os grants)
-- ---------------------------------------------------------------------------

revoke all on function
	public.painel_questoes(uuid, integer, integer),
	public.painel_alunos(uuid),
	public.painel_simulado_questoes(uuid),
	public.painel_simulados_resumo(uuid),
	public.painel_aluno(uuid, uuid)
from public, anon;

grant execute on function
	public.painel_questoes(uuid, integer, integer),
	public.painel_alunos(uuid),
	public.painel_simulado_questoes(uuid),
	public.painel_simulados_resumo(uuid),
	public.painel_aluno(uuid, uuid)
to authenticated;
