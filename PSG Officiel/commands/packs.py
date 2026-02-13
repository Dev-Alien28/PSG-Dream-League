# commands/packs.py - CORRIGÉ AVEC ESPACEMENT AMÉLIORÉ
import discord
import random
import os
from utils.database import (
    get_user_data, save_user_data, load_pack_cards,
    can_claim_free_pack, claim_free_pack, get_free_pack_cooldown
)
from config.settings import PSG_BLUE, PSG_RED, PACKS_CONFIG, CARD_TYPES

class PacksView(discord.ui.View):
    """Vue avec boutons pour acheter les packs - Expire après 1 minute"""
    
    def __init__(self, guild_id: str, user_id: str):
        super().__init__(timeout=60)
        self.guild_id = guild_id
        self.user_id = user_id
        self.message = None
        
        for pack_key, pack_info in PACKS_CONFIG.items():
            if pack_key == "pack_event":
                continue
            
            if pack_key == "free_pack":
                style = discord.ButtonStyle.success
            elif pack_info['prix'] == 0:
                style = discord.ButtonStyle.secondary
            else:
                style = discord.ButtonStyle.primary
            
            button = discord.ui.Button(
                label=f"{pack_info['emoji']} {pack_info['nom']} - {pack_info['prix']} 🪙",
                style=style,
                custom_id=pack_key
            )
            button.callback = self.create_callback(pack_key)
            self.add_item(button)
    
    def create_callback(self, pack_key: str):
        async def callback(interaction: discord.Interaction):
            if str(interaction.user.id) != self.user_id:
                await interaction.response.send_message(
                    "❌ Tu ne peux pas utiliser cette boutique !\n\n"
                    "Utilise `/packs` pour ouvrir ta propre boutique.",
                    ephemeral=True
                )
                return
            
            await buy_pack(interaction, pack_key)
        
        return callback
    
    async def on_timeout(self):
        if self.message:
            try:
                await self.message.delete()
            except:
                pass


async def packs_command(interaction: discord.Interaction):
    """Affiche la boutique de packs avec vérification des permissions de salon"""
    from utils.permissions import check_channel_permission, get_allowed_channel
    
    if not check_channel_permission(interaction, "packs"):
        allowed_channel = get_allowed_channel(interaction.guild.id, "packs", interaction.client)
        
        embed = discord.Embed(
            title="❌ Salon non autorisé",
            color=PSG_RED
        )
        
        if allowed_channel:
            embed.description = (
                f"Cette commande ne peut pas être utilisée dans ce salon.\n\n"
                f"➡️ **Utilise plutôt :** {allowed_channel.mention}"
            )
        else:
            embed.description = (
                "Cette commande ne peut pas être utilisée dans ce salon.\n\n"
                "Aucun salon n'est configuré pour cette commande.\n"
                "Contacte un administrateur pour configurer les salons avec `/config`."
            )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return
    
    guild_id = str(interaction.guild_id)
    user_id = str(interaction.user.id)
    
    user_data = get_user_data(guild_id, user_id)
    
    embed = discord.Embed(
        title="🎁 BOUTIQUE PSG - PACKS DISPONIBLES",
        description=(
            "Clique sur un bouton ci-dessous pour acheter un pack !\n"
            "Chaque pack contient **1 carte exclusive** avec des taux de drop différents.\n"
            "\u200b"  # Espace invisible pour séparer
        ),
        color=PSG_BLUE
    )
    
    # Image locale attachée
    embed.set_image(url="attachment://Boite.png")
    
    # ✅ Mise en page aérée avec espaces entre les packs
    pack_items = [(k, v) for k, v in PACKS_CONFIG.items() if k != "pack_event"]
    
    for i, (pack_key, pack_info) in enumerate(pack_items):
        extra_info = ""
        if pack_key == "free_pack":
            if can_claim_free_pack(guild_id, user_id):
                extra_info = "\n✅ **Disponible maintenant !**"
            else:
                cooldown = get_free_pack_cooldown(guild_id, user_id)
                hours = cooldown // 3600
                minutes = (cooldown % 3600) // 60
                extra_info = f"\n⏰ Disponible dans **{hours}h{minutes:02d}m**"
        
        # Format avec saut de ligne pour aérer
        value = f"{pack_info['description']}{extra_info}"
        
        # Ajouter un espace visuel entre les packs (sauf pour le dernier)
        if i < len(pack_items) - 1:
            value += "\n\u200b"  # Caractère invisible pour créer un espace
        
        embed.add_field(
            name=f"{pack_info['emoji']} **{pack_info['nom']}**",
            value=value,
            inline=False
        )
    
    embed.set_footer(
        text=f"Ton solde : {user_data['coins']} PSG Coins • {interaction.guild.name} • Expire dans 1 min",
        icon_url="https://upload.wikimedia.org/wikipedia/fr/thumb/8/86/Paris_Saint-Germain_Logo.svg/2048px-Paris_Saint-Germain_Logo.svg.png"
    )
    
    view = PacksView(guild_id, user_id)
    
    # Charger et attacher l'image locale
    image_path = "images/Boite.png"
    if os.path.exists(image_path):
        image_file = discord.File(image_path, filename="Boite.png")
        await interaction.response.send_message(embed=embed, view=view, file=image_file)
    else:
        # Si l'image n'existe pas, envoyer sans image
        await interaction.response.send_message(embed=embed, view=view)
    
    view.message = await interaction.original_response()


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


