from collections import Counter

class BeliefState:
    """Tracks what the agent believes about cards it cannot see.""" 
    
    def __init__(self, game):
        self._counts = Counter((card.card_type, card.value) for card in game._create_deck())
        self._total = sum(self._counts.values())
    
    def probability(self, card_type, value):
        """P(a random unknown card == this type) under the uniform prior."""
        if self._total == 0:
            return 0
        return self._counts[(card_type, value)] / self._total

    def _remove_from_pool(self, card_type, value, n):
        """Remove n copies of a card from the unknown pool."""
        k = (card_type, value)
        self._counts[k] = max(0, self._counts[k] - n)
        self._total = max(0, self._total - n)