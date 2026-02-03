import random
import pygame
from cards import CardType
from cards import Card  
from button import Button 

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
        self.knock_button_rect = (50, 550)

        # Buttons 
        self.knock_button = Button(self.knock_button_rect, 100, 50, 'images/knock-button.png')
        
        self._setup_game()

        if GUI:
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

    def _refresh(self):
        """Redraw the entire game screen. Called every frame."""
        mouse_pos = pygame.mouse.get_pos()

        # Render and display game title at the top
        # title = self.font.render("STOOL PIGEON", True, self.red_orange)
        # title_rect = title.get_rect(midtop=(self.screenWidth // 2, 10))
        # self.screen.blit(title, title_rect)

        # ========== DRAW PILE ==========
        # Label showing how many cards are left in draw pile
        pile_label = self.tinyFont.render(
            f"Discard: {len(self.discard_pile)}", True, self.white  
        )
        self.screen.blit(pile_label, (350, 260))
        
        # Draw the draw pile (generic card back) if cards remain
        if self.draw_pile:
            top_card = self.draw_pile[-1]
            top_card.draw(self.screen, (350, 280), self.font, self.tinyFont, mouse_pos, face_up=False)
            self.draw_pile_rect = top_card.rect
        else:
            self.draw_pile_rect = None
       
        # ========== DISCARD PILE ==========
        # Label showing how many cards are in discard pile
        pile_label = self.tinyFont.render(
            f"Discard: {len(self.discard_pile)}", True, self.white
        )
        self.screen.blit(pile_label, (450, 260))

        # Draw the top card of the discard pile (face-up) if it exists
        if self.discard_pile:
            top_card = self.discard_pile[-1]
            top_card.draw(self.screen, (450, 280), self.font, self.tinyFont, mouse_pos, face_up=True)
            self.discard_pile_rect = top_card.rect
        else:
            # Show empty discard pile placeholder (gray rectangle)
            self.discard_pile_rect = pygame.Rect(450, 280, Card.CARD_WIDTH, Card.CARD_HEIGHT)
            pygame.draw.rect(self.screen, (200, 200, 200), self.discard_pile_rect, 2)

        # ========== PLAYER HAND ==========
        # Display player's cards face-up at the bottom
        hand_label = self.tinyFont.render("Your Hand:", True, self.white)
        self.screen.blit(hand_label, (350, 400))
        for i, card in enumerate(self.user_hand):
            pos = (375 + i * (Card.CARD_WIDTH + 10), 430) if i < 2 else (375 + (i-2) * (Card.CARD_WIDTH + 10), 530)
            side = False if i < 2 else True
            card.draw(
                self.screen,
                pos,  # Position: left to right
                self.font,
                self.tinyFont,
                mouse_pos,
                face_up=side,  # Show card details
            )
        
        # ========== AGENT HAND ==========
        # Display agent's cards face-down at the top
        for i, card in enumerate(self.agent_hands):
            pos = (375 + i * (Card.CARD_WIDTH + 10), 150) if i < 2 else (375 + (i-2) * (Card.CARD_WIDTH + 10), 50)
            card.draw(
                self.screen,
                pos,  # Position: left to right
                self.font,
                self.tinyFont,
                mouse_pos,
                face_up=False,  # Hide card details
            )

        # ========== KNOCK BUTTON ==========
        self.knock_button.draw(self.screen, mouse_pos)

        # Update the display with all drawn elements
        pygame.display.flip()

    
    def _loop_gui(self):
        """Main game loop: continuously refresh screen and handle user input."""
        running = True 
        while running: 
            # Draw background
            if self.background:
                self.screen.blit(self.background, (0, 0))
            else:
                self.screen.fill((26, 26, 46))

            # self.screen.fill(self.white)  # Clear screen with white background
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
        # Check if player clicked on the draw pile
        if self.draw_pile_rect and self.draw_pile_rect.collidepoint(pos):
            if self.draw_pile:
                # Remove a card from draw pile and move it to discard
                card = self.draw_pile.pop()
                self.discard_pile.append(card)
                # Print card info for debugging
                print(f"Drew: {card.card_type.name}" + (f" ({card.value})" if card.value else ""))
        if self.knock_button_rect:
             print(f"Knocked.")

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
        
       