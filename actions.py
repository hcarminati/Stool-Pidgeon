from enum import Enum, auto

class ActionType(Enum):
    """Types of actions a player can take."""
    # Basic actions
    DRAW_FROM_PILE = auto()
    DRAW_FROM_DISCARD = auto()
    KEEP_CARD = auto()
    DISCARD_DRAWN = auto()
    KNOCK = auto()
    
    # Special card effects
    PEEK = auto()               # Stool Pigeon: peek at any card
    SWAP = auto()               # Bamboozle/Vendetta: swap two cards
    KINGPIN_ELIMINATE = auto()  # Kingpin: remove own card
    KINGPIN_ADD = auto()        # Kingpin: add card to opponent

class Action: 
    """Represents a player action with optional targets."""
    
    def __init__(self, action_type, target_player=None, target_idx=None, second_target=None):
        self.action_type = action_type
        self.target_player = target_player
        self.target_idx = target_idx # Target card index for actions like peeking at a card. 
        self.second_target = second_target
    
    def draw_from_pile():
        return Action(ActionType.DRAW_FROM_PILE)
    
    def draw_from_discard():
        return Action(ActionType.DRAW_FROM_DISCARD)
    
    def keep_card(hand_idx):
        return Action(ActionType.KEEP_CARD, target_idx=hand_idx)
    
    def discard_drawn():
        return Action(ActionType.DISCARD_DRAWN)
    
    def knock():
        return Action(ActionType.KNOCK)
    
    def peek(player_idx, card_idx):
        return Action(ActionType.PEEK, target_player=player_idx, target_idx=card_idx)
    
    def swap(player1, idx1, player2, idx2):
        return Action(ActionType.SWAP, target_player=player1, target_idx=idx1, second_target=(player2, idx2))
    
    def kingpin_eliminate(card_idx):
        return Action(ActionType.KINGPIN_ELIMINATE, target_idx=card_idx)
    
    def kingpin_add(opponent_idx, card_idx):
        return Action(ActionType.KINGPIN_ADD, target_player=opponent_idx, target_idx=card_idx)
    
    def execute_action(self, game, GamePhase):
        """Execute an action and update game state."""
        print(f"Executing: {self.action_type}")
        
        # Execute: Draw from pile
        if self.action_type == ActionType.DRAW_FROM_PILE:
            card = game.draw_pile.pop()
            game.state.drawn_card = card
            game.state.set_phase(GamePhase.DECIDE)
            print(f"Drew: {card.card_type.name}" + (f" ({card.value})" if card.value else ""))

        # Excute: Keep drawn card 
        elif self.action_type == ActionType.KEEP_CARD:
            # Swap drawn card with card in hand
            hand = game.get_current_hand()
            old_card = hand[self.target_idx]
            hand[self.target_idx] = game.state.drawn_card
            game.discard_pile.append(old_card)
            game.state.drawn_card = None
        
        # Execute: Draw from discard pile
        elif self.action_type == ActionType.DISCARD_DRAWN:
            game.discard_pile.append(game.state.drawn_card)
            game.state.drawn_card = None
            game.state.next_turn()
        
        