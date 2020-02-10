import copy
import random
import traceback
from enum import IntEnum, auto

from .cities import CITY_CARDS, City
from .decks import Card, InfectionDeck, PlayerDeck, CardType
from .players import PlayerRole, TurnPhase

class GameState(IntEnum):
	NOT_PLAYING = auto()
	PLAYING = auto()
	LOST = auto()
	WON = auto()

class Game():
	
	def __repr__(self):
		s = "Turn: "+str(self.current_turn)+", Current player: "+str(self.players[self.current_player].playerrole.name)+", Out.Counter: "+str(self.outbreak_counter)+", Inf.Counter: "+str(self.infection_counter)+", Inf.Rate: "+str(self.infection_rate)+"\n"
		s+= "Cures found: "+str([color+"="+str((2 if self.eradicated[color] else 1) if self.cures[color] else 0) for color in self.commons['colors']])+"\n"
		for p,player in enumerate(self.players):
			s += "Player "+str(p)+": "+str(player)+"\n"
		s+="Cities:\n"
		for city in self.cities:
			if self.cities[city].research_station or any([self.cities[city].disease_cubes[color]>0 for color in self.commons['colors']]):
				s += str(self.cities[city])+"\n"
		s+="Player deck: "+str(self.player_deck)+"\n"
		s+="Infection deck: "+str(self.infection_deck)
		return s
	
	def __call__(self):
		game = {
			'game_state': self.game_state.name,
			'game_turn': self.current_turn,
			'turn_phase': self.turn_phase.name,
			'current_player': self.current_player,
			'infections': self.infection_counter,
			'infection_rate': self.infection_rate,
			'outbreaks': self.outbreak_counter,
			'cures': self.cures,
			'eradicated': self.eradicated,
			'disease_cubes': self.remaining_disease_cubes,
			'players': {"p"+str(p): self.players[p]() for p in range(len(self.players))},
			'cities': {city: self.cities[city]() for city in self.cities},
			'quarantine_cities': self.protected_cities,
			'infection_deck': self.infection_deck(),
			'player_deck': self.player_deck(),
			'actions': self.players[self.current_player].available_actions(self),
			'remaining_actions': self.actions,
			'game_log': self.commons['game_log']
		}
		self.commons['game_log'] = ""
		return game
	
	def __init__(self,players,epidemic_cards=4,cities=CITY_CARDS,starting_city="atlanta",number_cubes=24,log_game=True,external_log=None):
		assert(starting_city in cities)
		# Save game parameters
		self.commons = {}
		self.commons['epidemic_cards'] = epidemic_cards
		self.commons['starting_city'] = starting_city
		self.commons['number_cubes'] = number_cubes
		self.commons['colors'] = []
		self.commons['logger'] = external_log
		self.commons['log_game'] = log_game
		self.commons['game_log'] = ""
		# Gather city colors and disease cubes
		for city in CITY_CARDS:
			if CITY_CARDS[city]['color'] not in self.commons['colors']:
				self.commons['colors'].append(CITY_CARDS[city]['color'])
		# Save players
		self.players = players
		# Create cities
		self.cities = {city: City(name=city,color=CITY_CARDS[city]['color'],neighbors=CITY_CARDS[city]['connects'],colors=self.commons['colors']) for city in CITY_CARDS}
		# Create decks
		# TODO: Include events?
		cities_deck = [Card(name=city,cardtype=CardType.CITY,color=self.cities[city].color) for city in self.cities]
		event_deck = []
		self.infection_deck = InfectionDeck(cities_deck)
		cities_deck.extend(event_deck)
		self.player_deck = PlayerDeck(cities_deck)
		self.actions = 0
		# Turn controls
		self.current_player = -1
		self.current_turn = -1
		self.turn_phase = TurnPhase.INACTIVE
		self.game_state = GameState.NOT_PLAYING
	
	def get_id(self):
		# Everything not included can be derived from other data
		return (
				self.game_state, 
				self.current_turn, 
				self.turn_phase,
				self.infection_counter,
				self.outbreak_counter,
				tuple(self.cures.values()),
				tuple(self.eradicated.values()),
				tuple(self.remaining_disease_cubes.values()),
				tuple(p.get_id() for p in self.players),
				tuple(c.get_id() for c in self.cities.values()),
				self.actions
		  )
	
	def log(self,new_log):
		if self.commons['log_game']:
			self.commons['game_log'] += new_log+"\n"
		if self.commons['logger'] is not None:
			self.commons['logger'].write(new_log+"\n")
	
	def setup(self,players_roles=None):
		self.log("Setting game up")
		if players_roles is None or len(players_roles)!=len(self.players):
			roles = list(PlayerRole)
			roles.remove(PlayerRole.NULL)
			# TODO: DISPATCHER and CONTINGENCY_PLANNER NOT FULLY IMPLEMENTED
			roles.remove(PlayerRole.CONTINGENCY_PLANNER)
			roles.remove(PlayerRole.DISPATCHER)
			# REMOVED OPERATIONS_EXPERT BECAUSE OF SEARCH SPACE EXPLOSION
			roles.remove(PlayerRole.OPERATIONS_EXPERT)
			players_roles = random.sample(roles,len(self.players))
		# Player setup
		for p,player in enumerate(self.players):
			player.pid = p
			player.position = self.commons['starting_city']
			player.playerrole = players_roles[p]
			if player.playerrole == PlayerRole.OPERATIONS_EXPERT:
				player.special_move = False
			self.player_deck.discard.extend(player.cards)
			player.cards = []
			player.colors = {color:0 for color in self.commons['colors']}
			player.colors[None] = 0
		# City setup
		for c in self.cities:
			city = self.cities[c]
			# Restarts disease cubes and research station flag
			for color in city.disease_cubes:
				city.disease_cubes[color] = 0
			city.research_station = False
		self.cities[self.commons['starting_city']].research_station = True
		self.calculate_distances()
		# Set counters
		self.remaining_disease_cubes = {color: self.commons['number_cubes'] for color in self.commons['colors']}
		self.cures = {color: False for color in self.commons['colors']}
		self.eradicated = {color: False for color in self.commons['colors']}
		self.outbreak_counter = 0
		self.infection_counter = 0
		self.infection_rate = 2
		self.research_station_counter = 1
		self.protected_cities = []
		self.medic_position = None
		# Prepare player deck
		# Removes epidemic cards
		self.player_deck.deck = [card for pile in self.player_deck.deck for card in pile if card.cardtype != CardType.EPIDEMIC]
		self.player_deck.deck.extend(self.player_deck.discard)
		self.player_deck.discard = []
		random.shuffle(self.player_deck.deck)
		# Deal players' hands
		for player in self.players:
			for c in range(6-len(self.players)):
				card = self.player_deck.deck.pop()
				self.log(player.playerrole.name+" drew: "+card.name)
				player.cards.append(card)
				player.colors[card.color]+=1
		self.player_deck.missing = False
		# Define starting player
		maximum_population = 0
		starting_player = 0
		for p, player in enumerate(self.players):
			current_population = max([CITY_CARDS[card.name]['pop'] if card.cardtype==CardType.CITY else 0 for card in player.cards])
			if current_population >= maximum_population:
				starting_player = p
				maximum_population = current_population
		# Setup player deck
		subpiles = [[Card(name="Epidemic",cardtype=CardType.EPIDEMIC,color="epidemic")] for i in range(self.commons['epidemic_cards'])]
		for index,card in enumerate(self.player_deck.deck):
			subpiles[index%self.commons['epidemic_cards']].append(card)
		self.player_deck.deck = []
		for pile in subpiles:
			random.shuffle(pile)
			self.player_deck.deck.append(pile)
		self.player_deck.remaining = sum(len(p) for p in self.player_deck.deck)
		self.player_deck.expecting_epidemic = True
		self.player_deck.epidemic_countdown = len(self.player_deck.deck[-1])
		self.player_deck.colors = {}
		for pile in self.player_deck.deck:
			for card in pile:
				if card.color not in self.player_deck.colors.keys():
					self.player_deck.colors[card.color] = 0
				self.player_deck.colors[card.color] += 1
		# Prepare infection deck
		single_pile = [card for pile in self.infection_deck.deck for card in pile]
		single_pile.extend(self.infection_deck.discard)
		random.shuffle(single_pile)
		self.infection_deck.deck = [single_pile]
		self.infection_deck.discard = []
		# Set initial infections
		for i in range(9):
			city = self.cities[self.infection_deck.draw().name]
			city.infect(self,infection=(i//3)+1,color=city.color)
		# Post setup players
		for player in self.players:
			player.move_triggers(self)
		# Start game
		self.commons['error_flag'] = False
		self.commons['game_log'] = ""
		self.current_player = starting_player
		self.real_current_player = None
		self.current_turn = 1
		self.turn_phase = TurnPhase.NEW
		self.game_state = GameState.PLAYING
		
	def calculate_distances(self):
		city_distances = {
				key: {target: (0 if target==key else (1 if target in self.cities[key].neighbors else len(self.cities))) for target in self.cities} for key in self.cities		
		}
		research_cities = [city for city in self.cities if self.cities[city].research_station]
		for rs in research_cities:
			for target in research_cities:
				if rs!=target:
					city_distances[rs][target] = 1
		for key in city_distances:
			unvisited = list(self.cities.keys())
			while unvisited:
				current_node = unvisited[0]
				current_distance = city_distances[key][current_node]
				for node in unvisited:
					if city_distances[key][node] < current_distance:
						current_node = node
						current_distance = city_distances[key][node]
				for neighbor in self.cities[current_node].neighbors:
					new_distance = current_distance + 1
					if new_distance < city_distances[key][neighbor]:
						city_distances[key][neighbor] = new_distance
				unvisited.remove(current_node)
		self.distances = city_distances
	
	def lost(self):
		return self.player_deck.remaining<0 or min(self.remaining_disease_cubes.values())<0 or self.outbreak_counter>=8
	
	def won(self):
		return all(self.cures.values())
		
	def start_turn(self):
		valid = self.turn_phase == TurnPhase.NEW
		if valid:
			self.log("Turn begin: "+self.players[self.current_player].playerrole.name)
			self.actions = 4
			self.turn_phase = TurnPhase.ACTIONS
		else:
			print("Invalid turn start, current turn phase: "+self.turn_phase.name)
		return valid
		
	def do_action(self,action,kwargs):
		valid = self.turn_phase == TurnPhase.ACTIONS and action!=self.players[self.current_player].discard.__name__
		if valid:
			try:
				self.players = copy.copy(self.players)
				self.players[self.current_player] = copy.copy(self.players[self.current_player])
				if self.players[self.current_player].perform_action(self,action,kwargs):
					self.actions -= 1
					# Check if still in ACTIONS to see if DISCARD interruption occured
					if self.actions == 0 and self.turn_phase == TurnPhase.ACTIONS:
						self.turn_phase = TurnPhase.DRAW
				else:
					valid = False
					print("Invalid move or something")
					print(self.players[self.current_player])
					print("Tried to do:",action,kwargs)
					print("In game state:",self)
					input("CONTINUE")
			except:
				print("Error, wrong function or something.")
				print(action)
				print(kwargs)
				traceback.print_exc()
				self.turn_phase = TurnPhase.INACTIVE
				self.commons['error_flag'] = True
			if self.won():
				self.turn_phase = TurnPhase.INACTIVE
				self.game_state = GameState.WON
		else:
			print("Invalid do action, current turn phase: "+self.turn_phase.name)
			input("CONTINUE")
		return valid
	
	def draw_phase(self):
		valid = self.turn_phase == TurnPhase.DRAW
		if valid:
			self.players = copy.copy(self.players)
			self.players[self.current_player] = copy.copy(self.players[self.current_player])
			self.players[self.current_player].draw(self,2)
			if self.lost():
				self.turn_phase = TurnPhase.INACTIVE
				self.game_state = GameState.LOST
			elif self.players[self.current_player].must_discard():
				self.turn_phase = TurnPhase.DISCARD
			else:
				self.turn_phase = TurnPhase.INFECT
		return valid
	
	def do_discard(self,discard):
		valid = self.turn_phase == TurnPhase.DISCARD
		if valid:
			self.players = copy.copy(self.players)
			self.players[self.current_player] = copy.copy(self.players[self.current_player])
			if self.players[self.current_player].discard(self,discard):
				if not self.players[self.current_player].must_discard():
					if self.real_current_player == None:
						self.turn_phase = TurnPhase.INFECT
					else:
						self.current_player = self.real_current_player
						self.real_current_player = None
						self.turn_phase = TurnPhase.ACTIONS if self.actions > 0 else TurnPhase.DRAW
			else:
				print("Invalid card discard")
		else:
			print("Invalid do discard, current turn phase: "+self.turn_phase.name)
		return valid
	
	def end_turn(self):
		valid = self.turn_phase == TurnPhase.INFECT
		if valid:
			self.cities = copy.copy(self.cities)
			for i in range(self.infection_rate):
				self.infection_deck = copy.copy(self.infection_deck)
				city_name = self.infection_deck.draw().name
				self.cities[city_name] = copy.copy(self.cities[city_name])
				city = self.cities[city_name]
				city.infect(self,infection=1,color=city.color)
			self.current_player = (self.current_player+1)%len(self.players)
			if self.lost():
				self.turn_phase = TurnPhase.INACTIVE
				self.game_state = GameState.LOST
			else:
				self.current_turn += 1
				self.turn_phase = TurnPhase.NEW
		else:
			print("Invalid end turn, current turn phase: "+self.turn_phase.name)
		return valid
	
	def game_turn(self):
		if self.turn_phase == TurnPhase.NEW:
			self.start_turn()
		while self.turn_phase == TurnPhase.ACTIONS or self.turn_phase == TurnPhase.DISCARD:
			if self.turn_phase == TurnPhase.ACTIONS:
				action, kwargs = self.players[self.current_player].request_action(self)
				self.do_action(action,kwargs)
			else:
				discard = self.players[self.current_player].request_discard(self)
				self.do_discard(discard)
		if self.turn_phase==TurnPhase.DRAW:
			self.draw_phase()
		while self.turn_phase == TurnPhase.DISCARD:
			discard = self.players[self.current_player].request_discard(self)
			self.do_discard(discard)
		if self.turn_phase == TurnPhase.INFECT:
			self.end_turn()

	def game_loop(self):
		self.log("Starting game")
		while self.game_state == GameState.PLAYING and self.turn_phase!= TurnPhase.INACTIVE:
			self.game_turn()
		if self.game_state == GameState.WON:
			self.log("Players won the game")
		elif self.game_state == GameState.LOST:
			self.log("Players lost the game")
		else:
			self.log("This should not happen")
	