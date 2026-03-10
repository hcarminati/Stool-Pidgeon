import random
from actions import Action, ActionType
from agents.basic_pomdp_agent.belief_state import BeliefState
from agents.basic_pomdp_agent.observation import Observation

# Knock if expected hand value is below this threshold
KNOCK_THRESHOLD = 15

class BasicPOMDPAgent:
    """Basic Partially Observable Markov Decision Process."""
    def __init__(self, game, player_idx: int = 1):
        self.game = game
        self.player_idx = player_idx
        self.belief = BeliefState(game)
        self._observations = []

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

        return random.choice(actions)

    # Decision Helpers
    def _should_knock(self) -> bool:
        """Knock if our expected hand value is below the threshold."""
        return self.belief.expected_hand_value(self.player_idx) < KNOCK_THRESHOLD


