-- Simulado agendado pelo professor (P1) e reporte de erro em questão (P3).
--
-- Roda DEPOIS de 20261021000000_turmas.sql. Arquivo que já rodou em produção
-- não se edita: mudança nova = arquivo novo.
--
-- Decisões (docs/DECISOES.md):
--   D12  o professor sorteia a prova no próprio navegador (o mesmo
--        `montarProva` do simulado individual) e o banco guarda só a lista
--        de ids. Cada resposta da prova sobe com `simulado_id`, então o
--        resultado é uma consulta sobre `respostas`, como o resto do painel.
--   D13  reportar erro não exige conta: quem estuda sem login também acha
--        gabarito errado. O teto por hora segura enxurrada.
--
-- Mesmas regras do arquivo anterior: tabela sem grant (só as funções
-- `security definer` mexem nela) e toda função com `set search_path = ''`.

-- ---------------------------------------------------------------------------
-- Simulados da turma
-- ---------------------------------------------------------------------------

-- id de questão do app: 2019-CE-Q09, 2014-FG-D01, GER-XVIII-F1
create function public.ids_de_questao_validos(ids text[])
returns boolean
language sql
immutable
set search_path = ''
as $$
	select coalesce(bool_and(x ~ '^[A-Z0-9-]{3,40}$'), false) from unnest(ids) as x;
$$;

create table public.simulados (
	id uuid primary key default gen_random_uuid(),
	turma_id uuid not null references public.turmas (id) on delete cascade,
	titulo text not null check (char_length(btrim(titulo)) between 2 and 80),
	-- na ordem da prova (FG, CE, discursiva): o app corrige por posição
	questoes text[] not null check (cardinality(questoes) between 1 and 60 and public.ids_de_questao_validos(questoes)),
	objetivas smallint not null check (objetivas between 1 and 60),
	abre_em timestamptz not null,
	fecha_em timestamptz not null,
	criado_por uuid references public.perfis (id) on delete set null,
	criado_em timestamptz not null default now(),
	check (fecha_em > abre_em),
	check (fecha_em - abre_em <= interval '60 days')
);

create index simulados_turma on public.simulados (turma_id, abre_em desc);

alter table public.simulados enable row level security;
revoke all on public.simulados from anon, authenticated;

alter table public.respostas
	add column simulado_id uuid references public.simulados (id) on delete set null;

create index respostas_simulado on public.respostas (simulado_id) where simulado_id is not null;

grant insert (simulado_id) on public.respostas to authenticated;

-- Resposta com simulado_id de turma que não é a do aluno (ou de simulado que
-- já foi apagado) entra SEM o vínculo, em vez de ser recusada. Recusar
-- travaria a fila do aparelho: o lote inteiro voltaria com erro para sempre,
-- e o aluno que saiu da turma antes de a internet voltar perderia até as
-- respostas do treino que estavam no mesmo lote.
create function public.conferir_simulado_da_resposta()
returns trigger
language plpgsql
security definer
set search_path = ''
as $$
begin
	if new.simulado_id is not null and not exists (
		select 1
		from public.simulados s
		join public.membros m on m.turma_id = s.turma_id and m.usuario_id = new.usuario_id
		where s.id = new.simulado_id
	) then
		new.simulado_id := null;
	end if;
	return new;
end;
$$;

create trigger respostas_conferir_simulado
before insert on public.respostas
for each row execute function public.conferir_simulado_da_resposta();

-- O professor agenda. A lista de ids vem sorteada do app.
create function public.criar_simulado(
	p_turma uuid,
	p_titulo text,
	p_questoes text[],
	p_objetivas integer,
	p_abre timestamptz,
	p_fecha timestamptz
)
returns setof public.simulados
language plpgsql
security definer
set search_path = ''
as $$
begin
	if not public.eh_professor(p_turma) then
		raise exception 'sem_permissao' using errcode = '42501';
	end if;
	return query
	insert into public.simulados (turma_id, titulo, questoes, objetivas, abre_em, fecha_em, criado_por)
	values (p_turma, btrim(p_titulo), p_questoes, p_objetivas, p_abre, p_fecha, auth.uid())
	returning *;
end;
$$;

-- Apagar o simulado não apaga as respostas: elas continuam no treino de cada
-- aluno, só perdem o vínculo (`on delete set null`).
create function public.apagar_simulado(p_simulado uuid)
returns void
language plpgsql
security definer
set search_path = ''
as $$
begin
	delete from public.simulados s
	where s.id = p_simulado and public.eh_professor(s.turma_id);
	if not found then
		raise exception 'sem_permissao' using errcode = '42501';
	end if;
end;
$$;

-- Os simulados da turma, para qualquer membro. Antes de abrir, o aluno não
-- recebe a lista de questões: senão dava para estudar exatamente a prova.
create function public.simulados_turma(p_turma uuid)
returns table (
	id uuid,
	titulo text,
	questoes text[],
	objetivas smallint,
	abre_em timestamptz,
	fecha_em timestamptz
)
language sql
stable
security definer
set search_path = ''
as $$
	select s.id, s.titulo,
		case when now() >= s.abre_em or public.eh_professor(p_turma) then s.questoes end,
		s.objetivas, s.abre_em, s.fecha_em
	from public.simulados s
	where s.turma_id = p_turma and public.eh_membro(p_turma)
	order by s.abre_em desc;
