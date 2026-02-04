import pygame

class Button:
    def __init__(self, position, width, height, image, clickable=True):
        self.x, self.y = position
        self.width = width
        self.height = height
        self.rect = pygame.Rect(self.x, self.y, width, height)
        self.image = image
        self.clickable = clickable
    
    def enable(self):
        """Make the button clickable."""
        self.clickable = True
    
    def disable(self):
        """Make the button non-clickable (no hover effect, ignored by clicks)."""
        self.clickable = False

    def is_clickable(self):
        """Check if the button is clickable."""
        return self.clickable
    
    def draw(self, screen, mouse_pos=None):
        try:
            # Load and draw button image
            card_image = pygame.image.load(self.image)
            card_image = pygame.transform.scale(card_image, (self.width, self.height))
            screen.blit(card_image, (self.rect.x, self.rect.y))
        except pygame.error:
            # If image loading fails, fall back to drawing a colored rectangle
            pygame.draw.rect(screen, "#000", self.rect)

        # Hover effect: draw white border if mouse is over this button
        if self.clickable and mouse_pos and self.rect.collidepoint(mouse_pos):
            pygame.draw.rect(screen, (255, 255, 255), self.rect, 3)