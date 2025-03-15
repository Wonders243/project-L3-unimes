import time
import random
import math
import json
import random
import asyncio
from channels.generic.websocket import AsyncWebsocketConsumer

class Simulation (AsyncWebsocketConsumer):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.largeur = largeur  # Largeur du canvas en pixels
        self.hauteur = hauteur  # Hauteur du canvas en pixels
        self.annee = 1
        self.mois = 1
        self.jour = 1
        self.heure = 0
        self.minute = 0
        self.seconde = 0

        self.tick_duree = 0.05  # 50 ms par tick
        self.ticks_par_jour = 72000  # 1 jour simulé = 1 heure réelle
        self.ticks_par_heure = 3000  # 1 heure simulée = 3000 ticks
        self.ticks_par_minute = 50  # 1 minute simulée = 50 ticks

        self.ticks_actuels = 0

    def est_jour(self):
        """Détermine si c'est le jour ou la nuit."""
        return 6 <= self.heure < 18  # Jour entre 6h et 18h

    def avancer_temps(self):
        """Avance la simulation d'un tick et met à jour l'heure et la date."""
        self.ticks_actuels += 1
        self.seconde += 1

        # Gestion des secondes, minutes et heures
        if self.seconde >= 60:
            self.seconde = 0
            self.minute += 1

        if self.minute >= 60:
            self.minute = 0
            self.heure += 1

        if self.heure >= 24:
            self.heure = 0
            self.jour += 1

            # Gestion des mois et années
            if self.jour > 30:  # Supposons 30 jours par mois
                self.jour = 1
                self.mois += 1

                if self.mois > 12:  # Supposons 12 mois par an
                    self.mois = 1
                    self.annee += 1

        # Déterminer si c'est le jour ou la nuit
        cycle = "Jour" if self.est_jour() else "Nuit"

        # Affichage formaté
        print(f"{self.annee}/{self.mois}/{self.jour} - {self.heure:02}:{self.minute:02}:{self.seconde:02} [{cycle}]")

    async def connect(self):
        await self.accept()
        self.animals = self.create_animals()
        self.cadavres = []
        asyncio.create_task(self.demarrer())

    async def demarrer(self):
        """Démarre la simulation avec un passage du temps automatique."""
        while True:
            self.avancer_temps()
            time.sleep(self.tick_duree)  # Pause de 50ms entre chaque tick
     


class Animal:
    def __init__(self, nom, x, y, age, poids, energie, faim, soif):
        self.nom = nom
        self.x = x  # Position en pixels
        self.y = y
        self.age = age
        self.poids = poids
        self.energie = energie  # (0-100)
        self.faim = faim  # (0-100)
        self.soif = soif  # (0-100)
        self.nourriture_dispo = 0  # Nourriture proche
        self.eau_proche = 0  # 1 si eau proche, 0 sinon
        self.predateurs = 0
        self.proies = 0
      

    def distance(self, autre):
        """Calcule la distance entre cet animal et un autre."""
        return math.sqrt((self.x - autre.x) ** 2 + (self.y - autre.y) ** 2)

    def voir_environ(self, autres_animaux):
        """Renvoie les animaux visibles dans un rayon défini."""
        return [autre for autre in autres_animaux if autre is not self and self.distance(autre) <= self.vision]

    def se_deplacer_vers(self, cible):
        """Se rapproche d'une cible avec déplacement progressif."""
        angle = math.atan2(cible.y - self.y, cible.x - self.x)
        self.x += math.cos(angle) * self.vitesse
        self.y += math.sin(angle) * self.vitesse
        print(f"{self.nom} se déplace vers {cible.nom} [{int(self.x)}, {int(self.y)}]")

    def executer_action(self, autres_animaux):
        """Exécute une action, comme chercher une proie."""
        proies = self.voir_environ(autres_animaux)
        if proies:
            print(f"{self.nom} repère {proies[0].nom} à proximité !")
            self.se_deplacer_vers(proies[0])
        else:
            self.se_deplacer_aleatoire()

    def se_deplacer_aleatoire(self):
        """Déplacement aléatoire en pixels."""
        angle = random.uniform(0, 2 * math.pi)
        self.x = max(0, min(self.x + math.cos(angle) * self.vitesse, 800))  # 800 = Largeur max
        self.y = max(0, min(self.y + math.sin(angle) * self.vitesse, 600))  # 600 = Hauteur max
        print(f"{self.nom} se déplace aléatoirement [{int(self.x)}, {int(self.y)}]")

# Exemple d'utilisation
sim = Simulation(800, 600)  # Canvas de 800x600 pixels
sim.demarrer()

# Exemple d'utilisation
sim = Simulation()
sim.demarrer()