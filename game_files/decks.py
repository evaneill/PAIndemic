from enum import IntEnum, auto
import random
import copy

class CardType(IntEnum):
	MISSING = auto()
	CITY = auto()
	EVENT = auto()
	EPIDEMIC = auto()

class Card(object):
	def __repr__(self):
		return self.name
	
	def __init__(self,name,cardtype,color=None):
		self.name = name
		self.cardtype = cardtype
		self.color = color
	
	def __eq__(self,other):
		return self.name == other

class PlayerDeck():
	def __repr__(self):
		return "Expecting epidemic: "+str(1 if self.expecting_epidemic else 0)+", Next epidemic in: "+str(self.epidemic_countdown)+", Remaining cards: "+str(self.remaining)
	
	def __call__(self):
		remaining_cards = [card.name for pile in self.deck for card in pile]
		remaining_cards.sort()
		return {
			'cards_left': self.remaining,
			'deck': remaining_cards,
			'discard': [card.name for card in self.discard],
			'epidemic_countdown': self.epidemic_countdown,
			'epidemic_expectation': self.expecting_epidemic
		}
	
	def __init__(self,cards):
		self.deck = [cards.copy()]
		self.discard = []
		self.remaining = 0
		self.expecting_epidemic = False
		self.epidemic_countdown = 0
		self.colors = {}
		
	def draw(self):
		if len(self.deck)>0:
			self.deck = copy.copy(self.deck)
			self.deck[-1] = copy.copy(self.deck[-1])
			self.colors = copy.copy(self.colors)
			card = self.deck[-1].pop()
			self.colors[card.color] -= 1
			self.remaining -= 1
			self.epidemic_countdown -= 1
			self.expecting_epidemic = self.expecting_epidemic and card.cardtype!=CardType.EPIDEMIC
			if len(self.deck[-1])==0:
				self.deck.pop()
				self.expecting_epidemic = True
				self.epidemic_countdown = len(self.deck[-1]) if len(self.deck)>0 else 0
		else:
			self.remaining -= 1
			card = Card(name="",cardtype=CardType.MISSING)
		return card
	
	@property
	def possible_deck(self):
		pile_info = [[len(pile),any([card.cardtype==CardType.EPIDEMIC for card in pile])] for pile in self.deck]		
		cards = [card for pile in self.deck for card in pile if card.cardtype != CardType.EPIDEMIC]
		deck = []
		random.shuffle(cards)
		for p in pile_info:
			pile = [Card(name="Epidemic",cardtype=CardType.EPIDEMIC,color="epidemic")] if p[1] else []
			for c in range(len(pile),p[0]):
				pile.append(cards.pop())
			random.shuffle(pile)
			deck.append(pile)
		return deck

class InfectionDeck():
	def __repr__(self):
		return "Possible next cards: "+str(self.known_cards)
	
	def __call__(self):
		return {
			'known_piles': self.known_cards,
			'discard': [card.name for card in self.discard]
		}
	
	def __init__(self,cities):
		self.deck = [cities.copy()]
		self.discard = []
		
	def draw(self):
		self.deck = copy.copy(self.deck)
		self.deck[-1] = copy.copy(self.deck[-1])
		card = self.deck[-1].pop()
		if len(self.deck[-1])==0:
			self.deck.pop()
		self.discard = copy.copy(self.discard)
		self.discard.append(card)
		return card
		
	def draw_bottom(self):
		self.deck = copy.copy(self.deck)
		self.deck[0] = copy.copy(self.deck[0])
		city = self.deck[0].pop(0)
		if len(self.deck[0])==0:
			self.deck.pop(0)
		self.discard = copy.copy(self.discard)
		self.discard.append(city)
		return city
	
	def intensify(self):
		self.deck = copy.copy(self.deck)
		self.discard = copy.copy(self.discard)
		random.shuffle(self.discard)
		self.deck.append(self.discard)
		self.discard = []
		
	@property
	def known_cards(self):
		known_cards = [[card.name for card in pile] for pile in self.deck]
		for pile in known_cards:
			pile.sort()
		return known_cards
		
	@property
	def possible_deck(self):
		deck = []
		for pile in self.deck:
			new_pile = copy.copy(pile)
			random.shuffle(new_pile)
			deck.append(new_pile)
		return deck
		