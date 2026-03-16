# evaluate.py
from StoolPigeonGame import StoolPigeonGame
from agents.basic_pomdp_agent.basic_pomdp_agent import BasicPOMDPAgent
from agents.random_agent import RandomAgent
from game_state import GamePhase
import os
import sys
import numpy as np

num_games = 20000
ev_errors = []

sys.stdout = open(os.devnull, 'w') 

def play_game():
    game = StoolPigeonGame(GUI=False, agent_class=BasicPOMDPAgent)
    game.state.set_phase(GamePhase.DRAW)

    random_agent = RandomAgent(game)

    while game.state.phase != GamePhase.GAME_OVER:
        if game.state.is_agent_turn():
            action = game.agent.choose_action()
            action.execute_action(game, GamePhase, agent=True)
        else:
            action = random_agent.choose_action()
            action.execute_action(game, GamePhase)
            if game.state.phase == GamePhase.GAME_OVER:
                break

    predicted_ev = game.agent.belief.expected_hand_value(1)
    actual_score = sum(c.value for c in game.agent_hands if c is not None)
    ev_errors.append(predicted_ev - actual_score)

    return game.get_scores()

wins = {"agent": 0, "user": 0, "tie": 0}
for i in range(num_games):
    result = play_game()
    wins[result["winner"]] += 1

sys.stdout = sys.__stdout__

print(f"POMDP wins: {wins['agent']}/{num_games}")
print(f"Random wins: {wins['user']}/{num_games}")
print(f"Ties: {wins['tie']}/{num_games}")

# avg signed error
# + = overestimate
# - = underestimate
# near 0 = unbiased
print(f"EV mean error: {np.mean(ev_errors):.2f}")
# spread of errors
# high = some games very accurate, others way off
print(f"EV std error:  {np.std(ev_errors):.2f}") 
# avg magnitude of error ignoring sign
# typical accuracy in points 
print(f"EV MAE:        {np.mean(np.abs(ev_errors)):.2f}") 