async def buy_pack(interaction: discord.Interaction, pack_key: str):
    """Fonction pour acheter un pack avec système de taux de drop"""
    guild_id = str(interaction.guild_id)
    user_id = str(interaction.user.id)
    
    user_data = get_user_data(guild_id, user_id)
    pack_info = PACKS_CONFIG[pack_key]
    user_coins = user_data["coins"]
    
    # Gestion du pack gratuit
    if pack_key == "free_pack":
        if not can_claim_free_pack(guild_id, user_id):
            cooldown = get_free_pack_cooldown(guild_id, user_id)
            hours = cooldown // 3600
            minutes = (cooldown % 3600) // 60
            
            embed = discord.Embed(
                title="⏰ Pack gratuit indisponible",
                description=f"Tu as déjà réclamé ton pack gratuit !\n\n"
                           f"**Prochain pack dans :** {hours}h {minutes}m",
                color=PSG_RED
            )
            embed.set_footer(text="Le pack gratuit se recharge toutes les 24 heures")
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        claim_free_pack(guild_id, user_id)
        user_data = get_user_data(guild_id, user_id)
    
    # Vérifier si le joueur a assez de coins
    elif user_coins < pack_info["prix"]:
        embed = discord.Embed(
            title="❌ Solde insuffisant",
            description=f"Tu n'as pas assez de PSG Coins pour acheter ce pack !",
            color=PSG_RED
        )
        embed.add_field(name="💰 Prix du pack", value=f"{pack_info['prix']} 🪙", inline=True)
        embed.add_field(name="💎 Ton solde", value=f"{user_coins} 🪙", inline=True)
        embed.add_field(name="❗ Il te manque", value=f"{pack_info['prix'] - user_coins} 🪙", inline=True)
        embed.set_footer(text="Contacte un administrateur pour obtenir des PSG Coins !")
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return
    
    # Charger les cartes du pack
    all_cards = load_pack_cards(pack_key)
    if not all_cards:
        embed = discord.Embed(
            title="❌ Erreur",
            description=f"Aucune carte disponible dans ce pack.\n\nContacte un administrateur.",
            color=PSG_RED
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return
    
    # Système de drop selon les taux
    drop_rates = pack_info['drop_rates']
    rarities = list(drop_rates.keys())
    weights = list(drop_rates.values())
    chosen_rarity = random.choices(rarities, weights=weights, k=1)[0]
    
    # Choisir une carte de la rareté obtenue
    cards_of_rarity = [card for card in all_cards if card.get('rareté') == chosen_rarity]
    card = random.choice(cards_of_rarity) if cards_of_rarity else random.choice(all_cards)
    
    # Déduire les coins (sauf pour le pack gratuit)
    if pack_key != "free_pack":
        user_data["coins"] -= pack_info["prix"]
    
    # Ajouter la carte à la collection
    user_data["collection"].append(card)
    save_user_data(guild_id, user_id, user_data)
    
    # Créer l'embed de résultat
    embed = discord.Embed(
        title=f"🎁 {pack_info['emoji']} {pack_info['nom']} ouvert !",
        description=f"# 🎴 {card['nom']}",
        color=get_rarity_color(card['rareté'])
    )
    
    # Type de carte
    type_emoji = CARD_TYPES.get(card.get('type', 'joueur'), {}).get("emoji", "🎴")
    embed.add_field(
        name=f"{type_emoji} Type", 
        value=card.get('type', 'joueur').capitalize(), 
        inline=True
    )
    
    # Chance de drop
    embed.add_field(
        name="🎲 Chance de drop",
        value=f"{drop_rates.get(card['rareté'], '?')}%",
        inline=True
    )
    
    # Espace vide pour alignement
    embed.add_field(name="\u200b", value="\u200b", inline=True)
    
    # Statistiques de la carte
    from commands.collection import format_card_stats_compact
    stats_text = format_card_stats_compact(card)
    embed.add_field(name="📊 Statistiques", value=stats_text, inline=False)
    
    # Nouveau solde et collection
    embed.add_field(
        name="💰 Nouveau solde", 
        value=f"{user_data['coins']} 🪙", 
        inline=True
    )
    embed.add_field(
        name="🎴 Collection", 
        value=f"{len(user_data['collection'])} cartes", 
        inline=True
    )
    
    embed.set_footer(
        text=f"Paris Saint-Germain • {interaction.guild.name}",
        icon_url="https://upload.wikimedia.org/wikipedia/fr/thumb/8/86/Paris_Saint-Germain_Logo.svg/2048px-Paris_Saint-Germain_Logo.svg.png"
    )
    
    # GESTION IMAGES - Priorité : fichier local > URL > thumbnail
    image_file = get_card_image_file(card)
    
    if image_file:
        embed.set_image(url=f"attachment://{image_file.filename}")
        await interaction.response.send_message(embed=embed, file=image_file)
    else:
        card_image_url = get_card_image_url(card)
        if card_image_url:
            embed.set_image(url=card_image_url)
        else:
            embed.set_thumbnail(url=get_rarity_card_image(card.get('rareté', 'Basic')))
        
        await interaction.response.send_message(embed=embed)


def get_rarity_color(rarity: str) -> int:
    """Retourne une couleur selon la rareté"""
    from config.settings import RARITIES, PSG_BLUE
    return RARITIES.get(rarity, {}).get("color", PSG_BLUE)


def get_rarity_emoji(rarity: str) -> str:
    """Retourne un emoji selon la rareté"""
    from config.settings import RARITIES
    return RARITIES.get(rarity, {}).get("emoji", "⚫")