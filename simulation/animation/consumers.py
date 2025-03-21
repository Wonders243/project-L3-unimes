import json
import random
import asyncio
import math
import numpy as np
import tensorflow as tf
from tensorflow.keras.models import load_model

import pickle
import numpy as np
import pandas as pd
import keras
from channels.generic.websocket import AsyncWebsocketConsumer

# 🔥 Chargement du modèle local
MODEL_PATH = "/workspaces/project-L3-unimes/animal_decision_model.h5"
SCALER_PATH = "/workspaces/project-L3-unimes/scaler.pkl"
ENCODER_ANIMAL_PATH = "/workspaces/project-L3-unimes/encoder_animal.pkl"
ENCODER_CLIMAT_PATH = "/workspaces/project-L3-unimes/encoder_climat.pkl"
ENCODER_DECISION_PATH = "/workspaces/project-L3-unimes/encoder_decision.pkl"

model = load_model(MODEL_PATH)

class AnimalConsumer(AsyncWebsocketConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.map_width = 600
        self.map_height = 800

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
                "faim": random.randint(0, 100),
                "soif": random.randint(0, 100),
                "temperature": random.randint(-10, 40),
                "climat": random.choice(["pluie", "soleil", "neige", "vent"]),
                "predateurs": 0,
                "proies": random.randint(0, 5),
                "heure": random.randint(0, 23),
                "age": random.randint(2, 15),
                "poids": random.randint(120, 250),
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
                "faim": random.randint(0, 100),
                "soif": random.randint(0, 100),
                "temperature": random.randint(-10, 40),
                "climat": random.choice(["pluie", "soleil", "neige", "vent"]),
                "predateurs": random.randint(0, 2),
                "proies": random.randint(0, 5),
                "heure": random.randint(0, 23),
                "age": random.randint(1, 10),
                "poids": random.randint(30, 70),
                "color": "green",
                "type": "prey"
            }
            animals.append(gazelle)

        return animals

    async def update_animals(self):
        while True:
            for animal in self.animals[:]:
                if animal["energy"] <= 0:
                    self.animals.remove(animal)
                    self.cadavres.append({"x": animal["x"], "y": animal["y"], "type": "cadavre", "energy": 50})
                    continue
                
                prediction = self.predict_behavior(animal)  # 🔥 Prédiction avec le modèle
                self.apply_prediction(animal, prediction)  # 🔥 Application des prédictions
                
                self.handle_boundaries(animal)

            self.update_cadavres()
            
            await self.send(text_data=json.dumps(self.animals + self.cadavres))
            await asyncio.sleep(0.05)

   

# Charger le scaler et les encodeurs
with open(SCALER_PATH, 'rb') as f:
    scaler = pickle.load(f)
with open(ENCODER_ANIMAL_PATH, 'rb') as f:
    encoder_animal = pickle.load(f)
with open(ENCODER_CLIMAT_PATH, 'rb') as f:
    encoder_climat = pickle.load(f)
with open(ENCODER_DECISION_PATH, 'rb') as f:
    encoder_decision = pickle.load(f)

def predict_behavior(animal):
    """ Prédit le comportement d'un animal en utilisant le modèle """
    try:
        # Transformer les données en DataFrame
        data = pd.DataFrame([[
            animal["nom"],  # Nom de l'animal
            animal["age"],
            animal["poids"],
            animal["energie"],
            animal["faim"],
            animal["soif"],
            animal["nourriture"],
            animal["eau"],
            animal["temperature"],
            animal["climat"],
            animal["predateurs"],
            animal["proies"],
            animal["heure"]
        ]], columns=[
            "animal", "age", "poids", "energie", "faim", "soif", 
            "nourriture", "eau", "temperature", "climat", 
            "predateurs", "proies", "heure"
        ])

        # Encodage des variables catégoriques
        data["animal"] = encoder_animal.transform(data["animal"])
        data["climat"] = encoder_climat.transform(data["climat"])

        # Normalisation des données
        data = scaler.transform(data)

        # Reshape pour modèle LSTM
        data = data.reshape((data.shape[0], 1, data.shape[1]))

        # Prédictions
        prediction = model.predict(data)
        action = encoder_decision.inverse_transform([np.argmax(prediction)])

        return {"action": action[0]}  # Retourner l'action prédite

    except Exception as e:
        print(f"Erreur lors de la prédiction : {e}")
        return {"action": "rien"}  # Si erreur, retourner "rien"
    
    def apply_prediction(self, animal, prediction):
        """ Applique les actions prédites par le modèle. """
        action = prediction.get("action", "rien")

        if action == "manger":
            if animal["type"] == "predator":
                self.update_lion(animal)
            elif animal["type"] == "prey":
                animal["dx"] += random.uniform(-0.5, 0.5)
                animal["dy"] += random.uniform(-0.5, 0.5)

        elif action == "fuir":
            if animal["type"] == "prey":
                self.update_gazelle(animal)

        elif action == "dormir":
            self.dormir(animal)

        animal["x"] += animal["dx"]
        animal["y"] += animal["dy"]

    def dormir(self, animal):
        animal["dx"] = 0
        animal["dy"] = 0
        animal["energy"] += 0.5
        if animal["energy"] > 100:
            animal["energy"] = 100

    def handle_boundaries(self, animal):
        if animal["x"] < 0 or animal["x"] > self.map_width:
            animal["dx"] *= -1
        if animal["y"] < 0 or animal["y"] > self.map_height:
            animal["dy"] *= -1
        animal["x"] = max(0, min(self.map_width, animal["x"]))
        animal["y"] = max(0, min(self.map_height, animal["y"]))

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

    def manger_cadavre(self, predator, cadavre):
        cadavre["energy"] -= 2
        predator["energy"] += 2
        if cadavre["energy"] <= 0:
            self.cadavres.remove(cadavre)

