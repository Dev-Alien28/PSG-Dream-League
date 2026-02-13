# handlers/commands.py - VERSION AVEC PARAMÈTRE MEMBRE POUR /COLLECTION ET /GIVE
import discord
from discord import app_commands
from discord.ext import commands
from commands.solde import solde_command
from commands.packs import packs_command
from commands.collection import collection_command
from commands.admin import addcoins_command, removecoins_command, setcoins_command
from commands.config import config_command
from commands.give import give_command

def setup_commands(bot: commands.Bot):
    
    # Wrapper pour logger les commandes APRÈS leur exécution (non bloquant)
    async def log_command_wrapper(interaction: discord.Interaction, command_name: str, func, *args, **kwargs):
        """Wrapper qui log l'utilisation de toutes les commandes"""
        from utils.logs import log_command_use
        
        try:
            # ⭐ IMPORTANT: Exécuter la commande EN PREMIER
            await func(interaction, *args, **kwargs)
            
            # ⭐ Logger APRÈS (en arrière-plan, ne bloque pas)
            # Créer une tâche asyncio pour logger sans bloquer
            bot.loop.create_task(log_command_use(interaction, command_name, success=True))
            
        except discord.errors.NotFound:
            # Interaction expirée, ignorer silencieusement
            pass
        except Exception as e:
            # Logger l'erreur
            bot.loop.create_task(log_command_use(interaction, command_name, success=False, error=str(e)))
            # Re-lever l'exception pour que Discord.py la gère
            raise
    
    # ========== COMMANDES MEMBRES ==========
    @bot.tree.command(name="solde", description="Consulte ta solde de PSG Coins")
    async def solde(interaction: discord.Interaction):
        await log_command_wrapper(interaction, "solde", solde_command)
    
    @bot.tree.command(name="packs", description="Voir les packs disponibles et acheter avec des boutons")
    async def packs(interaction: discord.Interaction):
        await log_command_wrapper(interaction, "packs", packs_command)
    
    @bot.tree.command(name="collection", description="Voir ta collection de cartes ou celle d'un autre membre")
    @app_commands.describe(
        membre="(Optionnel) Le membre dont tu veux voir la collection"
    )
    async def collection(interaction: discord.Interaction, membre: discord.Member = None):
        await log_command_wrapper(interaction, "collection", collection_command, membre)
    
    # ========== COMMANDES ADMINISTRATEUR ==========
    @bot.tree.command(name="addcoins", description="[ADMIN] Ajouter des PSG Coins à un membre")
    @app_commands.describe(
        membre="Le membre qui va recevoir les coins",
        montant="Nombre de PSG Coins à ajouter"
    )
    async def addcoins(interaction: discord.Interaction, membre: discord.Member, montant: int):
        await log_command_wrapper(interaction, f"addcoins membre:{membre.name} montant:{montant}", addcoins_command, membre, montant)
    
    @bot.tree.command(name="removecoins", description="[ADMIN] Retirer des PSG Coins à un membre")
    @app_commands.describe(
        membre="Le membre qui va perdre les coins",
        montant="Nombre de PSG Coins à retirer"
    )
    async def removecoins(interaction: discord.Interaction, membre: discord.Member, montant: int):
        await log_command_wrapper(interaction, f"removecoins membre:{membre.name} montant:{montant}", removecoins_command, membre, montant)
    
    @bot.tree.command(name="setcoins", description="[ADMIN] Définir la solde exacte d'un membre")
    @app_commands.describe(
        membre="Le membre dont tu veux modifier la solde",
        montant="Nouvelle solde en PSG Coins"
    )
    async def setcoins(interaction: discord.Interaction, membre: discord.Member, montant: int):
        await log_command_wrapper(interaction, f"setcoins membre:{membre.name} montant:{montant}", setcoins_command, membre, montant)
    
    @bot.tree.command(name="give", description="[ADMIN] Donner une carte à un membre")
    @app_commands.describe(
        carte_id="L'ID de la carte à donner (ex: gk_donnarumma_basic)",
        membre="Le membre qui va recevoir la carte",
        raison="(Optionnel) Raison ou message pour le membre"
    )
    async def give(interaction: discord.Interaction, carte_id: str, membre: discord.Member, raison: str = None):
        await log_command_wrapper(interaction, f"give carte:{carte_id} membre:{membre.name}", give_command, carte_id, membre, raison)
    
    # ========== COMMANDE CONFIGURATION UNIQUE ==========
    @bot.tree.command(name="config", description="[OWNER] Configurer le bot de manière interactive")
    async def config(interaction: discord.Interaction):
        await log_command_wrapper(interaction, "config", config_command)
    
    return bot