# predict_animal_decision.py
import pandas as pd
import numpy as np
import tensorflow as tf
from tensorflow import keras
import pickle




import random

class Simulation:
    def __init__(self):
        self.heure = 0  # Heure de 0 à 23
        self.temperature = 20  # Température en degrés Celsius
        self.climat = self.determine_climat()

        
    # Méthode pour tester le modèle
    def test_animal_model(model_path, scaler_path, encoder_animal_path, encoder_climat_path, encoder_decision_path, test_data):
        # Charger le modèle
        model = keras.models.load_model(model_path)
        
        # Charger le scaler et les encodeurs
        with open(scaler_path, 'rb') as f:
            scaler = pickle.load(f)
        with open(encoder_animal_path, 'rb') as f:
            encoder_animal = pickle.load(f)
        with open(encoder_climat_path, 'rb') as f:
            encoder_climat = pickle.load(f)
        with open(encoder_decision_path, 'rb') as f:
            encoder_decision = pickle.load(f)

        # Encodage des données de test
        test_data["animal"] = encoder_animal.transform(test_data["animal"])
        test_data["climat"] = encoder_climat.transform(test_data["climat"])

        # Normalisation des données
        test_data = scaler.transform(test_data)

        # Reshape pour LSTM
        test_data = test_data.reshape((test_data.shape[0], 1, test_data.shape[1]))

        # Prédictions
        predictions = model.predict(test_data)
        predicted_decisions = encoder_decision.inverse_transform(np.argmax(predictions, axis=1))

        return predicted_decisions


    def determine_climat(self):
        if 6 <= self.heure < 18:
            return 'ensoleillé'  # Climat ensoleillé pendant la journée
        elif 18 <= self.heure < 22:
            return 'nuageux'  # Climat nuageux en soirée
        else:
            return 'pluvieux'  # Climat pluvieux pendant la nuit


    def avancer_heure(self):
        # Avance l'heure et remet à zéro si nécessaire
        self.heure += 1
        if self.heure >= 24:
            self.heure = 0

    def ajuster_temperature(self):
        # Ajuste la température en fonction de l'heure et du climat
        if self.climat == 'ensoleillé':
            if 6 <= self.heure < 18:
                self.temperature += 2  # Temps chaud pendant la journée
            else:
                self.temperature -= 1  # Temps plus frais la nuit
        elif self.climat == 'nuageux':
            self.temperature += 0  # Température stable
        elif self.climat == 'pluvieux':
            self.temperature -= 2  # Temps frais et humide

    def simulation_step(self):
        # Étape de simulation
        self.avancer_heure()
        self.ajuster_temperature()
        self.climat = self.determine_climat()  # Change le climat
        print(f"Heure: {self.heure}h, Température: {self.temperature}°C, Climat: {self.climat}")

# Exécuter la simulation
simulation = Simulation()
for _ in range(24):  # Simulation d'une journée
    simulation.simulation_step()
