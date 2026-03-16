import pygame
from button import Button

def calculate_score(hand: list) -> int:
    """Calculates each player's score."""
    total = 0
    for card in hand:
        if card is None:
            continue
        total += card.value
    return total


class EndScreen:
    """Handles the end screen rendering and clicking."""
    CARD_W, CARD_H = 65, 90
    GAP = 12

    def __init__(self, screen_w: int, screen_h: int):
        self.screen_width  = screen_w
        self.screen_height = screen_h

        self.background = None
        try:
            bg = pygame.image.load('images/game-background.png')
            self.background = pygame.transform.scale(bg, (screen_w, screen_h))
        except pygame.error:
            pass

        # Colors
        self.white      = (255, 255, 255)
        self.off_white  = (210, 210, 220)
        self.red_orange = (245, 104,  90)
        self.muted      = (160, 155, 185)
        self.green      = (100, 210, 100)

        # Fonts
        self.title_font   = pygame.font.Font(None, 96)
        self.section_font = pygame.font.Font(None, 28)
        self.rule_font    = pygame.font.Font(None, 22)
        self.hint_font    = pygame.font.Font(None, 20)
        self.tiny_font    = pygame.font.Font(None, 20)

        # New Game button
        self.new_game_btn = Button(
            (screen_w // 2 - 75, 598), 150, 50,
            'images/new-game-button.png'
        )

    def render(self, screen, user_hand: list, agent_hand: list, mouse_pos=None):
        """Renders the end screen."""
        user_score  = calculate_score(user_hand)
        agent_score = calculate_score(agent_hand)

        # Background
        if self.background:
            screen.blit(self.background, (0, 0))
        else:
            screen.fill((26, 26, 46))

        # Title
        title_surf = self.title_font.render("GAME OVER", True, self.red_orange)
        screen.blit(title_surf, title_surf.get_rect(
            center=(self.screen_width // 2, 72)))

        # Main panel
        panel = pygame.Rect(30, 150, self.screen_width - 60, 390)
        pygame.draw.rect(screen, (40, 38, 60), panel, border_radius=8)
        pygame.draw.rect(screen, (70, 65, 100), panel, 1, border_radius=8)

        col_w  = (panel.width - 50) // 2
        left_x = panel.x + 16
        right_x = left_x + col_w + 18

        # Divider between columns
        divider_x = left_x + col_w + 9
        pygame.draw.line(screen, (70, 65, 100),
                         (divider_x, panel.y + 10),
                         (divider_x, panel.bottom - 10), 1)

        # Winner text
        if user_score < agent_score:
            winner_text, winner_col = "You Win!", self.green
        elif agent_score < user_score:
            winner_text, winner_col = "Agent Wins!", self.red_orange
        else:
            winner_text, winner_col = "It's a Tie!", self.off_white

        w_surf = self.section_font.render(winner_text, True, winner_col)
        screen.blit(w_surf, w_surf.get_rect(
            center=(self.screen_width // 2, panel.y + 18)))

        # Left column — Your Hand
        y = panel.y + 40
        y = self._draw_section(screen, "YOUR HAND", [f"Score: {user_score}"],
                               left_x, y, col_w)
        self._draw_cards(screen, user_hand, left_x, y, col_w)

        # Right column — Agent Hand
        y = panel.y + 40
        y = self._draw_section(screen, "AGENT HAND", [f"Score: {agent_score}"],
                               right_x, y, col_w)
        self._draw_cards(screen, agent_hand, right_x, y, col_w)

        # Hint line above button
        hint = self.hint_font.render(
            "Lower score wins!", True, self.muted)
        screen.blit(hint, hint.get_rect(
            center=(self.screen_width // 2, 582)))

        self.new_game_btn.draw(screen, mouse_pos)

    def handle_click(self, pos) -> bool:
        """Handles clicking the new game button."""
        return self.new_game_btn.contains(pos)

    # Helpers

    def _draw_section(self, screen, heading, lines, x, y, width):
        # Faint highlight bar behind the heading
        hghlght_bar = pygame.Surface((width, 22), pygame.SRCALPHA)
        pygame.draw.rect(hghlght_bar,
                         (*self.red_orange, 55),
                         hghlght_bar.get_rect(),
                         border_radius=4)
        screen.blit(hghlght_bar, (x, y))

        heading_surf = self.section_font.render(heading, True, self.red_orange)
        screen.blit(heading_surf, (x + 6, y + 2))
        y += 28

        for line in lines:
            line_surf = self.rule_font.render(line, True, self.off_white)
            screen.blit(line_surf, (x + 6, y))
            y += 19
        return y + 10

    def _draw_cards(self, screen, hand, col_x, y, col_w):
        """Render hand cards face-up with a +N label above each."""
        active  = [c for c in hand if c is not None]
        total_w = len(active) * self.CARD_W + max(0, len(active) - 1) * self.GAP
        start_x = col_x + (col_w - total_w) // 2

        for i, card in enumerate(active):
            cx = start_x + i * (self.CARD_W + self.GAP)
            pts = card.value

            # +N label
            label = self.tiny_font.render(f"+{pts}", True, self.muted)
            screen.blit(label, label.get_rect(centerx=cx + self.CARD_W // 2, y=y))

            card.draw(screen, (cx, y + 18),
                      mouse_pos=None, face_up=True, is_user_turn=False)
