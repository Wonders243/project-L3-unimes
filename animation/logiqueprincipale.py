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
    def __init__(self, nom, x, y, age, poids, energie, faim, soif, vitesse=1, vision=100, angle_vision=90):
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
        self.vitesse = vitesse  # Vitesse de déplacement
        self.vision = vision  # Distance de vision (rayon de détection)
        self.angle_vision = angle_vision  # Angle du champ de vision (en degrés)
        self.etat = "actif"  # L'état de l'animal (actif, fatigué, etc.)
        self.direction = 0  # Direction de l'animal (en radians)

    def distance(self, autre):
        """Calcule la distance entre cet animal et un autre."""
        return math.sqrt((self.x - autre.x) ** 2 + (self.y - autre.y) ** 2)

    def angle_entre(self, autre):
        """Calcule l'angle entre cet animal et un autre."""
        return math.degrees(math.atan2(autre.y - self.y, autre.x - self.x)) % 360

    def est_dans_vision(self, autre):
        """Vérifie si un autre animal est dans le champ de vision de cet animal."""
        # Calculer l'angle entre l'animal et l'autre
        angle = self.angle_entre(autre)
        
        # Vérifier si l'animal est dans le champ de vision (angle +/- angle_vision)
        angle_diff = abs(self.direction - angle)
        if angle_diff > 180:
            angle_diff = 360 - angle_diff
        
        return angle_diff <= self.angle_vision / 2 and self.distance(autre) <= self.vision

    def voir_environ(self, autres_animaux):
        """Renvoie les animaux visibles dans un rayon et un angle définis."""
        return [autre for autre in autres_animaux if autre is not self and self.est_dans_vision(autre)]

    def se_deplacer_vers(self, cible):
        """Se rapproche d'une cible avec déplacement progressif."""
        angle = math.atan2(cible.y - self.y, cible.x - self.x)
        self.x += math.cos(angle) * self.vitesse
        self.y += math.sin(angle) * self.vitesse
        print(f"{self.nom} se déplace vers {cible.nom} [{int(self.x)}, {int(self.y)}]")

    def se_deplacer_aleatoire(self):
        """Déplacement aléatoire en pixels."""
        angle = random.uniform(0, 2 * math.pi)
        self.x = max(0, min(self.x + math.cos(angle) * self.vitesse, 800))  # 800 = Largeur max
        self.y = max(0, min(self.y + math.sin(angle) * self.vitesse, 600))  # 600 = Hauteur max
        print(f"{self.nom} se déplace aléatoirement [{int(self.x)}, {int(self.y)}]")

    def marcher_vers(self, cible):
        """Marche lentement vers la cible."""
        print(f"{self.nom} marche lentement vers {cible.nom}.")
        self.se_deplacer_vers(cible)

    def courir_vers(self, cible):
        """Court rapidement vers la cible."""
        print(f"{self.nom} court rapidement vers {cible.nom}.")
        self.vitesse *= 2  # Double la vitesse pour simuler la course
        self.se_deplacer_vers(cible)
        self.vitesse /= 2  # Restaure la vitesse normale après la course

    def fuir(self, predateur):
        """Fuit un prédateur."""
        print(f"{self.nom} fuit {predateur.nom} !")
        angle = math.atan2(self.y - predateur.y, self.x - predateur.x)
        self.x += math.cos(angle) * self.vitesse * 2  # Fuite rapide
        self.y += math.sin(angle) * self.vitesse * 2
        print(f"{self.nom} fuit en direction [{int(self.x)}, {int(self.y)}]")

    def chasser(self, proie):
        """Logique de chasse : approche, attaque, etc."""
        distance = self.distance(proie)

        if distance > 5:
            # Si la proie est trop éloignée, marche vers elle
            self.marcher_vers(proie)
        elif distance <= 5:
            # Si la proie est proche, commence l'attaque
            print(f"{self.nom} commence à attaquer {proie.nom} !")
            self.mordre(proie)

    def mordre(self, proie):
        """Effectue l'attaque sur une proie."""
        if self.energie > 10:  # Vérifie si l'animal a assez d'énergie pour mordre
            print(f"{self.nom} mord {proie.nom} !")
            proie.subir_degats(20)  # inflige des dégâts à la proie
            self.energie -= 10  # consomme de l'énergie
        else:
            print(f"{self.nom} est trop fatigué pour mordre.")

    def subir_degats(self, degats):
        """Subit des dégâts et réagit en conséquence."""
        self.poids -= degats  # Réduit la masse de l'animal (peut être lié à sa santé)
        if self.poids <= 0:
            print(f"{self.nom} est trop affaibli et meurt.")
            self.etat = "mort"  # L'animal est mort

    def fuir_ou_chasser(self, autres_animaux):
        """Décide si l'animal doit fuir ou chasser en fonction de la situation."""
        proies = self.voir_environ(autres_animaux)
        predators = [a for a in autres_animaux if isinstance(a, Animal) and self.distance(a) < 20 and a.etat == "prédateur"]

        if predators:
            # Si des prédateurs sont à proximité, l'animal doit fuir
            for predateur in predators:
                self.fuir(predateur)
        elif proies:
            # Si des proies sont à proximité, commence à chasser
            self.chasser(proies[0])

    def se_reposer(self):
        """L'animal se repose pour récupérer de l'énergie."""
        if self.energie < 100:
            print(f"{self.nom} se repose pour récupérer de l'énergie.")
            self.energie = min(100, self.energie + 10)  # Récupère 10 points d'énergie
        else:
            print(f"{self.nom} est déjà plein d'énergie.")

    def ajuster_vision(self, valeur):
        """Ajuste le champ de vision de l'animal."""
        self.vision = valeur
        print(f"{self.nom} a maintenant une vision de {self.vision} pixels.")

    def ajuster_angle_vision(self, valeur):
        """Ajuste l'angle de vision de l'animal."""
        self.angle_vision = valeur
        print(f"{self.nom} a maintenant un angle de vision de {self.angle_vision} degrés.")

# Exemple d'utilisation
sim = Simulation(800, 600)  # Canvas de 800x600 pixels
sim.demarrer()

# Exemple d'utilisation
sim = Simulation()
sim.demarrer()