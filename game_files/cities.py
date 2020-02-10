import copy

CITY_CARDS = {
	'algiers': {'country':'algeria','color':'black','pop':2946000,'pop_density':6500,'connects':['madrid', 'paris', 'istanbul', 'cairo']},
	'atlanta': {'country':'united_states','color':'blue','pop':4715000,'pop_density':700,'connects':['chicago', 'washington', 'miami']},
	'baghdad': {'country':'iraq','color':'black','pop':6204000,'pop_density':10400,'connects':['istanbul', 'cairo', 'tehran', 'karachi', 'riyadh']},
	'bangkok': {'country':'thailand','color':'red','pop':7151000,'pop_density':3200,'connects':['chennai', 'kolkata', 'hong_kong', 'ho_chi_minh_city', 'jakarta']},
	'beijing': {'country':'peoples_republic_of_china','color':'red','pop':17311000,'pop_density':5000,'connects':['seoul', 'shanghai']},
	'bogota': {'country':'colombia','color':'yellow','pop':8702000,'pop_density':21000,'connects':['mexico_city', 'miami', 'sao_paulo', 'buenos_aires', 'lima']},
	'buenos_aires': {'country':'argentina','color':'yellow','pop':13639000,'pop_density':5200,'connects':['bogota', 'sao_paulo']},
	'cairo': {'country':'egypt','color':'black','pop':14718000,'pop_density':8900,'connects':['khartoum', 'algiers', 'istanbul', 'baghdad', 'riyadh']},
	'chennai': {'country':'india','color':'black','pop':8865000,'pop_density':14600,'connects':['mumbai', 'delhi', 'kolkata', 'bangkok', 'jakarta']},
	'chicago': {'country':'united_states','color':'blue','pop':9121000,'pop_density':1300,'connects':['san_francisco', 'montreal', 'atlanta', 'mexico_city', 'los_angeles']},
	'delhi': {'country':'india','color':'black','pop':22242000,'pop_density':11500,'connects':['tehran', 'karachi', 'mumbai', 'kolkata', 'chennai']},
	'essen': {'country':'germany','color':'blue','pop':575000,'pop_density':2800,'connects':['london', 'paris', 'st_petersburg', 'milan']},
	'ho_chi_minh_city': {'country':'vietnam','color':'red','pop':8314000,'pop_density':9900,'connects':['bangkok', 'jakarta', 'hong_kong', 'manila']},
	'hong_kong': {'country':'peoples_republic_of_china','color':'red','pop':7106000,'pop_density':25900,'connects':['kolkata', 'bangkok', 'shanghai', 'taipei', 'manila', 'ho_chi_minh_city']},
	'istanbul': {'country':'turkey','color':'black','pop':13576000,'pop_density':9700,'connects':['milan', 'st_petersburg', 'algiers', 'moscow', 'baghdad', 'cairo']},
	'jakarta': {'country':'indonesia','color':'red','pop':26063000,'pop_density':9400,'connects':['chennai', 'bangkok', 'ho_chi_minh_city', 'sydney']},
	'johannesburg': {'country':'south_africa','color':'yellow','pop':3888000,'pop_density':2400,'connects':['kinshasa', 'khartoum']},
	'karachi': {'country':'pakistan','color':'black','pop':20711000,'pop_density':25800,'connects':['baghdad', 'riyadh', 'tehran', 'delhi', 'mumbai']},
	'khartoum': {'country':'sudan','color':'yellow','pop':4887000,'pop_density':4500,'connects':['lagos', 'kinshasa', 'johannesburg', 'cairo']},
	'kinshasa': {'country':'democratic_republic_of_the_congo','color':'yellow','pop':9046000,'pop_density':15500,'connects':['lagos', 'khartoum', 'johannesburg']},
	'kolkata': {'country':'india','color':'black','pop':14374000,'pop_density':11900,'connects':['delhi', 'chennai', 'hong_kong', 'bangkok']},
	'lagos': {'country':'nigeria','color':'yellow','pop':11547000,'pop_density':12700,'connects':['sao_paulo', 'khartoum', 'kinshasa']},
	'lima': {'country':'peru','color':'yellow','pop':9121000,'pop_density':14100,'connects':['mexico_city', 'bogota', 'santiago']},
	'london': {'country':'united_kingdom','color':'blue','pop':8568000,'pop_density':5300,'connects':['new_york', 'essen', 'paris', 'madrid']},
	'los_angeles': {'country':'united_states','color':'yellow','pop':14900000,'pop_density':2400,'connects':['san_francisco', 'chicago', 'mexico_city', 'sydney']},
	'madrid': {'country':'spain','color':'blue','pop':5427000,'pop_density':5700,'connects':['new_york', 'london', 'paris', 'algiers', 'sao_paulo']},
	'manila': {'country':'philippines','color':'red','pop':20767000,'pop_density':14400,'connects':['san_francisco', 'hong_kong', 'ho_chi_minh_city', 'taipei', 'sydney']},
	'mexico_city': {'country':'mexico','color':'yellow','pop':19463000,'pop_density':9500,'connects':['chicago', 'los_angeles', 'miami', 'bogota', 'lima']},
	'miami': {'country':'united_states','color':'yellow','pop':5582000,'pop_density':1700,'connects':['atlanta', 'mexico_city', 'washington', 'bogota']},
	'milan': {'country':'italy','color':'blue','pop':5232000,'pop_density':2800,'connects':['paris', 'essen', 'istanbul']},
	'montreal': {'country':'canada','color':'blue','pop':3429000,'pop_density':2200,'connects':['chicago', 'new_york', 'washington']},
	'moscow': {'country':'russia','color':'black','pop':15512000,'pop_density':3500,'connects':['st_petersburg', 'istanbul', 'tehran']},
	'mumbai': {'country':'india','color':'black','pop':16910000,'pop_density':30900,'connects':['karachi', 'delhi', 'chennai']},
	'new_york': {'country':'united_states','color':'blue','pop':20464000,'pop_density':1800,'connects':['montreal', 'london', 'madrid', 'washington']},
	'osaka': {'country':'japan','color':'red','pop':2871000,'pop_density':13000,'connects':['taipei', 'tokyo']},
	'paris': {'country':'france','color':'blue','pop':10755000,'pop_density':3800,'connects':['london', 'madrid', 'essen', 'milan', 'algiers']},
	'riyadh': {'country':'saudi_arabia','color':'black','pop':5037000,'pop_density':3400,'connects':['cairo', 'baghdad', 'karachi']},
	'san_francisco': {'country':'united_states','color':'blue','pop':5864000,'pop_density':2100,'connects':['chicago', 'los_angeles', 'manila', 'tokyo']},
	'santiago': {'country':'chile','color':'yellow','pop':6015000,'pop_density':6500,'connects':['lima']},
	'sao_paulo': {'country':'brazil','color':'yellow','pop':20186000,'pop_density':6400,'connects':['madrid', 'bogota', 'lagos', 'buenos_aires']},
	'seoul': {'country':'south_korea','color':'red','pop':22547000,'pop_density':10400,'connects':['beijing', 'shanghai', 'tokyo']},
	'shanghai': {'country':'peoples_republic_of_china','color':'red','pop':13482000,'pop_density':2200,'connects':['beijing', 'seoul', 'tokyo', 'hong_kong', 'taipei']},
	'st_petersburg': {'country':'russia','color':'blue','pop':4879000,'pop_density':4100,'connects':['essen', 'moscow', 'istanbul']},
	'sydney': {'country':'australia','color':'red','pop':3785000,'pop_density':2100,'connects':['los_angeles', 'jakarta', 'manila']},
	'taipei': {'country':'taiwan','color':'red','pop':8338000,'pop_density':7300,'connects':['hong_kong', 'osaka', 'manila', 'shanghai']},
	'tehran': {'country':'iran','color':'black','pop':7419000,'pop_density':9500,'connects':['moscow', 'baghdad', 'delhi', 'karachi']},
	'tokyo': {'country':'japan','color':'red','pop':13189000,'pop_density':6030,'connects':['san_francisco', 'shanghai', 'seoul', 'osaka']},
	'washington': {'country':'united_states','color':'blue','pop':4679000,'pop_density':1400,'connects':['montreal', 'new_york', 'atlanta', 'miami']},
}

