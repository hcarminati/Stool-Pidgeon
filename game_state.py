from enum import Enum, auto

class GamePhase(Enum):
    """Represents the current phase of the game."""
    DRAW = auto()               # Player must draw from draw pile or discard pile
    DECIDE = auto()             # Player decides: keep drawn card or discard it
    RESOLVE_EFFECT = auto()     # Resolving a special card's effect
    STOOL_PIGEON_PEEK = auto()  # Stool Pigeon: peek at any card
    STOOL_PIGEON_SWAP = auto()  # Stool Pigeon: swap drawn card with own card
    BAMBOOZLE_SELECT = auto()   # Bamboozle: select two face-down cards to swap
    VENDETTA_PEEK = auto()      # Vendetta phase 1: peek at a card
    VENDETTA_SWAP = auto()      # Vendetta phase 2: swap two cards
    FINAL_TURN = auto()         # After someone knocks, others get one last turn
    GAME_OVER = auto()          # Game has ended, show scores

class GameState:
    """Holds all game state variables and state-related logic."""
    
    def __init__(self):
        self.current_player_idx = 0
        self.phase = GamePhase.DRAW
        self.knocked_by = None
        self.drawn_card = None
        self.pending_effect = None
        self.selected_card = None
        self.turns_since_knock = 0
    
    def reset(self):
        """Reset all state to initial values."""
        self.__init__()
    
    def get_current_player_name(self):
        """Returns the current player name."""
        return "User" if self.current_player_idx == 0 else "Agent"
    
    def is_user_turn(self):
        """Returns true if the current player index is 0, false otherwise."""
        return self.current_player_idx == 0
    
    def is_agent_turn(self):
        """Returns true if the current player index is 1, false otherwise."""
        return self.current_player_idx == 1

    def set_phase(self, new_phase):
        """Sets the current phase to the new passed in phase."""
        old_phase = self.phase
        self.phase = new_phase
        print(f"Phase: {old_phase.name} -> {new_phase.name}")
    
    def is_phase(self, phase):
        """Returns true if it is the passed in phase, false otherwise."""
        return self.phase == phase

    def get_phase_instructions(self):
        """Returns the instructions for the current phase's action."""
        instructions = {
            GamePhase.DRAW: "Draw a card from the draw pile or discard pile",
            GamePhase.DECIDE: "Keep the card (swap with one of yours) or discard it",
            GamePhase.RESOLVE_EFFECT: f"Resolve {self.pending_effect.name if self.pending_effect else 'effect'}",
            GamePhase.STOOL_PIGEON_PEEK: "Click any card to peek at it",
            GamePhase.STOOL_PIGEON_SWAP: "Swap the Stool Pigeon with one of your cards",
            GamePhase.BAMBOOZLE_SELECT: "Click two face-down cards to swap them",
            GamePhase.VENDETTA_PEEK: "Vendetta: Click any card to peek at it",
            GamePhase.VENDETTA_SWAP: "Vendetta: Click two cards to swap them",
            GamePhase.FINAL_TURN: "Final turn! Draw and decide",
            GamePhase.GAME_OVER: "Game Over!",
        }
        return instructions.get(self.phase, "")

    def next_turn(self):
        """Advance to the next player's turn. Returns True if game continues."""
        if self.knocked_by is not None:
            # Keep track of how many turns passed since the knock.
            self.turns_since_knock += 1
            # Set the game phase to Game Over once everyone had one last turn.
            if self.turns_since_knock >= 2:
                self.set_phase(GamePhase.GAME_OVER)
                return False
        
        self.current_player_idx = 1 - self.current_player_idx
        self.drawn_card = None
        self.pending_effect = None
        self.selected_card = None
        
        # Set the phase to final turn if the player knocked, if not set it to draw. 
        self.set_phase(GamePhase.FINAL_TURN if self.knocked_by is not None else GamePhase.DRAW)
        print(f"--- {self.get_current_player_name()}'s Turn ---")
        return True

    def handle_knock(self):
        """Handle when a player knocks. Returns True if knock was valid."""
        if self.knocked_by is None and self.phase != GamePhase.GAME_OVER:
            self.knocked_by = self.current_player_idx
            print(f"{self.get_current_player_name()} knocked!")
            return True
        return False
    
    def has_knocked(self):
        """Returns true if a player knocked, false otherwise."""
        return self.knocked_by is not None

    def select_card(self, player_idx, card_idx):
        """Sets the selected card and player who selected it."""
        self.selected_card = (player_idx, card_idx)
        print(f"Selected card: player {player_idx}, index {card_idx}")
    
    def clear_selection(self):
        """Clears the selected card."""
        self.selected_card = None
    
    def has_selection(self):
        """Returns true if there is a selected card, false otherwise."""
        return self.selected_card is not None

    def print_state(self):
        """For debugging purposes."""
        print(f"\n=== GAME STATE ===")
        print(f"Phase: {self.phase.name}")
        print(f"Current Player: {self.get_current_player_name()}")
        print(f"Knocked By: {self.knocked_by}")
        print(f"Drawn Card: {self.drawn_card}")
        print(f"Pending Effect: {self.pending_effect}")
        print(f"Selected Card: {self.selected_card}")
        print(f"==================\n")