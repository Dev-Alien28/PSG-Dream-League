# utils/permissions.py - VERSION AVEC SALONS SANS COINS
import discord
import json
import os
from typing import Optional, List

SERVERS_DIR = "data/servers"

def init_server_config(guild_id: str, guild_name: str):
    """Initialise la configuration d'un serveur"""
    os.makedirs(SERVERS_DIR, exist_ok=True)
    
    config_path = f"{SERVERS_DIR}/{guild_id}.json"
    if not os.path.exists(config_path):
        config = {
            "guild_id": guild_id,
            "guild_name": guild_name,
            "channels": {
                "solde": [],
                "packs": [],
                "collection": []
            },
            "roles": {
                "admin": [],
                "moderator": []
            },
            "no_coins_channels": []  # ✅ Nouvelle section
        }
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=4, ensure_ascii=False)
        return config
    
    return load_server_config(guild_id)

def load_server_config(guild_id: str) -> Optional[dict]:
    """Charge la configuration d'un serveur"""
    config_path = f"{SERVERS_DIR}/{guild_id}.json"
    if os.path.exists(config_path):
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return None

def save_server_config(guild_id: str, config: dict):
    """Sauvegarde la configuration d'un serveur"""
    os.makedirs(SERVERS_DIR, exist_ok=True)
    config_path = f"{SERVERS_DIR}/{guild_id}.json"
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=4, ensure_ascii=False)

def check_channel_permission(interaction: discord.Interaction, command_name: str) -> bool:
    """Vérifie si la commande peut être exécutée dans ce salon"""
    guild_id = str(interaction.guild_id)
    channel_id = str(interaction.channel_id)
    
    config = load_server_config(guild_id)
    if not config:
        # Si pas de config, autoriser partout par défaut
        return True
    
    allowed_channels = config.get("channels", {}).get(command_name, [])
    
    # Si la liste est vide, autoriser partout
    if not allowed_channels:
        return True
    
    # Convertir tous les IDs en string pour la comparaison
    allowed_channels_str = [str(ch_id) for ch_id in allowed_channels]
    
    # Vérifier si le salon est dans la liste
    return channel_id in allowed_channels_str

def get_allowed_channel(guild_id: int, command_name: str, bot_instance=None) -> Optional[discord.TextChannel]:
    """
    Récupère le premier salon autorisé pour une commande donnée
    
    Args:
        guild_id: ID du serveur Discord (int)
        command_name: Nom de la commande (ex: "packs", "collection", "solde")
        bot_instance: Instance du bot (optionnel, sera importé si None)
    
    Returns:
        discord.TextChannel ou None si aucun salon configuré
    """
    config = load_server_config(str(guild_id))
    
    if not config:
        return None
    
    # Récupérer la liste des channel_ids autorisés pour cette commande
    channel_ids = config.get("channels", {}).get(command_name, [])
    
    if not channel_ids:
        return None
    
    # Utiliser le bot passé en paramètre ou essayer de l'importer
    bot = bot_instance
    if bot is None:
        try:
            import main
            bot = main.bot
        except (ImportError, AttributeError):
            return None
    
    if bot is None:
        return None
    
    # Récupérer le serveur
    guild = bot.get_guild(guild_id)
    if not guild:
        return None
    
    # Retourner le premier salon trouvé
    for channel_id in channel_ids:
        channel = guild.get_channel(int(channel_id))
        if channel and isinstance(channel, discord.TextChannel):
            return channel
    
    return None

def check_role_permission(interaction: discord.Interaction, permission_type: str) -> bool:
    """Vérifie si l'utilisateur a les permissions requises"""
    # TOUJOURS autoriser le propriétaire du bot
    if interaction.user.id == 878724920987766796:
        return True
    
    # Si c'est le propriétaire du serveur, toujours autoriser
    if interaction.user.id == interaction.guild.owner_id:
        return True
    
    guild_id = str(interaction.guild_id)
    config = load_server_config(guild_id)
    
    if not config:
        # Si pas de config, vérifier les permissions Discord natives
        if permission_type == "admin":
            return interaction.user.guild_permissions.administrator
        elif permission_type == "moderator":
            return interaction.user.guild_permissions.moderate_members or \
                   interaction.user.guild_permissions.administrator
    
    allowed_roles = config.get("roles", {}).get(permission_type, [])
    
    # Si la liste est vide, vérifier les permissions Discord natives
    if not allowed_roles:
        if permission_type == "admin":
            return interaction.user.guild_permissions.administrator
        elif permission_type == "moderator":
            return interaction.user.guild_permissions.moderate_members or \
                   interaction.user.guild_permissions.administrator
    
    # Vérifier si l'utilisateur a un des rôles autorisés
    user_role_ids = [str(role.id) for role in interaction.user.roles]
    has_role = any(role_id in allowed_roles for role_id in user_role_ids)
    
    # Toujours autoriser aussi si permissions Discord natives
    if not has_role:
        if permission_type == "admin":
            return interaction.user.guild_permissions.administrator
        elif permission_type == "moderator":
            return interaction.user.guild_permissions.moderate_members or \
                   interaction.user.guild_permissions.administrator
    
    return has_role

