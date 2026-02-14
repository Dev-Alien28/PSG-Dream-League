# utils/logs.py - SYSTÈME DE LOGS COMPLET
import discord
from datetime import datetime
from utils.permissions import load_server_config
from config.settings import PSG_BLUE, PSG_RED

async def get_logs_channel(guild: discord.Guild):
    """Récupère le salon de logs configuré"""
    config = load_server_config(str(guild.id))
    if not config or "logs_channel" not in config:
        return None
    
    channel_id = config["logs_channel"]
    try:
        return guild.get_channel(int(channel_id))
    except:
        return None

# ==================== LOGS MEMBRES ====================
async def log_member_join(member: discord.Member):
    """Log quand un membre rejoint"""
    channel = await get_logs_channel(member.guild)
    if not channel:
        return
    
    embed = discord.Embed(
        title="📥 Membre rejoint",
        description=f"{member.mention} a rejoint le serveur",
        color=0x00FF00,
        timestamp=datetime.now()
    )
    embed.add_field(name="👤 Membre", value=f"{member.name}\n{member.mention}", inline=True)
    embed.add_field(name="🆔 ID", value=member.id, inline=True)
    embed.add_field(name="📅 Compte créé", value=f"<t:{int(member.created_at.timestamp())}:R>", inline=True)
    embed.set_thumbnail(url=member.avatar.url if member.avatar else member.default_avatar.url)
    embed.set_footer(text=f"Membres: {member.guild.member_count}")
    
    try:
        await channel.send(embed=embed)
    except:
        pass

async def log_member_leave(member: discord.Member):
    """Log quand un membre quitte"""
    channel = await get_logs_channel(member.guild)
    if not channel:
        return
    
    embed = discord.Embed(
        title="📤 Membre parti",
        description=f"{member.mention} a quitté le serveur",
        color=0xFF0000,
        timestamp=datetime.now()
    )
    embed.add_field(name="👤 Membre", value=f"{member.name}\n{member.mention}", inline=True)
    embed.add_field(name="🆔 ID", value=member.id, inline=True)
    
    if member.joined_at:
        embed.add_field(name="📅 A rejoint", value=f"<t:{int(member.joined_at.timestamp())}:R>", inline=True)
    
    if len(member.roles) > 1:
        roles = ", ".join([r.mention for r in member.roles[1:6]])
        if len(member.roles) > 6:
            roles += f" +{len(member.roles) - 6}"
        embed.add_field(name="🎭 Rôles", value=roles, inline=False)
    
    embed.set_thumbnail(url=member.avatar.url if member.avatar else member.default_avatar.url)
    embed.set_footer(text=f"Membres: {member.guild.member_count}")
    
    try:
        await channel.send(embed=embed)
    except:
        pass

async def log_member_update(before: discord.Member, after: discord.Member):
    """Log les modifications d'un membre"""
    channel = await get_logs_channel(before.guild)
    if not channel:
        return
    
    changes = []
    
    # Changement de pseudo
    if before.nick != after.nick:
        changes.append({
            "title": "✏️ Pseudo modifié",
            "fields": [
                ("📝 Avant", before.nick or "Aucun", True),
                ("📝 Après", after.nick or "Aucun", True)
            ]
        })
    
    # Changement de rôles
    if before.roles != after.roles:
        added = [r for r in after.roles if r not in before.roles]
        removed = [r for r in before.roles if r not in after.roles]
        
        if added or removed:
            fields = []
            if added:
                fields.append(("➕ Ajoutés", ", ".join([r.mention for r in added[:10]]), False))
            if removed:
                fields.append(("➖ Retirés", ", ".join([r.mention for r in removed[:10]]), False))
            
            changes.append({
                "title": "🎭 Rôles modifiés",
                "fields": fields
            })
    
    # Changement d'avatar
    if before.avatar != after.avatar:
        changes.append({
            "title": "🖼️ Avatar modifié",
            "fields": [
                ("🔗 Nouvel avatar", f"[Voir l'image]({after.avatar.url})" if after.avatar else "Avatar par défaut", False)
            ],
            "thumbnail": after.avatar.url if after.avatar else None
        })
    
    # Changement de timeout/mute
    if before.timed_out_until != after.timed_out_until:
        if after.timed_out_until:
            changes.append({
                "title": "🔇 Membre rendu muet",
                "fields": [
                    ("⏰ Jusqu'à", f"<t:{int(after.timed_out_until.timestamp())}:F>", False)
                ]
            })
        else:
            changes.append({
                "title": "🔊 Membre démuté",
                "fields": []
            })
    
    # Envoyer les logs
    for change in changes:
        embed = discord.Embed(
            title=change["title"],
            description=f"**Membre:** {after.mention}",
            color=PSG_BLUE,
            timestamp=datetime.now()
        )
        
        for field in change["fields"]:
            embed.add_field(name=field[0], value=field[1], inline=field[2])
        
        if "thumbnail" in change and change["thumbnail"]:
            embed.set_thumbnail(url=change["thumbnail"])
        else:
            embed.set_thumbnail(url=after.avatar.url if after.avatar else after.default_avatar.url)
        
        embed.set_footer(text=f"ID: {after.id}")
        
        try:
            await channel.send(embed=embed)
        except:
            pass

