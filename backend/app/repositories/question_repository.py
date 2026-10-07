"""
Question Repository - Database access layer for question-related entities.

Handles Question and News operations.
"""

from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models import Question, News


class QuestionRepository:
    """Repository for question-related database operations."""

    @staticmethod
    def get_question_by_id(db: Session, question_id: str) -> Question | None:
        """
        Retrieve a question by ID.

        Args:
            db: Database session
            question_id: ID of the question

        Returns:
            Question instance or None if not found
        """
        return db.query(Question).filter(Question.id == question_id).first()

    @staticmethod
    def get_questions_by_skill(
        db: Session,
        skill_id: str,
        limit: int | None = 100,
    ) -> list[Question]:
        """
        Get questions for a specific skill.

        Args:
            db: Database session
            skill_id: ID of the skill
            limit: Maximum number of questions to retrieve

        Returns:
            List of Question instances
        """
        query = db.query(Question).filter(Question.skill_id == skill_id)
        if limit is not None:
            query = query.limit(limit)
        return query.order_by(Question.id).all()

    @staticmethod
    def get_all_questions(db: Session) -> list[Question]:
        """Get all questions in stable ID order for selector fallback."""
        return db.query(Question).order_by(Question.id).all()

    @staticmethod
    def get_questions_by_news(db: Session, news_id: str) -> list[Question]:
        """
        Get all questions for a news item.

        Args:
            db: Database session
            news_id: ID of the news

        Returns:
            List of Question instances
        """
        return db.query(Question).filter(Question.news_id == news_id).all()

    @staticmethod
    def get_random_question_for_skill(
        db: Session,
        skill_id: str,
        exclude_ids: list[str] | None = None,
    ) -> Question | None:
        """
        Get a random question for a skill (excluding specific questions).

        Args:
            db: Database session
            skill_id: ID of the skill
            exclude_ids: Question IDs to exclude from selection

        Returns:
            Random Question instance or None if none available
        """
        query = db.query(Question).filter(Question.skill_id == skill_id)

        if exclude_ids:
            query = query.filter(Question.id.notin_(exclude_ids))

        # Order by random and get first
        # SQLite uses random(), PostgreSQL uses random()
        try:
            result = query.order_by(func.random()).first()
        except Exception:
            # Fallback to simple limit if random() not supported
            result = query.first()

        return result

    @staticmethod
    def get_questions_for_skill_paginated(
        db: Session,
        skill_id: str,
        offset: int = 0,
        limit: int = 20,
    ) -> list[Question]:
        """
        Get paginated questions for a skill.

        Args:
            db: Database session
            skill_id: ID of the skill
            offset: Number of questions to skip
            limit: Number of questions to return

        Returns:
            List of Question instances
        """
        return (
            db.query(Question)
            .filter(Question.skill_id == skill_id)
            .offset(offset)
            .limit(limit)
            .all()
        )


class NewsRepository:
    """Repository for news-related database operations."""

    @staticmethod
    def get_news_by_id(db: Session, news_id: str) -> News | None:
        """
        Retrieve news by ID.

        Args:
            db: Database session
            news_id: ID of the news

        Returns:
            News instance or None if not found
        """
        return db.query(News).filter(News.id == news_id).first()

    @staticmethod
    def get_all_news(db: Session, limit: int = 100) -> list[News]:
        """
        Get all news items.

        Args:
            db: Database session
            limit: Maximum number of news to retrieve

        Returns:
            List of News instances
        """
        return (
            db.query(News)
            .order_by(News.created_at.desc())
            .limit(limit)
            .all()
        )

    @staticmethod
    def get_random_news(db: Session, exclude_ids: list[str] | None = None) -> News | None:
        """
        Get a random news item (excluding specific news).

        Args:
            db: Database session
            exclude_ids: News IDs to exclude from selection

        Returns:
            Random News instance or None if none available
        """
        query = db.query(News)

        if exclude_ids:
            query = query.filter(News.id.notin_(exclude_ids))

        try:
            result = query.order_by(func.random()).first()
        except Exception:
            # Fallback if random() not supported
            result = query.first()

        return result

    @staticmethod
    def create_news(
        db: Session,
        title: str,
        content: str,
        image_url: str | None = None,
        verdict: str | None = None,
        fact_check_data: dict | None = None,
    ) -> News:
        """
        Create a new news item.

        Args:
            db: Database session
            title: Title of the news
            content: Content of the news
            image_url: URL to associated image
            verdict: Fact-check verdict
            fact_check_data: Additional fact-check data

        Returns:
            Created News instance
        """
        news = News(
            title=title,
            content=content,
            image_url=image_url,
            verdict=verdict,
            fact_check_data=fact_check_data,
        )
        db.add(news)
        db.commit()
        db.refresh(news)
        return news
