# handlers/events.py - AVEC SYSTÈME DE SALONS SANS COINS
import discord
from discord.ext import commands, tasks
from datetime import datetime
from utils.database import init_files, get_user_data, save_user_data, get_next_minigame_time, get_minigame_channel
from utils.permissions import init_server_config, is_coins_disabled_channel  # ✅ AJOUT
from utils.logs import (
    log_member_join, log_member_leave, log_message_delete, 
    log_message_edit, log_voice_state, log_channel_create,
    log_channel_delete, log_role_create, log_role_delete, 
    log_member_update, log_channel_update, log_role_update,
    log_guild_update, log_bulk_delete
)
from config.settings import PSG_BLUE, COINS_PER_MESSAGE_INTERVAL, MIN_MESSAGE_LENGTH

def setup_events(bot: commands.Bot):
    
    @bot.event
    async def on_ready():
        init_files()
        print(f'🔴🔵 Bot PSG connecté en tant que {bot.user}')
        print(f'📊 Serveurs : {len(bot.guilds)}')
        
        for guild in bot.guilds:
            init_server_config(str(guild.id), guild.name)
        
        try:
            synced = await bot.tree.sync()
            print(f"✅ {len(synced)} commande(s) slash synchronisée(s) :")
            for cmd in synced:
                print(f"   /{cmd.name}")
            print("\n💡 Les commandes sont maintenant disponibles avec / dans Discord !")
            print("📝 Système de logs activé")
            print("⚡ Système de mini-jeu activé")
            print(f"🔒 Anti-spam: longueur minimale des messages = {MIN_MESSAGE_LENGTH} caractères")
            print("🚫 Système de salons sans coins activé")  # ✅ NOUVEAU
        except Exception as e:
            print(f"❌ Erreur de synchronisation: {e}")
        
        if not check_minigame.is_running():
            check_minigame.start()
    
    @tasks.loop(minutes=1)
    async def check_minigame():
        """Vérifie toutes les minutes si un mini-jeu doit apparaître"""
        from commands.minigame import spawn_minigame
        
        for guild in bot.guilds:
            guild_id = str(guild.id)
            
            channel_id = get_minigame_channel(guild_id)
            if not channel_id:
                continue
            
            try:
                next_time = get_next_minigame_time(guild_id)
                
                if datetime.now() >= next_time:
                    print(f"⚡ Mini-jeu déclenché sur {guild.name}")
                    await spawn_minigame(bot, guild_id)
            except Exception as e:
                print(f"❌ Erreur mini-jeu pour {guild.name}: {e}")
    
    @check_minigame.before_loop
    async def before_check_minigame():
        """Attend que le bot soit prêt avant de démarrer la boucle"""
        await bot.wait_until_ready()
    
    @bot.event
    async def on_guild_join(guild):
        """Initialise la configuration quand le bot rejoint un serveur"""
        init_server_config(str(guild.id), guild.name)
        print(f"✅ Configuration créée pour {guild.name} ({guild.id})")
    
    # ==================== LOGS MEMBRES ====================
    @bot.event
    async def on_member_join(member: discord.Member):
        """Log quand un membre rejoint + initialisation"""
        await log_member_join(member)
        
        guild_id = str(member.guild.id)
        user_id = str(member.id)
        
        # Initialiser l'utilisateur sur CE serveur
        get_user_data(guild_id, user_id)
    
    @bot.event
    async def on_member_remove(member: discord.Member):
        """Log quand un membre quitte"""
        await log_member_leave(member)
    
    @bot.event
    async def on_member_update(before: discord.Member, after: discord.Member):
        """Log les modifications d'un membre"""
        await log_member_update(before, after)
    
    # ==================== LOGS MESSAGES ====================
    @bot.event
    async def on_message_delete(message: discord.Message):
        """Log quand un message est supprimé"""
        await log_message_delete(message)
    
    @bot.event
    async def on_message_edit(before: discord.Message, after: discord.Message):
        """Log quand un message est modifié"""
        await log_message_edit(before, after)
    
    @bot.event
    async def on_bulk_message_delete(messages):
        """Log quand plusieurs messages sont supprimés"""
        if messages:
            await log_bulk_delete(messages, messages[0].channel)
    
    # ==================== LOGS VOCAUX ====================
    @bot.event
    async def on_voice_state_update(member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
        """Log les changements de salon vocal"""
        await log_voice_state(member, before, after)
    
    # ==================== LOGS SALONS ====================
    @bot.event
    async def on_guild_channel_create(channel):
        """Log la création d'un salon"""
        await log_channel_create(channel)
    
    @bot.event
    async def on_guild_channel_delete(channel):
        """Log la suppression d'un salon"""
        await log_channel_delete(channel)
    
    @bot.event
    async def on_guild_channel_update(before, after):
        """Log les modifications d'un salon"""
        await log_channel_update(before, after)
    
    # ==================== LOGS RÔLES ====================
    @bot.event
    async def on_guild_role_create(role: discord.Role):
        """Log la création d'un rôle"""
        await log_role_create(role)
    
    @bot.event
    async def on_guild_role_delete(role: discord.Role):
        """Log la suppression d'un rôle"""
        await log_role_delete(role)
    
    @bot.event
    async def on_guild_role_update(before: discord.Role, after: discord.Role):
        """Log les modifications d'un rôle"""
        await log_role_update(before, after)
    
    # ==================== LOGS SERVEUR ====================
    @bot.event
    async def on_guild_update(before: discord.Guild, after: discord.Guild):
        """Log les modifications du serveur"""
        await log_guild_update(before, after)
    
    # ==================== SYSTÈME DE COINS AVEC VALIDATION ET SALONS SANS COINS ====================
    @bot.event
    async def on_message(message):
        # Ignorer les bots
        if message.author.bot:
            return
        
        # Ignorer les commandes
        if message.content.startswith('!') or message.content.startswith('/'):
            await bot.process_commands(message)
            return
        
        # Vérifier que c'est dans un serveur
        if not message.guild:
            await bot.process_commands(message)
            return
        
        guild_id = str(message.guild.id)
        user_id = str(message.author.id)
        channel_id = str(message.channel.id)
        
        # ✅ NOUVELLE VÉRIFICATION : Ne pas donner de coins dans les salons désactivés
        if is_coins_disabled_channel(guild_id, channel_id):
            await bot.process_commands(message)
            return
        
        # Vérifier la longueur minimale du message (anti-spam)
        message_clean = message.content.strip()
        message_length = len(message_clean)
        
        if message_length < MIN_MESSAGE_LENGTH:
            await bot.process_commands(message)
            return
        
        # Récupérer les données utilisateur
        user_data = get_user_data(guild_id, user_id)
        
        # Incrémenter le compteur de messages
        user_data["messages"] += 1
        
        # Donner des coins selon l'intervalle configuré
        if user_data["messages"] % COINS_PER_MESSAGE_INTERVAL == 0:
            user_data["coins"] += 1
            print(f"💰 {message.author.name} a gagné 1 coin sur {message.guild.name} (message de {message_length} car.)")
        
        # Sauvegarder les données
        save_user_data(guild_id, user_id, user_data)
        
        # Traiter les commandes
        await bot.process_commands(message)
    
    return bot