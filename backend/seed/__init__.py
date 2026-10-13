"""
Seed module for initial data.

Provides functions to populate the database with initial skills and optional test data.
"""

from sqlalchemy.orm import Session
from app.models import Skill
from app.repositories.skill_repository import SkillRepository


def seed_skills(db: Session) -> None:
    """
    Create the four core skills if they don't already exist.

    Args:
        db: Database session
    """
    skills = [
        {
            "code": "SOURCE",
            "name": "Source Analysis",
            "description": "Ability to analyze the origin and source of information",
        },
        {
            "code": "EVIDENCE",
            "name": "Evidence Evaluation",
            "description": "Ability to evaluate the evidence presented to support a claim",
        },
        {
            "code": "CONTEXT",
            "name": "Context Perception",
            "description": "Ability to perceive omitted, distorted, or incompatible context",
        },
        {
            "code": "VISUAL",
            "name": "Visual Analysis",
            "description": "Ability to evaluate if an image really supports the presented claim",
        },
    ]

    for skill_data in skills:
        existing = SkillRepository.get_skill_by_code(db, skill_data["code"])
        if not existing:
            skill = Skill(**skill_data)
            db.add(skill)
    
    db.commit()


# Notícias fictícias para o MVP do jogo: uma pergunta por notícia, três por skill.
# As pistas para responder estão no próprio texto da notícia.
# image_url aponta para arquivos em frontend/public/demo, servidos pelo Next.js.
SAMPLE_ROUNDS = [
    # SOURCE
    {
        "skill": "SOURCE",
        "title": "Médico de hospital renomado revela que chá de boldo cura diabetes",
        "content": "Áudio compartilhado no WhatsApp atribui a receita a \"um médico do maior hospital da capital\". "
                   "O nome do médico não é citado. Procurado, o hospital afirmou que não reconhece o áudio.",
        "image_url": None,
        "verdict": "falso",
        "text": "O que torna a fonte desta mensagem pouco confiável?",
        "difficulty": 0.3,
        "options": {
            "A": "Nada: o áudio cita um hospital conhecido.",
            "B": "O médico não é identificado e o próprio hospital não confirma a informação.",
            "C": "Mensagens de áudio são sempre falsas.",
        },
        "correct_option": "B",
        "explanation": "Citar uma instituição famosa não torna a fonte confiável. Sem autor identificado e com a "
                       "instituição negando, a mensagem não tem origem verificável.",
    },
    {
        "skill": "SOURCE",
        "title": "Governo vai bloquear poupanças a partir de segunda-feira",
        "content": "A notícia foi publicada pelo site \"jornaldaverdade-urgente.com\", criado há duas semanas. "
                   "O site não informa quem são seus responsáveis e nenhum outro veículo publicou a informação.",
        "image_url": None,
        "verdict": "falso",
        "text": "Qual o melhor primeiro passo para avaliar essa fonte?",
        "difficulty": 0.4,
        "options": {
            "A": "Verificar quem mantém o site e se veículos estabelecidos publicaram o mesmo fato.",
            "B": "Contar quantas pessoas já compartilharam a notícia.",
            "C": "Confiar, já que o nome do site tem a palavra \"jornal\".",
        },
        "correct_option": "A",
        "explanation": "Sites recém-criados, sem responsáveis identificados e sem repercussão em outros veículos "
                       "são sinais de alerta. O nome do site e o número de compartilhamentos não dizem nada sobre a veracidade.",
    },
    {
        "skill": "SOURCE",
        "title": "Escolas públicas terão aulas suspensas por um mês",
        "content": "O anúncio foi feito por um perfil chamado \"Notícias Nacional Oficial\", com logotipo parecido "
                   "com o de uma emissora conhecida. O perfil foi criado no mês passado e a notícia não aparece "
                   "no site nem nas redes oficiais da emissora.",
        "image_url": None,
        "verdict": "falso",
        "text": "O que indica que o perfil pode não ser quem aparenta?",
        "difficulty": 0.5,
        "options": {
            "A": "O logotipo é parecido com o da emissora, então é confiável.",
            "B": "O perfil tem muitos seguidores, então é confiável.",
            "C": "O perfil é recente e a notícia não aparece nos canais oficiais da emissora.",
        },
        "correct_option": "C",
        "explanation": "Perfis que imitam veículos conhecidos são comuns. Compare com os canais oficiais: "
                       "se a notícia não está lá, desconfie.",
    },
    # EVIDENCE
    {
        "skill": "EVIDENCE",
        "title": "Estudo prova que celular no bolso causa queda de cabelo",
        "content": "A postagem diz que \"pesquisadores comprovaram\" o efeito, mas não cita o estudo, a "
                   "instituição nem traz link. A única prova apresentada são depoimentos de três pessoas.",
        "image_url": None,
        "verdict": "falso",
        "text": "As evidências apresentadas sustentam a afirmação?",
        "difficulty": 0.35,
        "options": {
            "A": "Sim, há depoimentos de pessoas afetadas.",
            "B": "Não: poucos depoimentos e um estudo não identificável não comprovam causa e efeito.",
            "C": "Sim, porque menciona pesquisadores.",
        },
        "correct_option": "B",
        "explanation": "Depoimentos isolados não mostram causa. Uma afirmação científica precisa de um estudo "
                       "identificável, que possa ser consultado.",
    },
    {
        "skill": "EVIDENCE",
        "title": "Assaltos explodem no bairro: alta de 300%!",
        "content": "A postagem usa dados da delegacia local: os registros de assalto no bairro passaram de 2 "
                   "para 8 casos de um mês para o outro.",
        "image_url": None,
        "verdict": "enganoso",
        "text": "O que é preciso considerar para avaliar a gravidade da situação?",
        "difficulty": 0.6,
        "options": {
            "A": "Os números absolutos e o período: 2 para 8 casos em um mês é pouco para indicar uma tendência.",
            "B": "Nada: um aumento de 300% já mostra que a situação é grave.",
            "C": "Apenas quem escreveu a postagem.",
        },
        "correct_option": "A",
        "explanation": "Porcentagens sobre números pequenos parecem assustadoras. Olhe os valores absolutos e "
                       "compare períodos maiores antes de concluir que há uma tendência.",
    },
    {
        "skill": "EVIDENCE",
        "title": "Remédio caseiro baixa a febre em uma hora, garante enfermeira",
        "content": "Em um vídeo, uma mulher que se apresenta como enfermeira mede a temperatura de uma criança "
                   "antes e depois de aplicar uma compressa de vinagre. Não há outros dados.",
        "image_url": None,
        "verdict": "sem_evidencia",
        "text": "Que tipo de evidência seria necessária para confiar nessa afirmação?",
        "difficulty": 0.55,
        "options": {
            "A": "Mais visualizações no vídeo.",
            "B": "Outro vídeo mostrando o mesmo procedimento.",
            "C": "Estudos com muitos participantes e grupo de comparação, ou orientação de órgãos de saúde.",
        },
        "correct_option": "C",
        "explanation": "Um único caso não separa o efeito do remédio de uma melhora que aconteceria de qualquer "
                       "forma. Estudos controlados e órgãos de saúde dão evidência mais sólida.",
    },
    # CONTEXT
    {
        "skill": "CONTEXT",
        "title": "Prefeitura anuncia aumento de 50% na tarifa de ônibus",
        "content": "A mensagem circula hoje com um link para a reportagem original. Ao abrir o link, a data da "
                   "reportagem é de 2019, e uma atualização no fim do texto informa que o aumento foi revogado.",
        "image_url": None,
        "verdict": "enganoso",
        "text": "Qual o principal problema dessa mensagem?",
        "difficulty": 0.3,
        "options": {
            "A": "Uma notícia antiga, que já não vale, está sendo apresentada como atual.",
            "B": "A prefeitura não existe.",
            "C": "Nenhum: a reportagem é real.",
        },
        "correct_option": "A",
        "explanation": "Uma reportagem verdadeira pode enganar fora do seu tempo. Sempre confira a data e se "
                       "houve atualizações.",
    },
    {
        "skill": "CONTEXT",
        "title": "Cientista admite: \"a vacina não funciona\"",
        "content": "O vídeo compartilhado tem 10 segundos. Na entrevista completa, de 5 minutos, a cientista "
                   "diz: \"dizer que a vacina não funciona é um mito que já foi desmentido\".",
        "image_url": None,
        "verdict": "falso",
        "text": "Por que o vídeo curto é enganoso?",
        "difficulty": 0.45,
        "options": {
            "A": "Não é: a frase aparece no vídeo.",
            "B": "A frase foi recortada e, sem o resto da fala, tem o sentido invertido.",
            "C": "A cientista mudou de ideia depois.",
        },
        "correct_option": "B",
        "explanation": "Recortes podem inverter o sentido de uma fala. Procure a versão completa antes de "
                       "compartilhar uma citação curta.",
    },
    {
        "skill": "CONTEXT",
        "title": "País registra a maior temperatura de sua história",
        "content": "O dado vem de uma única estação meteorológica, que bateu o próprio recorde local. Segundo o "
                   "instituto de meteorologia, a temperatura ficou abaixo do recorde nacional.",
        "image_url": None,
        "verdict": "enganoso",
        "text": "Como a manchete distorce o contexto?",
        "difficulty": 0.65,
        "options": {
            "A": "Não distorce: a temperatura foi mesmo recorde.",
            "B": "O termômetro da estação estava quebrado.",
            "C": "Transforma o recorde de uma estação local em recorde de todo o país.",
        },
        "correct_option": "C",
        "explanation": "O fato existe, mas a manchete amplia seu alcance. Verifique a que lugar e período o dado "
                       "realmente se refere.",
    },
    # VISUAL
    {
        "skill": "VISUAL",
        "title": "Foto mostra enchente que atingiu o centro da cidade nesta semana",
        "content": "A postagem afirma que a imagem foi registrada ontem, após a chuva da madrugada. Uma busca "
                   "reversa encontra a mesma foto em uma reportagem de 2014 sobre uma enchente em outra cidade.",
        "image_url": "/demo/enchente.svg",
        "verdict": "enganoso",
        "text": "A imagem realmente mostra o evento descrito?",
        "difficulty": 0.4,
        "options": {
            "A": "Sim, a imagem corresponde ao evento descrito.",
            "B": "Não: a foto é antiga, de outro lugar, e foi usada fora de contexto.",
            "C": "Não é possível saber nada sobre a origem de uma imagem.",
        },
        "correct_option": "B",
        "explanation": "Uma foto real usada fora de contexto não comprova a alegação. A busca reversa ajuda a "
                       "descobrir quando e onde a imagem apareceu primeiro.",
    },
    {
        "skill": "VISUAL",
        "title": "Tubarão nada em avenida alagada após tempestade",
        "content": "A mesma foto volta a viralizar a cada grande enchente, em países diferentes. Observando com "
                   "atenção, a barbatana não tem reflexo nem ondulação na água ao redor, ao contrário dos carros.",
        "image_url": "/demo/tubarao.svg",
        "verdict": "falso",
        "text": "O que a imagem indica?",
        "difficulty": 0.5,
        "options": {
            "A": "É uma montagem: o tubarão não interage com a água e a foto reaparece em eventos diferentes.",
            "B": "É uma foto autêntica da tempestade.",
            "C": "É um tubarão que fugiu de um aquário.",
        },
        "correct_option": "A",
        "explanation": "Elementos sem sombra, reflexo ou interação com o ambiente são sinais de montagem. Fotos "
                       "que reaparecem em vários eventos também merecem desconfiança.",
    },
    {
        "skill": "VISUAL",
        "title": "Multidão lota a praça para o show gratuito de ontem",
        "content": "O show aconteceu em pleno verão. Na foto, o público usa casacos e gorros, e uma faixa ao "
                   "fundo traz o nome \"Festival de Inverno 2018\".",
        "image_url": "/demo/multidao.svg",
        "verdict": "enganoso",
        "text": "O que na imagem contradiz a legenda?",
        "difficulty": 0.6,
        "options": {
            "A": "Nada, a foto mostra uma multidão como a legenda diz.",
            "B": "A quantidade de pessoas.",
            "C": "As roupas de inverno e a faixa de outro evento mostram que a foto é de outra ocasião.",
        },
        "correct_option": "C",
        "explanation": "Detalhes como roupas, clima, faixas e placas ajudam a datar e localizar uma imagem. "
                       "Compare-os com o que a legenda afirma.",
    },
]


