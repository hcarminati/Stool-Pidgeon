"""
Stool Pigeon - A text-based card game engine for AI research.
Supports one human player vs one AI agent with optional clickable Pygame GUI.
"""

import random
import copy
import time
from enum import Enum, auto
from dataclasses import dataclass, field
from typing import Optional

# =============================================================================
# CARD DEFINITIONS
# =============================================================================

class CardType(Enum):
    NUMBERED = auto()
    STOOL_PIGEON = auto()
    BAMBOOZLE = auto()
    VENDETTA = auto()
    KINGPIN = auto()
    RAT = auto()
    MEATBALL = auto()

@dataclass
class Card:
    card_type: CardType
    value: int = 0
    
    def __post_init__(self):
        if self.card_type == CardType.MEATBALL:
            self.value = 0
        elif self.card_type != CardType.NUMBERED:
            self.value = 0
    
    def get_score_value(self, rat_value: int = 0) -> int:
        if self.card_type == CardType.RAT:
            return rat_value
        elif self.card_type == CardType.MEATBALL:
            return 0
        elif self.card_type == CardType.NUMBERED:
            return self.value
        return 0
    
    def __repr__(self):
        if self.card_type == CardType.NUMBERED:
            return f"{self.value}"
        names = {
            CardType.STOOL_PIGEON: "PIGEON",
            CardType.BAMBOOZLE: "BAMBOOZLE", 
            CardType.VENDETTA: "VENDETTA",
            CardType.KINGPIN: "KINGPIN",
            CardType.RAT: "RAT",
            CardType.MEATBALL: "MEATBALL"
        }
        return names.get(self.card_type, self.card_type.name)

# =============================================================================
# ACTION DEFINITIONS
# =============================================================================

class ActionType(Enum):
    SWAP_BLIND = auto()
    DISCARD = auto()
    KNOCK = auto()
    PEEK_OWN = auto()
    PEEK_OPPONENT = auto()
    SWAP_ANY_TWO = auto()
    KINGPIN_ELIMINATE = auto()
    KINGPIN_ADD = auto()
    SKIP_EFFECT = auto()

@dataclass
class Action:
    action_type: ActionType
    target_idx: Optional[int] = None
    target_idx2: Optional[int] = None
    target_player: Optional[int] = None
    target_player2: Optional[int] = None

class GamePhase(Enum):
    SETUP = auto()
    DRAW = auto()
    DECIDE = auto()
    RESOLVE_EFFECT = auto()
    VENDETTA_PEEK = auto()
    VENDETTA_SWAP = auto()
    FINAL_TURN = auto()
    GAME_OVER = auto()

# =============================================================================
# CLICKABLE BUTTON CLASS
# =============================================================================

