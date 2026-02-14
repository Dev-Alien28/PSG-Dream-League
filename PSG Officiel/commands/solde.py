# commands/solde.py - CORRIGÉ AVEC SÉPARATION PAR SERVEUR
import discord
from utils.database import get_user_data
from utils.permissions import check_channel_permission, get_allowed_channel
from config.settings import PSG_BLUE, PSG_RED

async def solde_command(interaction: discord.Interaction):
    # Vérifier si la commande peut être utilisée dans ce salon
    if not check_channel_permission(interaction, "solde"):
        allowed_channel = get_allowed_channel(interaction.guild.id, "solde", interaction.client)
        
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
    user_id = str(interaction.user.id)
    
    user_data = get_user_data(guild_id, user_id)
    
    coins = user_data["coins"]
    cards_count = len(user_data.get("collection", []))
    
    embed = discord.Embed(
        title=f"💰 Solde de {interaction.user.display_name}",
        description=f"Ton portefeuille PSG sur **{interaction.guild.name}**",
        color=PSG_BLUE
    )
    embed.add_field(
        name="💎 PSG Coins", 
        value=f"**{coins}** 🪙", 
        inline=True
    )
    embed.add_field(
        name="🎴 Collection", 
        value=f"{cards_count} carte(s)", 
        inline=True
    )
    
    embed.set_thumbnail(url=interaction.user.avatar.url if interaction.user.avatar else None)
    embed.set_footer(
        text=f"Paris Saint-Germain • {interaction.guild.name}",
        icon_url="https://upload.wikimedia.org/wikipedia/fr/thumb/8/86/Paris_Saint-Germain_Logo.svg/2048px-Paris_Saint-Germain_Logo.svg.png"
    )
    
    await interaction.response.send_message(embed=embed, ephemeral=True)