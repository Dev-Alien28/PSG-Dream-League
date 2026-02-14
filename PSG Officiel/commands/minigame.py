# commands/minigame.py - CORRIGÉ AVEC SÉPARATION PAR SERVEUR
import discord
import random
from config.settings import PSG_BLUE, PSG_RED, MINIGAME_CONFIG
from utils.database import (
    load_pack_cards, 
    add_card_to_user,
    get_minigame_channel,
    set_minigame_channel,
    schedule_next_minigame,
    get_next_minigame_time
)

# Liste de questions PSG (identique à avant)
PSG_QUESTIONS = [
    {"question": "En quelle année le PSG a-t-il été fondé ?", "answers": ["1970", "1965", "1975", "1980"], "correct": 0},
    {"question": "Quel joueur détient le record de buts au PSG ?", "answers": ["Zlatan Ibrahimović", "Edinson Cavani", "Kylian Mbappé", "Pauleta"], "correct": 1},
    {"question": "Quel est le surnom du PSG ?", "answers": ["Les Rouges", "Les Parisiens", "Les Bleus", "Les Princes"], "correct": 1},
    {"question": "En quelle année le PSG a-t-il atteint sa première finale de Ligue des Champions ?", "answers": ["2015", "2018", "2020", "2021"], "correct": 2},
    {"question": "Quel est le nom du stade du PSG ?", "answers": ["Stade de France", "Parc des Princes", "Stade Vélodrome", "Allianz Riviera"], "correct": 1},
    {"question": "Qui est le président actuel du PSG ?", "answers": ["Jean-Michel Aulas", "Nasser Al-Khelaïfi", "Frank McCourt", "Vincent Labrune"], "correct": 1},
    {"question": "Combien de fois le PSG a-t-il gagné la Ligue 1 ?", "answers": ["8 fois", "10 fois", "12 fois", "Plus de 10 fois"], "correct": 3},
    {"question": "Quel joueur brésilien légendaire a porté le maillot du PSG ?", "answers": ["Ronaldo", "Ronaldinho", "Rivaldo", "Romário"], "correct": 1},
    {"question": "Quelle est la capacité du Parc des Princes ?", "answers": ["45 000", "48 000", "50 000", "55 000"], "correct": 1},
    {"question": "En quelle année le Qatar a-t-il racheté le PSG ?", "answers": ["2009", "2011", "2013", "2015"], "correct": 1},
    {"question": "Quel est le rival historique du PSG ?", "answers": ["Lyon", "Marseille", "Monaco", "Lille"], "correct": 1},
    {"question": "Qui est l'entraîneur actuel du PSG (2024) ?", "answers": ["Thomas Tuchel", "Mauricio Pochettino", "Luis Enrique", "Christophe Galtier"], "correct": 2},
    {"question": "Quel gardien italien joue au PSG ?", "answers": ["Gianluigi Buffon", "Gianluigi Donnarumma", "Salvatore Sirigu", "Mattia Perin"], "correct": 1},
    {"question": "Quelle est la devise du PSG ?", "answers": ["Allez Paris", "Ici c'est Paris", "Paris est magique", "Ville Lumière"], "correct": 1},
    {"question": "En quelle année Neymar a-t-il rejoint le PSG ?", "answers": ["2016", "2017", "2018", "2019"], "correct": 1},
    {"question": "Combien a coûté le transfert de Neymar au PSG ?", "answers": ["200 millions", "222 millions", "250 millions", "300 millions"], "correct": 1},
    {"question": "Quel défenseur marocain joue au PSG ?", "answers": ["Achraf Hakimi", "Hakim Ziyech", "Noussair Mazraoui", "Romain Saïss"], "correct": 0},
    {"question": "Combien de Coupes de France le PSG a-t-il remportées ?", "answers": ["10", "12", "14", "Plus de 14"], "correct": 3},
    {"question": "Quel pays représente Marquinhos ?", "answers": ["Argentine", "Brésil", "Portugal", "Espagne"], "correct": 1},
    {"question": "En quelle année le PSG a-t-il remporté son premier titre de champion de France ?", "answers": ["1986", "1990", "1994", "1998"], "correct": 0}
]

