# main.py
import discord
from discord.ext import commands
import os
import sys

# Ajouter un peu de debug
print("🔍 Vérification de l'environnement...")
print(f"📁 Dossier de travail: {os.getcwd()}")
print(f"🐍 Version Python: {sys.version}")

try:
    from config.settings import TOKEN, INTENTS, DATA_DIR, PACKS_DIR
    print("✅ Configuration chargée avec succès")
    
    # Vérifier le token (afficher seulement les 10 premiers caractères)
    if TOKEN:
        print(f"🔑 Token détecté: {TOKEN[:10]}...")
    else:
        print("❌ ERREUR: Token non trouvé dans .env")
        sys.exit(1)
        
except ImportError as e:
    print(f"❌ ERREUR lors de l'import de la configuration: {e}")
    sys.exit(1)

from handlers.events import setup_events
from handlers.commands import setup_commands

# Variable globale pour le bot (nécessaire pour get_allowed_channel)
bot = None

def main():
    global bot  # Déclarer bot comme variable globale
    
    print("\n🔴🔵 Initialisation du bot PSG...")
    
    # Créer les dossiers nécessaires AVANT de démarrer le bot
    try:
        os.makedirs(DATA_DIR, exist_ok=True)
        os.makedirs(PACKS_DIR, exist_ok=True)
        print("✅ Dossiers créés/vérifiés")
    except Exception as e:
        print(f"❌ Erreur lors de la création des dossiers: {e}")
        sys.exit(1)
    
    # Créer le bot
    try:
        bot = commands.Bot(command_prefix="!", intents=INTENTS)
        print("✅ Bot créé")
    except Exception as e:
        print(f"❌ Erreur lors de la création du bot: {e}")
        sys.exit(1)
    
    # Setup des événements et commandes
    try:
        setup_events(bot)
        print("✅ Événements configurés")
        setup_commands(bot)
        print("✅ Commandes configurées")
    except Exception as e:
        print(f"❌ Erreur lors de la configuration: {e}")
        sys.exit(1)
    
    # Lancer le bot
    print("\n📋 Tentative de connexion à Discord...")
    print("⏳ Cela peut prendre quelques secondes...\n")
    
    try:
        bot.run(TOKEN)
    except discord.LoginFailure:
        print("\n❌ ERREUR DE CONNEXION: Token invalide")
        print("\n🔧 Solutions:")
        print("1. Vérifie que ton fichier .env contient bien le token")
        print("2. Va sur https://discord.com/developers/applications")
        print("3. Reset ton token et copie-le dans .env")
        print("4. Vérifie qu'il n'y a pas d'espaces avant/après le token")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERREUR INATTENDUE: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()