import copy
import itertools
from enum import IntEnum, auto
import numpy as np

from .decks import CardType

class PlayerRole(IntEnum):
	NULL = auto()
	CONTINGENCY_PLANNER = auto()
	DISPATCHER = auto()
	MEDIC = auto()
	OPERATIONS_EXPERT = auto()
	QUARANTINE_SPECIALIST = auto()
	RESEARCHER = auto()
	SCIENTIST = auto()

class TurnPhase(IntEnum):
	INACTIVE = auto()
	NEW = auto()
	ACTIONS = auto()
	DRAW = auto()
	DISCARD = auto()
	INFECT = auto()

class Player():
	def __repr__(self):
		return self.playerrole.name+" Current location: "+str(self.position)+" - Cards: "+str(self.cards)
	
	def __call__(self):
		return {
			'location': self.position,
			'role': self.playerrole.name,
			'cards': [card.name for card in self.cards]
		}
	
	def __init__(self):
		self.pid = -1
		self.cards = []
		self.position = None
		self.playerrole = PlayerRole.NULL
		self.colors = {}
		
	def get_id(self):
		return (self.position,tuple(c.name for c in self.cards))
		
	def draw(self,game,amount):
		game.player_deck = copy.copy(game.player_deck)
		self.cards = copy.copy(self.cards)
		for c in range(amount):
			card = game.player_deck.draw()
			if card.cardtype == CardType.EPIDEMIC:
				# Increase infection counter
				game.infection_counter += 1
				if game.infection_counter == 3 or game.infection_counter == 5:
					game.infection_rate+=1
				# Infect x3 bottom card				
				game.infection_deck = copy.copy(game.infection_deck)
				city_name = game.infection_deck.draw_bottom().name
				game.log(self.playerrole.name+" drew: epidemic\nEpidemic at: "+city_name)
				game.cities = copy.copy(game.cities)
				game.cities[city_name] = copy.copy(game.cities[city_name])
				city = game.cities[city_name]
				city.infect(game,infection=3,color=city.color)
				# Shuffle infect discard pile
				game.infection_deck.intensify()
			elif card.cardtype != CardType.MISSING:
				game.log(self.playerrole.name+" drew: "+card.name)
				self.colors = copy.copy(self.colors)
				self.colors[card.color]+=1
				# Normal card
				self.cards.append(card)
		# Draws at end of turn, so resets Operations Expert special ability
		if self.playerrole==PlayerRole.OPERATIONS_EXPERT:
			self.special_move = True
		
	def move_triggers(self,game):
		if self.playerrole == PlayerRole.MEDIC:
			game.medic_position = self.position
			for color in game.cures:
				if game.cures[color] and game.cities[self.position].disease_cubes[color]>0:
					game.cities = copy.copy(game.cities)
					game.cities[self.position] = copy.copy(game.cities[self.position])
					game.cities[self.position].disinfect(game,game.cities[self.position].disease_cubes[color],color)
					game.log("MEDIC healed "+str(color)+" at "+str(self.position))
		elif self.playerrole == PlayerRole.QUARANTINE_SPECIALIST:
			game.protected_cities = [self.position]
			game.protected_cities.extend(game.cities[self.position].neighbors)
	
	def must_discard(self):
		if self.playerrole == PlayerRole.CONTINGENCY_PLANNER:
			# TODO: Check if contingency planner has kept additional card
			return len(self.cards)>7
		else:
			return len(self.cards)>7
		
	def no_action(self):
		return True
		
	# Stub function, must be implemented in child
	def request_action(self,game):
		return self.no_action.__name__,{}
		
	# Stub function, must be implemented in child
	def request_discard(self,game):
		return self.cards[0]
	
	def perform_action(self,game,action,kwargs):
		actions = {
			self.no_action.__name__: self.no_action,
			self.discard.__name__: self.discard,
			self.drive_ferry.__name__: self.drive_ferry,
			self.direct_flight.__name__: self.direct_flight,
			self.charter_flight.__name__: self.charter_flight,
			self.shuttle_flight.__name__: self.shuttle_flight,
			self.build_researchstation.__name__: self.build_researchstation ,
			self.treat_disease.__name__: self.treat_disease,
			self.give_knowledge.__name__: self.give_knowledge,
			self.receive_knowledge.__name__: self.receive_knowledge,
			self.discover_cure.__name__: self.discover_cure,
			self.rally_flight.__name__: self.rally_flight,
			self.special_charter_flight.__name__: self.special_charter_flight
		}
		return actions[action](game,**kwargs) if action in actions else False
	
	def available_actions(self,game):
		valid_cities = [city for city in game.cities if city!=self.position]
		actions = {}
		if game.turn_phase==TurnPhase.ACTIONS:
			actions[self.drive_ferry.__name__] = [ {'target':city} for city in game.cities[self.position].neighbors ]
			actions[self.direct_flight.__name__] = [ {'target':card.name} for card in self.cards if (card.cardtype==CardType.CITY and card.name!=self.position) ]
			actions[self.charter_flight.__name__] = [ {'target':city} for city in valid_cities] if self.position in self.cards else []
			actions[self.shuttle_flight.__name__] = [ {'target':city} for city in valid_cities if game.cities[city].research_station] if (game.cities[self.position].research_station and game.research_station_counter>1) else []
			actions[self.build_researchstation.__name__] = ([{'replace':"none"}] if game.research_station_counter < 6 else [{'replace':city} for city in game.cities if game.cities[city].research_station]) if ((self.position in self.cards or self.playerrole == PlayerRole.OPERATIONS_EXPERT) and not game.cities[self.position].research_station) else []
			actions[self.treat_disease.__name__] = [ {'color':color} for color in game.commons['colors'] if game.cities[self.position].disease_cubes[color]>0 ]
			actions[self.give_knowledge.__name__] = [{'receiver':player.pid, 'target':card.name} for player in game.players for card in self.cards  if (player!=self and self.position==player.position and card.cardtype==CardType.CITY and (self.position==card.name or self.playerrole==PlayerRole.RESEARCHER))]
			actions[self.receive_knowledge.__name__] = [{'giver':player.pid, 'target':card.name} for player in game.players for card in player.cards if (player!=self and self.position==player.position and card.cardtype==CardType.CITY and (self.position==card.name or player.playerrole==PlayerRole.RESEARCHER))]
			actions[self.discover_cure.__name__] = [{'color':color,'chosen_cards':[self.cards[i].name for i in chosen_cards]} for chosen_cards in list(itertools.combinations(np.arange(len(self.cards)),4 if self.playerrole==PlayerRole.SCIENTIST else 5)) for color in game.commons['colors'] if all([city in game.cities.keys() and game.cities[city].color==color for city in [self.cards[i].name for i in chosen_cards]])] if game.cities[self.position].research_station and len(self.cards)>=(4 if self.playerrole==PlayerRole.SCIENTIST else 5) else []
			actions[self.rally_flight.__name__] = [{'player':player.pid,'target_player':target.pid} for player in game.players for target in game.players if player.position!=target.position] if self.playerrole==PlayerRole.DISPATCHER else []
			actions[self.special_charter_flight.__name__] = [{'discard':card.name,'target':city} for card in self.cards for city in valid_cities if card.name in game.cities.keys()] if self.playerrole==PlayerRole.OPERATIONS_EXPERT and self.special_move and game.cities[self.position].research_station else []
		elif game.turn_phase==TurnPhase.DISCARD:
			actions[self.discard.__name__] = [{'discard':card.name} for card in self.cards]
		return actions
	
	# Card is a string with the card name
	def discard(self,game,card):
		valid = card in self.cards
		if valid:
			game.log(self.playerrole.name+" discarded: "+card)
			self.cards = copy.copy(self.cards)
			game.player_deck = copy.copy(game.player_deck)
			card = self.cards.pop(self.cards.index(card))
			self.colors = copy.copy(self.colors)
			self.colors[card.color]-=1
			game.player_deck.discard = copy.copy(game.player_deck.discard)
			game.player_deck.discard.append(card)
		return valid
	
	# Target is string object to new position
	def drive_ferry(self,game,target):
		valid = target in game.cities[self.position].neighbors
		if valid:
			game.log(self.playerrole.name+" drove to: "+target)
			self.position = target
			self.move_triggers(game)
		return valid
	
	# Target is string object to new position
	def direct_flight(self,game,target):
		valid = target in self.cards and self.position!=target and target in game.cities.keys()
		if valid:
			game.log(self.playerrole.name+" direct flew to: "+target)
			self.discard(game,target)
			self.position = target
			self.move_triggers(game)
		return valid
	
	# Target is string object to new position
	def charter_flight(self,game,target):
		valid = self.position in self.cards and self.position!=target and target in game.cities.keys()
		if valid:
			game.log(self.playerrole.name+" charter flew to: "+target)
			self.discard(game,self.position)
			self.position = target
			self.move_triggers(game)
		return valid
	
	# Target is string object to new position
	def shuttle_flight(self,game,target):
		valid = game.cities[self.position].research_station and self.position!=target and target in game.cities.keys() and game.cities[target].research_station
		if valid:
			game.log(self.playerrole.name+" shuttle flew to: "+target)
			self.position = target
			self.move_triggers(game)
		return valid
	
	# Replace is None or string of city name in which research_station will be removed
	def build_researchstation(self,game,replace=None):
		if replace=="none":
			replace=None
		valid = (self.position in self.cards or self.playerrole == PlayerRole.OPERATIONS_EXPERT) and not game.cities[self.position].research_station and (game.research_station_counter<6 or (replace in game.cities.keys() and game.cities[replace].research_station))
		if valid:
			game.log(self.playerrole.name+" built research station")
			game.cities = copy.copy(game.cities)
			if game.research_station_counter == 6:
				game.cities[replace] = copy.copy(game.cities[replace])
				game.cities[replace].research_station = False
				game.log(self.playerrole.name+" removed research station at: "+replace)
			else:
				game.research_station_counter += 1
			if self.playerrole != PlayerRole.OPERATIONS_EXPERT:
				self.discard(game,self.position)
			game.cities[self.position] = copy.copy(game.cities[self.position])
			game.cities[self.position].research_station = True
			game.calculate_distances()
		return valid
	
	# Color is string object of the color name
	def treat_disease(self,game,color):
		valid = game.cities[self.position].disease_cubes[color] > 0
		if valid:
			game.log(self.playerrole.name+" treated: "+color)
			game.cities = copy.copy(game.cities)
			game.cities[self.position] = copy.copy(game.cities[self.position])
			game.cities[self.position].disinfect(game,game.cities[self.position].disease_cubes[color] if (self.playerrole == PlayerRole.MEDIC or game.cures[color]) else 1 ,color)
		return valid
	
	# Receiver is pid number, target is string object
	def give_knowledge(self,game,receiver,target):
		game.players[receiver  % len(game.players)] = copy.copy(game.players[receiver  % len(game.players)])
		receiver_player = game.players[receiver  % len(game.players)]
		valid = receiver_player!=self and self.position==receiver_player.position and target in self.cards and (self.position==target or self.playerrole==PlayerRole.RESEARCHER)
		if valid:
			game.log(self.playerrole.name+" gave "+target+" to: "+receiver_player.playerrole.name)
			receiver_player.cards = copy.copy(receiver_player.cards)
			self.cards = copy.copy(self.cards)
			receiver_player.cards.append(self.cards.pop(self.cards.index(target)))
			if receiver_player.must_discard():
				game.log(receiver_player.playerrole.name + " must discard")
				game.real_current_player = game.current_player
				game.current_player = receiver
				game.turn_phase = TurnPhase.DISCARD
		return valid
	
	# Giver is pid number, target is string object
	def receive_knowledge(self,game,giver,target):
		game.players[giver % len(game.players)] = copy.copy(game.players[giver % len(game.players)])
		giver = game.players[giver % len(game.players)]
		valid = giver!=self and self.position==giver.position and target in giver.cards and (self.position==target or giver.playerrole==PlayerRole.RESEARCHER)
		if valid:
			game.log(self.playerrole.name+" received "+target+" from: "+giver.playerrole.name)
			giver.cards = copy.copy(giver.cards)
			self.cards = copy.copy(self.cards)
			self.cards.append(giver.cards.pop(giver.cards.index(target)))
			if self.must_discard():
				game.log(self.playerrole.name + " must discard")
				game.real_current_player = game.current_player
				game.turn_phase = TurnPhase.DISCARD
		return valid
	
	# Color is a string object, chosen_cards is an array containing string objects
	def discover_cure(self,game,color,chosen_cards):
		valid = game.cities[self.position].research_station and len(chosen_cards)==(4 if self.playerrole==PlayerRole.SCIENTIST else 5) and all([(card in self.cards and self.cards[self.cards.index(card)].cardtype==CardType.CITY and game.cities[card].color==color) for card in chosen_cards])
		if valid:
			game.log(self.playerrole.name+" found cure for: "+color)
			for card in chosen_cards:
				self.discard(game,card)
			game.cures = copy.copy(game.cures)
			game.cures[color] = True
			if game.remaining_disease_cubes[color]==game.commons['number_cubes']:
				game.eradicated = copy.copy(game.eradicated)
				game.eradicated[color] = True
				game.log("Eradicated "+color+" disease")
			for player in game.players:
				if player.playerrole == PlayerRole.MEDIC:
					player.move_triggers(game)
		return valid
	
	# Player is pid number, target_player is pid number
	def rally_flight(self,game,player,target_player):
		game.players[player % len(game.players)] = copy.copy(game.players[player % len(game.players)])
		player = game.players[player % len(game.players)]
		target_player = game.players[target_player % len(game.players)]
		valid = self.playerrole==PlayerRole.DISPATCHER and player.position!=target_player.position
		if valid:
			game.log("DISPATCHER rallied "+player.playerrole.name+" to: "+target_player.playerrole.name)
			player.position = target_player.position
			player.move_triggers(game)
		return valid
	
	# Discard is a string of card name, target is a string to new location
	def special_charter_flight(self,game,discard,target):
		valid = self.playerrole==PlayerRole.OPERATIONS_EXPERT and self.special_move and game.cities[self.position].research_station and discard in self.cards and discard in game.cities.keys() and target!=self.position
		if valid:
			game.log(self.playerrole.name+" special charter flew to: "+target+" discarding: "+discard)
			self.special_move = False
			self.discard(game,discard)
			self.position = target
		return valid
	
	# TODO: Implement different event actions
	def use_event(self,event):
		pass

