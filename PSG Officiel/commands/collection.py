# commands/collection.py - CORRIGÉ AVEC SÉPARATION PAR SERVEUR + PARAMÈTRE MEMBRE
import discord
import os
from typing import Optional
from utils.database import get_user_data, get_user_cards_grouped
from config.settings import PSG_BLUE, PSG_RED, CARD_TYPES
from utils.permissions import check_channel_permission, get_allowed_channel

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

def get_rarity_order(rarity: str) -> int:
    """Retourne l'ordre de tri pour les raretés (du plus rare au moins rare)"""
    order = {
        "Légendaire": 0,
        "Legend": 0,
        "Unique": 1,
        "Épique": 2,
        "Elite": 2,
        "Advanced": 3,
        "Basic": 4
    }
    return order.get(rarity, 999)

def organize_cards_by_rarity(cards_grouped: dict) -> list:
    """Organise les cartes par rareté et crée des pages"""
    cards_by_rarity = {}
    for card_id, card_data in cards_grouped.items():
        rarity = card_data["card"]["rareté"]
        if rarity not in cards_by_rarity:
            cards_by_rarity[rarity] = []
        cards_by_rarity[rarity].append((card_id, card_data))
    
    sorted_rarities = sorted(cards_by_rarity.keys(), key=get_rarity_order)
    
    pages = []
    cards_per_page = 10
    
    for rarity in sorted_rarities:
        rarity_cards = cards_by_rarity[rarity]
        
        for i in range(0, len(rarity_cards), cards_per_page):
            page_cards = rarity_cards[i:i + cards_per_page]
            pages.append({
                'rarity': rarity,
                'cards': page_cards,
                'is_continuation': i > 0
            })
    
    return pages

