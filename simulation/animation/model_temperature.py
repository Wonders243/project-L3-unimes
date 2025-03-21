
from keras.models import Sequential
from keras.layers import LSTM, Dense, Dropout
import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler

import pandas as pd
import numpy as np

# Fonction pour générer des températures en fonction de la saison
def generer_temperature(mois):
    if mois in [12, 1, 2]:  # Hiver
        return np.random.normal(loc=5, scale=5)  # Température moyenne de 5°C
    elif mois in [3, 4, 5]:  # Printemps
        return np.random.normal(loc=15, scale=5)  # Température moyenne de 15°C
    elif mois in [6, 7, 8]:  # Été
        return np.random.normal(loc=25, scale=5)  # Température moyenne de 25°C
    elif mois in [9, 10, 11]:  # Automne
        return np.random.normal(loc=15, scale=5)  # Température moyenne de 15°C

# Dates pour deux ans
dates = pd.date_range(start='2023-01-01', end='2024-12-31', freq='D')

# Liste pour stocker les températures
temperatures = []

# Générer des températures pour chaque date
for date in dates:
    temperature = generer_temperature(date.month)
    temperatures.append(temperature)

# Créer le DataFrame
df = pd.DataFrame({
    'date': dates,
    'temperature': temperatures
})

# Ajouter une colonne pour les conditions climatiques
def determiner_condition(temperature):
    if temperature > 25:
        return 'ensoleillé'
    elif temperature > 15:
        return 'nuageux'
    else:
        return 'pluvieux'

df['condition'] = df['temperature'].apply(determiner_condition)

# Afficher les premières lignes du DataFrame
print(df.head())

# Sauvegarder le DataFrame dans un fichier CSV
df.to_csv('donnees_temperature_2_ans.csv', index=False)

# Charger les données depuis un fichier CSV
df = pd.read_csv('donnees_temperature_2_ans.csv')  # Remplacez par le chemin vers votre fichier

# Convertir la colonne de date en type datetime
df['date'] = pd.to_datetime(df['date'])

# Trier les données par date
df = df.sort_values('date')

# Extraire la température
temperature_data = df['temperature'].values

# Normaliser les données
scaler = MinMaxScaler(feature_range=(0, 1))
temperature_data = scaler.fit_transform(temperature_data.reshape(-1, 1))

# Créer des séquences pour l'entraînement
def create_dataset(data, time_step=1):
    X, y = [], []
    for i in range(len(data) - time_step - 1):
        X.append(data[i:(i + time_step), 0])
        y.append(data[i + time_step, 0])
    return np.array(X), np.array(y)

# Définir le nombre de pas de temps
time_step = 30  # Par exemple, utiliser 30 jours pour prédire le jour suivant
X, y = create_dataset(temperature_data, time_step)

# Reshaper X pour LSTM [samples, time steps, features]
X = X.reshape(X.shape[0], X.shape[1], 1)

# Créer le modèle LSTM
model = Sequential()
model.add(LSTM(50, return_sequences=True, input_shape=(X.shape[1], 1)))
model.add(Dropout(0.2))
model.add(LSTM(50, return_sequences=False))
model.add(Dropout(0.2))
model.add(Dense(1))  # Prédiction de la température

# Compiler le modèle
model.compile(optimizer='adam', loss='mean_squared_error')

# Afficher le résumé du modèle
model.summary()

# Entraîner le modèle
model.fit(X, y, epochs=100, batch_size=32)

# Faire des prédictions
train_predict = model.predict(X)

# Inverser la normalisation pour obtenir les valeurs originales
train_predict = scaler.inverse_transform(train_predict)

# Calculer la température prédite pour le prochain jour
last_sequence = temperature_data[-time_step:].reshape(1, time_step, 1)
next_temperature = model.predict(last_sequence)
next_temperature = scaler.inverse_transform(next_temperature)

print(f"Température prédite pour le jour suivant : {next_temperature[0][0]:.2f}°C")


def predire_condition(temperature):
    if temperature > 25:
        return 'ensoleillé'
    elif temperature > 15:
        return 'nuageux'
    else:
        return 'pluvieux'

condition_predite = predire_condition(next_temperature[2][0])
print(f"Condition climatique prédite : {condition_predite}")
