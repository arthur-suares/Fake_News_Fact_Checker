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


def seed_sample_news_and_questions(db: Session) -> None:
    """
    Create sample news and questions for testing.

    This is a minimal set just to demonstrate the system.
    More comprehensive content should be added via RF-19.

    Args:
        db: Database session
    """
    from app.models import News, Question
    from app.repositories.skill_repository import SkillRepository
    from app.repositories.question_repository import NewsRepository

    # Only create if no news exists yet
    existing_news = NewsRepository.get_all_news(db, limit=1)
    if existing_news:
        return

    # Get all skills
    skills = SkillRepository.get_all_skills(db)
    if not skills:
        seed_skills(db)
        skills = SkillRepository.get_all_skills(db)

    # Create a sample news item
    news = News(
        title="Exemplo de notícia para teste",
        content="Esta é uma notícia de exemplo para testar o sistema de jogo. " 
                "Ela será usada para criar perguntas associadas a diferentes habilidades.",
        image_url=None,
        verdict=None,
        fact_check_data={},
    )
    db.add(news)
    db.commit()
    db.refresh(news)

    # Create sample questions for each skill
    for skill in skills:
        if skill.code == "SOURCE":
            question = Question(
                news_id=news.id,
                skill_id=skill.id,
                text="Qual é a fonte primária desta informação?",
                difficulty=0.5,
                options={
                    "A": "Fonte oficial do governo",
                    "B": "Rede social sem verificação",
                    "C": "Jornalista independente",
                    "D": "Boato de rua",
                },
                correct_option="A",
                explanation="Fontes oficiais tendem a ser mais confiáveis.",
            )
        elif skill.code == "EVIDENCE":
            question = Question(
                news_id=news.id,
                skill_id=skill.id,
                text="Há evidências científicas suficientes para esta alegação?",
                difficulty=0.6,
                options={
                    "A": "Sim, com estudos publicados",
                    "B": "Não, apenas especulação",
                    "C": "Resultados conflitantes",
                    "D": "Ainda não há pesquisa",
                },
                correct_option="A",
                explanation="Evidências científicas são importantes para validar alegações.",
            )
        elif skill.code == "CONTEXT":
            question = Question(
                news_id=news.id,
                skill_id=skill.id,
                text="O contexto histórico foi considerado?",
                difficulty=0.7,
                options={
                    "A": "Sim, totalmente",
                    "B": "Não, contexto ignorado",
                    "C": "Parcialmente",
                    "D": "Contexto irrelevante",
                },
                correct_option="A",
                explanation="O contexto é essencial para interpretar corretamente uma alegação.",
            )
        elif skill.code == "VISUAL":
            question = Question(
                news_id=news.id,
                skill_id=skill.id,
                text="A imagem é relevante para a alegação?",
                difficulty=0.5,
                options={
                    "A": "Sim, suporta completamente",
                    "B": "Não, imagem antiga/fora de contexto",
                    "C": "Parcialmente relevante",
                    "D": "Imagem manipulada",
                },
                correct_option="A",
                explanation="Imagens manipuladas ou fora de contexto são comuns em desinformação.",
            )

        db.add(question)

    db.commit()