class CollectionView(discord.ui.View):
    """Vue pour naviguer dans la collection avec pagination par rareté"""
    
    def __init__(self, guild_id: str, user_id: str, user_name: str, cards_grouped: dict, viewer_id: str):
        super().__init__(timeout=180)
        self.guild_id = guild_id
        self.user_id = user_id
        self.user_name = user_name
        self.cards_grouped = cards_grouped
        self.viewer_id = viewer_id  # Qui regarde (pour les permissions)
        
        self.pages = organize_cards_by_rarity(cards_grouped)
        self.current_page = 0
        self.total_pages = len(self.pages)
        
        self.total_unique = len(cards_grouped)
        self.total_cards = sum(data["count"] for data in cards_grouped.values())
        
        self.update_buttons()
        self.update_select_menu()
    
    def get_current_page_data(self):
        """Retourne les données de la page actuelle"""
        if 0 <= self.current_page < len(self.pages):
            return self.pages[self.current_page]
        return None
    
    def update_buttons(self):
        """Met à jour l'état des boutons de navigation"""
        self.previous_button.disabled = self.current_page == 0
        self.next_button.disabled = self.current_page >= self.total_pages - 1
    
    def update_select_menu(self):
        """Met à jour le menu de sélection avec les cartes de la page actuelle"""
        for item in self.children[:]:
            if isinstance(item, discord.ui.Select):
                self.remove_item(item)
        
        page_data = self.get_current_page_data()
        if not page_data:
            return
        
        current_cards = page_data['cards']
        rarity = page_data['rarity']
        
        options = []
        for card_id, card_data in current_cards:
            card = card_data["card"]
            count = card_data["count"]
            
            type_emoji = CARD_TYPES.get(card['type'], {}).get("emoji", "🎴")
            
            label = f"{card['nom']} x{count}"
            if len(label) > 100:
                label = label[:97] + "..."
            
            description = f"{type_emoji} {card['type'].capitalize()} - {card['rareté']}"
            if len(description) > 100:
                description = description[:97] + "..."
            
            options.append(
                discord.SelectOption(
                    label=label,
                    description=description,
                    value=card_id,
                    emoji=get_rarity_emoji(card['rareté'])
                )
            )
        
        select = discord.ui.Select(
            placeholder=f"🎴 {rarity} - Page {self.current_page + 1}/{self.total_pages}",
            options=options,
            row=0
        )
        select.callback = self.select_callback
        self.add_item(select)
    
    async def select_callback(self, interaction: discord.Interaction):
        """Callback quand une carte est sélectionnée"""
        # Tout le monde peut voir les détails
        card_id = interaction.data['values'][0]
        card_data = self.cards_grouped[card_id]
        card = card_data["card"]
        count = card_data["count"]
        
        embed = discord.Embed(
            title=f"🎴 {card['nom']}",
            description=f"Carte {card['type']} de {self.user_name}",
            color=get_rarity_color(card['rareté'])
        )
        
        type_emoji = CARD_TYPES.get(card['type'], {}).get("emoji", "🎴")
        embed.add_field(name=f"{type_emoji} Type", value=card['type'].capitalize(), inline=True)
        embed.add_field(name="🏆 Rareté", value=f"{get_rarity_emoji(card['rareté'])} {card['rareté']}", inline=True)
        embed.add_field(name="📦 Exemplaires", value=f"x{count}", inline=True)
        
        stats_text = format_card_stats(card)
        embed.add_field(name="📊 Statistiques", value=stats_text, inline=False)
        
        embed.set_footer(
            text="Paris Saint-Germain • Ici c'est Paris",
            icon_url="https://upload.wikimedia.org/wikipedia/fr/thumb/8/86/Paris_Saint-Germain_Logo.svg/2048px-Paris_Saint-Germain_Logo.svg.png"
        )
        
        image_file = get_card_image_file(card)
        
        if image_file:
            embed.set_image(url=f"attachment://{image_file.filename}")
            await interaction.response.send_message(embed=embed, file=image_file, ephemeral=True)
        else:
            card_image_url = get_card_image_url(card)
            if card_image_url:
                embed.set_image(url=card_image_url)
            else:
                embed.set_thumbnail(url=get_rarity_card_image(card.get('rareté', 'Basic')))
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @discord.ui.button(label="◀️ Précédent", style=discord.ButtonStyle.primary, row=1)
    async def previous_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if str(interaction.user.id) != self.viewer_id:
            await interaction.response.send_message(
                "❌ Ce n'est pas ta vue!",
                ephemeral=True
            )
            return
        
        self.current_page -= 1
        self.update_buttons()
        self.update_select_menu()
        
        embed = create_collection_embed(
            self.user_name,
            self.get_current_page_data(),
            self.current_page + 1,
            self.total_pages,
            self.total_unique,
            self.total_cards
        )
        await interaction.response.edit_message(embed=embed, view=self)
    
    @discord.ui.button(label="Suivant ▶️", style=discord.ButtonStyle.primary, row=1)
    async def next_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if str(interaction.user.id) != self.viewer_id:
            await interaction.response.send_message(
                "❌ Ce n'est pas ta vue!",
                ephemeral=True
            )
            return
        
        self.current_page += 1
        self.update_buttons()
        self.update_select_menu()
        
        embed = create_collection_embed(
            self.user_name,
            self.get_current_page_data(),
            self.current_page + 1,
            self.total_pages,
            self.total_unique,
            self.total_cards
        )
        await interaction.response.edit_message(embed=embed, view=self)
    
    @discord.ui.button(label="🔄 Actualiser", style=discord.ButtonStyle.secondary, row=1)
    async def refresh_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if str(interaction.user.id) != self.viewer_id:
            await interaction.response.send_message(
                "❌ Ce n'est pas ta vue!",
                ephemeral=True
            )
            return
        
        # Recharger les cartes
        cards_grouped = get_user_cards_grouped(self.guild_id, self.user_id)
        self.cards_grouped = cards_grouped
        self.pages = organize_cards_by_rarity(cards_grouped)
        self.total_pages = len(self.pages)
        self.total_unique = len(cards_grouped)
        self.total_cards = sum(data["count"] for data in cards_grouped.values())
        
        if self.current_page >= self.total_pages:
            self.current_page = max(0, self.total_pages - 1)
        
        self.update_buttons()
        self.update_select_menu()
        
        embed = create_collection_embed(
            self.user_name,
            self.get_current_page_data(),
            self.current_page + 1,
            self.total_pages,
            self.total_unique,
            self.total_cards
        )
        await interaction.response.edit_message(embed=embed, view=self)

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

def format_card_stats(card: dict) -> str:
    """Formate les statistiques d'une carte selon son type"""
    return format_card_stats_compact(card)

def create_stat_bar(value: int, max_value: int = 100) -> str:
    """Crée une barre de progression visuelle"""
    filled = int((value / max_value) * 10)
    empty = 10 - filled
    return "█" * filled + "░" * empty

