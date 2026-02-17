import random
from actions import Action, ActionType
from game_state import GamePhase
from cards import CardType

class RandomAgent:
    def __init__(self, game, player_idx: int = 1):
        # player_idx: 0 for user position, 1 for agent position
        self.game = game
        self.player_idx = player_idx
    
    def choose_action(self):
        # Select a random legal action based on current game phase.
        phase = self.game.state.phase

        if phase == GamePhase.DRAW:
            return self._choose_draw_action()
        elif phase == GamePhase.DECIDE:
            return self._choose_decide_action()
        
        # TODO: Add other phases later
        else:
            # Fallback: just discard if we have a drawn card
            print(f"WARNING: Unhandled phase {phase}, discarding")
            return Action.discard_drawn()
        
    
    def _choose_draw_action(self) -> Action:
        """Choose between drawing from pile or discard."""
        if self.game.discard_pile and random.random() < 0.3:
            return Action.draw_from_discard()
        return Action.draw_from_pile()

    def _choose_decide_action(self, can_knock: bool = True):
        """Choose: keep card (swap), discard, or knock."""
        actions = []
        
        # Option 1: Keep card (swap with one of agent's cards)
        hand = self.game.agent_hands
        for i, card in enumerate(hand):
            if card is not None and card.card_type != CardType.RAT:
                actions.append(Action.keep_card(i))
        
        # Option 2: Discard
        actions.append(Action.discard_drawn())
        
        # Option 3: Knock (if allowed and not already knocked)
        if can_knock and not self.game.state.has_knocked():
            # Random agent knocks with small probability
            if random.random() < 0.1:
                actions.append(Action.knock())
        
        return random.choice(actions)