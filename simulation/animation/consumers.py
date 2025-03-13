
import json
import random
import asyncio
import math
from channels.generic.websocket import AsyncWebsocketConsumer

# Charger le modèle complet
model = load_model('mon_modele_lstm.h5')

class AnimalConsumer(AsyncWebsocketConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.map_width = 600
        self.map_height = 800
    def handle_boundaries(self, animal):
        if animal["x"] < 0 or animal["x"] > self.map_width:
            animal["dx"] *= -1
        if animal["y"] < 0 or animal["y"] > self.map_height:
            animal["dy"] *= -1
        animal["x"] = max(0, min(self.map_width, animal["x"]))
        animal["y"] = max(0, min(self.map_height, animal["y"]))

    async def update_animals(self):
        while True:
            for animal in self.animals[:]:
                if animal["energy"] <= 0:
                    self.animals.remove(animal)
                    self.cadavres.append({"x": animal["x"], "y": animal["y"], "type": "cadavre", "energy": 50})
                    continue
                
                animal["energy"] -= 0.1  # Perte d'énergie progressive
                if animal["energy"] < 20:
                    self.dormir(animal)
                else:
                    if animal["type"] == "predator":
                        self.update_lion(animal)
                    elif animal["type"] == "prey":
                        self.update_gazelle(animal)
                self.handle_boundaries(animal)
            
            self.update_cadavres()
            
            await self.send(text_data=json.dumps(self.animals + self.cadavres))
            await asyncio.sleep(0.05)

    async def connect(self):
        await self.accept()
        self.animals = self.create_animals()
        self.cadavres = []
        asyncio.create_task(self.update_animals())

    def create_animals(self):
        animals = []
        for _ in range(2):
            lion = {
                "id": "lion",
                "x": random.randint(100, 500),
                "y": random.randint(100, 500),
                "dx": 0,
                "dy": 0,
                "speed": 3,
                "max_speed": 12,
                "acceleration": 1.5,
                "vision": 200,
                "energy": 100,
                "color": "red",
                "type": "predator"
            }
            animals.append(lion)
        for _ in range(1):
            gazelle = {
                "id": "gazelle",
                "x": random.randint(100, 500),
                "y": random.randint(100, 500),
                "dx": random.uniform(-2, 2),
                "dy": random.uniform(-2, 2),
                "speed": 2,
                "max_speed": 10,
                "acceleration": 1,
                "vision": 100,
                "energy": 100,
                "color": "green",
                "type": "prey"
            }
            animals.append(gazelle)
        return animals

    def distance(self, a, b):
        return math.sqrt((a["x"] - b["x"]) ** 2 + (a["y"] - b["y"]) ** 2)

    def angle_between(self, a, b):
        return math.atan2(b["y"] - a["y"], b["x"] - a["x"])

    def update_lion(self, lion):
        prey_in_sight = [gazelle for gazelle in self.animals if gazelle["type"] == "prey" and self.distance(lion, gazelle) <= lion["vision"]]
        if prey_in_sight:
            target = min(prey_in_sight, key=lambda gazelle: self.distance(lion, gazelle))
            angle = self.angle_between(lion, target)
            lion["dx"] += math.cos(angle) * lion["acceleration"]
            lion["dy"] += math.sin(angle) * lion["acceleration"]
            speed = math.sqrt(lion["dx"]**2 + lion["dy"]**2)
            if speed > lion["max_speed"]:
                lion["dx"] *= lion["max_speed"] / speed
                lion["dy"] *= lion["max_speed"] / speed
            
            if self.distance(lion, target) < 5:
                self.manger(lion, target)
        else:
            lion["dx"] += random.uniform(-0.2, 0.2)
            lion["dy"] += random.uniform(-0.2, 0.2)
        lion["x"] += lion["dx"]
        lion["y"] += lion["dy"]

    def update_cadavres(self):
        for lion in [a for a in self.animals if a["type"] == "predator"]:
            cadavres_proches = [c for c in self.cadavres if self.distance(lion, c) < lion["vision"]]
            if cadavres_proches:
                target = min(cadavres_proches, key=lambda c: self.distance(lion, c))
                angle = self.angle_between(lion, target)
                lion["dx"] += math.cos(angle) * 0.5
                lion["dy"] += math.sin(angle) * 0.5
                if self.distance(lion, target) < 5:
                    self.manger_cadavre(lion, target)
    
    def manger(self, predator, prey):
        if prey in self.animals:
            self.animals.remove(prey)
            self.cadavres.append({"x": prey["x"], "y": prey["y"], "type": "cadavre", "energy": 50})
            predator["energy"] += 30
            if predator["energy"] > 100:
                predator["energy"] = 100
    
    def manger_cadavre(self, predator, cadavre):
        cadavre["energy"] -= 2
        predator["energy"] += 2
        if cadavre["energy"] <= 0:
            self.cadavres.remove(cadavre)
    def dormir(self, animal):
        animal["dx"] = 0
        animal["dy"] = 0
        animal["energy"] += 0.5  # Recharge lente de l'énergie
        if animal["energy"] > 100:
            animal["energy"] = 100

    def update_gazelle(self, gazelle):
        predators_nearby = [lion for lion in self.animals if lion["type"] == "predator" and self.distance(gazelle, lion) <= gazelle["vision"]]
        if predators_nearby:
            danger = min(predators_nearby, key=lambda lion: self.distance(gazelle, lion))
            angle = self.angle_between(gazelle, danger) + math.pi
            gazelle["dx"] += math.cos(angle) * gazelle["acceleration"]
            gazelle["dy"] += math.sin(angle) * gazelle["acceleration"]
            speed = math.sqrt(gazelle["dx"]**2 + gazelle["dy"]**2)
            if speed > gazelle["max_speed"]:
                gazelle["dx"] *= gazelle["max_speed"] / speed
                gazelle["dy"] *= gazelle["max_speed"] / speed
        gazelle["x"] += gazelle["dx"]
        gazelle["y"] += gazelle["dy"]