def create_collection_embed(user_name: str, page_data: dict, current_page: int, total_pages: int, unique_cards: int, total_cards: int) -> discord.Embed:
    """Crée l'embed pour afficher la collection avec pagination par rareté"""
    embed = discord.Embed(
        title=f"📋 Collection de {user_name}",
        description=f"🎴 Total: {total_cards} carte(s)\n"
                    f"✨ Cartes uniques: {unique_cards}\n"
                    f"📄 Page: {current_page}/{total_pages}",
        color=PSG_BLUE
    )
    
    if not page_data or not page_data['cards']:
        embed.add_field(
            name="🔭 Collection vide",
            value="Achète des packs avec `/packs` pour commencer ta collection !",
            inline=False
        )
        embed.set_footer(text="Paris Saint-Germain • Ici c'est Paris")
        return embed
    
    rarity = page_data['rarity']
    cards = page_data['cards']
    is_continuation = page_data['is_continuation']
    
    rarity_emoji = get_rarity_emoji(rarity)
    section_title = f"{rarity_emoji}  {rarity}"
    if is_continuation:
        section_title += " (suite)"
    
    card_lines = []
    for card_id, card_data in cards:
        card = card_data["card"]
        count = card_data["count"]
        type_emoji = CARD_TYPES.get(card['type'], {}).get("emoji", "🎴")
        card_lines.append(f"{type_emoji} {card['nom']} x{count}")
    
    embed.add_field(
        name=section_title,
        value="\n".join(card_lines),
        inline=False
    )
    
    embed.set_footer(
        text="Sélectionne une carte pour voir ses détails • Paris Saint-Germain",
        icon_url="https://upload.wikimedia.org/wikipedia/fr/thumb/8/86/Paris_Saint-Germain_Logo.svg/2048px-Paris_Saint-Germain_Logo.svg.png"
    )
    return embed

def get_rarity_color(rarity: str) -> int:
    """Retourne une couleur selon la rareté"""
    from config.settings import RARITIES, PSG_BLUE
    return RARITIES.get(rarity, {}).get("color", PSG_BLUE)

def get_rarity_emoji(rarity: str) -> str:
    """Retourne un emoji selon la rareté"""
    from config.settings import RARITIES
    return RARITIES.get(rarity, {}).get("emoji", "⚫")

async def collection_command(interaction: discord.Interaction, membre: Optional[discord.Member] = None):
    """Affiche la collection d'un utilisateur (soi-même ou un autre membre)"""
    if not check_channel_permission(interaction, "collection"):
        allowed_channel = get_allowed_channel(interaction.guild.id, "collection", interaction.client)
        
        embed = discord.Embed(
            title="❌ Salon non autorisé",
            color=PSG_RED
        )
        
        if allowed_channel:
            embed.description = (
                f"Cette commande ne peut pas être utilisée dans ce salon.\n\n"
                f"➡️ **Utilise plutôt:** {allowed_channel.mention}"
            )
        else:
            embed.description = (
                "Cette commande ne peut pas être utilisée dans ce salon.\n\n"
                "Aucun salon n'est configuré pour cette commande.\n"
                "Contacte un administrateur pour configurer les salons avec `/config`."
            )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return
    
    # ✅ CORRECTION: Ajouter guild_id
    guild_id = str(interaction.guild_id)
    
    # ✅ NOUVEAU: Supporter le paramètre membre
    if membre is None:
        # Voir sa propre collection
        target_user = interaction.user
    else:
        # Voir la collection d'un autre membre
        target_user = membre
    
    user_id = str(target_user.id)
    viewer_id = str(interaction.user.id)
    
    user_data = get_user_data(guild_id, user_id)
    cards_grouped = get_user_cards_grouped(guild_id, user_id)
    
    if not cards_grouped:
        embed = discord.Embed(
            title=f"📋 Collection de {target_user.display_name}",
            description="🔭 Cette collection est vide!\n\n"
                        "Utilise `/packs` pour découvrir les packs disponibles et commencer ta collection!",
            color=PSG_BLUE
        )
        embed.set_footer(
            text=f"Paris Saint-Germain • {interaction.guild.name}",
            icon_url="https://upload.wikimedia.org/wikipedia/fr/thumb/8/86/Paris_Saint-Germain_Logo.svg/2048px-Paris_Saint-Germain_Logo.svg.png"
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return
    
    view = CollectionView(guild_id, user_id, target_user.display_name, cards_grouped, viewer_id)
    
    embed = create_collection_embed(
        target_user.display_name,
        view.get_current_page_data(),
        1,
        view.total_pages,
        view.total_unique,
        view.total_cards
    )
    
    await interaction.response.send_message(embed=embed, view=view, ephemeral=True)