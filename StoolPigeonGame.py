import random
import pygame
from cards import CardType, Card  
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

        # RGB color definitions
        self.black = (0, 0, 0)
        self.white = (255, 255, 255)
        self.red_orange = (245, 104, 90)

        # Fonts
        self.font = None
        self.tinyFont = None
        
        # Game piles
        self.draw_pile = []
        self.discard_pile = []
        self.agent_hands = []
        self.user_hand = []

        # UI rects
        self.draw_pile_rect = None
        self.discard_pile_rect = None

        # Buttons 
        self.knock_button = Button((50, 575), 100, 50, 'images/knock-button.png')
        self.knock_button_rect = self.knock_button.rect
        self.done_button = Button((750, 575), 100, 50, 'images/done-button.png')
        self.done_button_rect = self.done_button.rect
        self.eliminate_button = Button((350, 400), 150, 50, 'images/eliminate-button.png')
        self.eliminate_button_rect = self.eliminate_button.rect
        self.add_button = Button((520, 400), 150, 50, 'images/add-button.png')
        self.add_button_rect = self.add_button.rect

        # Game state
        self.state = GameState()
        
        # Card tracking
        self.peeked_card = None
        self.bamboozle_first_card = None
        self.vendetta_first_card = None
        
        # Error messages
        self.error_message = None
        self.error_message_timer = 0
        
        self._setup_game()

        if self.GUI:
            pygame.init()
            self._initScreen()
            self._load_background()
            self._refresh()

    def _initScreen(self):
        """Initialize the pygame window and fonts."""
        self.cellSize = 40
        self.screenWidth = 900
        self.screenHeight = 700
        self.screen = pygame.display.set_mode((self.screenWidth, self.screenHeight))
        self.font = pygame.font.Font(None, 32)
        self.tinyFont = pygame.font.Font(None, 18)
        pygame.display.set_caption("Stool Pigeon")
    
    def _load_background(self):
        """Load and scale the background image."""
        try:
            bg_image = pygame.image.load('images/game-background-light.png')
            self.background = pygame.transform.scale(bg_image, (self.screenWidth, self.screenHeight))
        except pygame.error:
            self.background = None

    # ========== HELPER METHODS ==========

    def get_current_hand(self):
        """Returns the current player's hand."""
        return self.user_hand if self.state.is_user_turn() else self.agent_hands

    def get_opponent_hand(self):
        """Return the opponent's hand."""
        return self.agent_hands if self.state.is_user_turn() else self.user_hand
    
    def show_error_message(self, message, duration=3):
        """Display an error message for a specified duration (in seconds)."""
        self.error_message = message
        self.error_message_timer = duration * self.fps

    # ========== RENDERING METHODS ==========
    
    def _refresh(self):
        """Redraw the entire game screen."""
        mouse_pos = pygame.mouse.get_pos()
        is_user_turn = self.state.is_user_turn()
        active_mouse = mouse_pos if is_user_turn else None

        self._render_drawn_card(active_mouse, is_user_turn)
        self._render_game_state()
        self._render_draw_pile(active_mouse, is_user_turn)
        self._render_discard_pile(active_mouse, is_user_turn)
        self._render_player_hand(active_mouse, is_user_turn)
        self._render_agent_hand(active_mouse, is_user_turn)
        self._render_buttons(active_mouse)
        self._render_error_message()

        pygame.display.flip()

    def _render_drawn_card(self, active_mouse, is_user_turn):
        """Render the currently drawn card."""
        if not (self.state.drawn_card and self.state.is_user_turn()):
            return
        
        # Check if we're in a phase where drawn card should be shown
        show_phases = [
            GamePhase.DECIDE, GamePhase.STOOL_PIGEON_PEEK, GamePhase.STOOL_PIGEON_SWAP,
            GamePhase.BAMBOOZLE_SELECT, GamePhase.VENDETTA_PEEK, GamePhase.VENDETTA_SWAP,
            GamePhase.KINGPIN_CHOOSE, GamePhase.KINGPIN_ELIMINATE, GamePhase.KINGPIN_ADD
        ]
        
        if self.state.phase in show_phases:
            drawn_label = self.tinyFont.render("You drew:", True, self.white)
            self.screen.blit(drawn_label, (600, 270))
            self.state.drawn_card.draw(self.screen, (600, 300), self.font, self.tinyFont,
                                      active_mouse, face_up=True, is_user_turn=is_user_turn)
            self.state.drawn_card.disable()

    def _render_game_state(self):
        """Render game state information."""
        phase_text = self.tinyFont.render(
            f"Phase: {self.state.phase.name} | Turn: {self.state.get_current_player_name()}", 
            True, self.white
        )
        self.screen.blit(phase_text, (10, 10))
        
        instructions = self.tinyFont.render(self.state.get_phase_instructions(), True, self.white)
        self.screen.blit(instructions, (10, 35))

        if self.state.has_knocked():
            knocked_name = "User" if self.state.knocked_by == 0 else "Agent"
            knock_text = self.tinyFont.render(f"Knocked by: {knocked_name}", True, self.red_orange)
            self.screen.blit(knock_text, (10, 60))

    def _render_draw_pile(self, active_mouse, is_user_turn):
        """Render the draw pile."""
        pile_label = self.tinyFont.render(f"Draw: {len(self.draw_pile)}", True, self.white)
        self.screen.blit(pile_label, (350, 270))
        
        if self.draw_pile:
            top_card = self.draw_pile[-1]
            top_card.draw(self.screen, (350, 300), self.font, self.tinyFont, 
                         active_mouse, face_up=False, is_user_turn=is_user_turn)
            self.draw_pile_rect = top_card.rect
        else:
            self.draw_pile_rect = None

    def _render_discard_pile(self, active_mouse, is_user_turn):
        """Render the discard pile."""
        pile_label = self.tinyFont.render(f"Discard: {len(self.discard_pile)}", True, self.white)
        self.screen.blit(pile_label, (475, 270))

        if self.discard_pile:
            top_card = self.discard_pile[-1]
            top_card.draw(self.screen, (475, 300), self.font, self.tinyFont,
                         active_mouse, face_up=True, is_user_turn=is_user_turn)
            self.discard_pile_rect = top_card.rect
            
            if self.state.is_phase(GamePhase.DECIDE):
                top_card.enable()
            else:
                top_card.disable()
        else:
            self.discard_pile_rect = pygame.Rect(475, 300, Card.CARD_WIDTH, Card.CARD_HEIGHT)
            pygame.draw.rect(self.screen, (200, 200, 200), self.discard_pile_rect, 2)

    def _render_player_hand(self, active_mouse, is_user_turn):
        """Render the player's hand."""
        hand_label = self.tinyFont.render("Your Hand:", True, self.white)
        self.screen.blit(hand_label, (350, 420))
        
        for i, card in enumerate(self.user_hand):
            if card is None:
                continue
            
            pos = self._get_card_position(i, is_bottom_row=True)
            face_up = self._should_show_card_face_up(i, player_idx=0)
            
            card.draw(self.screen, pos, self.font, self.tinyFont, active_mouse,
                     face_up=face_up, is_user_turn=is_user_turn)
            
            self._highlight_selected_card(card, i, player_idx=0)
            self._set_card_enabled_state(card, i, player_idx=0)

    def _render_agent_hand(self, active_mouse, is_user_turn):
        """Render the agent's hand."""
        for i, card in enumerate(self.agent_hands):
            if card is None:
                continue
            
            pos = self._get_card_position(i, is_bottom_row=False)
            face_up = self._should_show_card_face_up(i, player_idx=1)
            
            card.draw(self.screen, pos, self.font, self.tinyFont, active_mouse,
                     face_up=face_up, is_user_turn=is_user_turn)
            
            self._highlight_selected_card(card, i, player_idx=1)
            self._set_card_enabled_state(card, i, player_idx=1)

    def _get_card_position(self, card_idx, is_bottom_row):
        """Calculate card position based on index and whether it's bottom row."""
        if is_bottom_row:
            y_pos = 450 if card_idx < 2 else 550
        else:
            y_pos = 150 if card_idx < 2 else 50
        
        x_offset = card_idx if card_idx < 2 else card_idx - 2
        x_pos = 375 + x_offset * (Card.CARD_WIDTH + 10)
        
        return (x_pos, y_pos)

    def _should_show_card_face_up(self, card_idx, player_idx):
        """Determine if a card should be shown face-up."""
        is_peeked = ((self.peeked_card == (player_idx, card_idx)) and
                    (self.state.is_phase(GamePhase.STOOL_PIGEON_PEEK) or
                     self.state.is_phase(GamePhase.VENDETTA_PEEK)))
        
        # Player cards: bottom 2 are face-up, or if being peeked
        # Agent cards: only show if being peeked
        if player_idx == 0:
            return (card_idx >= 2) or is_peeked
        else:
            return is_peeked

    def _highlight_selected_card(self, card, card_idx, player_idx):
        """Highlight a card if it's selected for Bamboozle or Vendetta."""
        is_first_bamboozle = (self.bamboozle_first_card == (player_idx, card_idx) and
                             self.state.is_phase(GamePhase.BAMBOOZLE_SELECT))
        is_first_vendetta = (self.vendetta_first_card == (player_idx, card_idx) and
                            self.state.is_phase(GamePhase.VENDETTA_SWAP))
        
        if is_first_bamboozle or is_first_vendetta:
            pygame.draw.rect(self.screen, (255, 255, 0), card.rect, 4)

    def _set_card_enabled_state(self, card, card_idx, player_idx):
        """Enable or disable a card based on current phase and card state."""
        phase = self.state.phase
        is_peeked = (self.peeked_card == (player_idx, card_idx))
        
        # Player cards
        if player_idx == 0:
            if phase == GamePhase.STOOL_PIGEON_PEEK or phase == GamePhase.VENDETTA_PEEK:
                card.enable() if not is_peeked else card.disable()
            elif phase == GamePhase.STOOL_PIGEON_SWAP:
                card.enable() if card.card_type != CardType.RAT else card.disable()
            elif phase == GamePhase.BAMBOOZLE_SELECT:
                card.enable() if card_idx < 2 else card.disable()
            elif phase == GamePhase.VENDETTA_SWAP or phase == GamePhase.KINGPIN_ELIMINATE:
                card.enable()
            elif phase == GamePhase.DECIDE:
                card.enable() if card.card_type != CardType.RAT else card.disable()
            else:
                card.enable() if card_idx >= 2 else card.disable()
        
        # Agent cards
        else:
            if phase in [GamePhase.STOOL_PIGEON_PEEK, GamePhase.VENDETTA_PEEK]:
                card.enable() if not is_peeked else card.disable()
            elif phase in [GamePhase.BAMBOOZLE_SELECT, GamePhase.VENDETTA_SWAP]:
                card.enable()
            else:
                card.disable()

    def _render_buttons(self, active_mouse):
        """Render all interactive buttons."""
        # Knock button (not shown during special card phases)
        special_phases = [
            GamePhase.STOOL_PIGEON_PEEK, GamePhase.STOOL_PIGEON_SWAP,
            GamePhase.BAMBOOZLE_SELECT, GamePhase.VENDETTA_PEEK, GamePhase.VENDETTA_SWAP,
            GamePhase.KINGPIN_CHOOSE, GamePhase.KINGPIN_ELIMINATE, GamePhase.KINGPIN_ADD
        ]
        
        if self.state.phase not in special_phases:
            self.knock_button.draw(self.screen, active_mouse)
        
        # Done button (shown during peek phases when card is selected)
        if ((self.state.is_phase(GamePhase.STOOL_PIGEON_PEEK) or 
             self.state.is_phase(GamePhase.VENDETTA_PEEK)) and 
            self.peeked_card is not None):
            self.done_button.draw(self.screen, active_mouse)
        
        # Kingpin choice buttons
        if self.state.is_phase(GamePhase.KINGPIN_CHOOSE):
            self.eliminate_button.draw(self.screen, active_mouse)
            self.add_button.draw(self.screen, active_mouse)

    def _render_error_message(self):
        """Render error message if active."""
        if self.error_message and self.error_message_timer > 0:
            error_surface = self.font.render(self.error_message, True, self.red_orange)
            error_rect = error_surface.get_rect(center=(self.screenWidth // 2, self.screenHeight // 2))
            
            bg_rect = error_rect.inflate(40, 20)
            bg_surface = pygame.Surface((bg_rect.width, bg_rect.height))
            bg_surface.set_alpha(200)
            bg_surface.fill((0, 0, 0))
            self.screen.blit(bg_surface, bg_rect)
            self.screen.blit(error_surface, error_rect)
            
            self.error_message_timer -= 1
            if self.error_message_timer <= 0:
                self.error_message = None

    # ========== INPUT HANDLING ==========
    
    def _handle_click(self, pos):
        """Handle mouse clicks on game elements."""
        if not self.state.is_user_turn():
            return
        
        # Route to phase-specific handler
        phase_handlers = {
            GamePhase.DRAW: self._handle_draw_phase_click,
            GamePhase.DECIDE: self._handle_decide_phase_click,
            GamePhase.STOOL_PIGEON_PEEK: self._handle_stool_pigeon_peek_click,
            GamePhase.STOOL_PIGEON_SWAP: self._handle_stool_pigeon_swap_click,
            GamePhase.BAMBOOZLE_SELECT: self._handle_bamboozle_select_click,
            GamePhase.VENDETTA_PEEK: self._handle_vendetta_peek_click,
            GamePhase.VENDETTA_SWAP: self._handle_vendetta_swap_click,
            GamePhase.KINGPIN_CHOOSE: self._handle_kingpin_choose_click,
            GamePhase.KINGPIN_ELIMINATE: self._handle_kingpin_eliminate_click,
        }
        
        handler = phase_handlers.get(self.state.phase)
        if handler:
            handler(pos)
        
        # Check knock button (available in most phases)
        self._check_knock_button(pos)

    def _handle_draw_phase_click(self, pos):
        """Handle clicks during DRAW phase."""
        if self.draw_pile_rect and self.draw_pile_rect.collidepoint(pos):
            Action.draw_from_pile().execute_action(self, GamePhase)
        elif self.discard_pile_rect and self.discard_pile_rect.collidepoint(pos) and self.discard_pile:
            Action.draw_from_discard().execute_action(self, GamePhase)

    def _handle_decide_phase_click(self, pos):
        """Handle clicks during DECIDE phase."""
        # Click on hand card to swap
        for i, card in enumerate(self.user_hand):
            if card is not None and card.contains(pos):
                Action.keep_card(i).execute_action(self, GamePhase)
                return
        
        # Click on discard pile to discard
        if self.discard_pile_rect and self.discard_pile_rect.collidepoint(pos):
            Action.discard_drawn().execute_action(self, GamePhase)

    def _handle_stool_pigeon_peek_click(self, pos):
        """Handle clicks during STOOL_PIGEON_PEEK phase."""
        # Check user cards
        for i, card in enumerate(self.user_hand):
            if card is not None and card.contains(pos):
                self.peeked_card = (0, i)
                print(f"Peeking at your card {i}")
                return
        
        # Check agent cards
        for i, card in enumerate(self.agent_hands):
            if card is not None and card.contains(pos):
                self.peeked_card = (1, i)
                print(f"Peeking at agent's card {i}")
                return
        
        # Check done button
        if self.peeked_card and self.done_button.contains(pos):
            print("Done peeking. Now swap the Stool Pigeon with one of your cards.")
            self.peeked_card = None
            self.state.set_phase(GamePhase.STOOL_PIGEON_SWAP)

    def _handle_stool_pigeon_swap_click(self, pos):
        """Handle clicks during STOOL_PIGEON_SWAP phase."""
        for i, card in enumerate(self.user_hand):
            if card is not None and card.contains(pos):
                Action.keep_card(i).execute_action(self, GamePhase)
                self.state.pending_effect = None
                return

    def _handle_bamboozle_select_click(self, pos):
        """Handle clicks during BAMBOOZLE_SELECT phase."""
        selected = self._check_card_click(pos)
        if selected:
            player_idx, card_idx = selected
            if self.bamboozle_first_card is None:
                self.bamboozle_first_card = (player_idx, card_idx)
                print(f"Selected first card: {'Your' if player_idx == 0 else 'Agent'} card {card_idx}")
            else:
                p1, c1 = self.bamboozle_first_card
                Action.swap(p1, c1, player_idx, card_idx).execute_action(self, GamePhase)
                self.bamboozle_first_card = None

    def _handle_vendetta_peek_click(self, pos):
        """Handle clicks during VENDETTA_PEEK phase."""
        selected = self._check_card_click(pos)
        if selected:
            self.peeked_card = selected
            player_idx, card_idx = selected
            print(f"Vendetta: Peeking at {'your' if player_idx == 0 else 'agent'} card {card_idx}")
            return
        
        if self.peeked_card and self.done_button.contains(pos):
            print("Done peeking. Now swap any two cards.")
            self.peeked_card = None
            self.state.set_phase(GamePhase.VENDETTA_SWAP)
            self.state.clear_selection()

    def _handle_vendetta_swap_click(self, pos):
        """Handle clicks during VENDETTA_SWAP phase."""
        selected = self._check_card_click(pos)
        if selected:
            player_idx, card_idx = selected
            if self.vendetta_first_card is None:
                self.vendetta_first_card = (player_idx, card_idx)
                print(f"Vendetta: Selected first card - {'Your' if player_idx == 0 else 'Agent'} card {card_idx}")
            else:
                p1, c1 = self.vendetta_first_card
                Action.swap(p1, c1, player_idx, card_idx).execute_action(self, GamePhase)
                self.vendetta_first_card = None

    def _handle_kingpin_choose_click(self, pos):
        """Handle clicks during KINGPIN_CHOOSE phase."""
        if self.eliminate_button.contains(pos):
            self.state.set_phase(GamePhase.KINGPIN_ELIMINATE)
            print("Kingpin: Eliminate mode - click a card to remove it from the game")
        elif self.add_button.contains(pos):
            Action.kingpin_add(1 if self.state.is_user_turn() else 0, 0).execute_action(self, GamePhase)

    def _handle_kingpin_eliminate_click(self, pos):
        """Handle clicks during KINGPIN_ELIMINATE phase."""
        for i, card in enumerate(self.user_hand):
            if card is not None and card.contains(pos):
                Action.kingpin_eliminate(i).execute_action(self, GamePhase)
                return

    def _check_card_click(self, pos):
        """Check if any card was clicked, return (player_idx, card_idx) or None."""
        for i, card in enumerate(self.user_hand):
            if card is not None and card.contains(pos):
                return (0, i)
        
        for i, card in enumerate(self.agent_hands):
            if card is not None and card.contains(pos):
                return (1, i)
        
        return None

    def _check_knock_button(self, pos):
        """Check if knock button was clicked."""
        special_phases = [
            GamePhase.STOOL_PIGEON_PEEK, GamePhase.STOOL_PIGEON_SWAP,
            GamePhase.BAMBOOZLE_SELECT, GamePhase.VENDETTA_PEEK, GamePhase.VENDETTA_SWAP,
            GamePhase.KINGPIN_CHOOSE, GamePhase.KINGPIN_ELIMINATE, GamePhase.KINGPIN_ADD
        ]
        
        if (self.knock_button.contains(pos) and not self.state.has_knocked() and
            self.state.phase not in special_phases):
            Action.knock().execute_action(self, GamePhase)

    # ========== GAME SETUP ==========

    def _create_deck(self):
        """Create a full deck of cards with proper distribution."""
        deck = []
        
        # Add numbered cards (2-10), 4 of each
        for value in range(2, 11):
            for _ in range(4):
                deck.append(Card(CardType.NUMBERED, value))
        
        # Add action cards, 4 of each
        for _ in range(4):
            deck.append(Card(CardType.STOOL_PIGEON))
            deck.append(Card(CardType.BAMBOOZLE))
            deck.append(Card(CardType.VENDETTA))
            deck.append(Card(CardType.KINGPIN))

        # Add special cards, 2 of each
        for _ in range(2):
            deck.append(Card(CardType.RAT))
            deck.append(Card(CardType.MEATBALL))
        
        return deck

    def _setup_game(self):
        """Initialize game state: create deck, shuffle, and deal."""
        self.draw_pile = self._create_deck()
        random.shuffle(self.draw_pile)
        self.discard_pile = []
        self.agent_hands = [self.draw_pile.pop() for _ in range(4)]
        self.user_hand = [self.draw_pile.pop() for _ in range(4)]

    # ========== MAIN LOOP ==========
    
    def _loop_gui(self):
        """Main game loop: refresh screen and handle input."""
        running = True
        clock = pygame.time.Clock()
        
        while running: 
            clock.tick(self.fps)
            
            if self.background:
                self.screen.blit(self.background, (0, 0))
            else:
                self.screen.fill((26, 26, 46))

            self._refresh()

            for event in pygame.event.get():
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    self._handle_click(event.pos)
                elif event.type == pygame.QUIT:
                    running = False

    def _main(self):
        """Start the game."""
        if self.GUI:
            self._loop_gui()


if __name__ == "__main__":
    game = StoolPigeonGame(GUI=True, render_delay_sec=0.1)
    game._main()