from agents.basic_pomdp_agent.basic_pomdp_agent import BasicPOMDPAgent
from agents.monte_carlo_agent.monte_carlo_agent import MonteCarloAgent
from actions import ActionType, Action

class MCPOMDPAgent(BasicPOMDPAgent):
    """Extends BasicPOMDPAgent with Monte Carlo action value estimation."""

    def __init__(self, game, player_idx: int = 1):
        super().__init__(game, player_idx)
        self.mc = MonteCarloAgent(game, self.belief, player_idx)
        
    def _should_knock(self):
        """Decides whether to knock based on Monte Carlo estimates,"""
        
        # replaces parent threshold with MC estimate
        actions = self.game.get_legal_actions()
        knock_action = next((a for a in actions if a.action_type == ActionType.KNOCK), None)

        if knock_action is None:
            return False

        non_knock = [a for a in actions if a.action_type != ActionType.KNOCK]

        if not non_knock:
            return True

        values = self.mc.estimate_action_values([knock_action] + non_knock)
        best = max(values, key=values.get)

        return best.action_type == ActionType.KNOCK

    def _best_draw_action(self, actions):
        """Decides whether to draw from pile or discard based on Monte Carlo estimates."""
        
        # replaces parent heuristic with MC estimate
        draw_actions = [a for a in actions if a.action_type in (ActionType.DRAW_FROM_PILE, ActionType.DRAW_FROM_DISCARD)]
        values = self.mc.estimate_action_values(draw_actions)

        return max(values, key=values.get)