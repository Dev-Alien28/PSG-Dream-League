# commands/admin.py - CORRIGÉ AVEC SÉPARATION PAR SERVEUR ET ORTHOGRAPHE
import discord
from discord import app_commands
from utils.database import get_user_data, save_user_data
from config.settings import PSG_BLUE, PSG_RED

async def addcoins_command(interaction: discord.Interaction, membre: discord.Member, montant: int):
    """Commande pour ajouter des PSG Coins à un membre (ADMIN SEULEMENT)"""
    from utils.permissions import check_role_permission
    if not check_role_permission(interaction, "admin"):
        embed = discord.Embed(
            title="❌ Accès refusé",
            description="Tu n'as pas les permissions administrateur pour utiliser cette commande.",
            color=PSG_RED
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return
    
    # ✅ CORRECTION: Ajouter guild_id
    guild_id = str(interaction.guild_id)
    user_id = str(membre.id)
    
    user_data = get_user_data(guild_id, user_id)
    
    # Ajouter les coins
    ancien_solde = user_data["coins"]
    user_data["coins"] += montant
    save_user_data(guild_id, user_id, user_data)
    
    embed = discord.Embed(
        title="✅ PSG Coins ajoutés!",
        description=f"Tu as ajouté **{montant} PSG Coins** à {membre.mention}!",
        color=PSG_BLUE
    )
    embed.add_field(name="💰 Ancien solde", value=f"{ancien_solde} 🪙", inline=True)
    embed.add_field(name="💎 Nouveau solde", value=f"{user_data['coins']} 🪙", inline=True)
    embed.set_footer(
        text=f"Paris Saint-Germain • {interaction.guild.name}",
        icon_url="https://upload.wikimedia.org/wikipedia/fr/thumb/8/86/Paris_Saint-Germain_Logo.svg/2048px-Paris_Saint-Germain_Logo.svg.png"
    )
    
    await interaction.response.send_message(embed=embed)
    
    # Notifier le membre
    try:
        notify_embed = discord.Embed(
            title="💰 Tu as reçu des PSG Coins!",
            description=f"Un administrateur de **{interaction.guild.name}** t'a ajouté **{montant} PSG Coins**!",
            color=PSG_BLUE
        )
        notify_embed.add_field(name="💎 Nouveau solde", value=f"{user_data['coins']} 🪙", inline=False)
        notify_embed.set_footer(
            text=f"Paris Saint-Germain • {interaction.guild.name}",
            icon_url="https://upload.wikimedia.org/wikipedia/fr/thumb/8/86/Paris_Saint-Germain_Logo.svg/2048px-Paris_Saint-Germain_Logo.svg.png"
        )
        await membre.send(embed=notify_embed)
    except:
        pass

async def removecoins_command(interaction: discord.Interaction, membre: discord.Member, montant: int):
    """Commande pour retirer des PSG Coins à un membre (ADMIN SEULEMENT)"""
    from utils.permissions import check_role_permission
    if not check_role_permission(interaction, "admin"):
        embed = discord.Embed(
            title="❌ Accès refusé",
            description="Tu n'as pas les permissions administrateur pour utiliser cette commande.",
            color=PSG_RED
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return
    
    # ✅ CORRECTION: Ajouter guild_id
    guild_id = str(interaction.guild_id)
    user_id = str(membre.id)
    
    user_data = get_user_data(guild_id, user_id)
    
    # Vérifier si le membre a assez de coins
    if user_data["coins"] < montant:
        embed = discord.Embed(
            title="⚠️ Attention",
            description=f"{membre.mention} n'a que **{user_data['coins']} PSG Coins** sur ce serveur.\n\n"
                        f"Tu essaies d'en retirer **{montant}**. Veux-tu vraiment mettre son solde à 0?",
            color=PSG_RED
        )
        embed.add_field(name="💰 Solde actuel", value=f"{user_data['coins']} 🪙", inline=True)
        embed.add_field(name="❗ Montant à retirer", value=f"{montant} 🪙", inline=True)
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return
    
    # Retirer les coins
    ancien_solde = user_data["coins"]
    user_data["coins"] -= montant
    save_user_data(guild_id, user_id, user_data)
    
    embed = discord.Embed(
        title="✅ PSG Coins retirés!",
        description=f"Tu as retiré **{montant} PSG Coins** à {membre.mention}!",
        color=PSG_BLUE
    )
    embed.add_field(name="💰 Ancien solde", value=f"{ancien_solde} 🪙", inline=True)
    embed.add_field(name="💎 Nouveau solde", value=f"{user_data['coins']} 🪙", inline=True)
    embed.set_footer(
        text=f"Paris Saint-Germain • {interaction.guild.name}",
        icon_url="https://upload.wikimedia.org/wikipedia/fr/thumb/8/86/Paris_Saint-Germain_Logo.svg/2048px-Paris_Saint-Germain_Logo.svg.png"
    )
    
    await interaction.response.send_message(embed=embed)
    
    # Notifier le membre
    try:
        notify_embed = discord.Embed(
            title="⚠️ Des PSG Coins ont été retirés",
            description=f"Un administrateur de **{interaction.guild.name}** t'a retiré **{montant} PSG Coins**.",
            color=PSG_RED
        )
        notify_embed.add_field(name="💎 Nouveau solde", value=f"{user_data['coins']} 🪙", inline=False)
        notify_embed.set_footer(
            text=f"Paris Saint-Germain • {interaction.guild.name}",
            icon_url="https://upload.wikimedia.org/wikipedia/fr/thumb/8/86/Paris_Saint-Germain_Logo.svg/2048px-Paris_Saint-Germain_Logo.svg.png"
        )
        await membre.send(embed=notify_embed)
    except:
        pass

async def setcoins_command(interaction: discord.Interaction, membre: discord.Member, montant: int):
    """Commande pour définir le solde exact d'un membre (ADMIN SEULEMENT)"""
    from utils.permissions import check_role_permission
    if not check_role_permission(interaction, "admin"):
        embed = discord.Embed(
            title="❌ Accès refusé",
            description="Tu n'as pas les permissions administrateur pour utiliser cette commande.",
            color=PSG_RED
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return
    
    # ✅ CORRECTION: Ajouter guild_id
    guild_id = str(interaction.guild_id)
    user_id = str(membre.id)
    
    user_data = get_user_data(guild_id, user_id)
    
    # Définir le solde
    ancien_solde = user_data["coins"]
    user_data["coins"] = montant
    save_user_data(guild_id, user_id, user_data)
    
    embed = discord.Embed(
        title="✅ Solde modifié!",
        description=f"Tu as défini le solde de {membre.mention} à **{montant} PSG Coins** sur ce serveur!",
        color=PSG_BLUE
    )
    embed.add_field(name="💰 Ancien solde", value=f"{ancien_solde} 🪙", inline=True)
    embed.add_field(name="💎 Nouveau solde", value=f"{montant} 🪙", inline=True)
    embed.set_footer(
        text=f"Paris Saint-Germain • {interaction.guild.name}",
        icon_url="https://upload.wikimedia.org/wikipedia/fr/thumb/8/86/Paris_Saint-Germain_Logo.svg/2048px-Paris_Saint-Germain_Logo.svg.png"
    )
    
    await interaction.response.send_message(embed=embed)
    
    # Notifier le membre
    try:
        notify_embed = discord.Embed(
            title="💰 Ton solde a été modifié",
            description=f"Un administrateur de **{interaction.guild.name}** a défini ton solde à **{montant} PSG Coins**.",
            color=PSG_BLUE
        )
        notify_embed.set_footer(
            text=f"Paris Saint-Germain • {interaction.guild.name}",
            icon_url="https://upload.wikimedia.org/wikipedia/fr/thumb/8/86/Paris_Saint-Germain_Logo.svg/2048px-Paris_Saint-Germain_Logo.svg.png"
        )
        await membre.send(embed=notify_embed)
    except:
        pass