class MinigameView(discord.ui.View):
    """Vue avec boutons pour le mini-jeu"""
    
    def __init__(self, guild_id: str, correct_answer: int, question_data: dict):
        super().__init__(timeout=MINIGAME_CONFIG["timeout"])
        self.guild_id = guild_id
        self.correct_answer = correct_answer
        self.question_data = question_data
        self.winner = None
        self.answered = set()
        
        labels = ["A", "B", "C", "D"]
        
        for i, answer in enumerate(question_data["answers"]):
            button = discord.ui.Button(
                label=f"{labels[i]}. {answer}",
                style=discord.ButtonStyle.primary,
                custom_id=f"answer_{i}"
            )
            button.callback = self.create_callback(i)
            self.add_item(button)
    
    def create_callback(self, answer_index: int):
        """Crée un callback pour chaque bouton"""
        async def callback(interaction: discord.Interaction):
            user_id = interaction.user.id
            
            if user_id in self.answered:
                await interaction.response.send_message("❌ Tu as déjà répondu !", ephemeral=True)
                return
            
            self.answered.add(user_id)
            
            if answer_index == self.correct_answer:
                if self.winner is None:
                    self.winner = interaction.user
                    
                    for item in self.children:
                        item.disabled = True
                    
                    self.children[self.correct_answer].style = discord.ButtonStyle.success
                    self.stop()
                    
                    await interaction.response.edit_message(view=self)
                    await self.give_reward(interaction)
                else:
                    await interaction.response.send_message(
                        f"✅ Bonne réponse mais {self.winner.mention} était plus rapide !",
                        ephemeral=True
                    )
            else:
                await interaction.response.send_message("❌ Mauvaise réponse ! Dommage...", ephemeral=True)
        
        return callback
    
    async def give_reward(self, interaction: discord.Interaction):
        """Donne la récompense au gagnant"""
        cards = load_pack_cards("pack_event")
        if not cards:
            await interaction.followup.send("❌ Erreur : Aucune carte disponible dans le pack événement.", ephemeral=True)
            return
        
        from config.settings import PACKS_CONFIG
        drop_rates = PACKS_CONFIG["pack_event"]["drop_rates"]
        
        rarities = list(drop_rates.keys())
        weights = list(drop_rates.values())
        chosen_rarity = random.choices(rarities, weights=weights, k=1)[0]
        
        cards_of_rarity = [card for card in cards if card.get('rareté') == chosen_rarity]
        card = random.choice(cards_of_rarity) if cards_of_rarity else random.choice(cards)
        
        # ✅ CORRECTION : Ajouter guild_id
        guild_id = self.guild_id
        user_id = str(self.winner.id)
        add_card_to_user(guild_id, user_id, card)
        
        embed = discord.Embed(
            title="🎉 CARTE CAPTURÉE !",
            description=f"**{self.winner.mention} a gagné la carte !**\n\n"
                       f"# 🎴 {card['nom']}",
            color=0xFFD700
        )
        
        from commands.collection import format_card_stats
        stats_text = format_card_stats(card)
        
        embed.add_field(name="📊 Statistiques", value=stats_text, inline=False)
        embed.add_field(name="🏆 Rareté", value=f"{get_rarity_emoji(card['rareté'])} {card['rareté']}", inline=True)
        embed.add_field(name="✨ Type", value=f"{get_card_type_emoji(card['type'])} {card['type'].capitalize()}", inline=True)
        
        if card.get('image'):
            embed.set_image(url=card['image'])
        
        embed.set_footer(
            text=f"Récompense mini-jeu • {self.winner.name}",
            icon_url=self.winner.avatar.url if self.winner.avatar else self.winner.default_avatar.url
        )
        
        await interaction.followup.send(embed=embed)
    
    async def on_timeout(self):
        """Appelé quand le temps est écoulé"""
        for item in self.children:
            item.disabled = True
        
        self.children[self.correct_answer].style = discord.ButtonStyle.success

