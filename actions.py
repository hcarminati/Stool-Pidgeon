from enum import Enum, auto
from cards import CardType

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
            
            # Check if it's a Stool Pigeon - automatically activate peek
            if card.card_type == CardType.STOOL_PIGEON:
                game.state.set_phase(GamePhase.STOOL_PIGEON_PEEK)
                game.state.pending_effect = CardType.STOOL_PIGEON
                print("Stool Pigeon effect activated! Click any card to peek at it.")
            
            # Check if it's a Bamboozle - automatically activate swap
            elif card.card_type == CardType.BAMBOOZLE:
                game.state.set_phase(GamePhase.BAMBOOZLE_SELECT)
                game.state.pending_effect = CardType.BAMBOOZLE
                game.state.clear_selection()  # Reset any previous selection
                print("Bamboozle effect activated! Click two face-down cards to swap them.")
            
            # Check if it's a Vendetta - automatically activate peek
            elif card.card_type == CardType.VENDETTA:
                game.state.set_phase(GamePhase.VENDETTA_PEEK)
                game.state.pending_effect = CardType.VENDETTA
                print("Vendetta effect activated! Peek at one card, then swap any two.")
            
            # Check if it's a Kingpin - show choice menu
            elif card.card_type == CardType.KINGPIN:
                game.state.set_phase(GamePhase.KINGPIN_CHOOSE)
                game.state.pending_effect = CardType.KINGPIN
                print("Kingpin effect activated! Choose: Eliminate a card OR Add card to opponent.")

        # Execute: Keep drawn card 
        elif self.action_type == ActionType.KEEP_CARD:
            # Swap drawn card with card in hand
            hand = game.get_current_hand()
            old_card = hand[self.target_idx]
            
            # Check if position is already empty (None)
            if old_card is None:
                print("Cannot swap with empty position!")
                if game.GUI:
                    game.show_error_message("This position is empty!")
                return
            
            # Check if trying to swap out a RAT card
            if old_card.card_type == CardType.RAT:
                print("Cannot swap out a RAT card! RAT cards are sticky and can only be removed by Kingpin.")
                if game.GUI:
                    game.show_error_message("RAT cards are sticky! Cannot swap.")
                return
            
            hand[self.target_idx] = game.state.drawn_card
            game.discard_pile.append(old_card)
            game.state.drawn_card = None
            
            # End turn after swapping
            game.state.next_turn()
        
        # Execute: Discard drawn card
        elif self.action_type == ActionType.DISCARD_DRAWN:
            game.discard_pile.append(game.state.drawn_card)
            game.state.drawn_card = None
            game.state.next_turn()

        # Execute: Draw from discard
        elif self.action_type == ActionType.DRAW_FROM_DISCARD:
            card = game.discard_pile.pop()
            game.state.drawn_card = card
            game.state.set_phase(GamePhase.DECIDE)
            
            # Check if it's a Stool Pigeon - automatically activate peek
            if card.card_type == CardType.STOOL_PIGEON:
                game.state.set_phase(GamePhase.STOOL_PIGEON_PEEK)
                game.state.pending_effect = CardType.STOOL_PIGEON
                print("Stool Pigeon effect activated! Click any card to peek at it.")
            
            # Check if it's a Bamboozle - automatically activate swap
            elif card.card_type == CardType.BAMBOOZLE:
                game.state.set_phase(GamePhase.BAMBOOZLE_SELECT)
                game.state.pending_effect = CardType.BAMBOOZLE
                game.state.clear_selection()  # Reset any previous selection
                print("Bamboozle effect activated! Click two face-down cards to swap them.")
            
            # Check if it's a Vendetta - automatically activate peek
            elif card.card_type == CardType.VENDETTA:
                game.state.set_phase(GamePhase.VENDETTA_PEEK)
                game.state.pending_effect = CardType.VENDETTA
                print("Vendetta effect activated! Peek at one card, then swap any two.")
            
            # Check if it's a Kingpin - show choice menu
            elif card.card_type == CardType.KINGPIN:
                game.state.set_phase(GamePhase.KINGPIN_CHOOSE)
                game.state.pending_effect = CardType.KINGPIN
                print("Kingpin effect activated! Choose: Eliminate a card OR Add card to opponent.")
        
        # Execute: Knock
        elif self.action_type == ActionType.KNOCK:
            game.state.handle_knock()
            game.state.next_turn()
        
        # Execute: Swap two cards (Bamboozle/Vendetta effect)
        elif self.action_type == ActionType.SWAP:
            player1_idx, card1_idx = self.target_player, self.target_idx
            player2_idx, card2_idx = self.second_target
            
            # Get the hands
            hand1 = game.user_hand if player1_idx == 0 else game.agent_hands
            hand2 = game.user_hand if player2_idx == 0 else game.agent_hands
            
            # Check if either position is empty (None)
            if hand1[card1_idx] is None or hand2[card2_idx] is None:
                print("Cannot swap with empty position!")
                if game.GUI:
                    game.show_error_message("Cannot swap with empty position!")
                # Reset selection
                game.bamboozle_first_card = None
                game.vendetta_first_card = None
                return
            
            # RAT cards CAN be swapped with Bamboozle/Vendetta - this is how you pass them to opponents!
            
            # Perform the swap
            hand1[card1_idx], hand2[card2_idx] = hand2[card2_idx], hand1[card1_idx]
            print(f"Swapped player {player1_idx} card {card1_idx} with player {player2_idx} card {card2_idx}")
            
            # Discard the Bamboozle/Vendetta card
            game.discard_pile.append(game.state.drawn_card)
            game.state.drawn_card = None
            game.state.pending_effect = None
            
            # End turn
            game.state.next_turn()
        
        # Execute: Kingpin Eliminate (remove card from hand, add to discard)
        elif self.action_type == ActionType.KINGPIN_ELIMINATE:
            hand = game.get_current_hand()
            eliminated_card = hand[self.target_idx]
            
            # Add eliminated card to discard pile
            game.discard_pile.append(eliminated_card)
            print(f"Kingpin eliminated: {eliminated_card.card_type.name}" + 
                  (f" ({eliminated_card.value})" if eliminated_card.value else ""))
            
            # Set position to None instead of removing to maintain card positions
            hand[self.target_idx] = None
            
            # Discard the Kingpin card
            game.discard_pile.append(game.state.drawn_card)
            game.state.drawn_card = None
            game.state.pending_effect = None
            
            active_cards = sum(1 for card in hand if card is not None)
            print(f"Player now has {active_cards} cards in hand")
            
            # End turn
            game.state.next_turn()
        
        # Execute: Kingpin Add (add card to opponent)
        elif self.action_type == ActionType.KINGPIN_ADD:
            # Draw a card from the deck
            if not game.draw_pile:
                print("No cards left in draw pile! Cannot add card to opponent.")
                if game.GUI:
                    game.show_error_message("No cards left in draw pile!")
                return
            
            new_card = game.draw_pile.pop()
            opponent_hand = game.get_opponent_hand()
            opponent_hand.append(new_card)
            
            opponent_name = "Agent" if game.state.is_user_turn() else "User"
            print(f"Kingpin added card to {opponent_name}: {new_card.card_type.name}" + 
                  (f" ({new_card.value})" if new_card.value else ""))
            
            # Discard the Kingpin card
            game.discard_pile.append(game.state.drawn_card)
            game.state.drawn_card = None
            game.state.pending_effect = None
            
            # End turn
            game.state.next_turn()