import copy
from actions import ActionType
from end_screen import calculate_score
from game_state import GamePhase

class MonteCarloAgent:
    """
    Estimates the value of actions by simulating many games from a sampled state.
    
    For each candidate action:
      1. Sample N concrete game states from the belief distribution
      2. Simulate each to game over using a simple rollout policy 
      3. Return average outcome (1=win, 0=tie, -1=loss)
    """

    NUM_SIMULATIONS = 100
    MAX_TURNS = 50  # safety cap to prevent infinite loops in simulation
    KEEP_THRESHOLD = 6  # heuristic threshold for deciding whether to keep a drawn card during rollout
    KNOCK_THRESHOLD = 15 # heuristic threshold for deciding whether to knock during rollout
    
    def __init__(self, game, belief, player_idx):
        self.game = game
        self.belief = belief
        self.player_idx = player_idx

    def estimate_action_values(self, actions):
        """Returns a dict mapping each action to its estimated value based on Monte Carlo simulations."""
        action_values = {}

        for action in actions:
            total_reward = 0
            for _ in range(self.NUM_SIMULATIONS):
                # Sample a concrete game state consistent with our belief
                sampled_game_state = self.belief.sample_game_state()
                # Simulate the game to the end after taking the action
                reward = self.simulate_from_state(action, sampled_game_state)
                total_reward += reward

            action_values[action] = total_reward / self.NUM_SIMULATIONS

        return action_values
    
    def simulate_from_state(self, action, sampled_state):
        """Simulates a game to the end starting from the given sampled state after taking the specified action. 
        Returns 1 for agent win, 0 for tie, -1 for loss."""

        # Create a copy of the game state to simulate on
        # deepcopy is over written in the StoolPigeonGame class to be efficient and only copy what is needed for simulation
        sim_game = copy.deepcopy(self.game)

        # Inject sampled state, replace hand cards with sampled cards
        for (player, slot), card in sampled_state.items():
            hand = sim_game.agent_hands if player == 1 else sim_game.user_hand
            if slot < len(hand):
                hand[slot] = card

        # Take the action
        action.execute_action(sim_game, GamePhase, agent=True)

        turn_count = 0

        # Simulate the rest of the game using a simple rollout policy
        while sim_game.state.phase != GamePhase.GAME_OVER and turn_count < self.MAX_TURNS:
            # Get legal actions for the current player
            legal_actions = sim_game.get_legal_actions()

            if not legal_actions:
                break
            
            sim_action = self._rollout_policy(sim_game, legal_actions)
            sim_action.execute_action(sim_game, GamePhase, agent=True)

            turn_count += 1

        agent_score = calculate_score(sim_game.agent_hands)
        user_score  = calculate_score(sim_game.user_hand)
        
        if agent_score < user_score:
            return 1 # agent wins
        elif agent_score > user_score:
            return -1 # agent loses
        else:
            return 0 # tie
        
    def _rollout_policy(self, sim, actions):
        """
        Simple policy used during rollout — not the full POMDP logic.
        Covers every possible action type so the simulation never gets stuck.
        Fast and good enough for rollout estimation.
        """
        action_types = [a.action_type for a in actions]

        # DRAW: prefer discard if top card is less than KEEP_THRESHOLD, else draw from pile
        if ActionType.DRAW_FROM_DISCARD in action_types or ActionType.DRAW_FROM_PILE in action_types:
            top = sim.discard_pile[-1] if sim.discard_pile else None

            if top and top.value is not None and top.value < self.KEEP_THRESHOLD:
                return next(a for a in actions if a.action_type == ActionType.DRAW_FROM_DISCARD)
            
            return next(a for a in actions if a.action_type == ActionType.DRAW_FROM_PILE)

        # KNOCK: knock if current hand score is less than or equal to KNOCK_THRESHOLD, else draw
        if ActionType.KNOCK in action_types:
            hand = sim.agent_hands if sim.state.is_agent_turn() else sim.user_hand

            if calculate_score(hand) < self.KNOCK_THRESHOLD:
                return next(a for a in actions if a.action_type == ActionType.KNOCK)

        # DECIDE: keep drawn card only if it improves the hand (lower than worst slot)
        if ActionType.KEEP_CARD in action_types:
            drawn = sim.state.drawn_card
            hand = sim.agent_hands if sim.state.is_agent_turn() else sim.user_hand

            if drawn and drawn.value is not None:
                worst_slot_val = max(c.value for c in hand if c is not None)

                # If the drawn card is better than the worst card in hand, keep it by replacing the worst card
                if drawn.value < worst_slot_val:
                    # Find the index of the worst card in hand to replace
                    worst_idx = max(
                        (i for i, c in enumerate(hand) if c is not None),
                        key=lambda i: hand[i].value
                    )

                    keep_actions = [a for a in actions if a.action_type == ActionType.KEEP_CARD]
                    match = next((a for a in keep_actions if a.target_idx == worst_idx), None)

                    if match:
                        return match

            if ActionType.DISCARD_DRAWN in action_types:
                return next(a for a in actions if a.action_type == ActionType.DISCARD_DRAWN)

        # PEEK: peek at first available target
        if ActionType.PEEK in action_types:
            return next(a for a in actions if a.action_type == ActionType.PEEK)

        # DONE PEEKING: always finish immediately
        if ActionType.DONE_PEEKING in action_types:
            return next(a for a in actions if a.action_type == ActionType.DONE_PEEKING)

        # SWAP (Bamboozle/Vendetta): pick first available swap
        if ActionType.SWAP in action_types:
            return next(a for a in actions if a.action_type == ActionType.SWAP)

        # KINGPIN: eliminate own highest value card, or add to opponent if they're winning
        if ActionType.KINGPIN_ELIMINATE in action_types or ActionType.KINGPIN_ADD in action_types:
            hand = sim.agent_hands if sim.state.is_agent_turn() else sim.user_hand
            opp  = sim.user_hand  if sim.state.is_agent_turn() else sim.agent_hands

            if calculate_score(opp) < calculate_score(hand):
                add = next((a for a in actions if a.action_type == ActionType.KINGPIN_ADD), None)
                if add:
                    return add
                
            elim = [a for a in actions if a.action_type == ActionType.KINGPIN_ELIMINATE]

            if elim:
                return max(elim, key=lambda a: hand[a.target_idx].value if hand[a.target_idx] else 0)
            
            return next(a for a in actions if a.action_type == ActionType.KINGPIN_ADD)

        return actions[0]