def seed_sample_news_and_questions(db: Session) -> None:
    """
    Ensure the reviewed sample questions exist, even alongside imported news.

    Args:
        db: Database session
    """
    from app.models import News, Question
    from app.repositories.skill_repository import SkillRepository

    seed_skills(db)
    skills_by_code = {skill.code: skill for skill in SkillRepository.get_all_skills(db)}

    for item in SAMPLE_ROUNDS:
        news = (
            db.query(News)
            .filter(News.title == item["title"], News.content == item["content"])
            .first()
        )
        if news is None:
            news = News(
                title=item["title"],
                content=item["content"],
                image_url=item["image_url"],
                verdict=item["verdict"],
                fact_check_data={"seed_key": f"game-demo-v1:{item['skill']}:{item['title']}"},
            )
            db.add(news)
            db.flush()

        skill_id = skills_by_code[item["skill"]].id
        question = (
            db.query(Question)
            .filter_by(news_id=news.id, skill_id=skill_id, text=item["text"])
            .first()
        )
        if question is None:
            db.add(
                Question(
                    news_id=news.id,
                    skill_id=skill_id,
                    text=item["text"],
                    difficulty=item["difficulty"],
                    options=item["options"],
                    correct_option=item["correct_option"],
                    explanation=item["explanation"],
                )
            )

    db.commit()