def add_channel_permission(guild_id: str, command_name: str, channel_id: str) -> bool:
    """Ajoute un salon autorisé pour une commande"""
    config = load_server_config(guild_id)
    if not config:
        return False
    
    if command_name not in config["channels"]:
        config["channels"][command_name] = []
    
    if channel_id not in config["channels"][command_name]:
        config["channels"][command_name].append(channel_id)
        save_server_config(guild_id, config)
        return True
    
    return False

def remove_channel_permission(guild_id: str, command_name: str, channel_id: str) -> bool:
    """Retire un salon autorisé pour une commande"""
    config = load_server_config(guild_id)
    if not config:
        return False
    
    if command_name in config["channels"] and channel_id in config["channels"][command_name]:
        config["channels"][command_name].remove(channel_id)
        save_server_config(guild_id, config)
        return True
    
    return False

def add_role_permission(guild_id: str, permission_type: str, role_id: str) -> bool:
    """Ajoute un rôle autorisé"""
    config = load_server_config(guild_id)
    if not config:
        return False
    
    if permission_type not in config["roles"]:
        config["roles"][permission_type] = []
    
    if role_id not in config["roles"][permission_type]:
        config["roles"][permission_type].append(role_id)
        save_server_config(guild_id, config)
        return True
    
    return False

def remove_role_permission(guild_id: str, permission_type: str, role_id: str) -> bool:
    """Retire un rôle autorisé"""
    config = load_server_config(guild_id)
    if not config:
        return False
    
    if permission_type in config["roles"] and role_id in config["roles"][permission_type]:
        config["roles"][permission_type].remove(role_id)
        save_server_config(guild_id, config)
        return True
    
    return False

def get_allowed_channels(guild_id: str, command_name: str) -> List[str]:
    """Récupère la liste des salons autorisés pour une commande"""
    config = load_server_config(guild_id)
    if not config:
        return []
    
    return config.get("channels", {}).get(command_name, [])

def get_allowed_roles(guild_id: str, permission_type: str) -> List[str]:
    """Récupère la liste des rôles autorisés pour un type de permission"""
    config = load_server_config(guild_id)
    if not config:
        return []
    
    return config.get("roles", {}).get(permission_type, [])


# ============================================
# ✅ FONCTIONS POUR LES SALONS SANS COINS
# ============================================

def get_no_coins_channels(guild_id: str) -> List[str]:
    """Récupère la liste des salons où les membres ne gagnent pas de coins"""
    config = load_server_config(guild_id)
    if not config:
        return []
    
    return config.get("no_coins_channels", [])


def add_no_coins_channel(guild_id: str, channel_id: str) -> bool:
    """Ajoute un salon à la liste des salons sans coins"""
    config = load_server_config(guild_id)
    if not config:
        return False
    
    if "no_coins_channels" not in config:
        config["no_coins_channels"] = []
    
    if channel_id not in config["no_coins_channels"]:
        config["no_coins_channels"].append(channel_id)
        save_server_config(guild_id, config)
        return True
    
    return False


def remove_no_coins_channel(guild_id: str, channel_id: str) -> bool:
    """Retire un salon de la liste des salons sans coins"""
    config = load_server_config(guild_id)
    if not config:
        return False
    
    if "no_coins_channels" in config and channel_id in config["no_coins_channels"]:
        config["no_coins_channels"].remove(channel_id)
        save_server_config(guild_id, config)
        return True
    
    return False


def is_coins_disabled_channel(guild_id: str, channel_id: str) -> bool:
    """Vérifie si un salon est dans la liste des salons sans coins"""
    no_coins_channels = get_no_coins_channels(guild_id)
    return str(channel_id) in no_coins_channels