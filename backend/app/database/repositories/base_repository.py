"""
Generic Base Repository

Provides abstract base class for all repositories.
Implements common CRUD operations using SQLAlchemy 2.x async patterns.

This repository follows the Repository Pattern and is completely generic,
allowing all concrete repositories to inherit standard CRUD functionality.

Design:
- Generic types for flexibility
- Async-first using AsyncSession
- No hardcoded queries
- Clean error handling
- Type-safe operations
- Dependency injection for sessions

Usage:
    class UserRepository(BaseRepository[User]):
        async def get_by_email(self, email: str) -> User | None:
            return await self.get_one(
                select(User).where(User.email == email)
            )
"""

from typing import Generic, TypeVar, Optional, List
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

# Generic model type
T = TypeVar("T")


class BaseRepository(Generic[T]):
    """
    Generic base repository for all entities.

    Provides common CRUD operations:
    - Create
    - Read (single, multiple)
    - Update
    - Delete
    - Exists
    - Count

    All repositories should inherit from this class.

    Type Parameters:
        T: The model class (e.g., User, Debate, Message)

    Example:
        class UserRepository(BaseRepository[User]):
            def __init__(self, session: AsyncSession):
                super().__init__(User, session)
    """

    def __init__(self, model: type[T], session: AsyncSession):
        """
        Initialize repository with model and session.

        Args:
            model: SQLAlchemy model class
            session: AsyncSession instance (dependency injected)

        Raises:
            ValueError: If model or session is None
        """
        if not model:
            raise ValueError("Model class cannot be None")
        if not session:
            raise ValueError("AsyncSession cannot be None")

        self.model = model
        self.session = session

    # ==================== CREATE ====================

    async def create(self, **kwargs) -> T:
        """
        Create and persist a new entity.

        Args:
            **kwargs: Field values for the model

        Returns:
            Created entity instance

        Raises:
            ValueError: If required fields are missing
            SQLAlchemy exceptions: On database errors

        Example:
            user = await user_repo.create(
                username="john",
                email="john@example.com",
                is_active=True
            )
        """
        instance = self.model(**kwargs)
        self.session.add(instance)
        await self.session.flush()
        return instance

    async def create_many(self, items: List[dict]) -> List[T]:
        """
        Create multiple entities in one operation.

        Args:
            items: List of dictionaries with field values

        Returns:
            List of created entities

        Example:
            users = await user_repo.create_many([
                {"username": "user1", "email": "user1@example.com"},
                {"username": "user2", "email": "user2@example.com"},
            ])
        """
        instances = [self.model(**item) for item in items]
        self.session.add_all(instances)
        await self.session.flush()
        return instances

    # ==================== READ ====================

    async def get_by_id(self, id: UUID) -> Optional[T]:
        """
        Get entity by primary key (UUID).

        Args:
            id: UUID primary key

        Returns:
            Entity instance or None if not found

        Example:
            user = await user_repo.get_by_id(user_id)
        """
        return await self.session.get(self.model, id)

    async def get_one(self, query: select) -> Optional[T]:
        """
        Execute query and return single result or None.

        Args:
            query: SQLAlchemy select statement

        Returns:
            Entity instance or None if not found

        Example:
            user = await user_repo.get_one(
                select(User).where(User.email == email)
            )
        """
        result = await self.session.execute(query)
        return result.scalars().first()

    async def get_all(self, query: Optional[select] = None) -> List[T]:
        """
        Get all entities or filter by query.

        Args:
            query: Optional SQLAlchemy select statement

        Returns:
            List of entities (empty list if none found)

        Example:
            all_users = await user_repo.get_all()
            active_users = await user_repo.get_all(
                select(User).where(User.is_active == True)
            )
        """
        if query is None:
            query = select(self.model)
        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_with_relations(
        self, 
        query: select,
        relations: dict[str, List] = None
    ) -> List[T]:
        """
        Get entities with eager-loaded relationships.

        Optimizes queries to avoid N+1 problems.

        Args:
            query: SQLAlchemy select statement
            relations: Dict mapping relationship names to selectinload paths

        Returns:
            List of entities with eager-loaded relationships

        Example:
            debates = await debate_repo.get_with_relations(
                select(Debate),
                relations={"messages": selectinload(Debate.messages)}
            )
        """
        if relations:
            for relation in relations.values():
                query = query.options(relation)
        result = await self.session.execute(query)
        return result.scalars().all()

    # ==================== UPDATE ====================

    async def update(self, instance: T, **kwargs) -> T:
        """
        Update entity attributes.

        Args:
            instance: Entity instance to update
            **kwargs: Field values to update

        Returns:
            Updated entity instance

        Example:
            user = await user_repo.update(user, username="new_name")
        """
        for key, value in kwargs.items():
            if hasattr(instance, key):
                setattr(instance, key, value)
        await self.session.flush()
        return instance

    async def update_many(
        self, 
        query: select, 
        values: dict
    ) -> int:
        """
        Update multiple entities matching query.

        Args:
            query: SQLAlchemy select statement
            values: Dictionary of field values to update

        Returns:
            Number of entities updated

        Example:
            count = await user_repo.update_many(
                select(User).where(User.is_active == False),
                {"is_active": True}
            )
        """
        # Convert select to update statement
        stmt = query.values(**values).execution_options(synchronize_session=False)
        result = await self.session.execute(stmt)
        await self.session.flush()
        return result.rowcount

    # ==================== DELETE ====================

    async def delete(self, instance: T) -> None:
        """
        Delete entity instance.

        Args:
            instance: Entity instance to delete

        Example:
            await user_repo.delete(user)
        """
        await self.session.delete(instance)
        await self.session.flush()

    async def delete_by_id(self, id: UUID) -> bool:
        """
        Delete entity by primary key.

        Args:
            id: UUID primary key

        Returns:
            True if deleted, False if not found

        Example:
            deleted = await user_repo.delete_by_id(user_id)
        """
        instance = await self.get_by_id(id)
        if instance:
            await self.delete(instance)
            return True
        return False

    async def delete_many(self, query: select) -> int:
        """
        Delete multiple entities matching query.

        Args:
            query: SQLAlchemy select statement

        Returns:
            Number of entities deleted

        Example:
            count = await user_repo.delete_many(
                select(User).where(User.is_active == False)
            )
        """
        stmt = query.delete().execution_options(synchronize_session=False)
        result = await self.session.execute(stmt)
        await self.session.flush()
        return result.rowcount

    # ==================== EXISTS ====================

    async def exists(self, query: select) -> bool:
        """
        Check if any entity matches the query.

        Args:
            query: SQLAlchemy select statement

        Returns:
            True if at least one entity exists

        Example:
            exists = await user_repo.exists(
                select(User).where(User.email == email)
            )
        """
        result = await self.session.execute(query)
        return result.scalars().first() is not None

    async def exists_by_id(self, id: UUID) -> bool:
        """
        Check if entity with given ID exists.

        Args:
            id: UUID primary key

        Returns:
            True if entity exists

        Example:
            exists = await user_repo.exists_by_id(user_id)
        """
        result = await self.session.get(self.model, id)
        return result is not None

    # ==================== COUNT ====================

    async def count(self, query: Optional[select] = None) -> int:
        """
        Count entities matching query or all entities.

        Args:
            query: Optional SQLAlchemy select statement

        Returns:
            Number of entities

        Example:
            total = await user_repo.count()
            active = await user_repo.count(
                select(User).where(User.is_active == True)
            )
        """
        if query is None:
            query = select(func.count()).select_from(self.model)
        else:
            # Convert select to count
            query = select(func.count()).select_from(query.froms[0])

        result = await self.session.execute(query)
        return result.scalar() or 0

    # ==================== TRANSACTIONS ====================

    async def commit(self) -> None:
        """
        Commit current transaction.

        Note: Use sparingly. Services should handle transaction coordination.
        """
        await self.session.commit()

    async def rollback(self) -> None:
        """
        Rollback current transaction.

        Note: Use only in error scenarios.
        """
        await self.session.rollback()

    async def flush(self) -> None:
        """
        Flush pending changes without committing.

        Used internally by create/update/delete operations.
        """
        await self.session.flush()
