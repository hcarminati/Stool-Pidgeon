import random
from actions import Action
from agents.basic_pomdp_agent.belief_state import BeliefState

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
        # TODO: Change later.
        """Random action for now..."""
        actions = self.game.get_legal_actions()
        if actions:
            return random.choice(actions)
        return Action.discard_drawn()
