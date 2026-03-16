import random
from actions import Action, ActionType
from agents.basic_pomdp_agent.belief_state import BeliefState
from cards import CardType

# Knock if expected hand value is below this threshold
KNOCK_THRESHOLD = 15

class BasicPOMDPAgent:
    """Basic Partially Observable Markov Decision Process."""
    def __init__(self, game, player_idx: int = 1):
        self.game = game
        self.player_idx = player_idx
        self.belief = BeliefState(game)
        self._observations = []
        self._peeked_this_turn = False

    def observe(self, obs):
        """Called by the game to deliver an observation to the agent."""
        self._observations.append(obs)

    def get_observations(self):
        """Return and clear pending observations."""
        obs = self._observations.copy()
        self._observations.clear()
        return obs

    def choose_action(self) -> Action:
        """Choose an action based on current beliefs."""

        for obs in self.get_observations():
            obs.update_belief(self.belief)

        actions = self.game.get_legal_actions()

        action_types = [a.action_type for a in actions]

        # Decide whether to knock
        if ActionType.KNOCK in action_types:
            if self._should_knock():
                return next(a for a in actions if a.action_type == ActionType.KNOCK)

        # Peek at the opponent's highest expected value slot
        if ActionType.PEEK in action_types and not self._peeked_this_turn:
            self._peeked_this_turn = True
            return self._best_peek_action(actions)

        # Finish peeking after one peek
        if ActionType.DONE_PEEKING in action_types:
            self._peeked_this_turn = False
            return next(a for a in actions if a.action_type == ActionType.DONE_PEEKING)
    
        # Keep drawn card if it improves hand, otherwise discard
        if ActionType.KEEP_CARD in action_types:
            keep = self._best_keep_action(actions)
            if keep:
                return keep
            if ActionType.DISCARD_DRAWN in action_types:
                return next(a for a in actions if a.action_type == ActionType.DISCARD_DRAWN)
            
        # Kingpin: eliminate own highest slot or add to opponent
        if ActionType.KINGPIN_ELIMINATE in action_types or ActionType.KINGPIN_ADD in action_types:
            return self._best_kingpin_action(actions)
        
        # Swap: move high own value to opponent, bring low opponent value to own hand
        if ActionType.SWAP in action_types:
            return self._best_swap_action(actions)

        print(f"Known: {[(k,v.value) for k,v in self.belief._known.items() if v is not None]}")

        return random.choice(actions)

    # Decision Helpers
    def _should_knock(self):
        ev = self.belief.expected_hand_value(self.player_idx)
        print(f"  _should_knock: player={self.player_idx} EV={ev:.1f} threshold={KNOCK_THRESHOLD}")
        return ev < KNOCK_THRESHOLD
    
    def _best_peek_action(self, actions) -> Action:
        """Peek at the opponent's unknown slot with the highest expected value.
        Falls back to any peek if no unknown opponent slots exist.
        """
        opponent_idx = 1 - self.player_idx

        # Find peek actions targeting unknown opponent slots, ranked by expected value
        best_action = None
        best_ev = -1

        for action in actions:
            if action.action_type != ActionType.PEEK:
                continue
            if action.target_player != opponent_idx:
                continue
            if self.belief.get_known(opponent_idx, action.target_idx) is not None:
                continue  # already known, no new info

            slot_ev = self.belief.slot_expected_value(opponent_idx, action.target_idx)
            if slot_ev > best_ev:
                best_ev = slot_ev
                best_action = action

        # Fallback: peek at anything if all opponent slots are known
        if best_action is None:
            best_action = next(a for a in actions if a.action_type == ActionType.PEEK)

        return best_action

    def _best_keep_action(self, actions) -> Action | None:
        """
        Return the keep action that most reduces expected hand value,
        or None if no keep improves the hand.
        Keeping drawn card is worth it if drawn_card.value < slot_expected_value.
        """
        drawn_card = self.game.state.drawn_card
        if drawn_card is None:
            return None

        current_ev = self.belief.expected_hand_value(self.player_idx)
        best_action = None
        best_ev = current_ev  # only keep if it strictly improves

        for action in actions:
            if action.action_type != ActionType.KEEP_CARD:
                continue

            slot_ev = self.belief.slot_expected_value(self.player_idx, action.target_idx)
            new_ev = current_ev - slot_ev + drawn_card.value
            if new_ev < best_ev:
                best_ev = new_ev
                best_action = action

        return best_action
    
    def _best_swap_action(self, actions) -> Action:
        """
        Pick the swap that maximises (own_slot_ev - opponent_slot_ev).
        Positive delta means we're moving high value out and bringing low value in.
        If no swap improves things, pick the least harmful one since swap is mandatory.
        """
        opponent_idx = 1 - self.player_idx
        best_action = None
        best_delta = float('-inf')

        for action in actions:
            if action.action_type != ActionType.SWAP:
                continue

            p1, s1 = action.target_player, action.target_idx
            p2, s2 = action.second_target

            # Determine which slot is ours and which is opponent's
            if p1 == self.player_idx and p2 == opponent_idx:
                own_ev = self.belief.slot_expected_value(p1, s1)
                opp_ev = self.belief.slot_expected_value(p2, s2)
            elif p2 == self.player_idx and p1 == opponent_idx:
                own_ev = self.belief.slot_expected_value(p2, s2)
                opp_ev = self.belief.slot_expected_value(p1, s1)
            else:
                # Both slots same player, skip
                continue

            delta = own_ev - opp_ev
            if delta > best_delta:
                best_delta = delta
                best_action = action

        # Fallback: any swap (e.g. both slots same player, mandatory swap)
        if best_action is None:
            best_action = next(a for a in actions if a.action_type == ActionType.SWAP)

        return best_action

    def _best_kingpin_action(self, actions) -> Action:
        """
        If opponent is winning (lower EV), add unknown card to burden them.
        Prioritize removing rat cards if the agent knows they have one. 
        Otherwise eliminate own highest expected value slot.
        """
        opponent_idx = 1 - self.player_idx
        own_ev = self.belief.expected_hand_value(self.player_idx)
        opp_ev = self.belief.expected_hand_value(opponent_idx)

        # Add to opponent if they're winning and add action is available
        if opp_ev < own_ev:
            add = next((a for a in actions if a.action_type == ActionType.KINGPIN_ADD), None)
            if add:
                return add

        # Eliminate own highest expected value slot
        # Priority: eliminate known RAT first (15 pts, can only be removed by Kingpin)
        for action in actions:
            if action.action_type != ActionType.KINGPIN_ELIMINATE:
                continue
            known = self.belief.get_known(self.player_idx, action.target_idx)
            if known and known.card_type == CardType.RAT:
                return action

        # Remove highest card from own
        best_action = None
        best_ev = -1
        for action in actions:
            if action.action_type != ActionType.KINGPIN_ELIMINATE:
                continue
            slot_ev = self.belief.slot_expected_value(self.player_idx, action.target_idx)
            if slot_ev > best_ev:
                best_ev = slot_ev
                best_action = action

        if best_action is None:
            return next(a for a in actions if a.action_type == ActionType.KINGPIN_ADD)
        return best_action