class City():
	def __repr__(self):
		return self.name+": Diseases: "+str([color+"="+str(self.disease_cubes[color]) for color in self.disease_cubes]) + " R.S: "+str(1 if self.research_station else 0)
	
	def __call__(self):
		return {
			'disease_cubes': self.disease_cubes,
			'research_station': self.research_station
		}
	
	def __init__(self,name,color,neighbors,colors):
		self.name = name
		self.color = color
		self.neighbors = neighbors
		self.disease_cubes = {c: 0 for c in colors}
		self.research_station = False
	
	def get_id(self):
		return (
				tuple(self.disease_cubes.values()),
				self.research_station
		)
	
	def infect(self,game,infection,color,outbreak_chain=[]):
		if not game.eradicated[color] and self.name not in game.protected_cities and not (game.medic_position==self.name and game.cures[color]):
			net_infection = min(3-self.disease_cubes[color],infection)
			self.disease_cubes = copy.copy(self.disease_cubes)
			self.disease_cubes[color] += net_infection
			game.remaining_disease_cubes = copy.copy(game.remaining_disease_cubes)
			game.remaining_disease_cubes[color] -= net_infection
			game.log("Infect "+str(net_infection)+"-"+color+" at: "+self.name)
			# Outbreak
			if infection > net_infection:
				game.log("Outbreak at: "+self.name)
				outbreak_chain.append(self.name)
				game.outbreak_counter += 1
				for city_name in self.neighbors:
					if city_name not in outbreak_chain:
						game.cities[city_name] = copy.copy(game.cities[city_name])
						game.cities[city_name].infect(game,1,color,outbreak_chain)
		else:
			game.log("Infection prevented at: "+self.name)
			
	def disinfect(self,game,disinfection,color):
		self.disease_cubes = copy.copy(self.disease_cubes)
		self.disease_cubes[color] -= disinfection
		game.remaining_disease_cubes = copy.copy(game.remaining_disease_cubes)
		game.remaining_disease_cubes[color] += disinfection
		if game.cures[color] and game.remaining_disease_cubes[color]==game.commons['number_cubes']:
			game.eradicated = copy.copy(game.eradicated)
			game.eradicated[color] = True
			game.log("Eradicated "+color+" disease")
