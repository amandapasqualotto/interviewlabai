# curadoria.py

INSIGHTS_GERAIS = """
DIRETRIZES DE AVALIAÇÃO DE RESPOSTAS EM ENTREVISTAS:
1. Alinhamento com a Vaga: Conectar exemplos aos valores da empresa e utilizar palavras-chave presentes no descritivo da vaga.
2. Estruturação Técnica e Storytelling: Perguntas comportamentais devem seguir STAR; perguntas de trajetória/visão pessoal devem usar Storytelling (Passado, Presente e Futuro com aprendizados marcantes).
3. Objetividade e Clareza: Evitar rodeios mantendo detalhes concretos (métricas, aprendizados, impactos).
4. Postura e Tom: Demonstrar autoconhecimento, inteligência emocional e capacidade de aprendizagem contínua.
"""

PERGUNTAS_CURATORIA = {
    "Descreva uma situação em que você precisou se adaptar rapidamente a uma nova demanda ou contexto": {
        "tecnica": "STAR (Situação, Tarefa, Ação e Resultado)",
        "expectativa": "Avalia flexibilidade, resiliência e agilidade de aprendizado. Espera-se que o candidato mostre como manteve a calma, reorganizou prioridades e gerou resultado rápido."
    },
    "Conte sobre uma situação em que você identificou uma oportunidade de melhoria ou um problema e tomou a iniciativa para resolvê-lo ou propor uma solução.": {
        "tecnica": "STAR",
        "expectativa": "Avalia proatividade, senso de dono (ownership) e visão crítica. Espera-se que o candidato não tenha apenas apontado o problema, mas liderado/executado a solução."
    },
    "Como você busca aprender e se desenvolver em novas áreas ou com novas ferramentas? Dê um exemplo de algo que você aprendeu recentemente por iniciativa própria.": {
        "tecnica": "Exemplo Prático + Aplicação",
        "expectativa": "Avalia 'Lifelong Learning' e curiosidade. Espera-se demonstrar métodos de estudo autônomos (cursos, projetos, testes) e o impacto prático do que foi aprendido."
    },
    "Descreva uma situação em que você precisou colaborar com outras pessoas para alcançar um objetivo. Como foi sua participação e qual foi o resultado?": {
        "tecnica": "STAR",
        "expectativa": "Avalia trabalho em equipe, empatia e inteligência interpessoal. Espera-se foco no papel do candidato sem anular a contribuição do grupo."
    },
    "Para começar, conte-me sobre sua trajetória profissional e formação. Quanto tempo de experiência você tem na área, quais foram suas principais responsabilidades e atividades em cada cargo": {
        "tecnica": "Pitch Pessoal (Passado, Presente e Futuro)",
        "expectativa": "Resumo cronológico e estratégico. Espera-se destaque aos marcos mais relevantes e conexões diretas entre o histórico e o momento atual/objetivo da vaga."
    },
    "Descreva uma situação em que você precisou explicar algo complexo para alguém que não tinha conhecimento técnico. Como você adaptou sua comunicação?": {
        "tecnica": "STAR (Foco em Didática)",
        "expectativa": "Avalia comunicação adaptável e empatia. Espera-se o uso de analogias, escuta ativa e verificação de entendimento do interlocutor."
    },
    "Conte uma vez em que você precisou 'trocar o pneu com o carro em movimento' — ou seja, manter algo funcionando enquanto tentava melhorar o processo. O que você priorizou em cada etapa para não deixar a peteca cair?": {
        "tecnica": "STAR (Foco em Priorização e Gestão de Risco)",
        "expectativa": "Avalia gestão sob pressão, triagem de tarefas críticas e capacidade de otimização contínua."
    },
    "Relate uma ocasião em que algo não saiu como o planejado ou em que você cometeu um erro em um projeto. Como você reagiu no momento, o que aprendeu com essa experiência e o que mudou na sua forma de trabalhar depois disso?": {
        "tecnica": "STAR (Foco na Reação, Aprendizado e Prevenção)",
        "expectativa": "Avalia maturidade, autorresponsabilidade e inteligência emocional. Não busque culpar terceiros; foque no aprendizado e na mudança de processo."
    },
    "Você mencionou que aprendeu com a experiência e que teve um fio condutor para resolver problemas semelhantes no futuro. Poderia compartilhar um exemplo específico de como você aplicou esse aprendizado em uma situação posterior?": {
        "tecnica": "STAR (Foco na Aplicação Prática da Lição Aprendida)",
        "expectativa": "Demonstrar a evolução e maturidade profissional após uma falha ou aprendizado prévio."
    },
    "Como a Inteligência Artificial faz parte da sua rotina atual? Como você a utiliza para resolver problemas cotidianos sem perder a visão crítica do resultado? Consegue nos dar algum exemplo mais concreto?": {
        "tecnica": "Uso Prático + Pensamento Crítico",
        "expectativa": "Avalia afinidade tecnológica e critério. O candidato deve citar ferramentas e ressaltar a checagem de fatos/supervisão humana."
    },
    "Conte sobre uma vez em que você discordou da opinião de um colega ou líder em um trabalho em grupo. Como você defendeu suas ideias e como chegaram a um consenso?": {
        "tecnica": "STAR (Foco em Negociação e Argumentação Baseada em Dados)",
        "expectativa": "Avalia diplomacia, escuta e capacidade de construir consensos focando no objetivo do projeto."
    },
    "Como você acredita que suas habilidades e interesses se alinham a essa missão e como você gostaria de contribuir para gerar impacto?": {
        "tecnica": "Conexão de Valores e Competências",
        "expectativa": "Demonstrar pesquisa prévia sobre a empresa, alinhando propósitos pessoais aos objetivos organizacionais."
    },
    "Porque vc é o melhor candidato para esse cargo?": {
        "tecnica": "Value Pitch (Diferencial Competitivo)",
        "expectativa": "Conexão direta entre hard/soft skills do candidato e as dores/necessidades imediatas descritas na vaga."
    },
    "Porque a nossa empresa?": {
        "tecnica": "Storytelling de Conexão de Propósito",
        "expectativa": "Contar o ponto de contato em que sua história cruzou com a missão, produto ou cultura da empresa, mostrando pesquisa prévia."
    },
    "Conte sobre uma vez em que você teve múltiplas entregas simultâneas. Como você organizou seu tempo e garantiu que todas fossem cumpridas?": {
        "tecnica": "STAR (Foco em Metodologia de Organização)",
        "expectativa": "Citar métodos reais de priorização (Matriz de Eisenhower, listas, Notion, Kanban) e alinhamento de prazos."
    },
    "Fale sobre uma habilidade que você aprendeu recentemente por conta própria. O que te motivou e como foi o processo?": {
        "tecnica": "Motivação + Processo + Resultado",
        "expectativa": "Autonomia e curiosidade intelectiva. Mostrar o caminho percorrido do zero à aplicação prática."
    },
    "Me conte sobre você": {
        "tecnica": "Storytelling: Passado, Presente e Futuro (Elevator Pitch)",
        "expectativa": "Construir uma narrativa fluida (máx. 2 min) ligando a origem do seu interesse na área, momentos-chave da sua trajetória, sua atuação atual e por que esta oportunidade é o próximo passo natural."
    },
    "Onde você se vê daqui a 5 anos?": {
        "tecnica": "Storytelling de Visão e Conectividade",
        "expectativa": "Pintar uma imagem clara da sua evolução profissional alinhada aos desafios e à trilha de crescimento da empresa."
    },
    "Como você lida com pressão ou prazos apertados?": {
        "tecnica": "Estratégia de Controle + Exemplo STAR curto",
        "expectativa": "Inteligência emocional, foco em resolução de problemas e comunicação antecipada de riscos."
    },
    "Como você lida com equipes ou colaboração em grupo?": {
        "tecnica": "Estilo de Trabalho + Exemplo Prático",
        "expectativa": "Demonstrar adaptabilidade, boa comunicação, respeito à diversidade de opiniões e foco em metas coletivas."
    },
    "Você tem alguma pergunta?": {
        "tecnica": "Perguntas Estratégicas sobre o Negócio/Cultura",
        "expectativa": "Demonstrar interesse genuíno fazendo 2 a 3 perguntas sobre a rotina da área, desafios do setor ou cultura da empresa."
    },
    "Quais são seus pontos fortes": {
        "tecnica": "Fortaleza + Exemplo de Aplicação",
        "expectativa": "Citar 2 a 3 fortalezas relevantes para a vaga acompanhadas de breves evidências práticas."
    },
    "Quais são seus pontos fracos?": {
        "tecnica": "Storytelling de Vulnerabilidade + Plano de Ação",
        "expectativa": "Narrar um momento real de dificuldade sem clichês, mostrando a tomada de consciência e o método prático adotado para superá-lo."
    },
    "Com quais ferramentas, frameworks ou tecnologias você tem mais experiência?": {
        "tecnica": "Objetiva + Nível de Proficiência + Contexto de Uso",
        "expectativa": "Listar tecnologias pertinentes informando contexto de aplicação em projetos reais."
    },
    "Que legado você espera deixar nesta organização?": {
        "tecnica": "Visão de Impacto a Longo Prazo",
        "expectativa": "Demonstrar vontade de construir soluções duradouras, melhorar processos ou impactar positivamente a cultura do time."
    },
    "Você teve oportunidade de liderar um projeto? Conte-nos como foi o processo.": {
        "tecnica": "STAR (Foco em Gestão de Projeto e Pessoas)",
        "expectativa": "Demonstrar planejamento, delegação de tarefas, acompanhamento de métricas e contorno de imprevistos."
    },
    "Voce teve oportunidade de exercer liderança? Conte essa experiencia.": {
        "tecnica": "STAR (Foco em Liderança Situacional/Informal)",
        "expectativa": "Mesmo sem cargo formal, demonstrar iniciativa para guiar, apoiar ou destravar colegas em prol de um objetivo comum."
    }
}