"""
Sliding window conversation memory. Keeps the last few turns and
exposes a short context string used to disambiguate follow up queries
like "what about a cheaper one" or "does it have ssd".
"""

from collections import deque

MAX_TURNS = 3


class ConversationMemory:
    def __init__(self, max_turns=MAX_TURNS):
        self.max_turns = max_turns
        self.turns = deque(maxlen=max_turns)

    def add_turn(self, user_message, bot_message):
        self.turns.append({"user": user_message, "bot": bot_message})

    def get_context_string(self):
        # only prior user messages are used as routing/retrieval context
        # bot answers are shown in the debug view but kept out of the
        # embedding context to avoid drifting the query with old answers
        if not self.turns:
            return ""
        prior_user_messages = [t["user"] for t in self.turns]
        return " ".join(prior_user_messages)

    def get_history(self):
        return list(self.turns)

    def clear(self):
        self.turns.clear()
