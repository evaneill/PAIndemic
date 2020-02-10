import random

from .players import Player

# Agents have to return (tuple action to use, arg to use w action)
class RandomPlayer(Player):
	def request_action(self,game):
		options = self.available_actions(game)
		all_options = []
		for action in options:
			possible_kwargs = options[action]
			for kwargs in possible_kwargs:
				all_options.append([action, kwargs])
		selection = random.choice(all_options)
		return selection[0],selection[1]
	
	def request_discard(self,game):
		return random.choice(self.cards).name

