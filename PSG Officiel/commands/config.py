# commands/config.py - VERSION INTERACTIVE SIMPLIFIÉE
import discord
from discord import app_commands
from discord.ui import View, Button, Select
from utils.permissions import (
    add_channel_permission, 
    remove_channel_permission,
    add_role_permission,
    remove_role_permission,
    load_server_config,
    save_server_config,
    get_allowed_channels,
    get_allowed_roles
)
from config.settings import PSG_BLUE, PSG_RED

OWNER_ID = 878724920987766796

# ==================== VIEWS ET COMPOSANTS ====================

class ConfigMainView(View):
    """Vue principale de configuration"""
    def __init__(self, interaction: discord.Interaction):
        super().__init__(timeout=300)  # 5 minutes
        self.interaction = interaction
        self.guild_id = str(interaction.guild_id)
    
    @discord.ui.button(label="📺 Salons de Commandes", style=discord.ButtonStyle.primary, row=0)
    async def config_channels(self, interaction: discord.Interaction, button: Button):
        await interaction.response.edit_message(
            embed=self.create_channels_embed(),
            view=ConfigChannelsView(self.interaction)
        )
    
    @discord.ui.button(label="👑 Rôles Administrateurs", style=discord.ButtonStyle.primary, row=0)
    async def config_roles(self, interaction: discord.Interaction, button: Button):
        await interaction.response.edit_message(
            embed=self.create_roles_embed(),
            view=ConfigRolesView(self.interaction)
        )
    
    @discord.ui.button(label="📋 Salon de Logs", style=discord.ButtonStyle.primary, row=1)
    async def config_logs(self, interaction: discord.Interaction, button: Button):
        await interaction.response.edit_message(
            embed=self.create_logs_embed(),
            view=ConfigLogsView(self.interaction)
        )
    
    @discord.ui.button(label="📊 Voir Configuration Complète", style=discord.ButtonStyle.success, row=1)
    async def view_config(self, interaction: discord.Interaction, button: Button):
        embed = await create_full_config_embed(self.interaction)
        await interaction.response.edit_message(embed=embed, view=ConfigMainView(self.interaction))
    
    @discord.ui.button(label="❌ Fermer", style=discord.ButtonStyle.danger, row=2)
    async def close_config(self, interaction: discord.Interaction, button: Button):
        embed = discord.Embed(
            title="✅ Configuration terminée",
            description="Tu peux utiliser `/config` à tout moment pour modifier la configuration.",
            color=PSG_BLUE
        )
        await interaction.response.edit_message(embed=embed, view=None)
    
    def create_channels_embed(self):
        embed = discord.Embed(
            title="📺 Configuration des Salons de Commandes",
            description="Configure les salons autorisés pour chaque commande.\n"
                       "Si aucun salon n'est configuré, la commande sera disponible partout.",
            color=PSG_BLUE
        )
        
        # Afficher les salons actuellement configurés
        for cmd in ["solde", "packs", "collection", "minigame"]:
            channels = get_allowed_channels(self.guild_id, cmd)
            if channels:
                channels_list = []
                for ch_id in channels:
                    channel = self.interaction.guild.get_channel(int(ch_id))
                    if channel:
                        channels_list.append(channel.mention)
                
                if channels_list:
                    embed.add_field(
                        name=f"/{cmd}",
                        value="\n".join(channels_list),
                        inline=True
                    )
            else:
                embed.add_field(
                    name=f"/{cmd}",
                    value="Partout ✅",
                    inline=True
                )
        
        embed.set_footer(text="Sélectionne une action ci-dessous")
        return embed
    
    def create_roles_embed(self):
        embed = discord.Embed(
            title="👑 Configuration des Rôles Administrateurs",
            description="Configure les rôles **du serveur** qui pourront utiliser les commandes admin.\n"
                       "Si aucun rôle n'est configuré, seules les permissions Discord natives seront utilisées.",
            color=PSG_BLUE
        )
        
        admin_roles = get_allowed_roles(self.guild_id, "admin")
        if admin_roles:
            roles_list = []
            for r_id in admin_roles:
                role = self.interaction.guild.get_role(int(r_id))
                if role:
                    roles_list.append(role.mention)
            
            embed.add_field(
                name="Rôles Admin actuels",
                value="\n".join(roles_list) if roles_list else "Aucun",
                inline=False
            )
        else:
            embed.add_field(
                name="Rôles Admin actuels",
                value="Permissions Discord natives 🔧",
                inline=False
            )
        
        embed.set_footer(text="Sélectionne un rôle du serveur ci-dessous")
        return embed
    
    def create_logs_embed(self):
        embed = discord.Embed(
            title="📋 Configuration du Salon de Logs",
            description="Configure le salon qui recevra tous les logs du serveur.",
            color=PSG_BLUE
        )
        
        config = load_server_config(self.guild_id)
        logs_channel_id = config.get("logs_channel") if config else None
        
        if logs_channel_id:
            logs_channel = self.interaction.guild.get_channel(int(logs_channel_id))
            if logs_channel:
                embed.add_field(
                    name="Salon de logs actuel",
                    value=logs_channel.mention,
                    inline=False
                )
        else:
            embed.add_field(
                name="Salon de logs actuel",
                value="Non configuré ❌",
                inline=False
            )
        
        embed.set_footer(text="Sélectionne une action ci-dessous")
        return embed