$$;

-- Resultado por aluno. Vale a PRIMEIRA resposta de cada questão: refazer a
-- prova depois de ver a correção não melhora a nota no painel.
-- Discursiva (id terminado em -Dnn) fica fora: é autoavaliada.
create function public.painel_simulado(p_simulado uuid)
returns table (
	usuario_id uuid,
	nome text,
	apelido text,
	ra text,
	respondidas bigint,
	certas bigint,
	entregue_em timestamptz
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
		select distinct on (r.usuario_id, r.questao_id) r.usuario_id, r.questao_id, r.resultado, r.respondida_em
		from public.respostas r
		join s on r.simulado_id = s.id
		where r.questao_id !~ '-D[0-9]+$'
		order by r.usuario_id, r.questao_id, r.respondida_em
	)
	select m.usuario_id, p.nome, m.apelido, m.ra,
		count(f.questao_id),
		count(f.questao_id) filter (where f.resultado in ('certa', 'anulada')),
		max(f.respondida_em)
	from s
	join public.membros m on m.turma_id = s.turma_id and m.papel = 'aluno'
	join public.perfis p on p.id = m.usuario_id
	left join primeira f on f.usuario_id = m.usuario_id
	group by m.usuario_id, p.nome, m.apelido, m.ra
	order by count(f.questao_id) = 0, 6 desc, 3;
$$;

-- Por questão (o app agrega por matéria): a lista da aula de correção.
create function public.painel_simulado_questoes(p_simulado uuid)
returns table (questao_id text, materia text, respondidas bigint, certas bigint)
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
		select distinct on (r.usuario_id, r.questao_id) r.questao_id, r.materia, r.resultado
		from public.respostas r
		join s on r.simulado_id = s.id
		join public.membros m on m.turma_id = s.turma_id and m.usuario_id = r.usuario_id and m.papel = 'aluno'
		where r.questao_id !~ '-D[0-9]+$'
		order by r.usuario_id, r.questao_id, r.respondida_em
	)
	select f.questao_id, max(f.materia), count(*), count(*) filter (where f.resultado in ('certa', 'anulada'))
	from primeira f
	group by f.questao_id
	-- pior acerto primeiro (ordinal dentro de expressão vira constante: escrito por extenso)
	order by (count(*) filter (where f.resultado in ('certa', 'anulada')))::numeric / count(*), 1;
$$;

-- ---------------------------------------------------------------------------
-- Reporte de erro em questão
-- ---------------------------------------------------------------------------

-- Lido por nós no painel do Supabase (Table Editor → reportes). Ninguém lê
-- pelo site: sem policy e sem grant.
create table public.reportes (
	id uuid primary key default gen_random_uuid(),
	usuario_id uuid references public.perfis (id) on delete set null,
	curso text not null default 'engcomp' references public.cursos (id),
	questao_id text not null check (questao_id ~ '^[A-Z0-9-]{3,40}$'),
	motivo text not null check (motivo in ('gabarito', 'enunciado', 'resolucao', 'imagem', 'outro')),
	detalhe text not null default '' check (char_length(detalhe) <= 1000),
	criado_em timestamptz not null default now(),
	resolvido_em timestamptz
);

create index reportes_abertos on public.reportes (criado_em desc) where resolvido_em is null;

alter table public.reportes enable row level security;
revoke all on public.reportes from anon, authenticated;

create function public.reportar_questao(p_questao text, p_motivo text, p_detalhe text default '')
returns void
language plpgsql
security definer
set search_path = ''
as $$
begin
	-- teto por hora: 20 por pessoa logada; 200 somando todos os anônimos
	if auth.uid() is null then
		if (select count(*) from public.reportes r
			where r.usuario_id is null and r.criado_em > now() - interval '1 hour') >= 200 then
			raise exception 'muitos_reportes' using errcode = '54000';
		end if;
	elsif (select count(*) from public.reportes r
		where r.usuario_id = auth.uid() and r.criado_em > now() - interval '1 hour') >= 20 then
		raise exception 'muitos_reportes' using errcode = '54000';
	end if;

	insert into public.reportes (usuario_id, questao_id, motivo, detalhe)
	values (
		(select p.id from public.perfis p where p.id = auth.uid()),
		p_questao,
		p_motivo,
		left(btrim(coalesce(p_detalhe, '')), 1000)
	);
end;
$$;

-- ---------------------------------------------------------------------------
-- Permissões das funções
-- ---------------------------------------------------------------------------

revoke all on function
	public.ids_de_questao_validos(text[]),
	public.conferir_simulado_da_resposta(),
	public.criar_simulado(uuid, text, text[], integer, timestamptz, timestamptz),
	public.apagar_simulado(uuid),
	public.simulados_turma(uuid),
	public.painel_simulado(uuid),
	public.painel_simulado_questoes(uuid),
	public.reportar_questao(text, text, text)
from public, anon;

grant execute on function
	public.criar_simulado(uuid, text, text[], integer, timestamptz, timestamptz),
	public.apagar_simulado(uuid),
	public.simulados_turma(uuid),
	public.painel_simulado(uuid),
	public.painel_simulado_questoes(uuid),
	public.reportar_questao(text, text, text)
to authenticated;

grant execute on function public.reportar_questao(text, text, text) to anon;
