from enum import Enum, auto

class ActionType(Enum):
    SWAP_BLIND = auto()
    DISCARD = auto()
    KNOCK = auto()
    PEEK_OWN = auto()
    PEEK_OPPONENT = auto()
    SWAP_ANY_TWO = auto()
    KINGPIN_ELIMINATE = auto()
    KINGPIN_ADD = auto()

class Action: 
    def __init__(self, action_type, target_player, target_idx=0):
        self.action_type = action_type
        self.target_player = target_player
        self.target_idx = target_idx