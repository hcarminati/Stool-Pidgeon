import pygame

class Button:
    def __init__(self, position, width, height, image):
        self.x, self.y = position
        self.width = width
        self.height = height
        self.rect = pygame.Rect(self.x, self.y, width, height)
        self.image = image
        self.enabled = True
        self.visible = True
    
    def contains(self, pos):
        return self.enabled and self.visible and self.rect.collidepoint(pos)
    
    def draw(self, screen, mouse_pos=None):
        """Draw the button at its fixed position."""
        if not self.visible:
            return
        self._draw_button(screen, mouse_pos)
    
    def _draw_button(self, screen, mouse_pos=None):
        try:
            # Load and draw button image
            card_image = pygame.image.load(self.image)
            card_image = pygame.transform.scale(card_image, (self.width, self.height))
            screen.blit(card_image, (self.rect.x, self.rect.y))
        except pygame.error:
            # If image loading fails, fall back to drawing a colored rectangle
            pygame.draw.rect(screen, "#000", self.rect)

        # Hover effect: draw white border if mouse is over this button
        if mouse_pos and self.rect.collidepoint(mouse_pos):
            pygame.draw.rect(screen, (255, 255, 255), self.rect, 3)