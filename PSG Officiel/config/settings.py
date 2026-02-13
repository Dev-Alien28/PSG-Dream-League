# config/settings.py - V3 AVEC VRAIES RARETÉS PSG
import discord
import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv('DISCORD_TOKEN')

if not TOKEN:
    raise ValueError("❌ ERREUR: Le token Discord n'est pas défini dans le fichier .env")

# Intents
INTENTS = discord.Intents.default()
INTENTS.message_content = True
INTENTS.members = True
INTENTS.guilds = True
INTENTS.voice_states = True

# Chemins
DATA_DIR = "data"
PACKS_DIR = f"{DATA_DIR}/packs"
ARGENT_FILE = f"{DATA_DIR}/argent.json"
EVENT_FILE = f"{DATA_DIR}/event_state.json"

# Paramètres
COINS_PER_MESSAGE_INTERVAL = 1
COINS_ON_JOIN = 10
MIN_MESSAGE_LENGTH = 10  # Longueur minimale d'un message pour gagner des coins (anti-spam)

# Couleurs PSG
PSG_BLUE = 0x001F5B
PSG_RED = 0xDA0037
PSG_GREEN = 0x00D25B  # Couleur verte pour les confirmations

# ============================================
# RARETÉS OFFICIELLES PSG
# ============================================
RARITIES = {
    "Basic": {
        "emoji": "🟢",
        "color": 0x00FF00,  # Vert
        "name": "Basic"
    },
    "Advanced": {
        "emoji": "🔵",
        "color": 0x0000FF,  # Bleu
        "name": "Advanced"
    },
    "Elite": {
        "emoji": "🟣",
        "color": 0x9D00FF,  # Violet
        "name": "Elite"
    },
    "Legend": {
        "emoji": "🟠",
        "color": 0xFF6B00,  # Orange
        "name": "Legend"
    },
    "Unique": {
        "emoji": "⭐",
        "color": 0xFFD700,  # Or (pour collectibles)
        "name": "Unique"
    }
}

# ============================================
# TYPES DE CARTES
# ============================================
CARD_TYPES = {
    "joueur": {
        "emoji": "⚽",
        "positions": {
            "Gardien": ["physique", "agilite", "arret"],
            "Défenseur": ["intelligence", "pression", "physique"],
            "Milieu": ["technique", "intelligence", "controle"],
            "Attaquant": ["frappe", "technique", "controle"]
        }
    },
    "collectible": {
        "emoji": "🎖️",
        "stats": ["prestige", "annee", "rarete"]
    }
}

# ============================================
# CONFIGURATION DES PACKS
# ============================================
PACKS_CONFIG = {
    "psg_start": {
        "nom": "PSG Start",
        "prix": 25,
        "description": "Set de base composé des joueurs des saisons 24/25 et 25/26, obtenez des joueurs de la rareté 'Elite' surpuissants comme Hakimi, Dembélé ou Vitinha",
        "fichier": "psg_start.json",
        "emoji": "🔴🔵",
        "drop_rates": {
            "Basic": 70,
            "Advanced": 25,
            "Elite": 5,
            "Unique": 0
        }
    },
    "free_pack": {
        "nom": "Pack Journalier",
        "prix": 0,
        "description": "Pack gratuit repris du PSG Start qui est disponible toutes les 24h, obtenez des joueurs jusqu'à la rareté 'Advanced' pour compléter votre collection",
        "fichier": "free_pack.json",
        "emoji": "🎁",
        "cooldown": 86400,
        "drop_rates": {
            "Basic": 85,
            "Advanced": 15
        }
    },
    "pack_event": {
        "nom": "Pack Événement",
        "prix": 0,
        "description": "Pack exclusif du mini-jeu",
        "fichier": "pack_event.json",
        "emoji": "✨",
        "drop_rates": {
            "Elite": 60,
            "Legend": 40
        }
    }
}

# ============================================
# MINI-JEU
# ============================================
MINIGAME_CONFIG = {
    "min_interval_days": 4,
    "max_interval_days": 7,
    "start_hour": 7,
    "end_hour": 24,
    "timeout": 30,
    "reward_pack": "pack_event"
}

