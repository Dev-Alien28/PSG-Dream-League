# commands/give.py - Commande pour donner des cartes aux membres
import discord
import os
import json
from typing import Optional
from utils.database import get_user_data, save_user_data
from config.settings import PSG_BLUE, PSG_RED, PSG_GREEN, CARD_TYPES
from utils.permissions import check_role_permission

def get_card_image_file(card: dict) -> discord.File:
    """Récupère le fichier image de la carte depuis le chemin local"""
    image_path = card.get('image', '')
    
    if image_path.startswith('http://') or image_path.startswith('https://'):
        return None
    
    if image_path and os.path.exists(image_path):
        try:
            filename = os.path.basename(image_path)
            return discord.File(image_path, filename=filename)
        except Exception as e:
            print(f"❌ Erreur lecture image {image_path}: {e}")
            return None
    
    return None

def get_card_image_url(card: dict) -> str:
    """Récupère l'URL valide de l'image ou None"""
    image_path = card.get('image', '')
    
    if image_path and (image_path.startswith('http://') or image_path.startswith('https://')):
        if len(image_path) <= 2048:
            return image_path
    
    return None

def get_rarity_card_image(rarity: str) -> str:
    """Retourne une image optimisée selon la rareté"""
    rarity_images = {
        "Basic": "https://upload.wikimedia.org/wikipedia/fr/thumb/8/86/Paris_Saint-Germain_Logo.svg/1200px-Paris_Saint-Germain_Logo.svg.png",
        "Advanced": "https://upload.wikimedia.org/wikipedia/fr/thumb/8/86/Paris_Saint-Germain_Logo.svg/1200px-Paris_Saint-Germain_Logo.svg.png",
        "Elite": "https://upload.wikimedia.org/wikipedia/fr/thumb/8/86/Paris_Saint-Germain_Logo.svg/2048px-Paris_Saint-Germain_Logo.svg.png",
        "Unique": "https://upload.wikimedia.org/wikipedia/commons/4/43/PSG_logo_logotype.png",
        "Légendaire": "https://upload.wikimedia.org/wikipedia/commons/4/43/PSG_logo_logotype.png",
        "Legend": "https://upload.wikimedia.org/wikipedia/commons/4/43/PSG_logo_logotype.png"
    }
    
    return rarity_images.get(rarity, "https://upload.wikimedia.org/wikipedia/fr/thumb/8/86/Paris_Saint-Germain_Logo.svg/2048px-Paris_Saint-Germain_Logo.svg.png")

def get_rarity_color(rarity: str) -> int:
    """Retourne une couleur selon la rareté"""
    from config.settings import RARITIES, PSG_BLUE
    return RARITIES.get(rarity, {}).get("color", PSG_BLUE)

def get_rarity_emoji(rarity: str) -> str:
    """Retourne un emoji selon la rareté"""
    from config.settings import RARITIES
    return RARITIES.get(rarity, {}).get("emoji", "⚫")

def format_card_stats_compact(card: dict) -> str:
    """Formate les statistiques d'une carte de manière compacte"""
    stats = card.get('stats', {})
    card_type = card.get('type', 'joueur')
    
    if card_type == "joueur":
        position = card.get('position', 'Inconnu')
        stat_names = {
            "Attaquant": ["frappe", "technique", "contrôle"],
            "Milieu": ["technique", "intelligence", "contrôle"],
            "Défenseur": ["intelligence", "pression", "physique"],
            "Gardien": ["physique", "agilité", "arrêt"]
        }
        
        names = stat_names.get(position, ["stat1", "stat2", "stat3"])
        lines = [f"**Position:** {position}"]
        max_name_length = max(len(name) for name in names)
        
        for name in names:
            value = stats.get(name, 0)
            bar = create_stat_bar(value)
            padded_name = name.capitalize().ljust(max_name_length + 1)
            lines.append(f"`{padded_name}` {bar} `{value:>2}/100`")
        
        return "\n".join(lines)
    
    else:
        lines = []
        stat_items = list(stats.items())
        
        if stat_items:
            max_name_length = max(len(name) for name, _ in stat_items)
            
            for stat_name, stat_value in stat_items:
                if isinstance(stat_value, int) and stat_value <= 100:
                    bar = create_stat_bar(stat_value)
                    padded_name = stat_name.capitalize().ljust(max_name_length + 1)
                    lines.append(f"`{padded_name}` {bar} `{stat_value:>2}/100`")
                else:
                    lines.append(f"**{stat_name.capitalize()}:** {stat_value}")
        
        return "\n".join(lines) if lines else "Aucune statistique"

def create_stat_bar(value: int, max_value: int = 100) -> str:
    """Crée une barre de progression visuelle"""
    filled = int((value / max_value) * 10)
    empty = 10 - filled
    return "█" * filled + "░" * empty

def load_all_cards() -> dict:
    """Charge toutes les cartes disponibles depuis tous les fichiers JSON dans data/packs/"""
    all_cards = {}
    packs_dir = "data/packs"
    
    if not os.path.exists(packs_dir):
        print(f"❌ Le dossier {packs_dir} n'existe pas")
        return all_cards
    
    for filename in os.listdir(packs_dir):
        if filename.endswith('.json'):
            filepath = os.path.join(packs_dir, filename)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    cards = json.load(f)
                    for card in cards:
                        card_id = card.get('id')
                        if card_id:
                            all_cards[card_id] = card
            except Exception as e:
                print(f"❌ Erreur lors du chargement de {filepath}: {e}")
    
    return all_cards

def find_card_by_id(card_id: str) -> Optional[dict]:
    """Recherche une carte par son ID dans tous les packs"""
    all_cards = load_all_cards()
    return all_cards.get(card_id)

