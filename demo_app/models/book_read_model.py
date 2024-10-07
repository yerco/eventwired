from typing import Dict, Optional, List

from src.services.redis_service import RedisService


class BookReadModel:
    def __init__(self, redis_service: RedisService):
        self.redis_service = redis_service

    async def add_book(self, title: str, book_data: Dict[str, Optional[str]]) -> None:
        # Filter out None values from book_data
        filtered_data = {k: v for k, v in book_data.items() if v is not None}

        # Ensure values are strings
        converted_data = {k: str(v) for k, v in filtered_data.items()}

        key = f"book:{title}"
        try:
            await self.redis_service.set_session(key, converted_data)
        except Exception as e:
            print(f"Error setting session for key '{key}': {e}")

    async def update_book(self, title: str, updated_data: Dict[str, Optional[str]]) -> None:
        # Filter out None values from updated_data
        filtered_data = {k: v for k, v in updated_data.items() if v is not None}

        # Ensure values are strings
        converted_data = {k: str(v) for k, v in filtered_data.items()}

        key = f"book:{title}"
        try:
            await self.redis_service.set_session(key, converted_data)
        except Exception as e:
            print(f"Error updating session for key '{key}': {e}")

    async def delete_book(self, title: str) -> None:
        key = f"book:{title}"
        await self.redis_service.client.delete(key)

    async def get_book(self, title: str) -> Optional[Dict[str, str]]:
        key = f"book:{title}"
        book_data = await self.redis_service.get_session(key)
        if book_data:
            # Decode bytes to strings if necessary
            return {k.decode() if isinstance(k, bytes) else k: v.decode() if isinstance(v, bytes) else v for k, v in book_data.items()}
        return None

    async def list_all_books(self) -> List[Dict[str, str]]:
        pattern = "book:*"
        keys = await self.redis_service.client.keys(pattern)
        books = []
        for key in keys:
            book_data = await self.redis_service.get_session(key)
            if book_data:
                # Decode bytes to strings if necessary
                books.append({k.decode() if isinstance(k, bytes) else k: v.decode() if isinstance(v, bytes) else v for k, v in book_data.items()})
        return books