class ConfigChannelsView(View):
    """Vue pour configurer les salons de commandes"""
    def __init__(self, interaction: discord.Interaction):
        super().__init__(timeout=300)
        self.interaction = interaction
        self.guild_id = str(interaction.guild_id)
        
        # Menu déroulant pour choisir la commande
        self.command_select = Select(
            placeholder="Choisis une commande à configurer",
            options=[
                discord.SelectOption(label="Solde", value="solde", emoji="💰"),
                discord.SelectOption(label="Packs", value="packs", emoji="📦"),
                discord.SelectOption(label="Collection", value="collection", emoji="🎴"),
                discord.SelectOption(label="Mini-jeu", value="minigame", emoji="⚡"),
            ]
        )
        self.command_select.callback = self.command_selected
        self.add_item(self.command_select)
    
    async def command_selected(self, interaction: discord.Interaction):
        command = self.command_select.values[0]
        await interaction.response.edit_message(
            embed=self.create_command_config_embed(command),
            view=ConfigChannelActionView(self.interaction, command)
        )
    
    def create_command_config_embed(self, command: str):
        embed = discord.Embed(
            title=f"Configuration de /{command}",
            description="Ajoute ou retire des salons autorisés.",
            color=PSG_BLUE
        )
        
        channels = get_allowed_channels(self.guild_id, command)
        if channels:
            channels_list = []
            for ch_id in channels:
                channel = self.interaction.guild.get_channel(int(ch_id))
                if channel:
                    channels_list.append(f"• {channel.mention}")
            
            if channels_list:
                embed.add_field(
                    name="Salons autorisés actuels",
                    value="\n".join(channels_list),
                    inline=False
                )
        else:
            embed.add_field(
                name="Salons autorisés actuels",
                value="Disponible partout ✅",
                inline=False
            )
        
        return embed
    
    @discord.ui.button(label="⬅️ Retour", style=discord.ButtonStyle.secondary, row=2)
    async def back_to_main(self, interaction: discord.Interaction, button: Button):
        main_view = ConfigMainView(self.interaction)
        await interaction.response.edit_message(
            embed=create_main_embed(self.interaction),
            view=main_view
        )


