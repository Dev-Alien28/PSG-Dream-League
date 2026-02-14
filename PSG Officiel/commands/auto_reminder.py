# auto_reminder.py - Système de rappel automatique (VERSION AMÉLIORÉE)
import discord
import asyncio
import json
import os
from config.settings import PSG_BLUE

REMINDER_CONFIG_FILE = "data/reminder_config.json"

class AutoReminder:
    """Classe pour gérer les rappels automatiques"""
    
    def __init__(self, bot):
        self.bot = bot
        self.config = self.load_config()
        self._restart_event = asyncio.Event()  # Déclenché pour interrompre le sleep
    
    def load_config(self) -> dict:
        """Charge la configuration des rappels"""
        if os.path.exists(REMINDER_CONFIG_FILE):
            try:
                with open(REMINDER_CONFIG_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return {}
        return {}
    
    def save_config(self):
        """Sauvegarde la configuration des rappels"""
        os.makedirs(os.path.dirname(REMINDER_CONFIG_FILE), exist_ok=True)
        with open(REMINDER_CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, indent=4, ensure_ascii=False)
    
    def _trigger_restart(self):
        """Interrompt le sleep en cours pour recalculer l'intervalle immédiatement"""
        self._restart_event.set()
    
    def set_reminder_channel(self, guild_id: str, channel_id: str):
        """Définir le salon où envoyer les rappels"""
        if guild_id not in self.config:
            self.config[guild_id] = {
                "enabled": False,
                "channel_id": None,
                "interval_hours": 6.0,
                "discussion_channel_id": None
            }
        
        self.config[guild_id]["channel_id"] = channel_id
        self.save_config()
    
    def set_discussion_channel(self, guild_id: str, channel_id: str):
        """Définir le salon de discussion à mentionner"""
        if guild_id not in self.config:
            self.config[guild_id] = {
                "enabled": False,
                "channel_id": None,
                "interval_hours": 6.0,
                "discussion_channel_id": None
            }
        
        self.config[guild_id]["discussion_channel_id"] = channel_id
        self.save_config()
    
    def set_interval(self, guild_id: str, hours: float):
        """Définir l'intervalle entre les rappels et interrompre le sleep en cours"""
        if guild_id not in self.config:
            self.config[guild_id] = {
                "enabled": False,
                "channel_id": None,
                "interval_hours": hours,
                "discussion_channel_id": None
            }
        else:
            self.config[guild_id]["interval_hours"] = hours
        
        self.save_config()
        self._trigger_restart()  # Interrompt le sleep immédiatement
    
    def enable_reminders(self, guild_id: str) -> bool:
        """Activer les rappels pour un serveur"""
        if guild_id not in self.config or not self.config[guild_id].get("channel_id"):
            return False
        
        self.config[guild_id]["enabled"] = True
        self.save_config()
        self._trigger_restart()  # Interrompt le sleep pour démarrer rapidement
        return True
    
    def disable_reminders(self, guild_id: str):
        """Désactiver les rappels pour un serveur"""
        if guild_id in self.config:
            self.config[guild_id]["enabled"] = False
            self.save_config()
    
    def get_interval(self, guild_id: str) -> float:
        """Obtenir l'intervalle configuré (en heures, float)"""
        return float(self.config.get(guild_id, {}).get("interval_hours", 6.0))
    
    def get_discussion_channel_id(self, guild_id: str) -> str | None:
        """Obtenir l'ID du salon de discussion"""
        return self.config.get(guild_id, {}).get("discussion_channel_id")
    
    def is_enabled(self, guild_id: str) -> bool:
        """Vérifier si les rappels sont activés pour un serveur"""
        return self.config.get(guild_id, {}).get("enabled", False)
    
    def get_channel_id(self, guild_id: str) -> str | None:
        """Obtenir l'ID du salon de rappel pour un serveur"""
        return self.config.get(guild_id, {}).get("channel_id")
    
    def remove_reminder_channel(self, guild_id: str):
        """Retirer complètement la configuration des rappels"""
        if guild_id in self.config:
            del self.config[guild_id]
            self.save_config()
    
    def _format_interval(self, hours: float) -> str:
        """Convertit un intervalle en heures (float) en texte lisible"""
        if hours < 1:
            minutes = int(round(hours * 60))
            return f"{minutes} minute{'s' if minutes > 1 else ''}"
        elif hours == 1:
            return "1 heure"
        else:
            return f"{int(hours)} heures"
    
    async def _interruptible_sleep(self, seconds: float):
        """Sleep interruptible : se termine quand le temps est écoulé OU quand _restart_event est déclenché"""
        self._restart_event.clear()
        try:
            await asyncio.wait_for(self._restart_event.wait(), timeout=seconds)
            print("⚡ Sleep interrompu : recalcul de l'intervalle")
        except asyncio.TimeoutError:
            pass  # Temps écoulé normalement
    
    async def start_reminder_loop(self):
        """Démarrer la boucle de rappel avec intervalle dynamique et interruptible"""
        await self.bot.wait_until_ready()
        
        while not self.bot.is_closed():
            await self.send_reminders()
            
            # Calculer l'intervalle le plus court parmi tous les serveurs actifs
            min_interval = 21600.0  # 6h par défaut en secondes
            for guild_id, settings in self.config.items():
                if settings.get("enabled", False):
                    interval_hours = float(settings.get("interval_hours", 6.0))
                    interval_seconds = interval_hours * 3600
                    min_interval = min(min_interval, interval_seconds)
            
            print(f"⏰ Prochain rappel dans {self._format_interval(min_interval / 3600)}")
            await self._interruptible_sleep(min_interval)
    
    async def send_reminders(self):
        """Envoyer les rappels dans tous les salons configurés et activés"""
        for guild_id, settings in list(self.config.items()):
            if not settings.get("enabled", False):
                continue
            
            channel_id = settings.get("channel_id")
            if not channel_id:
                continue
            
            try:
                channel = self.bot.get_channel(int(channel_id))
                
                if channel is None:
                    try:
                        channel = await self.bot.fetch_channel(int(channel_id))
                    except:
                        print(f"⚠️ Salon {channel_id} introuvable pour le guild {guild_id}")
                        continue
                
                # Récupérer le salon de discussion
                discussion_channel_id = settings.get("discussion_channel_id")
                discussion_text = "💬 Pour discuter, utilisez les autres salons du serveur !"
                
                if discussion_channel_id:
                    discussion_channel = self.bot.get_channel(int(discussion_channel_id))
                    if discussion_channel:
                        discussion_text = f"💬 Pour discuter, utilisez le salon {discussion_channel.mention}"
                
                # Intervalle lisible pour le footer
                interval_hours = float(settings.get("interval_hours", 6.0))
                interval_label = self._format_interval(interval_hours)
                
                embed = discord.Embed(
                    title="📢 RAPPEL AUTOMATIQUE",
                    description=(
                        "**Ce salon est réservé au jeu PSG Dream League !**\n\n"
                        "🚫 **Merci de ne pas discuter ici**\n\n"
                        "✅ **Commandes disponibles :**\n"
                        "• `/packs` - Acheter des packs de cartes\n"
                        "• `/collection` - Voir ta collection\n"
                        "• `/solde` - Voir ton solde de PSG Coins\n\n"
                        f"{discussion_text}"
                    ),
                    color=PSG_BLUE
                )
                
                embed.set_footer(
                    text=f"Ce message apparaît automatiquement toutes les {interval_label}",
                    icon_url="https://upload.wikimedia.org/wikipedia/fr/thumb/8/86/Paris_Saint-Germain_Logo.svg/2048px-Paris_Saint-Germain_Logo.svg.png"
                )
                
                await channel.send(embed=embed)
                print(f"✅ Rappel envoyé dans le salon {channel.name} ({guild_id})")
                
            except discord.Forbidden:
                print(f"❌ Pas de permission pour envoyer dans le salon {channel_id} ({guild_id})")
            except Exception as e:
                print(f"❌ Erreur lors de l'envoi du rappel pour {guild_id}: {e}")


def setup_auto_reminder(bot):
    """Initialiser le système de rappel automatique"""
    reminder = AutoReminder(bot)
    bot.auto_reminder = reminder
    
    original_setup_hook = bot.setup_hook if hasattr(bot, 'setup_hook') else None
    
    async def new_setup_hook():
        if original_setup_hook:
            await original_setup_hook()
        bot.loop.create_task(reminder.start_reminder_loop())
    
    bot.setup_hook = new_setup_hook
    
    return reminder