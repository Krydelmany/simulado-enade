-- Tira e-mail do ranking. Roda DEPOIS de 20261022020000_ranking_com_nome.sql.
--
-- A primeira versão do formulário da turma (21/10) sugeria como apelido o
-- primeiro "pedaço" do nome, e para quem não tinha nome no perfil (link de
-- e-mail, conta Google sem nome) esse nome era o E-MAIL. O ranking mostra o
-- apelido quando falta o nome, então os colegas viam "fulano@gmail.co". O
-- app de hoje não deriva mais nada do e-mail e pede o nome a quem não tem.
update public.membros set apelido = 'Sem nome' where apelido like '%@%';
