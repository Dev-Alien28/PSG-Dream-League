# utils/database.py
import json
import os
from typing import Dict, List
from config.settings import ARGENT_FILE, EXEMPLE_PACKS, PACKS_DIR, PACKS_CONFIG

def init_files():
    """Initialise tous les fichiers nécessaires"""
    # Créer le fichier argent.json s'il n'existe pas
    if not os.path.exists(ARGENT_FILE):
        with open(ARGENT_FILE, 'w', encoding='utf-8') as f:
            json.dump({}, f, indent=4, ensure_ascii=False)
    
    # Créer les fichiers de packs s'ils n'existent pas
    for filename, cards in EXEMPLE_PACKS.items():
        filepath = f"{PACKS_DIR}/{filename}"
        if not os.path.exists(filepath):
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(cards, f, indent=4, ensure_ascii=False)

def load_argent() -> Dict:
    """Charge les données d'argent (utilisateurs)"""
    if os.path.exists(ARGENT_FILE):
        with open(ARGENT_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_argent(users: Dict):
    """Sauvegarde les données d'argent"""
    with open(ARGENT_FILE, 'w', encoding='utf-8') as f:
        json.dump(users, f, indent=4, ensure_ascii=False)

def init_user(user_id: str) -> Dict:
    """Initialise un nouvel utilisateur"""
    from config.settings import COINS_ON_JOIN
    return {
        "coins": COINS_ON_JOIN,
        "messages": 0,
        "collection": []
    }

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

def get_user_cards_grouped(user_id: str) -> Dict:
    """Récupère les cartes d'un utilisateur groupées par ID avec compteur"""
    users = load_argent()
    if user_id not in users:
        return {}
    
    collection = users[user_id]["collection"]
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

def add_card_to_user(user_id: str, card: Dict):
    """Ajoute une carte à la collection d'un utilisateur"""
    users = load_argent()
    if user_id not in users:
        users[user_id] = init_user(user_id)
    
    users[user_id]["collection"].append(card)
    save_argent(users)

def remove_coins(user_id: str, amount: int) -> bool:
    """Retire des coins à un utilisateur, retourne True si succès"""
    users = load_argent()
    if user_id not in users:
        return False
    
    if users[user_id]["coins"] < amount:
        return False
    
    users[user_id]["coins"] -= amount
    save_argent(users)
    return True