from enum import Enum, auto
from cards import CardType
from agents.basic_pomdp_agent.observation import Observation, ObsType

class ActionType(Enum):
    """Types of actions a player can take."""
    # Basic actions
    DRAW_FROM_PILE = auto()
    DRAW_FROM_DISCARD = auto()
    KEEP_CARD = auto()
    DISCARD_DRAWN = auto()
    KNOCK = auto()
    
    # Special card effects
    PEEK = auto()               # Stool Pigeon/Vendetta: peek at any card
    SWAP = auto()               # Bamboozle/Vendetta: swap two cards
    KINGPIN_ELIMINATE = auto()  # Kingpin: remove own card
    KINGPIN_ADD = auto()        # Kingpin: add card to opponent

    DONE_PEEKING = auto()       # For the agent

class Action: 
    """Represents a player action with optional targets."""
    
    def __init__(self, action_type, target_player=None, target_idx=None, second_target=None):
        self.action_type = action_type
        self.target_player = target_player
        self.target_idx = target_idx # Target card index for actions like peeking at a card. 
        self.second_target = second_target
    
    # ========== FACTORY METHODS ==========
    
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

    def done_peeking():
        return Action(ActionType.DONE_PEEKING)
    
    # ========== EXECUTION METHODS ==========
    
    def execute_action(self, game, GamePhase, agent=False):
        """Execute an action and update game state."""
        print(f"Executing: {self.action_type}")
        
        # Route to appropriate handler
        if self.action_type == ActionType.DRAW_FROM_PILE:
            self._execute_draw_from_pile(game, GamePhase, agent)
        elif self.action_type == ActionType.DRAW_FROM_DISCARD:
            self._execute_draw_from_discard(game, GamePhase, agent)
        elif self.action_type == ActionType.KEEP_CARD:
            self._execute_keep_card(game, GamePhase)
        elif self.action_type == ActionType.DISCARD_DRAWN:
            self._execute_discard_drawn(game, GamePhase)
        elif self.action_type == ActionType.KNOCK:
            self._execute_knock(game, GamePhase)
        elif self.action_type == ActionType.PEEK:    
            self._execute_peek(game, GamePhase, agent) 
        elif self.action_type == ActionType.SWAP:
            self._execute_swap(game, GamePhase)
        elif self.action_type == ActionType.KINGPIN_ELIMINATE:
            self._execute_kingpin_eliminate(game, GamePhase)
        elif self.action_type == ActionType.KINGPIN_ADD:
            self._execute_kingpin_add(game, GamePhase)
        elif self.action_type == ActionType.DONE_PEEKING:
            self._execute_done_peeking(game, GamePhase)
  
    def _execute_draw_from_pile(self, game, GamePhase, agent=False):
        """Draw a card from the draw pile."""
        card = game.draw_pile.pop()
        game.state.drawn_card = card
        game.state.set_phase(GamePhase.DECIDE)
        print(f"Drew: {card.card_type.name}" + (f" ({card.value})" if card.value else ""))
       
        self._activate_special_card_effect(game, GamePhase, card, agent) 

        if game.state.is_agent_turn() and hasattr(game.agent, 'observe'):
            game.agent.observe(Observation(ObsType.AGENT_DRAW_PILE))

    def _execute_draw_from_discard(self, game, GamePhase, agent=False):
        """Draw a card from the discard pile."""
        card = game.discard_pile.pop()
        game.state.drawn_card = card
        game.state.set_phase(GamePhase.DECIDE)
        
        self._activate_special_card_effect(game, GamePhase, card, agent) 

        if game.state.is_user_turn() and hasattr(game.agent, 'observe'):
            game.agent.observe(Observation(ObsType.PLAYER_DRAW_DISCARD, card=card, player=game.state.current_player_idx))

    def _activate_special_card_effect(self, game, GamePhase, card, agent=False):
        """Activate special effects for action cards."""
        if card.card_type == CardType.STOOL_PIGEON:
            game.state.pending_effect = CardType.STOOL_PIGEON
            if agent:
                print("Stool Pigeon: Agent skips peek.")
            else:
                game.state.set_phase(GamePhase.STOOL_PIGEON_PEEK)
                print("Stool Pigeon effect activated! Click any card to peek at it.")
        
        elif card.card_type == CardType.BAMBOOZLE:
            game.state.set_phase(GamePhase.BAMBOOZLE_SELECT)
            game.state.pending_effect = CardType.BAMBOOZLE
            game.state.clear_selection()
            print("Bamboozle effect activated! Click two face-down cards to swap them.")
        
        elif card.card_type == CardType.VENDETTA:
            game.state.pending_effect = CardType.VENDETTA
            if agent:
                # Agent skips peek, goes straight to swap
                game.state.set_phase(GamePhase.VENDETTA_SWAP)
                print("Vendetta: Agent skips peek, ready to swap.")
            else:
                game.state.set_phase(GamePhase.VENDETTA_PEEK)
                print("Vendetta effect activated! Peek at one card, then swap any two.")
        
        elif card.card_type == CardType.KINGPIN:
            game.state.set_phase(GamePhase.KINGPIN_CHOOSE)
            game.state.pending_effect = CardType.KINGPIN
            print("Kingpin effect activated! Choose: Eliminate a card OR Add card to opponent.")
            
    def _execute_keep_card(self, game, GamePhase):
        """Keep the drawn card by swapping it with a card in hand."""
        hand = game.get_current_hand()
        old_card = hand[self.target_idx]
        
        # Validate swap
        if old_card is None:
            print("Cannot swap with empty position!")
            if game.GUI:
                game.show_error_message("This position is empty!")
            return
        
        if old_card.card_type == CardType.RAT:
            print("Cannot swap out a RAT card! RAT cards are sticky and can only be removed by Kingpin.")
            if game.GUI:
                game.show_error_message("RAT cards are sticky! Cannot swap.")
            return
        
        # Perform swap
        hand[self.target_idx] = game.state.drawn_card
        game.discard_pile.append(old_card)

        if hasattr(game.agent, 'observe'):
            obs_type = ObsType.AGENT_KEEP if game.state.is_agent_turn() else ObsType.PLAYER_KEEP
            game.agent.observe(Observation(obs_type,
                                        card=old_card,
                                        player=game.state.current_player_idx,
                                        slot=self.target_idx))
    
        game.state.drawn_card = None
        game.state.next_turn()
    
    def _execute_discard_drawn(self, game, GamePhase):
        """Discard the drawn card."""
        game.discard_pile.append(game.state.drawn_card)

        if game.state.is_user_turn() and hasattr(game.agent, 'observe'):
            game.agent.observe(Observation(ObsType.PLAYER_DISCARD, card=game.state.drawn_card))

        game.state.drawn_card = None
        game.state.next_turn()
    
    def _execute_knock(self, game, GamePhase):
        """Execute knock action."""
        game.state.handle_knock()
        # game.state.next_turn()
        if hasattr(game.agent, 'observe'):
            game.agent.observe(Observation(ObsType.KNOCK, player=game.state.current_player_idx))
    
    def _execute_swap(self, game, GamePhase):
        """Swap two cards (Bamboozle/Vendetta effect)."""
        player1_idx, card1_idx = self.target_player, self.target_idx
        player2_idx, card2_idx = self.second_target
        
        hand1 = game.user_hand if player1_idx == 0 else game.agent_hands
        hand2 = game.user_hand if player2_idx == 0 else game.agent_hands
        
        # Validate swap
        if hand1[card1_idx] is None or hand2[card2_idx] is None:
            print("Cannot swap with empty position!")
            if game.GUI:
                game.show_error_message("Cannot swap with empty position!")
            game.bamboozle_first_card = None
            game.vendetta_first_card = None
            return
        
        # Perform swap (RAT cards CAN be swapped with Bamboozle/Vendetta)
        hand1[card1_idx], hand2[card2_idx] = hand2[card2_idx], hand1[card1_idx]

        if hasattr(game.agent, 'observe'):
            obs_type = ObsType.AGENT_SWAP if not game.state.is_user_turn() else ObsType.PLAYER_SWAP
            game.agent.observe(Observation(obs_type, p1=player1_idx, s1=card1_idx, p2=player2_idx, s2=card2_idx))

        print(f"Swapped player {player1_idx} card {card1_idx} with player {player2_idx} card {card2_idx}")
        
        # Clean up
        game.discard_pile.append(game.state.drawn_card)
        game.state.drawn_card = None
        game.state.pending_effect = None
        game.state.next_turn()
    
    def _execute_kingpin_eliminate(self, game, GamePhase):
        """Eliminate a card from hand (Kingpin effect)."""
        hand = game.get_current_hand()
        eliminated_card = hand[self.target_idx]
        
        game.discard_pile.append(eliminated_card)
        print(f"Kingpin eliminated: {eliminated_card.card_type.name}" + 
              (f" ({eliminated_card.value})" if eliminated_card.value else ""))
        
        hand[self.target_idx] = None

        if hasattr(game.agent, 'observe'):
            game.agent.observe(Observation(ObsType.KINGPIN_ELIMINATE,
                                           card=eliminated_card,
                                           player=game.state.current_player_idx,
                                           slot=self.target_idx))
        
        active_cards = sum(1 for card in hand if card is not None)
        print(f"Player now has {active_cards} cards in hand")
        
        # Clean up
        game.discard_pile.append(game.state.drawn_card)
        game.state.drawn_card = None
        game.state.pending_effect = None
        game.state.next_turn()
    
    def _execute_kingpin_add(self, game, GamePhase):
        """Add a card to opponent's hand (Kingpin effect)."""
        if not game.draw_pile:
            print("No cards left in draw pile! Cannot add card to opponent.")
            if game.GUI:
                game.show_error_message("No cards left in draw pile!")
            return
        
        new_card = game.draw_pile.pop()
        opponent_hand = game.get_opponent_hand()
        opponent_hand.append(new_card)
        
        if hasattr(game.agent, 'observe'):
            game.agent.observe(Observation(ObsType.KINGPIN_ADD, player=self.target_player))

        opponent_name = "Agent" if game.state.is_user_turn() else "User"
        print(f"Kingpin added card to {opponent_name}: {new_card.card_type.name}" + 
              (f" ({new_card.value})" if new_card.value else ""))
        
        # Clean up
        game.discard_pile.append(game.state.drawn_card)
        game.state.drawn_card = None
        game.state.pending_effect = None
        game.state.next_turn()

    def _execute_peek(self, game, GamePhase, agent=False):
        """
        Execute peek action (Stool Pigeon / Vendetta).
        
        For humans: Sets peeked_card so UI shows it, waits for "done" button
        For agents: Sets peeked_card and immediately advances to next phase
        """
        game.peeked_card = (self.target_player, self.target_idx)
        if game.state.is_agent_turn() and hasattr(game.agent, 'observe'):
            peeked = game.agent_hands[self.target_idx] if self.target_player == 1 else game.user_hand[self.target_idx]
            game.agent.observe(Observation(ObsType.AGENT_PEEK, card=peeked, player=self.target_player, slot=self.target_idx))

        print(f"Peeked at player {self.target_player}, card {self.target_idx}")
        
        if agent:
            # Agent doesn't need to wait for UI - advance to next phase
            game.peeked_card = None
            if game.state.phase == GamePhase.VENDETTA_PEEK:
                game.state.set_phase(GamePhase.VENDETTA_SWAP)
        # For humans, phase stays the same - they click "done" button to advance
    
    def _execute_done_peeking(self, game, GamePhase):
        """Finish peeking phase and move to next phase."""
        game.peeked_card = None
        
        if game.state.phase == GamePhase.VENDETTA_PEEK:
            game.state.set_phase(GamePhase.VENDETTA_SWAP)
            print("Done peeking. Now swap any two cards.")
