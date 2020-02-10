import sys

from game_files import Game

if __name__ == '__main__':
	from game_files.agents import RandomPlayer
	game = Game([RandomPlayer(),RandomPlayer()],external_log=sys.stdout)
	game.setup()
	print(game)
	game.game_loop()