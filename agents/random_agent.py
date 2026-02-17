import random
from actions import Action


class RandomAgent:
    def __init__(self, game, player_idx: int = 1):
        self.game = game
        self.player_idx = player_idx
    
    def choose_action(self) -> Action:
        """Pick a random legal action."""
        actions = self.game.get_legal_actions()
        print(actions)
        
        if actions:
            return random.choice(actions)
        
        return Action.discard_drawn()