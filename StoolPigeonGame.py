import random
import pygame
from cards import CardType
from cards import Card  
from button import Button 
from game_state import GameState, GamePhase
from actions import Action, ActionType


class StoolPigeonGame:
    """Main game class that handles game logic, rendering, and user input."""
    
    def __init__(self, GUI=False, render_delay_sec=0.3):
        """Initialize the game."""
        # Game configuration
        self.GUI = GUI
        self.cardWidth = 65
        self.cardHeight = 90
        self.fps = 60
        self.background = None

        # RGB color definitions for UI
        self.black = (0, 0, 0)
        self.white = (255, 255, 255)
        self.red_orange = (245, 104, 90)

        # Pygame font objects (initialized in _initScreen if GUI mode)
        self.font = None  # Large font for title
        self.tinyFont = None  # Small font for labels and descriptions
        
        # Piles: tracks all cards in play
        self.draw_pile = []     # Cards remaining to be drawn
        self.discard_pile = []  # Cards that have been played/discarded
        self.agent_hands = []   # Agent's face-down cards
        self.user_hand = []     # Player's face-up cards

        # Pygame Rect objects for click detection (updated in _refresh)
        self.draw_pile_rect = None      # Clickable area for draw pile
        self.discard_pile_rect = None   # Clickable area for discard pile

        # Buttons 
        self.knock_button = Button((50, 575), 100, 50, 'images/knock-button.png')
        self.knock_button_rect = self.knock_button.rect
        
        # Done button for card effects
        self.done_button = Button((750, 575), 100, 50, 'images/done-button.png')
        self.done_button_rect = self.done_button.rect
        
        # Kingpin choice buttons
        self.eliminate_button = Button((350, 400), 150, 50, 'images/eliminate-button.png')
        self.eliminate_button_rect = self.eliminate_button.rect
        self.add_button = Button((520, 400), 150, 50, 'images/add-button.png')
        self.add_button_rect = self.add_button.rect

        # Game state
        self.state = GameState()
        
        # Track which card is being peeked at
        self.peeked_card = None  # Tuple of (player_idx, card_idx)
        
        # Track first card selection for Bamboozle
        self.bamboozle_first_card = None  # Tuple of (player_idx, card_idx)
        
        # Track first card selection for Vendetta swap
        self.vendetta_first_card = None  # Tuple of (player_idx, card_idx)
        
        # Error message display
        self.error_message = None
        self.error_message_timer = 0
        
        self._setup_game()

        if self.GUI:
            pygame.init()
            self._initScreen()
            self._load_background()
            self._refresh()

    def _initScreen(self):
        """Initialize the pygame window and fonts. Only called if GUI=True."""
        self.cellSize = 40
        self.screenWidth = 900
        self.screenHeight = 700
        self.screen = pygame.display.set_mode((self.screenWidth, self.screenHeight))

        # Create fonts for rendering text
        self.font = pygame.font.Font(None, 32)      # Large font for title
        self.tinyFont = pygame.font.Font(None, 18)  # Small font for labels
        
        pygame.display.set_caption("Stool Pigeon")
    
    def _load_background(self):
        """Load and scale the background image for the game."""
        try:
            bg_image = pygame.image.load('images/game-background-light.png')
            self.background = pygame.transform.scale(bg_image, (self.screenWidth, self.screenHeight))
        except pygame.error:
            self.background = None  # If loading fails, use plain background

    def get_current_hand(self):
        """Returns the current player's hand."""
        return self.user_hand if self.state.is_user_turn() else self.agent_hands

    def get_opponent_hand(self):
        """Return the opponent's hand"""
        return self.agent_hands if self.state.is_user_turn() else self.user_hand
    
    def show_error_message(self, message, duration=3):
        """Display an error message for a specified duration (in seconds)."""
        self.error_message = message
        self.error_message_timer = duration * self.fps  # Convert seconds to frames
    
    def _refresh(self):
        """Redraw the entire game screen. Called every frame."""
        mouse_pos = pygame.mouse.get_pos()

        mouse_pos = pygame.mouse.get_pos()
        is_user_turn = self.state.is_user_turn()
        active_mouse = mouse_pos if is_user_turn else None

        # ========== DRAWN CARD ==========
        # Show drawn card during DECIDE, special card phases
        if (self.state.drawn_card and self.state.is_user_turn() and 
            (self.state.is_phase(GamePhase.DECIDE) or 
             self.state.is_phase(GamePhase.STOOL_PIGEON_PEEK) or 
             self.state.is_phase(GamePhase.STOOL_PIGEON_SWAP) or
             self.state.is_phase(GamePhase.BAMBOOZLE_SELECT) or
             self.state.is_phase(GamePhase.VENDETTA_PEEK) or
             self.state.is_phase(GamePhase.VENDETTA_SWAP) or
             self.state.is_phase(GamePhase.KINGPIN_CHOOSE) or
             self.state.is_phase(GamePhase.KINGPIN_ELIMINATE) or
             self.state.is_phase(GamePhase.KINGPIN_ADD))):
            drawn_label = self.tinyFont.render("You drew:", True, self.white)
            self.screen.blit(drawn_label, (600, 270))
            self.state.drawn_card.draw(
                self.screen,
                (600, 300),
                self.font,
                self.tinyFont,
                active_mouse,
                face_up=True,
                is_user_turn=is_user_turn
            )
            self.state.drawn_card.disable()


        # ========== GAME STATE ==========

        # Shows the current game phase and whose turn it is
        phase_text = self.tinyFont.render(
            f"Phase: {self.state.phase.name} | Turn: {self.state.get_current_player_name()}", 
            True, self.white
        )
        self.screen.blit(phase_text, (10, 10))
        
        # Displays instructions based on the current phase
        instructions = self.tinyFont.render(
            self.state.get_phase_instructions(),
            True,
            self.white
        )
        self.screen.blit(instructions, (10, 35))

        # Indicates if a player has knocked and shows who initiated it
        if self.state.has_knocked():
            knocked_name = "User" if self.state.knocked_by == 0 else "Agent"
            knock_text = self.tinyFont.render(f"Knocked by: {knocked_name}", True, self.red_orange)
            self.screen.blit(knock_text, (10, 60))
        
        # ========== DRAW PILE ==========
        # Label showing how many cards are left in draw pile
        pile_label = self.tinyFont.render(
            f"Draw: {len(self.draw_pile)}", True, self.white  
        )
        self.screen.blit(pile_label, (350, 270))
        
        # Draw the draw pile (generic card back) if cards remain
        if self.draw_pile:
            top_card = self.draw_pile[-1]
            top_card.draw(self.screen, (350, 300), self.font, self.tinyFont, active_mouse, face_up=False, is_user_turn=is_user_turn)
            self.draw_pile_rect = top_card.rect
        else:
            self.draw_pile_rect = None
       
        # ========== DISCARD PILE ==========
        # Label showing how many cards are in discard pile
        pile_label = self.tinyFont.render(
            f"Discard: {len(self.discard_pile)}", True, self.white
        )
        self.screen.blit(pile_label, (475, 270))

        # Draw the top card of the discard pile (face-up) if it exists
        if self.discard_pile:
            top_card = self.discard_pile[-1]
            top_card.draw(self.screen, (475, 300), self.font, self.tinyFont, active_mouse, face_up=True, is_user_turn=is_user_turn)
            self.discard_pile_rect = top_card.rect
            # Enable discard pile during DECIDE phase (for discarding drawn card)
            if self.state.is_phase(GamePhase.DECIDE):
                top_card.enable()
            else:
                top_card.disable()
        else:
            # Show empty discard pile placeholder (gray rectangle)
            self.discard_pile_rect = pygame.Rect(475, 300, Card.CARD_WIDTH, Card.CARD_HEIGHT)
            pygame.draw.rect(self.screen, (200, 200, 200), self.discard_pile_rect, 2)

        # ========== PLAYER HAND ==========
        # Display player's cards face-up at the bottom
        hand_label = self.tinyFont.render("Your Hand:", True, self.white)
        self.screen.blit(hand_label, (350, 420))
        for i, card in enumerate(self.user_hand):
            # Skip eliminated cards (None)
            if card is None:
                continue
                
            pos = (375 + i * (Card.CARD_WIDTH + 10), 450) if i < 2 else (375 + (i-2) * (Card.CARD_WIDTH + 10), 550)
            
            # Check if this card is being peeked at
            is_peeked = ((self.peeked_card == (0, i) and 
                         self.state.is_phase(GamePhase.STOOL_PIGEON_PEEK)) or
                        (self.peeked_card == (0, i) and 
                         self.state.is_phase(GamePhase.VENDETTA_PEEK)))
            
            # Check if this is the first selected card for Bamboozle
            is_first_bamboozle = (self.bamboozle_first_card == (0, i) and
                                 self.state.is_phase(GamePhase.BAMBOOZLE_SELECT))
            
            # Check if this is the first selected card for Vendetta swap
            is_first_vendetta = (self.vendetta_first_card == (0, i) and
                                self.state.is_phase(GamePhase.VENDETTA_SWAP))
            
            # Normally bottom 2 cards are face-up, top 2 are face-down
            # But if we're peeking at this card, show it face-up
            face_up = (i >= 2) or is_peeked
            
            card.draw(
                self.screen,
                pos,
                self.font,
                self.tinyFont,
                active_mouse,
                face_up=face_up,
                is_user_turn=is_user_turn
            )
            
            # Highlight first selected card with yellow border
            if is_first_bamboozle or is_first_vendetta:
                pygame.draw.rect(self.screen, (255, 255, 0), card.rect, 4)
            
            # Enable/disable based on phase
            if self.state.is_phase(GamePhase.STOOL_PIGEON_PEEK):
                # During peek, only enable cards that aren't already being peeked
                if is_peeked:
                    card.disable()
                else:
                    card.enable()
            elif self.state.is_phase(GamePhase.STOOL_PIGEON_SWAP):
                # During Stool Pigeon swap, disable RAT cards (they can't be swapped out with regular swaps)
                if card.card_type == CardType.RAT:
                    card.disable()
                else:
                    card.enable()
            elif self.state.is_phase(GamePhase.BAMBOOZLE_SELECT):
                # During bamboozle, enable face-down cards (top 2) - INCLUDING RAT cards!
                # This allows you to pass RAT cards to opponents
                if i < 2:
                    card.enable()
                else:
                    card.disable()
            elif self.state.is_phase(GamePhase.VENDETTA_PEEK):
                # During Vendetta peek, enable all cards
                if is_peeked:
                    card.disable()
                else:
                    card.enable()
            elif self.state.is_phase(GamePhase.VENDETTA_SWAP):
                # During Vendetta swap, enable all cards - INCLUDING RAT cards!
                # This allows you to pass RAT cards to opponents
                card.enable()
            elif self.state.is_phase(GamePhase.KINGPIN_ELIMINATE):
                # During Kingpin eliminate, enable all cards (even RAT can be eliminated!)
                card.enable()
            elif self.state.is_phase(GamePhase.DECIDE):
                # During decide, disable RAT cards (can't swap them out with regular swaps)
                if card.card_type == CardType.RAT:
                    card.disable()
                else:
                    card.enable()
            else:
                # Normal phases - top 2 cards (index 0,1) disabled, bottom 2 enabled
                if i < 2:
                    card.disable()
                else:
                    card.enable()
        
        # ========== AGENT HAND ==========
        # Display agent's cards face-down at the top
        for i, card in enumerate(self.agent_hands):
            # Skip eliminated cards (None)
            if card is None:
                continue
                
            pos = (375 + i * (Card.CARD_WIDTH + 10), 150) if i < 2 else (375 + (i-2) * (Card.CARD_WIDTH + 10), 50)
            
            # Check if this card is being peeked at
            is_peeked = ((self.peeked_card == (1, i) and 
                         self.state.is_phase(GamePhase.STOOL_PIGEON_PEEK)) or
                        (self.peeked_card == (1, i) and 
                         self.state.is_phase(GamePhase.VENDETTA_PEEK)))
            
            # Check if this is the first selected card for Bamboozle
            is_first_bamboozle = (self.bamboozle_first_card == (1, i) and
                                 self.state.is_phase(GamePhase.BAMBOOZLE_SELECT))
            
            # Check if this is the first selected card for Vendetta swap
            is_first_vendetta = (self.vendetta_first_card == (1, i) and
                                self.state.is_phase(GamePhase.VENDETTA_SWAP))
            
            card.draw(
                self.screen,
                pos,
                self.font,
                self.tinyFont,
                active_mouse,
                face_up=is_peeked,  # Show face-up only if being peeked
                is_user_turn=is_user_turn
            )
            
            # Highlight first selected card with yellow border
            if is_first_bamboozle or is_first_vendetta:
                pygame.draw.rect(self.screen, (255, 255, 0), card.rect, 4)
            
            # During peek phase, enable agent cards for selection
            if self.state.is_phase(GamePhase.STOOL_PIGEON_PEEK):
                if is_peeked:
                    card.disable()
                else:
                    card.enable()
            elif self.state.is_phase(GamePhase.BAMBOOZLE_SELECT):
                # During bamboozle, enable all agent cards
                card.enable()
            elif self.state.is_phase(GamePhase.VENDETTA_PEEK):
                # During Vendetta peek, enable all agent cards
                if is_peeked:
                    card.disable()
                else:
                    card.enable()
            elif self.state.is_phase(GamePhase.VENDETTA_SWAP):
                # During Vendetta swap, enable all agent cards (RAT can be swapped)
                card.enable()
            else:
                card.disable()

        # ========== KNOCK BUTTON ==========
        # Only show knock button in normal phases
        if (not self.state.is_phase(GamePhase.STOOL_PIGEON_PEEK) and 
            not self.state.is_phase(GamePhase.STOOL_PIGEON_SWAP) and
            not self.state.is_phase(GamePhase.BAMBOOZLE_SELECT) and
            not self.state.is_phase(GamePhase.VENDETTA_PEEK) and
            not self.state.is_phase(GamePhase.VENDETTA_SWAP) and
            not self.state.is_phase(GamePhase.KINGPIN_CHOOSE) and
            not self.state.is_phase(GamePhase.KINGPIN_ELIMINATE) and
            not self.state.is_phase(GamePhase.KINGPIN_ADD)):
            self.knock_button.draw(self.screen, active_mouse)
        
        # ========== DONE BUTTON ==========
        # Show done button during peek phases when a card is selected
        if ((self.state.is_phase(GamePhase.STOOL_PIGEON_PEEK) or 
             self.state.is_phase(GamePhase.VENDETTA_PEEK)) and 
            self.peeked_card is not None):
            self.done_button.draw(self.screen, active_mouse)
        
        # ========== KINGPIN CHOICE BUTTONS ==========
        # Show Eliminate and Add buttons during Kingpin choice phase
        if self.state.is_phase(GamePhase.KINGPIN_CHOOSE):
            self.eliminate_button.draw(self.screen, active_mouse)
            self.add_button.draw(self.screen, active_mouse)
        
        # ========== ERROR MESSAGE ==========
        # Display error message if active
        if self.error_message and self.error_message_timer > 0:
            error_surface = self.font.render(self.error_message, True, self.red_orange)
            error_rect = error_surface.get_rect(center=(self.screenWidth // 2, self.screenHeight // 2))
            # Draw semi-transparent background
            bg_rect = error_rect.inflate(40, 20)
            bg_surface = pygame.Surface((bg_rect.width, bg_rect.height))
            bg_surface.set_alpha(200)
            bg_surface.fill((0, 0, 0))
            self.screen.blit(bg_surface, bg_rect)
            # Draw message
            self.screen.blit(error_surface, error_rect)
            self.error_message_timer -= 1
            if self.error_message_timer <= 0:
                self.error_message = None

        # Update the display with all drawn elements
        pygame.display.flip()

    
    def _loop_gui(self):
        """Main game loop: continuously refresh screen and handle user input."""
        running = True
        clock = pygame.time.Clock()  # Create clock for frame rate control
        
        while running: 
            clock.tick(self.fps)  # Limit to specified FPS
            
            # Draw background
            if self.background:
                self.screen.blit(self.background, (0, 0))
            else:
                self.screen.fill((26, 26, 46))

            self._refresh()  # Redraw all game elements

            # Check for user input events
            for event in pygame.event.get():
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:  # Left mouse button clicked
                        self._handle_click(event.pos)

    def _handle_click(self, pos):
        """Handle mouse clicks on game elements.
        
        Args:
            pos: Tuple (x, y) of click position
        """
        # Only allow actions during user's turn 
        if not self.state.is_user_turn():
            return
        
        # ========== DRAW PHASE ==========
        if self.state.is_phase(GamePhase.DRAW):
            if self.draw_pile_rect and self.draw_pile_rect.collidepoint(pos):
                Action.draw_from_pile().execute_action(self, GamePhase)
            elif self.discard_pile_rect and self.discard_pile_rect.collidepoint(pos) and self.discard_pile:
                Action.draw_from_discard().execute_action(self, GamePhase)

        # ========== DECIDE PHASE ==========
        elif self.state.is_phase(GamePhase.DECIDE):
            # For normal cards, allow keeping or discarding
            # Click on hand card = swap with drawn card
            for i, card in enumerate(self.user_hand):
                if card is not None and card.contains(pos):
                    Action.keep_card(i).execute_action(self, GamePhase)
                    return
            # Click on discard pile = discard drawn card
            if self.discard_pile_rect and self.discard_pile_rect.collidepoint(pos):
                Action.discard_drawn().execute_action(self, GamePhase)
        
        # ========== STOOL PIGEON PEEK PHASE ==========
        elif self.state.is_phase(GamePhase.STOOL_PIGEON_PEEK):
            # Check if clicked on a user card
            for i, card in enumerate(self.user_hand):
                if card is not None and card.contains(pos):
                    self.peeked_card = (0, i)  # Player 0, card index i
                    print(f"Peeking at your card {i}")
                    return
            
            # Check if clicked on an agent card
            for i, card in enumerate(self.agent_hands):
                if card is not None and card.contains(pos):
                    self.peeked_card = (1, i)  # Player 1 (agent), card index i
                    print(f"Peeking at agent's card {i}")
                    return
            
            # Check if clicked done button
            if self.peeked_card and self.done_button.contains(pos):
                print("Done peeking. Now swap the Stool Pigeon with one of your cards.")
                self.peeked_card = None
                self.state.set_phase(GamePhase.STOOL_PIGEON_SWAP)
        
        # ========== STOOL PIGEON SWAP PHASE ==========
        elif self.state.is_phase(GamePhase.STOOL_PIGEON_SWAP):
            # Click on hand card to swap with drawn Stool Pigeon
            for i, card in enumerate(self.user_hand):
                if card is not None and card.contains(pos):
                    Action.keep_card(i).execute_action(self, GamePhase)
                    self.state.pending_effect = None
                    return
        
        # ========== BAMBOOZLE SELECT PHASE ==========
        elif self.state.is_phase(GamePhase.BAMBOOZLE_SELECT):
            # Check if clicked on a user card (only face-down cards, indices 0-1)
            for i, card in enumerate(self.user_hand):
                if card is not None and card.contains(pos):
                    if self.bamboozle_first_card is None:
                        # First card selection
                        self.bamboozle_first_card = (0, i)
                        print(f"Selected first card: Your card {i}")
                    else:
                        # Second card selection - execute swap
                        player1_idx, card1_idx = self.bamboozle_first_card
                        Action.swap(player1_idx, card1_idx, 0, i).execute_action(self, GamePhase)
                        self.bamboozle_first_card = None
                    return
            
            # Check if clicked on an agent card
            for i, card in enumerate(self.agent_hands):
                if card is not None and card.contains(pos):
                    if self.bamboozle_first_card is None:
                        # First card selection
                        self.bamboozle_first_card = (1, i)
                        print(f"Selected first card: Agent's card {i}")
                    else:
                        # Second card selection - execute swap
                        player1_idx, card1_idx = self.bamboozle_first_card
                        Action.swap(player1_idx, card1_idx, 1, i).execute_action(self, GamePhase)
                        self.bamboozle_first_card = None
                    return
        
        # ========== VENDETTA PEEK PHASE ==========
        elif self.state.is_phase(GamePhase.VENDETTA_PEEK):
            # Check if clicked on a user card
            for i, card in enumerate(self.user_hand):
                if card is not None and card.contains(pos):
                    self.peeked_card = (0, i)
                    print(f"Vendetta: Peeking at your card {i}")
                    return
            
            # Check if clicked on an agent card
            for i, card in enumerate(self.agent_hands):
                if card is not None and card.contains(pos):
                    self.peeked_card = (1, i)
                    print(f"Vendetta: Peeking at agent's card {i}")
                    return
            
            # Check if clicked done button
            if self.peeked_card and self.done_button.contains(pos):
                print("Done peeking. Now swap any two cards.")
                self.peeked_card = None
                self.state.set_phase(GamePhase.VENDETTA_SWAP)
                self.state.clear_selection()  # Reset selection for swap phase
        
        # ========== VENDETTA SWAP PHASE ==========
        elif self.state.is_phase(GamePhase.VENDETTA_SWAP):
            # Check if clicked on a user card
            for i, card in enumerate(self.user_hand):
                if card is not None and card.contains(pos):
                    if self.vendetta_first_card is None:
                        # First card selection
                        self.vendetta_first_card = (0, i)
                        print(f"Vendetta: Selected first card - Your card {i}")
                    else:
                        # Second card selection - execute swap
                        player1_idx, card1_idx = self.vendetta_first_card
                        Action.swap(player1_idx, card1_idx, 0, i).execute_action(self, GamePhase)
                        self.vendetta_first_card = None
                    return
            
            # Check if clicked on an agent card
            for i, card in enumerate(self.agent_hands):
                if card is not None and card.contains(pos):
                    if self.vendetta_first_card is None:
                        # First card selection
                        self.vendetta_first_card = (1, i)
                        print(f"Vendetta: Selected first card - Agent's card {i}")
                    else:
                        # Second card selection - execute swap
                        player1_idx, card1_idx = self.vendetta_first_card
                        Action.swap(player1_idx, card1_idx, 1, i).execute_action(self, GamePhase)
                        self.vendetta_first_card = None
                    return
        
        # ========== KINGPIN CHOOSE PHASE ==========
        elif self.state.is_phase(GamePhase.KINGPIN_CHOOSE):
            # Check if clicked Eliminate button
            if self.eliminate_button.contains(pos):
                self.state.set_phase(GamePhase.KINGPIN_ELIMINATE)
                print("Kingpin: Eliminate mode - click a card to remove it from the game")
                return
            
            # Check if clicked Add button
            if self.add_button.contains(pos):
                # Execute add immediately (draws card and adds to opponent)
                Action.kingpin_add(1 if self.state.is_user_turn() else 0, 0).execute_action(self, GamePhase)
                return
        
        # ========== KINGPIN ELIMINATE PHASE ==========
        elif self.state.is_phase(GamePhase.KINGPIN_ELIMINATE):
            # Click on any of your cards to eliminate it
            for i, card in enumerate(self.user_hand):
                if card is not None and card.contains(pos):
                    Action.kingpin_eliminate(i).execute_action(self, GamePhase)
                    return
        
        # ========== KNOCK BUTTON ==========
        if self.knock_button.contains(pos) and not self.state.has_knocked():
            if (not self.state.is_phase(GamePhase.STOOL_PIGEON_PEEK) and 
                not self.state.is_phase(GamePhase.STOOL_PIGEON_SWAP) and
                not self.state.is_phase(GamePhase.BAMBOOZLE_SELECT) and
                not self.state.is_phase(GamePhase.VENDETTA_PEEK) and
                not self.state.is_phase(GamePhase.VENDETTA_SWAP) and
                not self.state.is_phase(GamePhase.KINGPIN_CHOOSE) and
                not self.state.is_phase(GamePhase.KINGPIN_ELIMINATE) and
                not self.state.is_phase(GamePhase.KINGPIN_ADD)):
                Action.knock().execute_action(self, GamePhase)

    def _create_deck(self):
        """Create a full deck of cards with proper distribution.
        
        Returns:
            List of Card objects ready to be shuffled
        """
        deck = []
        
        # Add 4 of each numbered card (values 2-10)
        for value in range(2, 11):
            for _ in range(4):
                deck.append(Card(CardType.NUMBERED, value))
        
        # Add action cards: 4 of each type
        for _ in range(4):
            deck.append(Card(CardType.STOOL_PIGEON))
            deck.append(Card(CardType.BAMBOOZLE))
            deck.append(Card(CardType.VENDETTA))
            deck.append(Card(CardType.KINGPIN))

        # Add special cards: 2 of each
        for _ in range(2):
            deck.append(Card(CardType.RAT))
            deck.append(Card(CardType.MEATBALL))
        
        return deck

    def _setup_game(self):
        """Initialize game state: create deck, shuffle, and deal starting hands."""
        # Create and shuffle the deck
        self.draw_pile = self._create_deck()
        random.shuffle(self.draw_pile)
        self.discard_pile = []

        # Deal 4 cards to agent (face-down)
        self.agent_hands = [self.draw_pile.pop() for _ in range(4)]
        # Deal 4 cards to player (face-up)
        self.user_hand = [self.draw_pile.pop() for _ in range(4)]
            
    def _main(self):
        """Start the game. In GUI mode, runs the game loop; otherwise does nothing."""
        if self.GUI:
            self._loop_gui()


if __name__ == "__main__":
    # Create game instance with GUI enabled and run it
    game = StoolPigeonGame(GUI=True, render_delay_sec=0.1)
    game._main()