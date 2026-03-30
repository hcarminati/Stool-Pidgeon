import pygame

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

        # Difficulty selection buttons
        btn_w = 160
        btn_h = 48
        btn_y = 580
        self.difficulty_buttons = [
            ("EASY", "Random", pygame.Rect(100, btn_y, btn_w, btn_h)),
            ("MEDIUM", "Heuristic", pygame.Rect(280, btn_y, btn_w, btn_h)),
            ("HARD", "POMDP", pygame.Rect(460, btn_y, btn_w, btn_h)),
            ("EXPERT", "MC+POMDP", pygame.Rect(640, btn_y, btn_w, btn_h)),
        ]
        self.selected_difficulty = None

        self.btn_label_font = pygame.font.Font(None, 26)
        self.btn_sub_font = pygame.font.Font(None, 20)

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
        highlight_bar = pygame.Surface((width, 22), pygame.SRCALPHA)
        pygame.draw.rect(highlight_bar, (245, 104, 90, 55), highlight_bar.get_rect(), border_radius=4)
        screen.blit(highlight_bar, (x, y))

        heading_text = self.section_font.render(heading, True, self.red_orange)
        screen.blit(heading_text, (x + 6, y + 2))
        y += 28

        for line in lines:
            line_text = self.rule_font.render(line, True, self.off_white)
            screen.blit(line_text, (x + 6, y))
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
        title_text = self.title_font.render("STOOL PIGEON", True, self.red_orange)
        screen.blit(title_text, title_text.get_rect(center=(self.screen_width // 2, 72)))

        # Rules panel
        panel = pygame.Rect(30, 150, self.screen_width - 60, 390)
        pygame.draw.rect(screen, (40, 38, 60), panel, border_radius=8)
        pygame.draw.rect(screen, (70, 65, 100), panel, 1, border_radius=8)

        col_w = (panel.width - 50) // 2
        left_x = panel.x + 16
        right_x = left_x + col_w + 18
        left_y = panel.y + 14
        right_y = panel.y + 14

        for heading, lines in self.left_sections:
            left_y = self._draw_section(screen, heading, lines, left_x, left_y, col_w)

        for heading, lines in self.right_sections:
            right_y = self._draw_section(screen, heading, lines, right_x, right_y, col_w)

        # Divider line between columns
        divider_x = left_x + col_w + 9
        pygame.draw.line(screen, (70, 65, 100),
                         (divider_x, panel.y + 10),
                         (divider_x, panel.bottom - 10), 1)

        # "Choose difficulty" label
        label_text = self.hint_font.render(
            "Choose your difficulty to start:",
            True, self.muted
        )
        screen.blit(label_text, label_text.get_rect(center=(self.screen_width // 2, 562)))

        # Difficulty buttons
        difficulty_colors = {
            "EASY": (60, 170, 90),
            "MEDIUM": (200, 160, 40),
            "HARD": (210, 90, 50),
            "EXPERT": (140, 50, 180),
        }
        for label, sublabel, rect in self.difficulty_buttons:
            is_selected = self.selected_difficulty == label
            base_color = difficulty_colors[label]

            if is_selected:
                bg_color = base_color
            elif active_mouse and rect.collidepoint(active_mouse):
                bg_color = (65, 63, 85)
            else:
                bg_color = (40, 38, 60)

            pygame.draw.rect(screen, bg_color, rect, border_radius=6)
            pygame.draw.rect(screen, base_color, rect, 2, border_radius=6)

            btn_label_text = self.btn_label_font.render(label, True, self.white)
            btn_sub_text = self.btn_sub_font.render(sublabel, True, self.off_white)
            screen.blit(btn_label_text, btn_label_text.get_rect(center=(rect.centerx, rect.centery - 8)))
            screen.blit(btn_sub_text, btn_sub_text.get_rect(center=(rect.centerx, rect.centery + 12)))

    def handle_click(self, pos):
        """Handles clicking a difficulty button. Returns difficulty label string or None."""
        for label, _sublabel, rect in self.difficulty_buttons:
            if rect.collidepoint(pos):
                self.selected_difficulty = label
                return label
        return None