async def spawn_minigame(bot, guild_id: str):
    """Fait apparaître le mini-jeu dans le salon configuré"""
    channel_id = get_minigame_channel(guild_id)
    if not channel_id:
        return
    
    guild = bot.get_guild(int(guild_id))
    if not guild:
        return
    
    channel = guild.get_channel(int(channel_id))
    if not channel:
        return
    
    question_data = random.choice(PSG_QUESTIONS)
    
    embed = discord.Embed(
        title="⚡ JOUEUR FUYARD APPARU !",
        description="Un joueur légendaire vient d'apparaître ! Réponds correctement et rapidement pour gagner une carte exclusive !\n\n"
                   f"**❓ {question_data['question']}**",
        color=0xFFD700
    )
    
    embed.add_field(name="⏱️ Temps", value=f"{MINIGAME_CONFIG['timeout']} secondes", inline=True)
    embed.add_field(name="🏆 Récompense", value="Carte Légendaire/Épique", inline=True)
    
    embed.set_footer(
        text="Première bonne réponse gagne !",
        icon_url="https://upload.wikimedia.org/wikipedia/fr/thumb/8/86/Paris_Saint-Germain_Logo.svg/2048px-Paris_Saint-Germain_Logo.svg.png"
    )
    
    view = MinigameView(guild_id, question_data["correct"], question_data)
    message = await channel.send(embed=embed, view=view)
    
    await view.wait()
    
    if view.winner is None:
        end_embed = discord.Embed(
            title="⏰ Temps écoulé !",
            description=f"Personne n'a trouvé la bonne réponse à temps !\n\n"
                       f"**✅ Réponse correcte :** {question_data['answers'][question_data['correct']]}",
            color=PSG_RED
        )
        await message.edit(embed=end_embed, view=view)
    else:
        end_embed = discord.Embed(
            title="🎉 GAGNANT !",
            description=f"**{view.winner.mention} a capturé le joueur fuyard !**\n\n"
                       f"Bonne réponse : {question_data['answers'][question_data['correct']]}",
            color=0xFFD700
        )
        await message.edit(embed=end_embed, view=view)
    
    schedule_next_minigame(guild_id)

async def config_minigame_command(interaction: discord.Interaction, salon: discord.TextChannel):
    """Configure le salon pour le mini-jeu"""
    OWNER_ID = 878724920987766796
    if interaction.user.id != OWNER_ID:
        embed = discord.Embed(
            title="❌ Accès refusé",
            description="Seul le propriétaire du bot peut utiliser cette commande.",
            color=PSG_RED
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return
    
    guild_id = str(interaction.guild_id)
    set_minigame_channel(guild_id, str(salon.id))
    
    next_time = get_next_minigame_time(guild_id)
    
    embed = discord.Embed(
        title="✅ Mini-jeu configuré",
        description=f"Le mini-jeu **Joueur Fuyard** apparaîtra dans {salon.mention}",
        color=PSG_BLUE
    )
    
    embed.add_field(
        name="⏰ Prochaine apparition",
        value=f"<t:{int(next_time.timestamp())}:F>\n(<t:{int(next_time.timestamp())}:R>)",
        inline=False
    )
    
    embed.add_field(
        name="📋 Intervalle",
        value=f"Entre {MINIGAME_CONFIG['min_interval_days']} et {MINIGAME_CONFIG['max_interval_days']} jours",
        inline=True
    )
    
    embed.add_field(
        name="🕐 Heures d'apparition",
        value=f"Entre {MINIGAME_CONFIG['start_hour']}h et {MINIGAME_CONFIG['end_hour']}h",
        inline=True
    )
    
    embed.set_footer(
        text="Paris Saint-Germain • Système événementiel",
        icon_url="https://upload.wikimedia.org/wikipedia/fr/thumb/8/86/Paris_Saint-Germain_Logo.svg/2048px-Paris_Saint-Germain_Logo.svg.png"
    )
    
    await interaction.response.send_message(embed=embed)

def get_rarity_emoji(rarity: str) -> str:
    """Retourne un emoji selon la rareté"""
    from config.settings import RARITIES
    return RARITIES.get(rarity, {}).get("emoji", "⚫")

def get_card_type_emoji(card_type: str) -> str:
    """Retourne un emoji selon le type de carte"""
    from config.settings import CARD_TYPES
    return CARD_TYPES.get(card_type, {}).get("emoji", "🎴")