# ==================== LOGS MESSAGES ====================
async def log_message_delete(message: discord.Message):
    """Log quand un message est supprimé"""
    if message.author.bot:
        return
    
    channel = await get_logs_channel(message.guild)
    if not channel:
        return
    
    embed = discord.Embed(
        title="🗑️ Message supprimé",
        description=f"**Auteur:** {message.author.mention}\n**Salon:** {message.channel.mention}",
        color=PSG_RED,
        timestamp=datetime.now()
    )
    
    if message.content:
        content = message.content[:1024]
        embed.add_field(name="📝 Contenu", value=content, inline=False)
    
    if message.attachments:
        attachments = "\n".join([f"[{att.filename}]({att.url})" for att in message.attachments[:5]])
        embed.add_field(name="📎 Pièces jointes", value=attachments, inline=False)
    
    embed.set_footer(text=f"ID Message: {message.id} • ID Auteur: {message.author.id}")
    
    try:
        await channel.send(embed=embed)
    except:
        pass

async def log_message_edit(before: discord.Message, after: discord.Message):
    """Log quand un message est modifié"""
    if before.author.bot or before.content == after.content:
        return
    
    channel = await get_logs_channel(before.guild)
    if not channel:
        return
    
    embed = discord.Embed(
        title="✏️ Message modifié",
        description=f"**Auteur:** {before.author.mention}\n**Salon:** {before.channel.mention}\n[Aller au message]({after.jump_url})",
        color=0xFFA500,
        timestamp=datetime.now()
    )
    
    if before.content:
        embed.add_field(name="📝 Avant", value=before.content[:1024], inline=False)
    
    if after.content:
        embed.add_field(name="📝 Après", value=after.content[:1024], inline=False)
    
    embed.set_footer(text=f"ID Message: {before.id} • ID Auteur: {before.author.id}")
    
    try:
        await channel.send(embed=embed)
    except:
        pass

async def log_bulk_delete(messages: list, channel: discord.TextChannel):
    """Log quand plusieurs messages sont supprimés"""
    logs_channel = await get_logs_channel(channel.guild)
    if not logs_channel:
        return
    
    embed = discord.Embed(
        title="🗑️ Suppression en masse",
        description=f"**{len(messages)}** messages supprimés dans {channel.mention}",
        color=PSG_RED,
        timestamp=datetime.now()
    )
    
    # Compter les auteurs
    authors = {}
    for msg in messages:
        author_name = str(msg.author)
        authors[author_name] = authors.get(author_name, 0) + 1
    
    authors_text = "\n".join([f"{name}: {count}" for name, count in sorted(authors.items(), key=lambda x: x[1], reverse=True)[:10]])
    embed.add_field(name="👥 Auteurs", value=authors_text or "Aucun", inline=False)
    
    embed.set_footer(text=f"Salon: {channel.name}")
    
    try:
        await logs_channel.send(embed=embed)
    except:
        pass

