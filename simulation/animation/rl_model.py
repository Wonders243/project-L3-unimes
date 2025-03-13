import pandas as pd
import numpy as np
import random
import tensorflow as tf
from tensorflow import keras
from sklearn.preprocessing import LabelEncoder, StandardScaler

# Nouvelle logique améliorée pour l'attribution des décisions
def determine_decision(animal, faim, soif, energie, nourriture, eau, predateurs, proies, temperature, temps):
    # Probabilité d'activité nocturne pour certains animaux
    chasse_nuit_prob = 0.3 if animal in ["lion", "loup"] else 0.1  # Prédateurs plus actifs la nuit

    if temps == "nuit":
        if energie < 30 and random.random() > chasse_nuit_prob:
            return "dormir"  # La plupart des animaux dorment
        elif faim > 80 and proies > 0 and random.random() < chasse_nuit_prob:
            return "chasser"  # Un prédateur affamé peut chasser malgré la nuit
        else:
            return "se reposer"

    # Logique de jour (matin / après-midi)
    if faim > 80 and proies > 0:
        return "chasser"
    elif faim > 80 and nourriture > 5:
        return "chercher de la nourriture"
    elif soif > 80 and eau == 1:
        return "boire"
    elif soif > 80 and eau == 0:
        return "chercher de l'eau"
    elif predateurs >= 2 and energie < 40:
        return "se cacher"
    elif predateurs >= 2 and energie >= 40:
        return "fuir"
    elif predateurs > 0 and energie > 50:
        return "se regrouper"
    elif temperature < -5 or temperature > 35:
        return "migrer"
    elif energie < 20:
        return "se reposer"
    elif faim < 30 and soif < 30 and energie > 60:
        return "jouer / interagir"
    else:
        return "explorer"

def generate_animal_data(n_samples=1000):
    data = []
    
    for _ in range(n_samples):
        animal = random.choice(["lion", "gazelle", "loup", "lapin", "ours"])
        age = random.randint(0, 15)  # En années
        poids = random.randint(5, 250)  # En kg
        energie = random.randint(0, 100)
        faim = random.randint(0, 100)
        soif = random.randint(0, 100)
        nourriture = random.randint(0, 50)  # Quantité dispo
        eau = random.choice([0, 1])  # 1 si point d'eau proche
        temperature = random.randint(-10, 40)
        climat = random.choice(["pluie", "soleil", "neige", "vent"])
        predateurs = random.randint(0, 2)  # Nombre de prédateurs proches
        proies = random.randint(0, 5)  # Nombre de proies proches
        temps = random.randint(0, 23)  # Heure de la journée
        
        decision = determine_decision(animal, faim, soif, energie, nourriture, eau, predateurs, proies, temperature, temps)
 
        data.append([animal, age, poids, energie, faim, soif, nourriture, eau, temperature, climat, predateurs, proies, temps, decision])
    
    columns = ["animal", "age", "poids", "energie", "faim", "soif", "nourriture", "eau", "temperature", "climat", "predateurs", "proies", "heure", "decision"]
    df = pd.DataFrame(data, columns=columns)
    
    return df

# Générer les données
df = generate_animal_data(1000000)

# Encodage des variables catégoriques
encoder_animal = LabelEncoder()
df["animal"] = encoder_animal.fit_transform(df["animal"])

encoder_climat = LabelEncoder()
df["climat"] = encoder_climat.fit_transform(df["climat"])

encoder_decision = LabelEncoder()
df["decision"] = encoder_decision.fit_transform(df["decision"])

# Séparation des features et labels
X = df.drop(columns=["decision"])
y = df["decision"]

# Normalisation des données
scaler = StandardScaler()
X = scaler.fit_transform(X)

# Reshape pour LSTM
X = X.reshape((X.shape[0], 1, X.shape[1]))

# Définition du modèle LSTM
model = keras.Sequential([
    keras.layers.LSTM(50, return_sequences=True, input_shape=(1, X.shape[2])),
    keras.layers.LSTM(50),
    keras.layers.Dense(20, activation='relu'),
    keras.layers.Dense(len(df["decision"].unique()), activation='softmax')
])

# Compilation du modèle
model.compile(loss='sparse_categorical_crossentropy', optimizer='adam', metrics=['accuracy'])

# Entraînement du modèle
model.fit(X, y, epochs=10, batch_size=32, validation_split=0.2)

# Sauvegarde du modèle
model.save("animal_decision_model.h5")

# Tester le modèle avec 3 animaux
test_animals = pd.DataFrame([
    ["lion", 10, 200, 30, 80, 50, 10, 1, 30, "soleil", 1, 3, 14],
    ["gazelle", 3, 50, 90, 20, 40, 30, 1, 25, "pluie", 0, 2, 8],
    ["ours", 8, 180, 20, 50, 90, 5, 0, -5, "neige", 2, 1, 23]
], columns=["animal", "age", "poids", "energie", "faim", "soif", "nourriture", "eau", "temperature", "climat", "predateurs", "proies", "heure"])

# Encodage et normalisation
test_animals["animal"] = encoder_animal.transform(test_animals["animal"])
test_animals["climat"] = encoder_climat.transform(test_animals["climat"])
test_animals = scaler.transform(test_animals)
test_animals = test_animals.reshape((test_animals.shape[0], 1, test_animals.shape[1]))

# Charger le modèle et faire les prédictions
model = keras.models.load_model("animal_decision_model.h5")
predictions = model.predict(test_animals)
predicted_decisions = encoder_decision.inverse_transform(np.argmax(predictions, axis=1))

# Affichage des résultats
for i, animal in enumerate(["lion", "gazelle", "ours"]):
    print(f"{animal} dans ces conditions choisit de : {predicted_decisions[i]}")

# Évaluation
loss, accuracy = model.evaluate(X, y)
print(f"Précision du modèle: {accuracy:.2f}")

# Télécharger le fichier CSV
df.to_csv("animal_data.csv", index=False)
files.download("animal_data.csv")
