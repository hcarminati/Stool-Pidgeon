from dataclasses import dataclass
from enum import Enum, auto

class ObsType(Enum):
    """Types of observations the agent can have."""
    AGENT_DRAW_PILE     = auto()  # agent drew from pile — card unknown
    PLAYER_DISCARD      = auto()  # player discarded a visible card
    AGENT_KEEP          = auto()  # agent kept drawn, discarded old card (visible)
    PLAYER_KEEP         = auto()  # player kept drawn, discarded old card (visible)
    PLAYER_DRAW_DISCARD = auto()  # player took from discard (visible), swapped one back (visible)
    AGENT_PEEK          = auto()  # agent peeked at (player, slot)
    AGENT_SWAP          = auto()  # agent swapped (p1,s1) ↔ (p2,s2)
    PLAYER_SWAP         = auto()  # player swapped (p1,s1) ↔ (p2,s2)
    KINGPIN_ELIMINATE   = auto()  # card eliminated from (player, slot)
    KINGPIN_ADD         = auto()  # unknown card added to opponent (player = recipient)
    KNOCK               = auto()  # player knocked

@dataclass
class Observation:
    """Observation attributes."""
    obs_type: ObsType
    card:   object = None  # visible card (discarded, peeked, eliminated, or taken from discard)
    card2:  object = None  # PLAYER_DRAW_DISCARD only: card put back into discard
    player: int    = None  # acting or target player index
    slot:   int    = None  # affected slot index
    p1:     int    = None  # swap: source player
    s1:     int    = None  # swap: source slot
    p2:     int    = None  # swap: dest player
    s2:     int    = None  # swap: dest slot