class ConfigChannelActionView(View):
    """Vue pour ajouter/retirer un salon pour une commande"""
    def __init__(self, interaction: discord.Interaction, command: str):
        super().__init__(timeout=300)
        self.interaction = interaction
        self.guild_id = str(interaction.guild_id)
        self.command = command
        
        # Menu pour sélectionner un salon à ajouter
        channels = [ch for ch in interaction.guild.text_channels if ch.permissions_for(interaction.guild.me).send_messages]
        
        if len(channels) <= 25:  # Limite Discord
            add_options = [
                discord.SelectOption(
                    label=f"#{ch.name}"[:100],
                    value=str(ch.id),
                    description=ch.category.name if ch.category else "Pas de catégorie"
                )
                for ch in channels[:25]
            ]
            
            self.add_channel_select = Select(
                placeholder="Ajouter un salon autorisé",
                options=add_options,
                row=0
            )
            self.add_channel_select.callback = self.add_channel
            self.add_item(self.add_channel_select)
        
        # Menu pour sélectionner un salon à retirer
        allowed = get_allowed_channels(self.guild_id, command)
        if allowed:
            remove_options = []
            for ch_id in allowed[:25]:
                channel = interaction.guild.get_channel(int(ch_id))
                if channel:
                    remove_options.append(
                        discord.SelectOption(
                            label=f"#{channel.name}"[:100],
                            value=str(channel.id)
                        )
                    )
            
            if remove_options:
                self.remove_channel_select = Select(
                    placeholder="Retirer un salon autorisé",
                    options=remove_options,
                    row=1
                )
                self.remove_channel_select.callback = self.remove_channel
                self.add_item(self.remove_channel_select)
    
    async def add_channel(self, interaction: discord.Interaction):
        channel_id = self.add_channel_select.values[0]
        channel = interaction.guild.get_channel(int(channel_id))
        
        if not channel:
            await interaction.response.send_message("❌ Salon introuvable!", ephemeral=True)
            return
        
        # Vérifier si déjà autorisé
        allowed = get_allowed_channels(self.guild_id, self.command)
        if channel_id in allowed:
            await interaction.response.send_message(
                f"⚠️ {channel.mention} est déjà autorisé pour `/{self.command}`",
                ephemeral=True
            )
            return
        
        # Ajouter le salon
        add_channel_permission(self.guild_id, self.command, channel_id)
        
        embed = discord.Embed(
            title="✅ Salon ajouté",
            description=f"{channel.mention} est maintenant autorisé pour `/{self.command}`",
            color=PSG_BLUE
        )
        
        # Afficher tous les salons
        all_allowed = get_allowed_channels(self.guild_id, self.command)
        channels_list = []
        for ch_id in all_allowed:
            ch = interaction.guild.get_channel(int(ch_id))
            if ch:
                channels_list.append(f"• {ch.mention}")
        
        if channels_list:
            embed.add_field(
                name=f"Tous les salons pour /{self.command}",
                value="\n".join(channels_list),
                inline=False
            )
        
        await interaction.response.edit_message(
            embed=embed,
            view=ConfigChannelActionView(self.interaction, self.command)
        )
    
    async def remove_channel(self, interaction: discord.Interaction):
        channel_id = self.remove_channel_select.values[0]
        channel = interaction.guild.get_channel(int(channel_id))
        
        # Retirer le salon
        success = remove_channel_permission(self.guild_id, self.command, channel_id)
        
        if not success:
            await interaction.response.send_message("❌ Erreur lors de la suppression", ephemeral=True)
            return
        
        embed = discord.Embed(
            title="✅ Salon retiré",
            description=f"{channel.mention if channel else 'Le salon'} n'est plus autorisé pour `/{self.command}`",
            color=PSG_BLUE
        )
        
        # Afficher les salons restants
        all_allowed = get_allowed_channels(self.guild_id, self.command)
        if all_allowed:
            channels_list = []
            for ch_id in all_allowed:
                ch = interaction.guild.get_channel(int(ch_id))
                if ch:
                    channels_list.append(f"• {ch.mention}")
            
            if channels_list:
                embed.add_field(
                    name=f"Salons restants pour /{self.command}",
                    value="\n".join(channels_list),
                    inline=False
                )
        else:
            embed.add_field(
                name="ℹ️ Info",
                value="Plus aucun salon spécifique. La commande est disponible partout.",
                inline=False
            )
        
        await interaction.response.edit_message(
            embed=embed,
            view=ConfigChannelActionView(self.interaction, self.command)
        )
    
    @discord.ui.button(label="⬅️ Retour", style=discord.ButtonStyle.secondary, row=2)
    async def back_to_channels(self, interaction: discord.Interaction, button: Button):
        # CORRECTION: Créer l'embed depuis ConfigMainView
        main_view = ConfigMainView(self.interaction)
        view = ConfigChannelsView(self.interaction)
        await interaction.response.edit_message(
            embed=main_view.create_channels_embed(),
            view=view
        )


