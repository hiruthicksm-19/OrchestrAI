"""
User Repository

Specialized repository for User model operations.

Implements user-specific queries beyond basic CRUD:
- Get by email
- Get by username
- Get active users
- Deactivate user
- User existence checks

All operations use the injected AsyncSession.
"""

from typing import Optional, List
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import User
from app.database.repositories.base_repository import BaseRepository


class UserRepository(BaseRepository[User]):
    """
    Repository for User entity operations.

    Provides User-specific queries in addition to generic CRUD.

    Example:
        repo = UserRepository(session)
        user = await repo.get_by_email("user@example.com")
        users = await repo.get_active_users()
    """

    def __init__(self, session: AsyncSession):
        """
        Initialize UserRepository with AsyncSession.

        Args:
            session: AsyncSession instance (dependency injected)
        """
        super().__init__(User, session)

    # ==================== USER-SPECIFIC QUERIES ====================

    async def get_by_email(self, email: str) -> Optional[User]:
        """
        Get user by email address.

        Args:
            email: Email address to search for

        Returns:
            User instance or None if not found

        Example:
            user = await user_repo.get_by_email("john@example.com")
        """
        query = select(User).where(User.email == email)
        return await self.get_one(query)

    async def get_by_username(self, username: str) -> Optional[User]:
        """
        Get user by username.

        Args:
            username: Username to search for

        Returns:
            User instance or None if not found

        Example:
            user = await user_repo.get_by_username("john_doe")
        """
        query = select(User).where(User.username == username)
        return await self.get_one(query)

    async def get_active_users(self) -> List[User]:
        """
        Get all active users.

        Returns:
            List of active User instances

        Example:
            active = await user_repo.get_active_users()
        """
        query = select(User).where(User.is_active == True)
        return await self.get_all(query)

    async def get_inactive_users(self) -> List[User]:
        """
        Get all inactive users.

        Returns:
            List of inactive User instances

        Example:
            inactive = await user_repo.get_inactive_users()
        """
        query = select(User).where(User.is_active == False)
        return await self.get_all(query)

    async def count_active_users(self) -> int:
        """
        Count active users.

        Returns:
            Number of active users

        Example:
            count = await user_repo.count_active_users()
        """
        query = select(User).where(User.is_active == True)
        return await self.count(query)

    # ==================== USER OPERATIONS ====================

    async def deactivate(self, user: User) -> User:
        """
        Deactivate a user account.

        Args:
            user: User instance to deactivate

        Returns:
            Updated User instance

        Example:
            user = await user_repo.deactivate(user)
        """
        return await self.update(user, is_active=False)

    async def activate(self, user: User) -> User:
        """
        Activate a user account.

        Args:
            user: User instance to activate

        Returns:
            Updated User instance

        Example:
            user = await user_repo.activate(user)
        """
        return await self.update(user, is_active=True)

    async def update_username(self, user: User, new_username: str) -> User:
        """
        Update user's username.

        Args:
            user: User instance
            new_username: New username value

        Returns:
            Updated User instance

        Raises:
            ValueError: If username already exists

        Example:
            user = await user_repo.update_username(user, "new_name")
        """
        # Check if new username is already in use
        existing = await self.get_by_username(new_username)
        if existing and existing.id != user.id:
            raise ValueError(f"Username '{new_username}' already in use")

        return await self.update(user, username=new_username)

    async def update_email(self, user: User, new_email: str) -> User:
        """
        Update user's email address.

        Args:
            user: User instance
            new_email: New email address

        Returns:
            Updated User instance

        Raises:
            ValueError: If email already exists

        Example:
            user = await user_repo.update_email(user, "new@example.com")
        """
        # Check if new email is already in use
        existing = await self.get_by_email(new_email)
        if existing and existing.id != user.id:
            raise ValueError(f"Email '{new_email}' already in use")

        return await self.update(user, email=new_email)

    # ==================== CHECKS ====================

    async def email_exists(self, email: str, exclude_id: Optional[UUID] = None) -> bool:
        """
        Check if email exists (optionally excluding a user by ID).

        Args:
            email: Email to check
            exclude_id: Optional user ID to exclude from check

        Returns:
            True if email exists

        Example:
            exists = await user_repo.email_exists("john@example.com")
        """
        query = select(User).where(User.email == email)
        if exclude_id:
            query = query.where(User.id != exclude_id)
        return await self.exists(query)

    async def username_exists(self, username: str, exclude_id: Optional[UUID] = None) -> bool:
        """
        Check if username exists (optionally excluding a user by ID).

        Args:
            username: Username to check
            exclude_id: Optional user ID to exclude from check

        Returns:
            True if username exists

        Example:
            exists = await user_repo.username_exists("john_doe")
        """
        query = select(User).where(User.username == username)
        if exclude_id:
            query = query.where(User.id != exclude_id)
        return await self.exists(query)
