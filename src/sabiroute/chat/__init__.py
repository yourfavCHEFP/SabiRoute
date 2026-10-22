"""SabiChat backend: user identity, sessions, conversations, gateway chat.

SabiChat is a product surface over the existing SabiRoute gateway. This
package never routes, scores, or executes providers itself: the chat endpoint
calls the authenticated ``POST /v1/chat/completions`` path in-process, so
policy, budgets, Free Pool eligibility, and usage accounting all apply
unchanged. The gateway service credential stays server-side.
"""

from .store import SabiChatStore

__all__ = ["SabiChatStore"]