class ConfigRolesView(View):
    """Vue pour configurer les rôles admin"""
    def __init__(self, interaction: discord.Interaction):
        super().__init__(timeout=300)
        self.interaction = interaction
        self.guild_id = str(interaction.guild_id)
        
        # Menu pour ajouter un rôle (rôles RÉELS du serveur)
        roles = [r for r in interaction.guild.roles if r.name != "@everyone"]
        
        if len(roles) <= 25:
            add_options = [
                discord.SelectOption(
                    label=role.name[:100],
                    value=str(role.id),
                    emoji="👑"
                )
                for role in roles[:25]
            ]
            
            self.add_role_select = Select(
                placeholder="Ajouter un rôle admin (rôles du serveur)",
                options=add_options,
                row=0
            )
            self.add_role_select.callback = self.add_role
            self.add_item(self.add_role_select)
        
        # Menu pour retirer un rôle
        allowed = get_allowed_roles(self.guild_id, "admin")
        if allowed:
            remove_options = []
            for r_id in allowed[:25]:
                role = interaction.guild.get_role(int(r_id))
                if role:
                    remove_options.append(
                        discord.SelectOption(
                            label=role.name[:100],
                            value=str(role.id)
                        )
                    )
            
            if remove_options:
                self.remove_role_select = Select(
                    placeholder="Retirer un rôle admin",
                    options=remove_options,
                    row=1
                )
                self.remove_role_select.callback = self.remove_role
                self.add_item(self.remove_role_select)
    
    async def add_role(self, interaction: discord.Interaction):
        role_id = self.add_role_select.values[0]
        role = interaction.guild.get_role(int(role_id))
        
        if not role:
            await interaction.response.send_message("❌ Rôle introuvable!", ephemeral=True)
            return
        
        # Vérifier si déjà autorisé
        allowed = get_allowed_roles(self.guild_id, "admin")
        if role_id in allowed:
            await interaction.response.send_message(
                f"⚠️ {role.mention} est déjà un rôle admin",
                ephemeral=True
            )
            return
        
        # Ajouter le rôle
        add_role_permission(self.guild_id, "admin", role_id)
        
        embed = discord.Embed(
            title="✅ Rôle admin ajouté",
            description=f"{role.mention} peut maintenant utiliser les commandes admin",
            color=PSG_BLUE
        )
        
        # Afficher tous les rôles
        all_allowed = get_allowed_roles(self.guild_id, "admin")
        roles_list = []
        for r_id in all_allowed:
            r = interaction.guild.get_role(int(r_id))
            if r:
                roles_list.append(f"• {r.mention}")
        
        if roles_list:
            embed.add_field(
                name="Tous les rôles admin",
                value="\n".join(roles_list),
                inline=False
            )
        
        await interaction.response.edit_message(
            embed=embed,
            view=ConfigRolesView(self.interaction)
        )
    
    async def remove_role(self, interaction: discord.Interaction):
        role_id = self.remove_role_select.values[0]
        role = interaction.guild.get_role(int(role_id))
        
        # Retirer le rôle
        success = remove_role_permission(self.guild_id, "admin", role_id)
        
        if not success:
            await interaction.response.send_message("❌ Erreur lors de la suppression", ephemeral=True)
            return
        
        embed = discord.Embed(
            title="✅ Rôle admin retiré",
            description=f"{role.mention if role else 'Le rôle'} n'est plus un rôle admin",
            color=PSG_BLUE
        )
        
        # Afficher les rôles restants
        all_allowed = get_allowed_roles(self.guild_id, "admin")
        if all_allowed:
            roles_list = []
            for r_id in all_allowed:
                r = interaction.guild.get_role(int(r_id))
                if r:
                    roles_list.append(f"• {r.mention}")
            
            if roles_list:
                embed.add_field(
                    name="Rôles admin restants",
                    value="\n".join(roles_list),
                    inline=False
                )
        else:
            embed.add_field(
                name="ℹ️ Info",
                value="Plus aucun rôle spécifique. Seules les permissions Discord natives seront utilisées.",
                inline=False
            )
        
        await interaction.response.edit_message(
            embed=embed,
            view=ConfigRolesView(self.interaction)
        )
    
    @discord.ui.button(label="⬅️ Retour", style=discord.ButtonStyle.secondary, row=2)
    async def back_to_main(self, interaction: discord.Interaction, button: Button):
        main_view = ConfigMainView(self.interaction)
        await interaction.response.edit_message(
            embed=create_main_embed(self.interaction),
            view=main_view
        )