async def give_command(interaction: discord.Interaction, carte_id: str, membre: discord.Member, raison: Optional[str] = None):
    """Commande pour donner une carte à un membre"""
    
    # Vérifier les permissions admin
    if not check_role_permission(interaction, "admin"):
        embed = discord.Embed(
            title="❌ Permission refusée",
            description="Seuls les administrateurs peuvent utiliser cette commande.",
            color=PSG_RED
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return
    
    # Vérifier que le membre n'est pas un bot
    if membre.bot:
        embed = discord.Embed(
            title="❌ Erreur",
            description="Tu ne peux pas donner de cartes à un bot !",
            color=PSG_RED
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return
    
    # Rechercher la carte
    card = find_card_by_id(carte_id)
    
    if not card:
        embed = discord.Embed(
            title="❌ Carte introuvable",
            description=f"Aucune carte trouvée avec l'ID : `{carte_id}`\n\n"
                       f"Vérifie l'ID dans les fichiers JSON du dossier `data/packs/`",
            color=PSG_RED
        )
        embed.set_footer(text="Exemple d'ID valide : gk_donnarumma_basic")
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return
    
    guild_id = str(interaction.guild_id)
    user_id = str(membre.id)
    
    # Ajouter la carte à la collection du membre
    user_data = get_user_data(guild_id, user_id)
    user_data["collection"].append(card)
    save_user_data(guild_id, user_id, user_data)
    
    # Créer l'embed de confirmation pour l'admin
    admin_embed = discord.Embed(
        title="✅ Carte donnée avec succès !",
        description=f"Tu as donné la carte **{card['nom']}** à {membre.mention}",
        color=PSG_GREEN
    )
    
    if raison:
        admin_embed.add_field(name="📝 Raison", value=raison, inline=False)
    
    admin_embed.add_field(name="🎴 Carte", value=card['nom'], inline=True)
    admin_embed.add_field(name="🏆 Rareté", value=f"{get_rarity_emoji(card['rareté'])} {card['rareté']}", inline=True)
    admin_embed.add_field(name="👤 Bénéficiaire", value=membre.mention, inline=True)
    
    admin_embed.set_footer(
        text=f"Donné par {interaction.user.display_name} • {interaction.guild.name}",
        icon_url="https://upload.wikimedia.org/wikipedia/fr/thumb/8/86/Paris_Saint-Germain_Logo.svg/2048px-Paris_Saint-Germain_Logo.svg.png"
    )
    
    await interaction.response.send_message(embed=admin_embed, ephemeral=True)
    
    # Créer l'embed pour le membre qui reçoit la carte
    member_embed = discord.Embed(
        title="🎁 TU AS REÇU UNE CARTE !",
        description=f"# 🎴 {card['nom']}\n\nFélicitations ! Un administrateur t'a offert une carte exclusive !",
        color=get_rarity_color(card['rareté'])
    )
    
    # Type de carte
    type_emoji = CARD_TYPES.get(card.get('type', 'joueur'), {}).get("emoji", "🎴")
    member_embed.add_field(
        name=f"{type_emoji} Type", 
        value=card.get('type', 'joueur').capitalize(), 
        inline=True
    )
    
    # Rareté
    member_embed.add_field(
        name="🏆 Rareté",
        value=f"{get_rarity_emoji(card['rareté'])} {card['rareté']}",
        inline=True
    )
    
    # Espace vide pour alignement
    member_embed.add_field(name="\u200b", value="\u200b", inline=True)
    
    # Statistiques de la carte
    stats_text = format_card_stats_compact(card)
    member_embed.add_field(name="📊 Statistiques", value=stats_text, inline=False)
    
    # Raison si fournie
    if raison:
        member_embed.add_field(name="💬 Message", value=raison, inline=False)
    
    # Collection mise à jour
    member_embed.add_field(
        name="🎴 Ta collection", 
        value=f"{len(user_data['collection'])} cartes", 
        inline=True
    )
    
    member_embed.set_footer(
        text=f"Offert par {interaction.user.display_name} • Paris Saint-Germain",
        icon_url="https://upload.wikimedia.org/wikipedia/fr/thumb/8/86/Paris_Saint-Germain_Logo.svg/2048px-Paris_Saint-Germain_Logo.svg.png"
    )
    
    # GESTION IMAGES - Priorité : fichier local > URL > thumbnail
    image_file = get_card_image_file(card)
    
    try:
        if image_file:
            member_embed.set_image(url=f"attachment://{image_file.filename}")
            await membre.send(embed=member_embed, file=image_file)
        else:
            card_image_url = get_card_image_url(card)
            if card_image_url:
                member_embed.set_image(url=card_image_url)
            else:
                member_embed.set_thumbnail(url=get_rarity_card_image(card.get('rareté', 'Basic')))
            
            await membre.send(embed=member_embed)
    except discord.Forbidden:
        # Si on ne peut pas envoyer de DM au membre
        followup_embed = discord.Embed(
            title="⚠️ Message privé non envoyé",
            description=f"Je n'ai pas pu envoyer un message privé à {membre.mention}.\n"
                       f"La carte a bien été ajoutée à sa collection.",
            color=0xFFA500  # Orange
        )
        await interaction.followup.send(embed=followup_embed, ephemeral=True)
    except Exception as e:
        print(f"❌ Erreur lors de l'envoi du DM : {e}")
        followup_embed = discord.Embed(
            title="⚠️ Erreur d'envoi",
            description=f"Une erreur est survenue lors de l'envoi du message à {membre.mention}.\n"
                       f"La carte a bien été ajoutée à sa collection.",
            color=0xFFA500  # Orange
        )
        await interaction.followup.send(embed=followup_embed, ephemeral=True)