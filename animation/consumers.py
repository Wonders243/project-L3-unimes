import json
import random
import asyncio
import math
from channels.generic.websocket import AsyncWebsocketConsumer

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
            for animal in self.animals:
                if animal["type"] == "predator":
                    self.update_lion(animal)
                elif animal["type"] == "prey":
                    self.update_gazelle(animal)
                self.handle_boundaries(animal)
            await self.send(text_data=json.dumps(self.animals))
            await asyncio.sleep(0.05)

    async def connect(self):
        await self.accept()
        self.animals = self.create_animals()
        asyncio.create_task(self.update_animals())

    def create_animals(self):
        animals = []
        for _ in range(3):
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
        else:
            lion["dx"] += random.uniform(-0.2, 0.2)
            lion["dy"] += random.uniform(-0.2, 0.2)
        lion["x"] += lion["dx"]
        lion["y"] += lion["dy"]

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