class ConfigLogsView(View):
    """Vue pour configurer le salon de logs"""
    def __init__(self, interaction: discord.Interaction):
        super().__init__(timeout=300)
        self.interaction = interaction
        self.guild_id = str(interaction.guild_id)
        
        # Menu pour sélectionner le salon de logs
        channels = [ch for ch in interaction.guild.text_channels if ch.permissions_for(interaction.guild.me).send_messages]
        
        if len(channels) <= 25:
            options = [
                discord.SelectOption(
                    label=f"#{ch.name}"[:100],
                    value=str(ch.id),
                    description=ch.category.name if ch.category else "Pas de catégorie"
                )
                for ch in channels[:25]
            ]
            
            self.logs_select = Select(
                placeholder="Définir le salon de logs",
                options=options,
                row=0
            )
            self.logs_select.callback = self.set_logs_channel
            self.add_item(self.logs_select)
    
    async def set_logs_channel(self, interaction: discord.Interaction):
        channel_id = self.logs_select.values[0]
        channel = interaction.guild.get_channel(int(channel_id))
        
        if not channel:
            await interaction.response.send_message("❌ Salon introuvable!", ephemeral=True)
            return
        
        # Sauvegarder
        config = load_server_config(self.guild_id)
        if not config:
            await interaction.response.send_message("❌ Configuration introuvable!", ephemeral=True)
            return
        
        config["logs_channel"] = channel_id
        save_server_config(self.guild_id, config)
        
        embed = discord.Embed(
            title="✅ Salon de logs configuré",
            description=f"{channel.mention} recevra maintenant tous les logs du serveur",
            color=PSG_BLUE
        )
        
        embed.add_field(
            name="📋 Logs activés",
            value="• Membres (arrivées/départs)\n"
                  "• Messages (modifications/suppressions)\n"
                  "• Salons vocaux\n"
                  "• Modifications du serveur\n"
                  "• Rôles et permissions",
            inline=False
        )
        
        await interaction.response.edit_message(embed=embed, view=ConfigLogsView(self.interaction))
    
    @discord.ui.button(label="🗑️ Désactiver les logs", style=discord.ButtonStyle.danger, row=1)
    async def remove_logs(self, interaction: discord.Interaction, button: Button):
        config = load_server_config(self.guild_id)
        if config:
            config["logs_channel"] = None
            save_server_config(self.guild_id, config)
        
        embed = discord.Embed(
            title="✅ Logs désactivés",
            description="Le bot n'enverra plus de logs.",
            color=PSG_BLUE
        )
        
        await interaction.response.edit_message(embed=embed, view=ConfigLogsView(self.interaction))
    
    @discord.ui.button(label="⬅️ Retour", style=discord.ButtonStyle.secondary, row=2)
    async def back_to_main(self, interaction: discord.Interaction, button: Button):
        main_view = ConfigMainView(self.interaction)
        await interaction.response.edit_message(
            embed=create_main_embed(self.interaction),
            view=main_view
        )


# ==================== FONCTIONS HELPER ====================

def create_main_embed(interaction: discord.Interaction):
    """Créer l'embed principal de configuration"""
    embed = discord.Embed(
        title="⚙️ Configuration du Bot PSG",
        description=f"Bienvenue dans le panneau de configuration pour **{interaction.guild.name}**\n\n"
                    "Choisis une catégorie à configurer :",
        color=PSG_BLUE
    )
    
    embed.add_field(
        name="📺 Salons de Commandes",
        value="Configure où `/solde`, `/packs`, `/collection` et le mini-jeu peuvent être utilisés",
        inline=False
    )
    
    embed.add_field(
        name="👑 Rôles Administrateurs",
        value="Définis quels **rôles du serveur** peuvent utiliser `/addcoins`, `/removecoins`, `/setcoins`",
        inline=False
    )
    
    embed.add_field(
        name="📋 Salon de Logs",
        value="Définis où le bot enverra les logs du serveur",
        inline=False
    )
    
    embed.set_footer(
        text="Paris Saint-Germain • Configuration propriétaire",
        icon_url="https://upload.wikimedia.org/wikipedia/fr/thumb/8/86/Paris_Saint-Germain_Logo.svg/2048px-Paris_Saint-Germain_Logo.svg.png"
    )
    
    return embed


