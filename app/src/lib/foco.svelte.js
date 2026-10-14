// Tela de questão em andamento: o layout esconde a tab bar do celular e
// reserva espaço para a barra de ação fixa. Treino e Estudo são reconhecidos
// pela URL; o Simulado só vira tela de questão depois que a prova começa
// (a página inicial do modo é uma página comum), então avisa por aqui.
export const foco = $state({ quiz: false });
