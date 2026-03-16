# evaluate.py
from StoolPigeonGame import StoolPigeonGame
from agents.basic_pomdp_agent.basic_pomdp_agent import BasicPOMDPAgent
from agents.random_agent import RandomAgent
from game_state import GamePhase
import os
import sys

num_games = 10500
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

    return game.get_scores()

wins = {"agent": 0, "user": 0, "tie": 0}
for i in range(num_games):
    result = play_game()
    wins[result["winner"]] += 1

sys.stdout = sys.__stdout__

print(f"POMDP wins: {wins['agent']}/{num_games}")
print(f"Random wins: {wins['user']}/{num_games}")
print(f"Ties: {wins['tie']}/{num_games}")