# ==================== LOGS VOCAUX ====================
async def log_voice_state(member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
    """Log les changements de salon vocal"""
    channel = await get_logs_channel(member.guild)
    if not channel:
        return
    
    embed = None
    
    # Connexion
    if before.channel is None and after.channel is not None:
        embed = discord.Embed(
            title="🔊 Connexion vocale",
            description=f"{member.mention} a rejoint {after.channel.mention}",
            color=0x00FF00,
            timestamp=datetime.now()
        )
    
    # Déconnexion
    elif before.channel is not None and after.channel is None:
        embed = discord.Embed(
            title="🔇 Déconnexion vocale",
            description=f"{member.mention} a quitté {before.channel.mention}",
            color=0xFF0000,
            timestamp=datetime.now()
        )
    
    # Changement de salon
    elif before.channel != after.channel and before.channel is not None and after.channel is not None:
        embed = discord.Embed(
            title="🔄 Changement de salon vocal",
            description=f"{member.mention} est passé de {before.channel.mention} à {after.channel.mention}",
            color=PSG_BLUE,
            timestamp=datetime.now()
        )
    
    # Mute/Unmute
    elif before.self_mute != after.self_mute or before.mute != after.mute:
        if after.self_mute or after.mute:
            embed = discord.Embed(
                title="🔇 Membre muté (vocal)",
                description=f"{member.mention} s'est {'mis en' if after.self_mute else 'fait mettre en'} mute",
                color=0xFF6B6B,
                timestamp=datetime.now()
            )
        else:
            embed = discord.Embed(
                title="🔊 Membre démuté (vocal)",
                description=f"{member.mention} a {'enlevé son' if not after.self_mute else 'été démuté du'} mute",
                color=0x51CF66,
                timestamp=datetime.now()
            )
    
    # Deaf/Undeaf
    elif before.self_deaf != after.self_deaf or before.deaf != after.deaf:
        if after.self_deaf or after.deaf:
            embed = discord.Embed(
                title="🔇 Membre sourd (vocal)",
                description=f"{member.mention} s'est {'mis en' if after.self_deaf else 'fait mettre en'} sourd",
                color=0xFF6B6B,
                timestamp=datetime.now()
            )
        else:
            embed = discord.Embed(
                title="🔊 Membre entend (vocal)",
                description=f"{member.mention} {'entend à nouveau' if not after.self_deaf else 'a été retiré du mode sourd'}",
                color=0x51CF66,
                timestamp=datetime.now()
            )
    
    # Caméra/Partage d'écran
    elif before.self_video != after.self_video:
        if after.self_video:
            embed = discord.Embed(
                title="📹 Caméra activée",
                description=f"{member.mention} a activé sa caméra dans {after.channel.mention}",
                color=PSG_BLUE,
                timestamp=datetime.now()
            )
        else:
            embed = discord.Embed(
                title="📹 Caméra désactivée",
                description=f"{member.mention} a désactivé sa caméra",
                color=0x868E96,
                timestamp=datetime.now()
            )
    
    elif before.self_stream != after.self_stream:
        if after.self_stream:
            embed = discord.Embed(
                title="🖥️ Partage d'écran activé",
                description=f"{member.mention} partage son écran dans {after.channel.mention}",
                color=PSG_BLUE,
                timestamp=datetime.now()
            )
        else:
            embed = discord.Embed(
                title="🖥️ Partage d'écran désactivé",
                description=f"{member.mention} a arrêté de partager son écran",
                color=0x868E96,
                timestamp=datetime.now()
            )
    
    if embed:
        embed.set_thumbnail(url=member.avatar.url if member.avatar else member.default_avatar.url)
        embed.set_footer(text=f"Membre: {member.name}")
        
        try:
            await channel.send(embed=embed)
        except:
            pass

# ==================== LOGS SALONS ====================
async def log_channel_create(channel_obj):
    """Log la création d'un salon"""
    logs_channel = await get_logs_channel(channel_obj.guild)
    if not logs_channel:
        return
    
    channel_type = "Textuel" if isinstance(channel_obj, discord.TextChannel) else "Vocal" if isinstance(channel_obj, discord.VoiceChannel) else "Catégorie" if isinstance(channel_obj, discord.CategoryChannel) else "Autre"
    
    embed = discord.Embed(
        title="➕ Salon créé",
        description=f"**Nom:** {channel_obj.mention if isinstance(channel_obj, discord.TextChannel) else channel_obj.name}\n**Type:** {channel_type}",
        color=0x00FF00,
        timestamp=datetime.now()
    )
    embed.add_field(name="🆔 ID", value=channel_obj.id, inline=True)
    
    if channel_obj.category:
        embed.add_field(name="📁 Catégorie", value=channel_obj.category.name, inline=True)
    
    try:
        await logs_channel.send(embed=embed)
    except:
        pass

async def log_channel_delete(channel_obj):
    """Log la suppression d'un salon"""
    logs_channel = await get_logs_channel(channel_obj.guild)
    if not logs_channel:
        return
    
    channel_type = "Textuel" if isinstance(channel_obj, discord.TextChannel) else "Vocal" if isinstance(channel_obj, discord.VoiceChannel) else "Catégorie" if isinstance(channel_obj, discord.CategoryChannel) else "Autre"
    
    embed = discord.Embed(
        title="➖ Salon supprimé",
        description=f"**Nom:** {channel_obj.name}\n**Type:** {channel_type}",
        color=PSG_RED,
        timestamp=datetime.now()
    )
    embed.add_field(name="🆔 ID", value=channel_obj.id, inline=True)
    
    if channel_obj.category:
        embed.add_field(name="📁 Catégorie", value=channel_obj.category.name, inline=True)
    
    try:
        await logs_channel.send(embed=embed)
    except:
        pass

async def log_channel_update(before, after):
    """Log les modifications d'un salon"""
    logs_channel = await get_logs_channel(before.guild)
    if not logs_channel:
        return
    
    changes = []
    
    # Changement de nom
    if before.name != after.name:
        changes.append(("📝 Nom", f"{before.name} → {after.name}"))
    
    # Changement de topic (pour TextChannel)
    if isinstance(before, discord.TextChannel) and before.topic != after.topic:
        changes.append(("📋 Description", f"{before.topic or 'Aucune'} → {after.topic or 'Aucune'}"))
    
    # Changement de catégorie
    if before.category != after.category:
        changes.append(("📁 Catégorie", f"{before.category.name if before.category else 'Aucune'} → {after.category.name if after.category else 'Aucune'}"))
    
    # Changement de position
    if before.position != after.position:
        changes.append(("🔢 Position", f"{before.position} → {after.position}"))
    
    # Changement de slowmode (pour TextChannel)
    if isinstance(before, discord.TextChannel) and before.slowmode_delay != after.slowmode_delay:
        changes.append(("⏱️ Mode lent", f"{before.slowmode_delay}s → {after.slowmode_delay}s"))
    
    # Changement NSFW
    if isinstance(before, discord.TextChannel) and before.nsfw != after.nsfw:
        changes.append(("🔞 NSFW", f"{'Oui' if after.nsfw else 'Non'}"))
    
    if changes:
        embed = discord.Embed(
            title="✏️ Salon modifié",
            description=f"**Salon:** {after.mention if isinstance(after, discord.TextChannel) else after.name}",
            color=PSG_BLUE,
            timestamp=datetime.now()
        )
        
        for name, value in changes:
            embed.add_field(name=name, value=value, inline=False)
        
        embed.set_footer(text=f"ID: {after.id}")
        
        try:
            await logs_channel.send(embed=embed)
        except:
            pass

# ==================== LOGS RÔLES ====================
async def log_role_create(role: discord.Role):
    """Log la création d'un rôle"""
    channel = await get_logs_channel(role.guild)
    if not channel:
        return
    
    embed = discord.Embed(
        title="🎭 Rôle créé",
        description=f"**Nom:** {role.mention}",
        color=role.color if role.color != discord.Color.default() else 0x00FF00,
        timestamp=datetime.now()
    )
    embed.add_field(name="🆔 ID", value=role.id, inline=True)
    embed.add_field(name="🎨 Couleur", value=str(role.color), inline=True)
    embed.add_field(name="🔢 Position", value=role.position, inline=True)
    embed.add_field(name="📌 Affiché séparément", value="Oui" if role.hoist else "Non", inline=True)
    embed.add_field(name="🔗 Mentionnable", value="Oui" if role.mentionable else "Non", inline=True)
    
    try:
        await channel.send(embed=embed)
    except:
        pass

async def log_role_delete(role: discord.Role):
    """Log la suppression d'un rôle"""
    channel = await get_logs_channel(role.guild)
    if not channel:
        return
    
    embed = discord.Embed(
        title="🎭 Rôle supprimé",
        description=f"**Nom:** {role.name}",
        color=role.color if role.color != discord.Color.default() else PSG_RED,
        timestamp=datetime.now()
    )
    embed.add_field(name="🆔 ID", value=role.id, inline=True)
    embed.add_field(name="🎨 Couleur", value=str(role.color), inline=True)
    embed.add_field(name="👥 Membres", value=len(role.members), inline=True)
    
    try:
        await channel.send(embed=embed)
    except:
        pass

async def log_role_update(before: discord.Role, after: discord.Role):
    """Log les modifications d'un rôle"""
    channel = await get_logs_channel(before.guild)
    if not channel:
        return
    
    changes = []
    
    # Changement de nom
    if before.name != after.name:
        changes.append(("📝 Nom", f"{before.name} → {after.name}"))
    
    # Changement de couleur
    if before.color != after.color:
        changes.append(("🎨 Couleur", f"{before.color} → {after.color}"))
    
    # Changement de position
    if before.position != after.position:
        changes.append(("🔢 Position", f"{before.position} → {after.position}"))
    
    # Changement hoist
    if before.hoist != after.hoist:
        changes.append(("📌 Affiché séparément", f"{'Oui' if after.hoist else 'Non'}"))
    
    # Changement mentionable
    if before.mentionable != after.mentionable:
        changes.append(("🔗 Mentionnable", f"{'Oui' if after.mentionable else 'Non'}"))
    
    # Changement de permissions
    if before.permissions != after.permissions:
        changes.append(("🔐 Permissions", "Modifiées"))
    
    if changes:
        embed = discord.Embed(
            title="✏️ Rôle modifié",
            description=f"**Rôle:** {after.mention}",
            color=after.color if after.color != discord.Color.default() else PSG_BLUE,
            timestamp=datetime.now()
        )
        
        for name, value in changes:
            embed.add_field(name=name, value=value, inline=False)
        
        embed.set_footer(text=f"ID: {after.id}")
        
        try:
            await channel.send(embed=embed)
        except:
            pass

# ==================== LOGS SERVEUR ====================
async def log_guild_update(before: discord.Guild, after: discord.Guild):
    """Log les modifications du serveur"""
    channel = await get_logs_channel(before)
    if not channel:
        return
    
    changes = []
    
    # Changement de nom
    if before.name != after.name:
        changes.append(("📝 Nom", f"{before.name} → {after.name}"))
    
    # Changement d'icône
    if before.icon != after.icon:
        changes.append(("🖼️ Icône", "Modifiée"))
    
    # Changement de bannière
    if before.banner != after.banner:
        changes.append(("🎨 Bannière", "Modifiée"))
    
    # Changement de niveau de vérification
    if before.verification_level != after.verification_level:
        changes.append(("🔒 Niveau de vérification", f"{before.verification_level.name} → {after.verification_level.name}"))
    
    if changes:
        embed = discord.Embed(
            title="⚙️ Serveur modifié",
            color=PSG_BLUE,
            timestamp=datetime.now()
        )
        
        for name, value in changes:
            embed.add_field(name=name, value=value, inline=False)
        
        if after.icon:
            embed.set_thumbnail(url=after.icon.url)
        
        try:
            await channel.send(embed=embed)
        except:
            pass

# ==================== LOGS COMMANDES ====================
async def log_command_use(interaction: discord.Interaction, command_name: str, success: bool = True, error: str = None):
    """Log l'utilisation d'une commande"""
    channel = await get_logs_channel(interaction.guild)
    if not channel:
        return
    
    # Couleur selon le résultat
    if success:
        color = PSG_BLUE
        title = "✅ Commande exécutée"
    else:
        color = PSG_RED
        title = "❌ Commande échouée"
    
    embed = discord.Embed(
        title=title,
        description=f"**Utilisateur:** {interaction.user.mention}\n**Commande:** `/{command_name}`",
        color=color,
        timestamp=datetime.now()
    )
    
    # Salon où la commande a été utilisée
    embed.add_field(
        name="📺 Salon",
        value=interaction.channel.mention if interaction.channel else "DM",
        inline=True
    )
    
    # Paramètres de la commande (si disponibles)
    if interaction.data:
        options = interaction.data.get('options', [])
        if options:
            params_text = []
            for option in options:
                value = option.get('value', 'N/A')
                # Limiter la longueur pour éviter spam
                if isinstance(value, str) and len(value) > 100:
                    value = value[:97] + "..."
                params_text.append(f"• {option['name']}: `{value}`")
            
            if params_text:
                embed.add_field(
                    name="⚙️ Paramètres",
                    value="\n".join(params_text[:5]),  # Max 5 paramètres
                    inline=False
                )
    
    # Si erreur, l'afficher
    if error:
        embed.add_field(
            name="⚠️ Erreur",
            value=f"```{error[:500]}```",  # Limiter à 500 caractères
            inline=False
        )
    
    embed.set_footer(text=f"ID: {interaction.user.id}")
    
    try:
        await channel.send(embed=embed)
    except:
        pass