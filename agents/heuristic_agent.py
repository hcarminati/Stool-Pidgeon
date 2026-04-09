import random
from actions import Action, ActionType

# Thresholds
KEEP_THRESHOLD = 5 # keep a drawn card only if its value is below this
KNOCK_THRESHOLD = 12 # knock if sum of known cards is at or below this

class HeuristicAgent:
    """
    Rule-based agent with no belief state, that makes decisions based on 
    simple heuristics and the information directly visible at decision time.

    Only acts on information that is directly visible at decision time:
      - The drawn card (always visible when deciding keep/discard)
      - The top of the discard pile (always visible)
      - Its own running tally of cards it has drawn and kept

    Heuristics:
      Draw : take from discard if top card value < KEEP_THRESHOLD
      Decide : keep drawn card if value < KEEP_THRESHOLD, else discard
      Knock : knock if sum of kept card values <= KNOCK_THRESHOLD
      Special: all peek / swap / kingpin decisions are random
    """

    def __init__(self, game, player_idx: int = 1):
        self.game = game
        self.player_idx = player_idx
        # Running tally of values for cards we have drawn and kept
        self._kept_values: dict[int, float] = {} # slot -> value

    def choose_action(self) -> Action:
        """Chooses an action based on heuristics. """
        actions = self.game.get_legal_actions()
        if not actions:
            return Action.discard_drawn()

        types = {a.action_type for a in actions}

        if ActionType.DRAW_FROM_PILE in types or ActionType.DRAW_FROM_DISCARD in types:
            return self._choose_draw(actions)

        if ActionType.KEEP_CARD in types or ActionType.DISCARD_DRAWN in types:
            return self._choose_keep_or_discard(actions)

        if ActionType.KNOCK in types:
            return self._choose_knock_or_draw(actions)

        # Peek, swap, kingpin have no basis to reason, pick randomly
        return random.choice(actions)

    # Decision helpers
    def _choose_draw(self, actions) -> Action:
        """Take from discard if the top card is less than KEEP_THRESHOLD, else draw from pile."""
        discard = next((a for a in actions if a.action_type == ActionType.DRAW_FROM_DISCARD), None)
        pile    = next((a for a in actions if a.action_type == ActionType.DRAW_FROM_PILE), None)

        if discard and self.game.discard_pile:
            top = self.game.discard_pile[-1]
            if top.value is not None and top.value < KEEP_THRESHOLD:
                return discard

        return pile if pile else random.choice(actions)

    def _choose_keep_or_discard(self, actions) -> Action:
        """Keep drawn card if it's less than KEEP_THRESHOLD; record kept slot for knock logic."""
        drawn = self.game.state.drawn_card
        if drawn is None:
            return Action.discard_drawn()

        # Action cards have no value — always discard them
        if drawn.value is None:
            return Action.discard_drawn()

        if drawn.value < KEEP_THRESHOLD:
            keep_actions = [a for a in actions if a.action_type == ActionType.KEEP_CARD]
            if keep_actions:
                # Replace the slot with the highest known kept value, else pick randomly
                best = max(
                    keep_actions,
                    key=lambda a: self._kept_values.get(a.target_idx, 0)
                )
                self._kept_values[best.target_idx] = drawn.value
                return best

        return Action.discard_drawn()

    def _choose_knock_or_draw(self, actions) -> Action:
        """Knock if sum of kept card values is at or below KNOCK_THRESHOLD, else draw."""
        known_total = sum(self._kept_values.values())
        if known_total <= KNOCK_THRESHOLD:
            knock = next((a for a in actions if a.action_type == ActionType.KNOCK), None)
            if knock:
                return knock

        draw = next((a for a in actions if a.action_type == ActionType.DRAW_FROM_PILE), None)
        return draw if draw else random.choice(actions)