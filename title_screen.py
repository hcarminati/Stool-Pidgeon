import pygame
from button import Button

class TitleScreen:
    """Start screen."""
    def __init__(self, screen_width, screen_height):
        self.screen_width = screen_width
        self.screen_height = screen_height

        # Load background, fall back to solid color if missing
        self.background = None
        try:
            bg = pygame.image.load('images/game-background.png')
            self.background = pygame.transform.scale(bg, (screen_width, screen_height))
        except pygame.error:
            pass

        # Colors
        self.white = (255, 255, 255)
        self.off_white = (210, 210, 220)
        self.red_orange = (245, 104, 90)
        self.muted = (160, 155, 185)

        # Fonts
        self.title_font = pygame.font.Font(None, 96)
        self.section_font = pygame.font.Font(None, 28)
        self.rule_font = pygame.font.Font(None, 22)
        self.hint_font = pygame.font.Font(None, 20)

        # Start Button
        self.start_button = Button((screen_width // 2 - 50, 598),
                                   100, 50,
                                   'images/start-button.png')

        # Left column rule sections
        self.left_sections = [
            ("THE GOAL", [
                "Have the lowest total card value",
                "when the round ends.",
            ]),
            ("YOUR TURN", [
                "Draw from the draw or discard pile.",
                "Swap it with a hand card, or discard it.",
                "Knock if you think you have the lowest score.",
            ]),
            ("YOUR HAND", [
                "You start with 4 cards.",
                "Bottom 2 are face-up (known to you).",
                "Top 2 are face-down (unknown).",
            ]),
        ]

        # Right column rule sections
        self.right_sections = [
            ("CARD VALUES", [
                "Numbers  \u2192  face value",
                "Action cards  \u2192  10 pts",
                "RAT  \u2192  15 pts    |    Meatball  \u2192  0 pts",
            ]),
            ("ACTION CARDS", [
                "Stool Pigeon  \u2014  peek at any card",
                "Bamboozle  \u2014  swap any two cards",
                "Vendetta  \u2014  peek, then swap",
                "Kingpin  \u2014  remove your card, or",
                "               add a card to opponent",
            ]),
            ("SPECIAL RULES", [
                "RAT cards can only be removed by Kingpin.",
                "After a knock, everyone gets one last turn.",
            ]),
        ]

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

    def render(self, screen, active_mouse):
        """Renders title screen."""
        # Background
        if self.background:
            screen.blit(self.background, (0, 0))
        else:
            screen.fill((26, 26, 46))

        # Title
        title_surf = self.title_font.render("STOOL PIGEON", True, self.red_orange)
        screen.blit(title_surf, title_surf.get_rect(center=(self.screen_width // 2, 72)))

        # Rules panel
        panel = pygame.Rect(30, 150, self.screen_width - 60, 390)
        pygame.draw.rect(screen, (40, 38, 60), panel, border_radius=8)
        pygame.draw.rect(screen, (70, 65, 100), panel, 1, border_radius=8)

        col_w = (panel.width - 50) // 2
        left_x = panel.x + 16
        right_x = left_x + col_w + 18
        left_y = right_y = panel.y + 14

        for heading, lines in self.left_sections:
            left_y = self._draw_section(screen, heading, lines, left_x, left_y, col_w)

        for heading, lines in self.right_sections:
            right_y = self._draw_section(screen, heading, lines, right_x, right_y, col_w)

        # Divider line between columns
        divider_x = left_x + col_w + 9
        pygame.draw.line(screen, (70, 65, 100),
                         (divider_x, panel.y + 10),
                         (divider_x, panel.bottom - 10), 1)

        # Hint text above start button
        hint = self.hint_font.render(
            "Watch the instruction bar at the top left corner during play!",
            True, self.muted
        )
        screen.blit(hint, hint.get_rect(center=(self.screen_width // 2, 582)))

        self.start_button.draw(screen, active_mouse)

    def handle_click(self, pos):
        """Handles clicking start button."""
        return self.start_button.contains(pos)