async def create_full_config_embed(interaction: discord.Interaction):
    """Créer l'embed de configuration complète"""
    guild_id = str(interaction.guild_id)
    config = load_server_config(guild_id)
    
    embed = discord.Embed(
        title=f"📊 Configuration Complète - {interaction.guild.name}",
        description="Voici un résumé de toute la configuration actuelle",
        color=PSG_BLUE
    )
    
    # Salons de commandes
    for cmd in ["solde", "packs", "collection"]:
        channels = get_allowed_channels(guild_id, cmd)
        if channels:
            channels_list = []
            for ch_id in channels:
                channel = interaction.guild.get_channel(int(ch_id))
                if channel:
                    channels_list.append(channel.mention)
            
            embed.add_field(
                name=f"📺 /{cmd}",
                value="\n".join(channels_list) if channels_list else "Partout ✅",
                inline=True
            )
        else:
            embed.add_field(
                name=f"📺 /{cmd}",
                value="Partout ✅",
                inline=True
            )
    
    # Mini-jeu
    from utils.database import get_minigame_channel, get_next_minigame_time
    minigame_channel_id = get_minigame_channel(guild_id)
    if minigame_channel_id:
        minigame_channel = interaction.guild.get_channel(int(minigame_channel_id))
        if minigame_channel:
            try:
                next_time = get_next_minigame_time(guild_id)
                embed.add_field(
                    name="⚡ Mini-jeu",
                    value=f"{minigame_channel.mention}\n⏰ <t:{int(next_time.timestamp())}:R>",
                    inline=True
                )
            except:
                embed.add_field(
                    name="⚡ Mini-jeu",
                    value=minigame_channel.mention,
                    inline=True
                )
    else:
        embed.add_field(
            name="⚡ Mini-jeu",
            value="Non configuré ❌",
            inline=True
        )
    
    # Rôles admin
    admin_roles = get_allowed_roles(guild_id, "admin")
    if admin_roles:
        roles_list = []
        for r_id in admin_roles:
            role = interaction.guild.get_role(int(r_id))
            if role:
                roles_list.append(role.mention)
        
        embed.add_field(
            name="👑 Rôles Admin",
            value="\n".join(roles_list) if roles_list else "Aucun",
            inline=False
        )
    else:
        embed.add_field(
            name="👑 Rôles Admin",
            value="Permissions Discord natives 🔧",
            inline=False
        )
    
    # Salon de logs
    logs_channel_id = config.get("logs_channel") if config else None
    if logs_channel_id:
        logs_channel = interaction.guild.get_channel(int(logs_channel_id))
        if logs_channel:
            embed.add_field(
                name="📋 Salon de Logs",
                value=logs_channel.mention,
                inline=False
            )
    else:
        embed.add_field(
            name="📋 Salon de Logs",
            value="Non configuré ❌",
            inline=False
        )
    
    embed.set_footer(
        text="Paris Saint-Germain",
        icon_url="https://upload.wikimedia.org/wikipedia/fr/thumb/8/86/Paris_Saint-Germain_Logo.svg/2048px-Paris_Saint-Germain_Logo.svg.png"
    )
    
    return embed


# ==================== COMMANDE PRINCIPALE ====================

async def config_command(interaction: discord.Interaction):
    """Commande unique de configuration interactive"""
    # Vérifier si c'est le propriétaire du bot
    if interaction.user.id != OWNER_ID:
        embed = discord.Embed(
            title="❌ Accès refusé",
            description="Seul le propriétaire du bot peut utiliser cette commande.",
            color=PSG_RED
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return
    
    # Envoyer le menu principal
    embed = create_main_embed(interaction)
    view = ConfigMainView(interaction)
    
    await interaction.response.send_message(embed=embed, view=view, ephemeral=True)