class Button:
    def __init__(self, x, y, width, height, text, color, hover_color, text_color=(0,0,0)):
        self.rect = (x, y, width, height)
        self.text = text
        self.color = color
        self.hover_color = hover_color
        self.text_color = text_color
        self.enabled = True
        self.visible = True
    
    def contains(self, pos):
        x, y, w, h = self.rect
        return self.enabled and self.visible and x <= pos[0] <= x+w and y <= pos[1] <= y+h
    
    def draw(self, screen, font, mouse_pos=None):
        if not self.visible:
            return
        import pygame
        x, y, w, h = self.rect
        color = self.hover_color if (mouse_pos and self.contains(mouse_pos) and self.enabled) else self.color
        if not self.enabled:
            color = (128, 128, 128)
        pygame.draw.rect(screen, color, self.rect, border_radius=5)
        pygame.draw.rect(screen, (0,0,0), self.rect, 2, border_radius=5)
        text_surf = font.render(self.text, True, self.text_color if self.enabled else (80,80,80))
        screen.blit(text_surf, (x + w//2 - text_surf.get_width()//2, y + h//2 - text_surf.get_height()//2))

# =============================================================================
# CLICKABLE CARD CLASS
# =============================================================================

class ClickableCard:
    def __init__(self, x, y, width, height, card=None, face_up=False, label="", player_idx=0, card_idx=0):
        self.rect = (x, y, width, height)
        self.card = card
        self.face_up = face_up
        self.label = label
        self.player_idx = player_idx
        self.card_idx = card_idx
        self.selected = False
        self.enabled = True
        self.visible = True
    
    def contains(self, pos):
        x, y, w, h = self.rect
        return self.enabled and self.visible and x <= pos[0] <= x+w and y <= pos[1] <= y+h
    
    def draw(self, screen, font, small_font, card_colors, mouse_pos=None, emoji_font=None, card_emojis=None, card_fallback=None):
        if not self.visible:
            return
        import pygame
        x, y, w, h = self.rect
        
        # Determine colors
        if self.face_up and self.card:
            bg_color = card_colors.get(self.card.card_type, (240, 240, 240))
        else:
            bg_color = (65, 105, 225)  # Blue for face-down
        
        # Hover/selection effect
        border_color = (0, 0, 0)
        border_width = 2
        if self.selected:
            border_color = (255, 215, 0)  # Gold
            border_width = 4
        elif mouse_pos and self.contains(mouse_pos) and self.enabled:
            border_color = (255, 255, 0)  # Yellow hover
            border_width = 3
        
        pygame.draw.rect(screen, bg_color, self.rect, border_radius=5)
        pygame.draw.rect(screen, border_color, self.rect, border_width, border_radius=5)
        
        # Draw card content
        if self.face_up and self.card:
            if self.card.card_type == CardType.NUMBERED:
                # Draw number
                text_surf = font.render(str(self.card.value), True, (0, 0, 0))
                screen.blit(text_surf, (x + w//2 - text_surf.get_width()//2, y + h//2 - text_surf.get_height()//2))
            else:
                # Draw emoji or fallback text for special cards
                emoji = card_emojis.get(self.card.card_type, "?") if card_emojis else "?"
                fallback = card_fallback.get(self.card.card_type, "?") if card_fallback else "?"
                
                if emoji_font:
                    try:
                        emoji_surf = emoji_font.render(emoji, True, (0, 0, 0))
                        screen.blit(emoji_surf, (x + w//2 - emoji_surf.get_width()//2, y + h//2 - emoji_surf.get_height()//2 - 5))
                    except:
                        text_surf = small_font.render(fallback, True, (0, 0, 0))
                        screen.blit(text_surf, (x + w//2 - text_surf.get_width()//2, y + h//2 - text_surf.get_height()//2))
                else:
                    text_surf = small_font.render(fallback, True, (0, 0, 0))
                    screen.blit(text_surf, (x + w//2 - text_surf.get_width()//2, y + h//2 - text_surf.get_height()//2))
        elif self.label:
            text_surf = small_font.render(self.label, True, (255, 255, 255))
            screen.blit(text_surf, (x + w//2 - text_surf.get_width()//2, y + h//2 - text_surf.get_height()//2))

# =============================================================================
# MAIN GAME CLASS
# =============================================================================

class StoolPigeonGame:
    def __init__(self, GUI=False, render_delay_sec=0.3, human_player_idx=0):
        self.GUI = GUI
        self.sleeptime = render_delay_sec
        self.cardWidth = 65
        self.cardHeight = 90
        self.fps = 60
        
        # Colors
        self.green = (34, 100, 34)
        self.white = (255, 255, 255)
        self.black = (0, 0, 0)
        self.gold = (255, 215, 0)
        self.red = (220, 20, 60)
        
        self.cardColors = {
            CardType.NUMBERED: (125, 124, 122), #
            CardType.STOOL_PIGEON: (18, 13, 49), #
            CardType.BAMBOOZLE: (108, 207, 246), #
            CardType.VENDETTA: (69, 74, 222), #
            CardType.KINGPIN: (216, 241, 160),
            CardType.RAT: (224, 153, 0), #
            CardType.MEATBALL: (49, 37, 9) #
        }
        
        # Emoji icons for special cards
        self.cardEmojis = {
            CardType.STOOL_PIGEON: "𓅪",
            CardType.BAMBOOZLE: "⇆",
            CardType.VENDETTA: "💀",
            CardType.KINGPIN: "👑",
            CardType.RAT: "🐀",
            CardType.MEATBALL: "🍖"
        }
        
        # Fallback text if emoji font unavailable
        self.cardFallback = {
            CardType.STOOL_PIGEON: "PGN",
            CardType.BAMBOOZLE: "BMB",
            CardType.VENDETTA: "VND",
            CardType.KINGPIN: "KNG",
            CardType.RAT: "RAT",
            CardType.MEATBALL: "MTB"
        }
        
        # Pygame objects
        self.screen = None
        self.clock = None
        self.font = None
        self.smallFont = None
        self.tinyFont = None
        
        # Game state
        self.human_player_idx = human_player_idx
        self.draw_pile = []
        self.discard_pile = []
        self.players = [
            {"name": "You" if human_player_idx == 0 else "AI", 
             "crime_scene": [], "memory": {}, "opp_memory": {}, "is_human": human_player_idx == 0},
            {"name": "AI" if human_player_idx == 0 else "You",
             "crime_scene": [], "memory": {}, "opp_memory": {}, "is_human": human_player_idx == 1}
        ]
        self.current_player_idx = 0
        self.phase = GamePhase.SETUP
        self.knocked_by = None
        self.drawn_card = None
        self.pending_effect = None
        self.turn_count = 0
        self.done = False
        self.winner = None
        self.scores = (0, 0)
        
        # GUI state
        self.buttons = []
        self.clickable_cards = []
        self.selected_card = None  # For two-card swaps
        self.message = ""
        self.message_timer = 0
        
        self._setup_game()
        
        if self.GUI:
            self._init_pygame()
    
    def _init_pygame(self):
        try:
            import pygame
            pygame.init()
            self.screenWidth = 900
            self.screenHeight = 700
            self.screen = pygame.display.set_mode((self.screenWidth, self.screenHeight))
            pygame.display.set_caption("Stool Pigeon")
            self.clock = pygame.time.Clock()
            self.font = pygame.font.Font(None, 32)
            self.smallFont = pygame.font.Font(None, 24)
            self.tinyFont = pygame.font.Font(None, 18)
            
            # Try to load emoji font for icons
            self.emojiFont = None
            self._load_emoji_font()
            
            self._refresh()
        except ImportError:
            print("Pygame not available.")
            self.GUI = False
    
    def _load_emoji_font(self):
        """Try to load a font that supports emoji."""
        import pygame
        import platform
        
        emoji_font_paths = []
        system = platform.system()
        
        if system == "Windows":
            emoji_font_paths = [
                "C:/Windows/Fonts/seguiemj.ttf",  # Segoe UI Emoji
                "C:/Windows/Fonts/segoe ui emoji.ttf",
            ]
        elif system == "Darwin":  # macOS
            emoji_font_paths = [
                "/System/Library/Fonts/Apple Color Emoji.ttc",
                "/Library/Fonts/Apple Color Emoji.ttc",
            ]
        else:  # Linux
            emoji_font_paths = [
                "/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf",
                "/usr/share/fonts/noto-emoji/NotoColorEmoji.ttf",
                "/usr/share/fonts/google-noto-emoji/NotoColorEmoji.ttf",
                "/usr/share/fonts/truetype/ancient-scripts/Symbola_hint.ttf",
            ]
        
        for path in emoji_font_paths:
            try:
                self.emojiFont = pygame.font.Font(path, 28)
                print(f"Loaded emoji font: {path}")
                return
            except (FileNotFoundError, OSError):
                continue
        
        print("No emoji font found, using text fallback for card icons.")
    
    def _create_deck(self) -> list:
        deck = []
        for val in range(1, 13):
            deck.append(Card(CardType.NUMBERED, val))
            deck.append(Card(CardType.NUMBERED, val))
        for _ in range(4):
            deck.append(Card(CardType.STOOL_PIGEON))
            deck.append(Card(CardType.BAMBOOZLE))
            deck.append(Card(CardType.VENDETTA))
        for _ in range(2):
            deck.append(Card(CardType.KINGPIN))
            deck.append(Card(CardType.RAT))
            deck.append(Card(CardType.MEATBALL))
        return deck
    
    def _setup_game(self):
        self.draw_pile = self._create_deck()
        random.shuffle(self.draw_pile)
        
        for player in self.players:
            player["crime_scene"] = []
            player["memory"] = {}
            player["opp_memory"] = {}
            for _ in range(4):
                player["crime_scene"].append(self.draw_pile.pop())
        
        for player in self.players:
            player["memory"][0] = player["crime_scene"][0]
            player["memory"][1] = player["crime_scene"][1]
        
        self.discard_pile = []
        self.current_player_idx = 0
        self.phase = GamePhase.DRAW
        self.knocked_by = None
        self.drawn_card = None
        self.pending_effect = None
        self.turn_count = 0
        self.done = False
        self.winner = None
        self.selected_card = None
        self.message = "Game started! Click DRAW to begin."
    
    # =========================================================================
    # CORE GAME LOGIC
    # =========================================================================
    
    def get_legal_actions(self) -> list:
        actions = []
        player = self.players[self.current_player_idx]
        opp = self.players[1 - self.current_player_idx]
        
        if self.phase == GamePhase.DRAW:
            return []
        
        elif self.phase in (GamePhase.DECIDE, GamePhase.FINAL_TURN):
            for i in range(len(player["crime_scene"])):
                actions.append(Action(ActionType.SWAP_BLIND, target_idx=i))
            actions.append(Action(ActionType.DISCARD))
            if self.phase == GamePhase.DECIDE and self.knocked_by is None:
                actions.append(Action(ActionType.KNOCK))
        
        elif self.phase == GamePhase.RESOLVE_EFFECT:
            if self.pending_effect == CardType.STOOL_PIGEON:
                for i in range(len(player["crime_scene"])):
                    actions.append(Action(ActionType.PEEK_OWN, target_idx=i))
                for i in range(len(opp["crime_scene"])):
                    actions.append(Action(ActionType.PEEK_OPPONENT, target_idx=i))
                actions.append(Action(ActionType.SKIP_EFFECT))
            
            elif self.pending_effect == CardType.BAMBOOZLE:
                actions.extend(self._get_swap_any_two_actions())
                actions.append(Action(ActionType.SKIP_EFFECT))
            
            elif self.pending_effect == CardType.KINGPIN:
                for i, card in enumerate(player["crime_scene"]):
                    if card.card_type != CardType.RAT:
                        actions.append(Action(ActionType.KINGPIN_ELIMINATE, target_idx=i))
                if len(self.draw_pile) > 0:
                    actions.append(Action(ActionType.KINGPIN_ADD))
                actions.append(Action(ActionType.SKIP_EFFECT))
        
        elif self.phase == GamePhase.VENDETTA_PEEK:
            for i in range(len(player["crime_scene"])):
                actions.append(Action(ActionType.PEEK_OWN, target_idx=i))
            for i in range(len(opp["crime_scene"])):
                actions.append(Action(ActionType.PEEK_OPPONENT, target_idx=i))
            actions.append(Action(ActionType.SKIP_EFFECT))
        
        elif self.phase == GamePhase.VENDETTA_SWAP:
            actions.extend(self._get_swap_any_two_actions())
            actions.append(Action(ActionType.SKIP_EFFECT))
        
        return actions
    
    def _get_swap_any_two_actions(self):
        actions = []
        player = self.players[self.current_player_idx]
        opp = self.players[1 - self.current_player_idx]
        all_cards = [(0, i) for i in range(len(player["crime_scene"]))]
        all_cards += [(1, i) for i in range(len(opp["crime_scene"]))]
        for idx1, (p1, c1) in enumerate(all_cards):
            for p2, c2 in all_cards[idx1+1:]:
                actions.append(Action(ActionType.SWAP_ANY_TWO,
                                     target_idx=c1, target_player=p1,
                                     target_idx2=c2, target_player2=p2))
        return actions
    
    def apply_action(self, action: Action):
        if self.phase == GamePhase.DRAW:
            self._do_draw()
        self._apply_action(action)
        if self.GUI:
            self._refresh()
    
    def _apply_action(self, action: Action):
        player = self.players[self.current_player_idx]
        opp = self.players[1 - self.current_player_idx]
        
        if action.action_type == ActionType.SWAP_BLIND:
            idx = action.target_idx
            old_card = player["crime_scene"][idx]
            player["crime_scene"][idx] = self.drawn_card
            self.discard_pile.append(old_card)
            player["memory"][idx] = self.drawn_card
            if idx in opp["opp_memory"]:
                del opp["opp_memory"][idx]
            self.message = f"Swapped with position {idx}, discarded {old_card}"
            self.drawn_card = None
            self._end_turn()
        
        elif action.action_type == ActionType.DISCARD:
            card = self.drawn_card
            self.discard_pile.append(card)
            self.drawn_card = None
            if card.card_type == CardType.STOOL_PIGEON:
                self.pending_effect = CardType.STOOL_PIGEON
                self.phase = GamePhase.RESOLVE_EFFECT
                self.message = "STOOL PIGEON! Click any card to peek."
            elif card.card_type == CardType.BAMBOOZLE:
                self.pending_effect = CardType.BAMBOOZLE
                self.phase = GamePhase.RESOLVE_EFFECT
                self.message = "BAMBOOZLE! Click two cards to swap them."
            elif card.card_type == CardType.VENDETTA:
                self.pending_effect = CardType.VENDETTA
                self.phase = GamePhase.VENDETTA_PEEK
                self.message = "VENDETTA! First, click a card to peek."
            elif card.card_type == CardType.KINGPIN:
                self.pending_effect = CardType.KINGPIN
                self.phase = GamePhase.RESOLVE_EFFECT
                self.message = "KINGPIN! Eliminate your card or add to opponent."
            else:
                self.message = f"Discarded {card}"
                self._end_turn()
        
        elif action.action_type == ActionType.KNOCK:
            self.knocked_by = self.current_player_idx
            self.message = f"{player['name']} KNOCKED! Final turn for opponent."
            self.phase = GamePhase.FINAL_TURN
            self.current_player_idx = 1 - self.current_player_idx
            self.turn_count += 1
            self._do_draw()
        
        elif action.action_type == ActionType.PEEK_OWN:
            idx = action.target_idx
            player["memory"][idx] = player["crime_scene"][idx]
            self.message = f"Peeked: position {idx} is {player['crime_scene'][idx]}"
            self._resolve_effect_done()
        
        elif action.action_type == ActionType.PEEK_OPPONENT:
            idx = action.target_idx
            player["opp_memory"][idx] = opp["crime_scene"][idx]
            self.message = f"Peeked: opponent's {idx} is {opp['crime_scene'][idx]}"
            self._resolve_effect_done()
        
        elif action.action_type == ActionType.SWAP_ANY_TWO:
            p1_idx, c1_idx = action.target_player, action.target_idx
            p2_idx, c2_idx = action.target_player2, action.target_idx2
            players_map = {0: player, 1: opp}
            p1, p2 = players_map[p1_idx], players_map[p2_idx]
            p1["crime_scene"][c1_idx], p2["crime_scene"][c2_idx] = \
                p2["crime_scene"][c2_idx], p1["crime_scene"][c1_idx]
            # Clear memories
            if c1_idx in player["memory"] and p1_idx == 0:
                del player["memory"][c1_idx]
            if c2_idx in player["memory"] and p2_idx == 0:
                del player["memory"][c2_idx]
            if c1_idx in player["opp_memory"] and p1_idx == 1:
                del player["opp_memory"][c1_idx]
            if c2_idx in player["opp_memory"] and p2_idx == 1:
                del player["opp_memory"][c2_idx]
            self.message = "Cards swapped!"
            self.selected_card = None
            self._resolve_effect_done()
        
        elif action.action_type == ActionType.KINGPIN_ELIMINATE:
            idx = action.target_idx
            removed = player["crime_scene"].pop(idx)
            self.discard_pile.append(removed)
            new_mem = {}
            for k, v in player["memory"].items():
                if k < idx:
                    new_mem[k] = v
                elif k > idx:
                    new_mem[k-1] = v
            player["memory"] = new_mem
            self.message = f"Eliminated {removed} from position {idx}"
            self._resolve_effect_done()
        
        elif action.action_type == ActionType.KINGPIN_ADD:
            if self.draw_pile:
                new_card = self.draw_pile.pop()
                opp["crime_scene"].append(new_card)
                self.message = "Added a card to opponent's crime scene!"
            self._resolve_effect_done()
        
        elif action.action_type == ActionType.SKIP_EFFECT:
            self.message = "Skipped effect."
            self.selected_card = None
            self._resolve_effect_done()
    
    def _resolve_effect_done(self):
        if self.phase == GamePhase.VENDETTA_PEEK:
            self.phase = GamePhase.VENDETTA_SWAP
            self.message = "Now click two cards to swap."
        else:
            self.pending_effect = None
            self._end_turn()
    
    def _end_turn(self):
        self.selected_card = None
        if self.phase == GamePhase.FINAL_TURN:
            self.phase = GamePhase.GAME_OVER
            self._calculate_scores()
            self.done = True
        elif self.knocked_by is not None:
            self.phase = GamePhase.FINAL_TURN
            self.current_player_idx = 1 - self.knocked_by
            self.turn_count += 1
            self._do_draw()
        else:
            self.current_player_idx = 1 - self.current_player_idx
            self.turn_count += 1
            self.phase = GamePhase.DRAW
            self.message = f"{self.players[self.current_player_idx]['name']}'s turn. Click DRAW."
    
    def _do_draw(self):
        if not self.draw_pile:
            if len(self.discard_pile) > 1:
                top = self.discard_pile.pop()
                self.draw_pile = self.discard_pile
                self.discard_pile = [top]
                random.shuffle(self.draw_pile)
            else:
                self.phase = GamePhase.GAME_OVER
                self._calculate_scores()
                self.done = True
                return
        
        self.drawn_card = self.draw_pile.pop()
        if self.phase != GamePhase.FINAL_TURN:
            self.phase = GamePhase.DECIDE
        self.message = f"Drew {self.drawn_card}. Choose: swap with a card, discard, or knock."
    
    def _calculate_scores(self):
        rat_value = 0
        if self.draw_pile:
            top = self.draw_pile[-1]
            if top.card_type == CardType.NUMBERED:
                rat_value = top.value
        
        s0 = sum(c.get_score_value(rat_value) for c in self.players[0]["crime_scene"])
        s1 = sum(c.get_score_value(rat_value) for c in self.players[1]["crime_scene"])
        self.scores = (s0, s1)
        
        if s0 < s1:
            self.winner = 0
        elif s1 < s0:
            self.winner = 1
        else:
            self.winner = None
        
        self.message = f"Game Over! {self.players[0]['name']}: {s0}, {self.players[1]['name']}: {s1}"
    
    def is_terminal(self) -> bool:
        return self.done
    
    def get_scores(self) -> tuple:
        return self.scores
    
    def get_winner(self) -> Optional[int]:
        return self.winner
    
    # =========================================================================
    # PYGAME GUI WITH CLICK HANDLING
    # =========================================================================
    
    def _build_ui(self):
        """Build clickable buttons and cards based on current state."""
        self.buttons = []
        self.clickable_cards = []
        
        player = self.players[self.current_player_idx]
        opp = self.players[1 - self.current_player_idx]
        human = self.players[self.human_player_idx]
        is_human_turn = self.current_player_idx == self.human_player_idx
        
        # Draw pile (clickable to draw)
        draw_btn = Button(50, 280, self.cardWidth, self.cardHeight, 
                         f"DRAW\n({len(self.draw_pile)})", (65, 105, 225), (100, 140, 255), (255,255,255))
        draw_btn.enabled = is_human_turn and self.phase == GamePhase.DRAW
        self.buttons.append(("draw", draw_btn))
        
        # Discard pile (not clickable, just display)
        
        # Drawn card (clickable to discard in DECIDE phase)
        if self.drawn_card and is_human_turn:
            drawn_card = ClickableCard(350, 280, self.cardWidth, self.cardHeight,
                                       self.drawn_card, True, "", -1, -1)
            drawn_card.enabled = self.phase in (GamePhase.DECIDE, GamePhase.FINAL_TURN)
            self.clickable_cards.append(("discard", drawn_card))
        
        # Action buttons
        btn_y = 400
        btn_w, btn_h = 100, 40
        
        # Knock button
        knock_btn = Button(50, btn_y, btn_w, btn_h, "KNOCK", (255, 200, 100), (255, 220, 150))
        knock_btn.enabled = is_human_turn and self.phase == GamePhase.DECIDE and self.knocked_by is None
        knock_btn.visible = self.phase in (GamePhase.DECIDE, GamePhase.FINAL_TURN)
        self.buttons.append(("knock", knock_btn))
        
        # Skip button
        skip_btn = Button(160, btn_y, btn_w, btn_h, "SKIP", (200, 200, 200), (230, 230, 230))
        skip_btn.enabled = is_human_turn and self.phase in (GamePhase.RESOLVE_EFFECT, GamePhase.VENDETTA_PEEK, GamePhase.VENDETTA_SWAP)
        skip_btn.visible = skip_btn.enabled
        self.buttons.append(("skip", skip_btn))
        
        # Kingpin buttons
        if self.pending_effect == CardType.KINGPIN and is_human_turn:
            add_btn = Button(270, btn_y, 120, btn_h, "ADD TO OPP", (255, 150, 150), (255, 180, 180))
            add_btn.enabled = len(self.draw_pile) > 0
            self.buttons.append(("kingpin_add", add_btn))
        
        # New Game button (when game over)
        if self.done:
            new_btn = Button(self.screenWidth//2 - 60, 500, 120, 50, "NEW GAME", (100, 200, 100), (130, 230, 130))
            self.buttons.append(("new_game", new_btn))
        
        # Player's crime scene cards (bottom)
        human_idx = self.human_player_idx
        opp_idx = 1 - human_idx
        
        # Your cards (bottom)
        y_yours = 550
        x_start = 250
        for i, card in enumerate(self.players[human_idx]["crime_scene"]):
            known = self.players[human_idx]["memory"].get(i)
            face_up = known is not None or self.done
            display_card = known if known else card
            cc = ClickableCard(x_start + i * 80, y_yours, self.cardWidth, self.cardHeight,
                              display_card if face_up else None, face_up, str(i), human_idx, i)
            # Enable based on phase
            if is_human_turn:
                if self.phase in (GamePhase.DECIDE, GamePhase.FINAL_TURN):
                    cc.enabled = True  # For swap
                elif self.phase == GamePhase.RESOLVE_EFFECT:
                    if self.pending_effect in (CardType.STOOL_PIGEON, CardType.BAMBOOZLE):
                        cc.enabled = True
                    elif self.pending_effect == CardType.KINGPIN:
                        cc.enabled = card.card_type != CardType.RAT  # Can eliminate non-RAT
                elif self.phase in (GamePhase.VENDETTA_PEEK, GamePhase.VENDETTA_SWAP):
                    cc.enabled = True
                else:
                    cc.enabled = False
            else:
                cc.enabled = False
            
            if self.selected_card and self.selected_card == (human_idx, i):
                cc.selected = True
            self.clickable_cards.append(("player_card", cc))
        
        # Opponent's cards (top)
        y_opp = 120
        for i, card in enumerate(self.players[opp_idx]["crime_scene"]):
            known = self.players[human_idx]["opp_memory"].get(i)
            face_up = known is not None or self.done
            display_card = known if known else card
            cc = ClickableCard(x_start + i * 80, y_opp, self.cardWidth, self.cardHeight,
                              display_card if face_up else None, face_up, str(i), opp_idx, i)
            # Enable for peek/swap actions
            if is_human_turn:
                if self.phase == GamePhase.RESOLVE_EFFECT:
                    if self.pending_effect in (CardType.STOOL_PIGEON, CardType.BAMBOOZLE):
                        cc.enabled = True
                elif self.phase in (GamePhase.VENDETTA_PEEK, GamePhase.VENDETTA_SWAP):
                    cc.enabled = True
                else:
                    cc.enabled = False
            else:
                cc.enabled = False
            
            if self.selected_card and self.selected_card == (opp_idx, i):
                cc.selected = True
            self.clickable_cards.append(("opp_card", cc))
    
    def _handle_click(self, pos):
        """Handle mouse click at position."""
        if self.done:
            # Check new game button
            for name, btn in self.buttons:
                if name == "new_game" and btn.contains(pos):
                    self._setup_game()
                    self._refresh()
                    return
            return
        
        is_human_turn = self.current_player_idx == self.human_player_idx
        if not is_human_turn:
            return
        
        # Check buttons
        for name, btn in self.buttons:
            if btn.contains(pos):
                if name == "draw" and self.phase == GamePhase.DRAW:
                    self._do_draw()
                    self._refresh()
                    return
                elif name == "knock":
                    self.apply_action(Action(ActionType.KNOCK))
                    return
                elif name == "skip":
                    self.apply_action(Action(ActionType.SKIP_EFFECT))
                    return
                elif name == "kingpin_add":
                    self.apply_action(Action(ActionType.KINGPIN_ADD))
                    return
        
        # Check clickable cards
        for name, cc in self.clickable_cards:
            if cc.contains(pos) and cc.enabled:
                if name == "discard":
                    # Click on drawn card = discard it
                    self.apply_action(Action(ActionType.DISCARD))
                    return
                
                elif name in ("player_card", "opp_card"):
                    p_idx = cc.player_idx
                    c_idx = cc.card_idx
                    
                    # Handle based on phase
                    if self.phase in (GamePhase.DECIDE, GamePhase.FINAL_TURN):
                        # Swap drawn card with this card
                        if p_idx == self.human_player_idx:
                            self.apply_action(Action(ActionType.SWAP_BLIND, target_idx=c_idx))
                        return
                    
                    elif self.phase == GamePhase.RESOLVE_EFFECT:
                        if self.pending_effect == CardType.STOOL_PIGEON:
                            # Peek
                            if p_idx == self.current_player_idx:
                                self.apply_action(Action(ActionType.PEEK_OWN, target_idx=c_idx))
                            else:
                                self.apply_action(Action(ActionType.PEEK_OPPONENT, target_idx=c_idx))
                            return
                        
                        elif self.pending_effect == CardType.BAMBOOZLE:
                            # Two-card swap
                            self._handle_two_card_selection(p_idx, c_idx)
                            return
                        
                        elif self.pending_effect == CardType.KINGPIN:
                            # Eliminate own card
                            if p_idx == self.current_player_idx:
                                self.apply_action(Action(ActionType.KINGPIN_ELIMINATE, target_idx=c_idx))
                            return
                    
                    elif self.phase == GamePhase.VENDETTA_PEEK:
                        if p_idx == self.current_player_idx:
                            self.apply_action(Action(ActionType.PEEK_OWN, target_idx=c_idx))
                        else:
                            self.apply_action(Action(ActionType.PEEK_OPPONENT, target_idx=c_idx))
                        return
                    
                    elif self.phase == GamePhase.VENDETTA_SWAP:
                        self._handle_two_card_selection(p_idx, c_idx)
                        return
    
    def _handle_two_card_selection(self, p_idx, c_idx):
        """Handle selection for two-card swaps (Bamboozle/Vendetta)."""
        cur_p = self.current_player_idx
        # Map to 0=current player, 1=opponent for action
        if p_idx == cur_p:
            action_p = 0
        else:
            action_p = 1
        
        if self.selected_card is None:
            self.selected_card = (p_idx, c_idx)
            self.message = f"Selected card {c_idx}. Click another to swap."
            self._refresh()
        else:
            # Second selection - perform swap
            p1_idx, c1_idx = self.selected_card
            if p1_idx == cur_p:
                action_p1 = 0
            else:
                action_p1 = 1
            
            if (p1_idx, c1_idx) == (p_idx, c_idx):
                # Clicked same card - deselect
                self.selected_card = None
                self.message = "Deselected. Click a card to select."
                self._refresh()
            else:
                # Perform swap
                self.apply_action(Action(ActionType.SWAP_ANY_TWO,
                                        target_idx=c1_idx, target_player=action_p1,
                                        target_idx2=c_idx, target_player2=action_p))
    
    def _refresh(self):
        if not self.GUI or self.screen is None:
            return
        
        import pygame
        mouse_pos = pygame.mouse.get_pos()
        
        self.screen.fill(self.green)
        
        # Build UI elements
        self._build_ui()
        
        # Title with pigeon emoji
        title_text = "STOOL PIGEON"
        if self.emojiFont:
            try:
                pigeon = self.emojiFont.render("🐦", True, self.white)
                title = self.font.render(title_text, True, self.gold)
                total_w = pigeon.get_width() + 10 + title.get_width() + 10 + pigeon.get_width()
                start_x = self.screenWidth//2 - total_w//2
                self.screen.blit(pigeon, (start_x, 8))
                self.screen.blit(title, (start_x + pigeon.get_width() + 10, 10))
                self.screen.blit(pigeon, (start_x + pigeon.get_width() + 10 + title.get_width() + 10, 8))
            except:
                title = self.font.render(title_text, True, self.gold)
                self.screen.blit(title, (self.screenWidth//2 - title.get_width()//2, 10))
        else:
            title = self.font.render(title_text, True, self.gold)
            self.screen.blit(title, (self.screenWidth//2 - title.get_width()//2, 10))
        
        # Status
        phase_name = self.phase.name.replace("_", " ")
        current = self.players[self.current_player_idx]["name"]
        status = f"Turn {self.turn_count} | {phase_name} | {current}'s turn"
        status_surf = self.smallFont.render(status, True, self.white)
        self.screen.blit(status_surf, (20, 50))
        
        # Knock indicator
        if self.knocked_by is not None:
            knock_text = self.font.render(f"{self.players[self.knocked_by]['name']} KNOCKED!", True, self.red)
            self.screen.blit(knock_text, (self.screenWidth//2 - knock_text.get_width()//2, 75))
        
        # Draw legend for card types (right side)
        self._draw_legend()
        
        # Labels
        opp_label = self.smallFont.render(f"Opponent ({self.players[1-self.human_player_idx]['name']})", True, self.white)
        self.screen.blit(opp_label, (250, 95))
        
        your_label = self.smallFont.render(f"Your Crime Scene ({self.players[self.human_player_idx]['name']})", True, self.white)
        self.screen.blit(your_label, (250, 525))
        
        # Draw pile info
        pile_label = self.tinyFont.render(f"Draw: {len(self.draw_pile)}", True, self.white)
        self.screen.blit(pile_label, (50, 260))
        
        # Discard pile
        discard_label = self.tinyFont.render("Discard", True, self.white)
        self.screen.blit(discard_label, (150, 260))
        if self.discard_pile:
            top_discard = self.discard_pile[-1]
            self._draw_card_at(150, 280, top_discard, True, mouse_pos)
        else:
            pygame.draw.rect(self.screen, (80, 80, 80), (150, 280, self.cardWidth, self.cardHeight), 2, border_radius=5)
        
        # Drawn card label
        if self.drawn_card:
            drawn_label = self.tinyFont.render("Drawn (click to discard)", True, self.white)
            self.screen.blit(drawn_label, (300, 260))
        
        # Draw buttons
        for name, btn in self.buttons:
            btn.draw(self.screen, self.smallFont, mouse_pos)
        
        # Draw clickable cards
        for name, cc in self.clickable_cards:
            cc.draw(self.screen, self.font, self.smallFont, self.cardColors, mouse_pos,
                   self.emojiFont, self.cardEmojis, self.cardFallback)
        
        # Message
        if self.message:
            msg_surf = self.smallFont.render(self.message, True, self.gold)
            pygame.draw.rect(self.screen, (0, 0, 0), (10, self.screenHeight - 40, self.screenWidth - 20, 35))
            self.screen.blit(msg_surf, (20, self.screenHeight - 32))
        
        # Game over overlay
        if self.done:
            overlay = pygame.Surface((self.screenWidth, self.screenHeight))
            overlay.fill((0, 0, 0))
            overlay.set_alpha(200)
            self.screen.blit(overlay, (0, 0))
            
            go_text = self.font.render("GAME OVER", True, self.gold)
            self.screen.blit(go_text, (self.screenWidth//2 - go_text.get_width()//2, 300))
            
            p0, p1 = self.players[0]["name"], self.players[1]["name"]
            score_text = self.font.render(f"{p0}: {self.scores[0]}  |  {p1}: {self.scores[1]}", True, self.white)
            self.screen.blit(score_text, (self.screenWidth//2 - score_text.get_width()//2, 350))
            
            if self.winner is not None:
                winner_text = self.font.render(f"{self.players[self.winner]['name']} WINS!", True, self.gold)
            else:
                winner_text = self.font.render("TIE!", True, self.gold)
            self.screen.blit(winner_text, (self.screenWidth//2 - winner_text.get_width()//2, 400))
            
            # Redraw new game button on top
            for name, btn in self.buttons:
                if name == "new_game":
                    btn.draw(self.screen, self.smallFont, mouse_pos)
        
        pygame.display.flip()
        self.clock.tick(self.fps)
    
    def _draw_legend(self):
        """Draw a legend showing card types and their effects."""
        import pygame
        
        legend_x = 700
        legend_y = 120
        line_height = 28
        
        # Background
        pygame.draw.rect(self.screen, (20, 60, 20), (legend_x - 10, legend_y - 10, 195, 220), border_radius=8)
        pygame.draw.rect(self.screen, self.gold, (legend_x - 10, legend_y - 10, 195, 220), 2, border_radius=8)
        
        # Title
        legend_title = self.smallFont.render("CARD LEGEND", True, self.gold)
        self.screen.blit(legend_title, (legend_x + 40, legend_y))
        
        # Card types with emojis and descriptions
        legend_items = [
            (CardType.STOOL_PIGEON, "Peek any card"),
            (CardType.BAMBOOZLE, "Swap any 2"),
            (CardType.VENDETTA, "Peek + Swap 2"),
            (CardType.KINGPIN, "Elim/Add card"),
            (CardType.RAT, "=Draw pile top"),
            (CardType.MEATBALL, "Value = 0"),
        ]
        
        y = legend_y + 30
        for card_type, desc in legend_items:
            emoji = self.cardEmojis.get(card_type, "?")
            fallback = self.cardFallback.get(card_type, "?")
            color = self.cardColors.get(card_type, self.white)
            
            # Draw small color swatch
            pygame.draw.rect(self.screen, color, (legend_x, y, 20, 20), border_radius=3)
            pygame.draw.rect(self.screen, self.black, (legend_x, y, 20, 20), 1, border_radius=3)
            
            # Draw emoji or fallback
            if self.emojiFont:
                try:
                    emoji_surf = self.emojiFont.render(emoji, True, self.white)
                    self.screen.blit(emoji_surf, (legend_x + 25, y - 3))
                    desc_surf = self.tinyFont.render(desc, True, self.white)
                    self.screen.blit(desc_surf, (legend_x + 55, y + 3))
                except:
                    text_surf = self.tinyFont.render(f"{fallback}: {desc}", True, self.white)
                    self.screen.blit(text_surf, (legend_x + 25, y + 3))
            else:
                text_surf = self.tinyFont.render(f"{fallback}: {desc}", True, self.white)
                self.screen.blit(text_surf, (legend_x + 25, y + 3))
            
            y += line_height
    
    def _draw_card_at(self, x, y, card, face_up, mouse_pos):
        """Simple card drawing helper with emoji support."""
        import pygame
        if face_up and card:
            bg = self.cardColors.get(card.card_type, (240, 240, 240))
        else:
            bg = (65, 105, 225)
        pygame.draw.rect(self.screen, bg, (x, y, self.cardWidth, self.cardHeight), border_radius=5)
        pygame.draw.rect(self.screen, self.black, (x, y, self.cardWidth, self.cardHeight), 2, border_radius=5)
        
        if face_up and card:
            if card.card_type == CardType.NUMBERED:
                text = self.font.render(str(card.value), True, self.black)
                self.screen.blit(text, (x + self.cardWidth//2 - text.get_width()//2, 
                                        y + self.cardHeight//2 - text.get_height()//2))
            else:
                # Draw emoji or fallback
                emoji = self.cardEmojis.get(card.card_type, "?")
                fallback = self.cardFallback.get(card.card_type, "?")
                
                if self.emojiFont:
                    try:
                        emoji_surf = self.emojiFont.render(emoji, True, self.black)
                        self.screen.blit(emoji_surf, (x + self.cardWidth//2 - emoji_surf.get_width()//2,
                                                      y + self.cardHeight//2 - emoji_surf.get_height()//2 - 5))
                    except:
                        text = self.smallFont.render(fallback, True, self.black)
                        self.screen.blit(text, (x + self.cardWidth//2 - text.get_width()//2,
                                                y + self.cardHeight//2 - text.get_height()//2))
                else:
                    text = self.smallFont.render(fallback, True, self.black)
                    self.screen.blit(text, (x + self.cardWidth//2 - text.get_width()//2,
                                            y + self.cardHeight//2 - text.get_height()//2))
    
    # =========================================================================
    # MAIN GAME LOOP
    # =========================================================================
    
    def run_gui(self):
        """Main loop for GUI mode with click handling."""
        if not self.GUI:
            print("GUI not enabled. Use play_text() for text mode.")
            return
        
        import pygame
        ai = RandomAgent(self, 1 - self.human_player_idx)
        
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:  # Left click
                        self._handle_click(event.pos)
            
            # AI turn
            if not self.done and self.current_player_idx != self.human_player_idx:
                time.sleep(0.5)
                if self.phase == GamePhase.DRAW:
                    self._do_draw()
                    self._refresh()
                    time.sleep(0.3)
                
                if not self.done:
                    action = ai.choose_action()
                    if action:
                        self.apply_action(action)
            
            self._refresh()
        
        pygame.quit()
    
    # =========================================================================
    # TEXT MODE
    # =========================================================================
    
    def display_state(self, for_player_idx=None):
        if for_player_idx is None:
            for_player_idx = self.human_player_idx
        player = self.players[for_player_idx]
        opp = self.players[1 - for_player_idx]
        
        print("\n" + "="*50)
        print(f"Turn {self.turn_count} | Phase: {self.phase.name}")
        print(f"Draw: {len(self.draw_pile)} | Discard: {len(self.discard_pile)}", end="")
        if self.discard_pile:
            print(f" (top: {self.discard_pile[-1]})")
        else:
            print()
        
        if self.knocked_by is not None:
            print(f"*** {self.players[self.knocked_by]['name']} KNOCKED! ***")
        
        print(f"\nYour crime scene:")
        for i, card in enumerate(player["crime_scene"]):
            known = player["memory"].get(i)
            print(f"  [{i}] {known if known else '???'}")
        
        print(f"\nOpponent's crime scene:")
        for i in range(len(opp["crime_scene"])):
            known = player["opp_memory"].get(i)
            print(f"  [{i}] {known if known else '???'}")
        
        if self.drawn_card:
            print(f"\nDrawn: {self.drawn_card}")
        print("="*50)
    
    def print_legal_actions(self):
        actions = self.get_legal_actions()
        print("\nActions:")
        for i, a in enumerate(actions):
            print(f"  {i}: {a.action_type.name} {a.target_idx if a.target_idx is not None else ''}")
        return actions

# =============================================================================
# RANDOM AI
# =============================================================================

class RandomAgent:
    def __init__(self, game: StoolPigeonGame, player_idx: int):
        self.game = game
        self.player_idx = player_idx
    
    def choose_action(self) -> Optional[Action]:
        actions = self.game.get_legal_actions()
        return random.choice(actions) if actions else None

# =============================================================================
# TEXT MODE PLAY
# =============================================================================

def play_text():
    game = StoolPigeonGame(GUI=False, human_player_idx=0)
    ai = RandomAgent(game, 1)
    
    print("\nSTOOL PIGEON - Text Mode")
    print("Goal: Lowest crime scene total wins!")
    
    while not game.is_terminal():
        if game.phase == GamePhase.DRAW:
            game._do_draw()
        
        game.display_state()
        
        if game.players[game.current_player_idx]["is_human"]:
            actions = game.print_legal_actions()
            try:
                idx = int(input("Choose action #: "))
                if 0 <= idx < len(actions):
                    game.apply_action(actions[idx])
            except (ValueError, IndexError):
                print("Invalid input.")
        else:
            action = ai.choose_action()
            if action:
                print(f"AI: {action.action_type.name}")
                game.apply_action(action)
    
    print(f"\nGAME OVER! Scores: {game.scores}")
    if game.winner is not None:
        print(f"{game.players[game.winner]['name']} wins!")

# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "--text":
        play_text()
    else:
        game = StoolPigeonGame(GUI=True, render_delay_sec=0.1, human_player_idx=0)
        game.run_gui()