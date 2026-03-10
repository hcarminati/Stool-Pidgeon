from collections import Counter

class BeliefState:
    """Tracks what the agent believes about cards it cannot see.

        Cause a card to be known:
        -  game start (own face-up cards)
        - peek (Stool Pigeon/Vendetta)
        - keep card (agent swaps drawn card in, it knows what it just placed)

        Remove from game completely:
        -  discard
        - Kingpin eliminate

        * Swap (Bamboozle/Vendetta) shuffles slots
        - if A is known (card X) and slot B is unknown, 
        after the swap slot B now contains card X — we know that. 
        Only slot A becomes uncertain.
    """

    def __init__(self, game):
        # counts of unknown cards
        self._unknown = Counter((card.card_type, card.value) for card in game._create_deck())

        # All slots start unknown at first
        self._known: dict[tuple, object] = {
            (p, s): None
            for p in range(2) # position
            for s in range(len(game.agent_hands)) # slots
        }

        # Knows its own face-up cards at game start
        for slot in (2, 3):
            if slot < len(game.agent_hands) and game.agent_hands[slot] is not None:
                self.mark_known(1, slot, game.agent_hands[slot])

    def get_known(self, opponent_idx, action):
        return self._known.get((opponent_idx, action.target_idx))

    def probability(self, card):
        """P(a random unknown card == this type) under the uniform prior."""
        total = sum(self._unknown.values())

        if total == 0:
            return 0
        return self._unknown[(card.card_type, card.value)] / total

    def mark_known(self, player, slot, card):
        """ Remove card from the unknown pool and record the slot.
            Called in game start(own face-up cards), peek, keep_card.
        """
        # check if card is known
        previous_card = self._known.get((player, slot))
        if previous_card is None: # was unknown, remove from unknown pool
            self._unknown[(card.card_type, card.value)] = max(
                0, self._unknown[(card.card_type, card.value)] - 1
            )
        self._known[(player, slot)] = card

    def mark_removed(self, card):
        """ A card has been removed from the game entirely (discarded or Kingpin eliminated)."""
        for key, known_card in self._known.items():
            if known_card is card:
                self._known[key] = None
                return  # was known - pool already didn't count it

        k = (card.card_type, card.value)
        if self._unknown[k] > 0:  # only remove if still in pool
            self._unknown[k] -= 1

    def mark_unknown(self, player, slot):
        """Slot is no longer certain, add its card back into the unknown pool."""
        card = self._known.get((player, slot))
        if card is not None:
            self._unknown[(card.card_type, card.value)] += 1
        self._known[(player, slot)] = None

    def after_swap(self, p1, s1, p2, s2):
        """Update known slots after a Bamboozle/Vendetta swap."""
        c1 = self._known.get((p1, s1))
        c2 = self._known.get((p2, s2))

        # If both cards are known
        if c1 is not None and c2 is not None:
            self._known[(p1, s1)] = c2
            self._known[(p2, s2)] = c1

        # If only card 1 is known
        elif c1 is not None:
            self._known[(p2, s2)] = c1
            self._known[(p1, s1)] = None

        # If only card 2 is known
        elif c2 is not None:
            self._known[(p1, s1)] = c2
            self._known[(p2, s2)] = None

    def slot_expected_value(self, player, slot):
        """ Expected point value of a single slot 
        If its a known value then return the card.value 
        If its an unknown value then return the probability-weighted average over _unknown values"""

        card = self._known.get((player, slot))
        if card is not None:
            return card.value

        total = sum(self._unknown.values())
        if total == 0:
            return 0.0

        expected = 0.0
        for (card_type, value), count in self._unknown.items():
            expected += value * count / total
        return expected

    def expected_hand_value(self, player):
        """ Expected total hand value for a player, sum across all slots.
        Lower is better. Agent uses this to decide whether to knock.
        """
        total = 0.0

        for (p, s) in self._known:
            if p == player:
                total += self.slot_expected_value(player, s)

        return total
