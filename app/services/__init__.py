"""
Service layer for the Arcanum application.

Provides business logic and orchestration for chat and message operations,
including creation, retrieval, update, deletion, search, and filtering.
Each service delegates database access to the DAO layer, while handling
validation, normalization, and application-specific logic.
"""

from app.services.dao.chats import ChatDAO
from app.services.dao.messages import MessageDAO
from app.services.dao.filters import FiltersDAO
from app.services.chats_service import ChatService
from app.services.messages_service import MessageService
from app.services.filters_service import FilterService

# Global service instance
chat_service = ChatService(ChatDAO())
message_service = MessageService(MessageDAO())
filter_service = FilterService(FiltersDAO())
