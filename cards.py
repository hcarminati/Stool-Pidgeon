import pygame
from enum import Enum, auto

# Define all card types available in the game
class CardType(Enum):
    NUMBERED = auto()       # Regular numbered cards (1 - 9)
    STOOL_PIGEON = auto()   # Action: Peek at any face-down card
    BAMBOOZLE = auto()      # Action: Swap any two face-down cards
    VENDETTA = auto()       # Action: Peek at one, then swap any two
    KINGPIN = auto()        # Action: Eliminate own card OR add card to opponent
    RAT = auto()            # Special: Cannot be removed except by Kingpin
    MEATBALL = auto()       # Special: Value = 0

class Card: 
    # Card dimensions in pixels
    CARD_WIDTH = 65
    CARD_HEIGHT = 90

    IMAGE_FILES = {
        CardType.STOOL_PIGEON: "images/stool_pigeon.png",
        CardType.BAMBOOZLE: "images/bamboozle.png",
        CardType.VENDETTA: "images/vendetta.png",
        CardType.KINGPIN: "images/kingpin.png",
        CardType.RAT: "images/rat.png",
        CardType.MEATBALL: "images/meatball.png",
    }
    
    # RGB colors for each card type (used when drawing face-up)
    CARD_COLORS = {
        CardType.NUMBERED: (125, 124, 122), 
        CardType.STOOL_PIGEON: (18, 13, 49), 
        CardType.BAMBOOZLE: (108, 207, 39), 
        CardType.VENDETTA: (69, 74, 222), 
        CardType.KINGPIN: (216, 160, 65),
        CardType.RAT: (250, 153, 0), 
        CardType.MEATBALL: (49, 37, 9) 
    }

        # card_type: The CardType enum value (e.g., NUMBERED, STOOL_PIGEON)
        # value: Only used for NUMBERED cards (2-10)
    def __init__(self, card_type, value=None, clickable=True):
        self.card_type = card_type
        self.value = value
        self.face_up = False  # Default to face-down
        self.rect = None  # Updated when drawn; used for click detection
        self.clickable = clickable

    def get_image_file(self):
        """Return the image file path for this card, if it has one."""
        if self.card_type == CardType.NUMBERED: 
            return f'images/witness-{self.value}.png'
        return self.IMAGE_FILES.get(self.card_type, None)

    def enable(self):
        """Make the card clickable."""
        self.clickable = True
    
    def disable(self):
        """Make the card non-clickable (no hover effect, ignored by clicks)."""
        self.clickable = False

    def is_clickable(self):
        """Check if the card is clickable."""
        return self.clickable

    def contains(self, pos):
        """Check if a position (e.g., mouse click) is inside the card."""
        return self.is_clickable and self.rect.collidepoint(pos)
    
    def draw(self, screen, position, font, small_font, mouse_pos=None, face_up=None, is_user_turn=None):
        """
        Draw this card on the screen at the given position.
        """
        x, y = position
        self.rect = pygame.Rect(x, y, self.CARD_WIDTH, self.CARD_HEIGHT)
        card_color = self.CARD_COLORS[self.card_type]

        # Use parameter if provided, otherwise use instance attribute
        show_face = face_up if face_up is not None else self.face_up

        if show_face:
            self._draw_card_face(screen, card_color, position, mouse_pos, is_user_turn)
        else:
            self._draw_face_down(screen, position, mouse_pos, is_user_turn)

    def _draw_card_face(self, screen, card_color, position, mouse_pos=None, is_user_turn=None):
        """Draw the front of the card showing its details (color, name, value, description)."""
        image = self.get_image_file()
        if image:
            try:
                # If image 
                card_image = pygame.image.load(image)
                card_image = pygame.transform.scale(card_image, (self.CARD_WIDTH, self.CARD_HEIGHT))
                screen.blit(card_image, self.rect)
            except pygame.error:
                # If image loading fails, fall back to drawing a colored rectangle
                pygame.draw.rect(screen, card_color, self.rect)
        else:
            pygame.draw.rect(screen, card_color, self.rect)
    
        # Hover effect: brighten color if mouse is over this card
        if is_user_turn and self.clickable and mouse_pos and self.rect.collidepoint(mouse_pos):
            pygame.draw.rect(screen, (255, 255, 255), self.rect, 3)
            
    def _draw_face_down(self, screen, position, mouse_pos, is_user_turn):
        """Draw the back of the card (generic purple/blue design for hidden cards)."""
        try:
            cardback_image = pygame.image.load("images/cardback.png")
            cardback_image = pygame.transform.scale(cardback_image, (self.CARD_WIDTH, self.CARD_HEIGHT))
            screen.blit(cardback_image, self.rect)
        except pygame.error:
            pygame.draw.rect(screen, (100, 70, 120), self.rect)
            pygame.draw.rect(screen, (80, 50, 100), self.rect, 2)

        # Hover highlight: show white border if mouse is over this card
        if is_user_turn and self.clickable and mouse_pos and self.rect.collidepoint(mouse_pos):
            pygame.draw.rect(screen, (255, 255, 255), self.rect, 3)