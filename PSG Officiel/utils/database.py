# utils/database.py - V3 AVEC SÉPARATION PAR SERVEUR
import json
import os
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from config.settings import ARGENT_FILE, EXEMPLE_PACKS, PACKS_DIR, PACKS_CONFIG, DATA_DIR, EVENT_FILE

def init_files():
    """Initialise tous les fichiers nécessaires"""
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(PACKS_DIR, exist_ok=True)
    
    # Créer le fichier argent.json
    if not os.path.exists(ARGENT_FILE):
        with open(ARGENT_FILE, 'w', encoding='utf-8') as f:
            json.dump({}, f, indent=4, ensure_ascii=False)
    
    # Créer le fichier event_state.json
    if not os.path.exists(EVENT_FILE):
        with open(EVENT_FILE, 'w', encoding='utf-8') as f:
            json.dump({}, f, indent=4, ensure_ascii=False)
    
    # Créer les fichiers de packs
    for filename, cards in EXEMPLE_PACKS.items():
        filepath = f"{PACKS_DIR}/{filename}"
        if not os.path.exists(filepath):
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(cards, f, indent=4, ensure_ascii=False)

def load_argent() -> Dict:
    """Charge les données d'argent (par serveur)"""
    if os.path.exists(ARGENT_FILE):
        with open(ARGENT_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_argent(data: Dict):
    """Sauvegarde les données d'argent"""
    with open(ARGENT_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def init_user(user_id: str) -> Dict:
    """Initialise un nouvel utilisateur"""
    from config.settings import COINS_ON_JOIN
    return {
        "coins": COINS_ON_JOIN,
        "messages": 0,
        "collection": [],
        "last_free_pack": None
    }

def get_guild_data(guild_id: str) -> Dict:
    """Récupère les données d'un serveur spécifique"""
    all_data = load_argent()
    
    if guild_id not in all_data:
        all_data[guild_id] = {}
        save_argent(all_data)
    
    return all_data[guild_id]

def get_user_data(guild_id: str, user_id: str) -> Dict:
    """Récupère les données d'un utilisateur sur un serveur spécifique"""
    guild_data = get_guild_data(guild_id)
    
    if user_id not in guild_data:
        guild_data[user_id] = init_user(user_id)
        all_data = load_argent()
        all_data[guild_id] = guild_data
        save_argent(all_data)
    
    return guild_data[user_id]

def save_user_data(guild_id: str, user_id: str, user_data: Dict):
    """Sauvegarde les données d'un utilisateur"""
    all_data = load_argent()
    
    if guild_id not in all_data:
        all_data[guild_id] = {}
    
    all_data[guild_id][user_id] = user_data
    save_argent(all_data)

def load_pack_cards(pack_key: str) -> List[Dict]:
    """Charge les cartes d'un pack spécifique depuis son fichier JSON"""
    pack_info = PACKS_CONFIG.get(pack_key)
    if not pack_info:
        return []
    
    filepath = f"{PACKS_DIR}/{pack_info['fichier']}"
    if os.path.exists(filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def get_user_cards_grouped(guild_id: str, user_id: str) -> Dict:
    """Récupère les cartes d'un utilisateur groupées par ID avec compteur"""
    user_data = get_user_data(guild_id, user_id)
    collection = user_data.get("collection", [])
    card_count = {}
    
    for card in collection:
        card_id = card["id"]
        if card_id not in card_count:
            card_count[card_id] = {
                "card": card,
                "count": 0
            }
        card_count[card_id]["count"] += 1
    
    return card_count

def add_card_to_user(guild_id: str, user_id: str, card: Dict):
    """Ajoute une carte à la collection d'un utilisateur"""
    user_data = get_user_data(guild_id, user_id)
    user_data["collection"].append(card)
    save_user_data(guild_id, user_id, user_data)

def remove_coins(guild_id: str, user_id: str, amount: int) -> bool:
    """Retire des coins à un utilisateur, retourne True si succès"""
    user_data = get_user_data(guild_id, user_id)
    
    if user_data["coins"] < amount:
        return False
    
    user_data["coins"] -= amount
    save_user_data(guild_id, user_id, user_data)
    return True

def can_claim_free_pack(guild_id: str, user_id: str) -> bool:
    """Vérifie si l'utilisateur peut réclamer le pack gratuit"""
    user_data = get_user_data(guild_id, user_id)
    last_claim = user_data.get("last_free_pack")
    
    if not last_claim:
        return True
    
    try:
        last_claim_time = datetime.fromisoformat(last_claim)
        cooldown = PACKS_CONFIG["free_pack"]["cooldown"]
        elapsed = (datetime.now() - last_claim_time).total_seconds()
        return elapsed >= cooldown
    except (ValueError, TypeError) as e:
        print(f"Erreur parsing last_free_pack pour {user_id}: {e}")
        return True

def claim_free_pack(guild_id: str, user_id: str):
    """Marque le pack gratuit comme réclamé"""
    user_data = get_user_data(guild_id, user_id)
    user_data["last_free_pack"] = datetime.now().isoformat()
    save_user_data(guild_id, user_id, user_data)
    print(f"✅ Pack gratuit réclamé par {user_id} sur {guild_id} à {datetime.now()}")

def get_free_pack_cooldown(guild_id: str, user_id: str) -> int:
    """Retourne le temps restant avant le prochain pack gratuit (en secondes)"""
    user_data = get_user_data(guild_id, user_id)
    last_claim = user_data.get("last_free_pack")
    
    if not last_claim:
        return 0
    
    try:
        last_claim_time = datetime.fromisoformat(last_claim)
        cooldown = PACKS_CONFIG["free_pack"]["cooldown"]
        elapsed = (datetime.now() - last_claim_time).total_seconds()
        remaining = max(0, int(cooldown - elapsed))
        return remaining
    except (ValueError, TypeError) as e:
        print(f"Erreur calcul cooldown pour {user_id}: {e}")
        return 0

# ==================== SYSTÈME EVENT ====================
def load_event_state() -> Dict:
    """Charge l'état des événements"""
    if os.path.exists(EVENT_FILE):
        with open(EVENT_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_event_state(state: Dict):
    """Sauvegarde l'état des événements"""
    with open(EVENT_FILE, 'w', encoding='utf-8') as f:
        json.dump(state, f, indent=4, ensure_ascii=False)

def get_next_minigame_time(guild_id: str) -> datetime:
    """Récupère la prochaine date d'apparition du mini-jeu"""
    from config.settings import MINIGAME_CONFIG
    import random
    
    state = load_event_state()
    guild_key = f"minigame_{guild_id}"
    
    if guild_key not in state or "next_spawn" not in state[guild_key]:
        days = random.randint(MINIGAME_CONFIG["min_interval_days"], MINIGAME_CONFIG["max_interval_days"])
        next_time = datetime.now() + timedelta(days=days)
        
        hour = random.randint(MINIGAME_CONFIG["start_hour"], MINIGAME_CONFIG["end_hour"] - 1)
        minute = random.randint(0, 59)
        
        next_time = next_time.replace(hour=hour, minute=minute, second=0, microsecond=0)
        
        if guild_key not in state:
            state[guild_key] = {}
        
        state[guild_key]["next_spawn"] = next_time.isoformat()
        if "last_spawn" not in state[guild_key]:
            state[guild_key]["last_spawn"] = None
        
        save_event_state(state)
        return next_time
    
    return datetime.fromisoformat(state[guild_key]["next_spawn"])

def schedule_next_minigame(guild_id: str):
    """Planifie le prochain mini-jeu"""
    from config.settings import MINIGAME_CONFIG
    import random
    
    state = load_event_state()
    guild_key = f"minigame_{guild_id}"
    
    days = random.randint(MINIGAME_CONFIG["min_interval_days"], MINIGAME_CONFIG["max_interval_days"])
    next_time = datetime.now() + timedelta(days=days)
    
    hour = random.randint(MINIGAME_CONFIG["start_hour"], MINIGAME_CONFIG["end_hour"] - 1)
    minute = random.randint(0, 59)
    
    next_time = next_time.replace(hour=hour, minute=minute, second=0, microsecond=0)
    
    if guild_key not in state:
        state[guild_key] = {}
    
    state[guild_key]["next_spawn"] = next_time.isoformat()
    state[guild_key]["last_spawn"] = datetime.now().isoformat()
    
    save_event_state(state)
    return next_time

def get_minigame_channel(guild_id: str) -> str:
    """Récupère le salon configuré pour le mini-jeu"""
    state = load_event_state()
    guild_key = f"minigame_{guild_id}"
    
    if guild_key not in state:
        return None
    
    return state[guild_key].get("channel_id", None)

def set_minigame_channel(guild_id: str, channel_id: str = None):
    """Définit le salon pour le mini-jeu"""
    state = load_event_state()
    guild_key = f"minigame_{guild_id}"
    
    if guild_key not in state:
        state[guild_key] = {}
    
    if channel_id is None:
        if "channel_id" in state[guild_key]:
            del state[guild_key]["channel_id"]
    else:
        state[guild_key]["channel_id"] = str(channel_id)
    
    save_event_state(state)