# ============================================
# EXEMPLE DE STRUCTURE PSG START
# ============================================
EXEMPLE_PACKS = {
    "psg_start.json": [
        # GARDIENS - Basic
        {
            "id": "gk_donnarumma_basic",
            "type": "joueur",
            "nom": "Gianluigi Donnarumma 24/25",
            "rareté": "Basic",
            "position": "Gardien",
            "stats": {"physique": 83, "agilite": 85, "arret": 85},
            "image": "https://example.com/donnarumma_basic.png"
        },
        {
            "id": "gk_chevalier_basic",
            "type": "joueur",
            "nom": "Lucas Chevalier 25/26",
            "rareté": "Basic",
            "position": "Gardien",
            "stats": {"physique": 76, "agilite": 79, "arret": 78},
            "image": "https://example.com/chevalier.png"
        },
        # DÉFENSEURS - Basic
        {
            "id": "def_hakimi_basic",
            "type": "joueur",
            "nom": "Achraf Hakimi 24/25 Home",
            "rareté": "Basic",
            "position": "Défenseur",
            "stats": {"intelligence": 83, "pression": 83, "physique": 85},
            "image": "https://example.com/hakimi.png"
        },
        {
            "id": "def_mendes_basic",
            "type": "joueur",
            "nom": "Nuno Mendes 25/26 Home",
            "rareté": "Basic",
            "position": "Défenseur",
            "stats": {"intelligence": 83, "pression": 85, "physique": 83},
            "image": "https://example.com/mendes.png"
        },
        # MILIEUX - Basic
        {
            "id": "mid_vitinha_basic",
            "type": "joueur",
            "nom": "Vitinha 25/26 Fourth",
            "rareté": "Basic",
            "position": "Milieu",
            "stats": {"technique": 83, "intelligence": 84, "controle": 85},
            "image": "https://example.com/vitinha.png"
        },
        # ATTAQUANTS - Basic
        {
            "id": "att_dembele_basic",
            "type": "joueur",
            "nom": "Ousmane Dembélé 25/26 Home",
            "rareté": "Basic",
            "position": "Attaquant",
            "stats": {"frappe": 83, "technique": 86, "controle": 85},
            "image": "https://example.com/dembele.png"
        },
        # GARDIENS - Advanced
        {
            "id": "gk_donnarumma_adv",
            "type": "joueur",
            "nom": "Gianluigi Donnarumma 24/25",
            "rareté": "Advanced",
            "position": "Gardien",
            "stats": {"physique": 86, "agilite": 88, "arret": 88},
            "image": "https://example.com/donnarumma_adv.png"
        },
        # GARDIENS - Elite
        {
            "id": "gk_donnarumma_elite",
            "type": "joueur",
            "nom": "Gianluigi Donnarumma 24/25",
            "rareté": "Elite",
            "position": "Gardien",
            "stats": {"physique": 89, "agilite": 91, "arret": 91},
            "image": "https://example.com/donnarumma_elite.png"
        },
        # COLLECTIBLES - Unique
        {
            "id": "coll_enrique",
            "type": "collectible",
            "nom": "Luis Enrique",
            "rareté": "Unique",
            "stats": {"prestige": 95, "annee": 2024, "rarete": 99},
            "image": "https://example.com/luisenrique.png"
        },
        {
            "id": "coll_ucl",
            "type": "collectible",
            "nom": "The Champions League 2024/2025",
            "rareté": "Unique",
            "stats": {"prestige": 100, "annee": 2025, "rarete": 100},
            "image": "https://example.com/ucl.png"
        }
    ],
    "free_pack.json": [
        {
            "id": "gk_tenas_basic",
            "type": "joueur",
            "nom": "Arnau Tenas 24/25",
            "rareté": "Basic",
            "position": "Gardien",
            "stats": {"physique": 71, "agilite": 75, "arret": 72},
            "image": "https://example.com/tenas.png"
        }
    ],
    "pack_event.json": [
        {
            "id": "att_dembele_elite",
            "type": "joueur",
            "nom": "Ousmane Dembélé 25/26 Home",
            "rareté": "Elite",
            "position": "Attaquant",
            "stats": {"frappe": 89, "technique": 92, "controle": 91},
            "image": "https://example.com/dembele_elite.png"
        }
    ]
}