from agents.basic_pomdp_agent.basic_pomdp_agent import BasicPOMDPAgent
from agents.monte_carlo_agent.monte_carlo_agent import MonteCarloAgent
from actions import ActionType, Action

class MCPOMDPAgent(BasicPOMDPAgent):
    """Extends BasicPOMDPAgent with Monte Carlo action value estimation."""

    def __init__(self, game, player_idx: int = 1):
        super().__init__(game, player_idx)
        self.mc = MonteCarloAgent(game, self.belief, player_idx)

    def _should_knock(self):
        knock_action = Action.knock()
        knock_value = self.mc.estimate_action_values([knock_action])[knock_action]
        return knock_value > 0.0
    
    def _best_draw_action(self, actions):
        # replaces parent heuristic with MC estimate
        draw_actions = [a for a in actions if a.action_type in (ActionType.DRAW_FROM_PILE, ActionType.DRAW_FROM_DISCARD)]
        values = self.mc.estimate_action_values(draw_actions)
        return max(values, key=values.get)