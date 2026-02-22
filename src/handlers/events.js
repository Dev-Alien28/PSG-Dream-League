// src/handlers/events.js - Gestion des événements Discord
const { initFiles, getUserData, saveUserData, getMinigameChannel, getNextMinigameTime } = require('../utils/database');
const { initServerConfig, isCoinsDisabledChannel } = require('../utils/permissions');
const {
  logMemberJoin, logMemberLeave, logMemberUpdate,
  logMessageDelete, logMessageEdit, logBulkDelete,
  logVoiceState, logChannelCreate, logChannelDelete, logChannelUpdate,
  logRoleCreate, logRoleDelete, logRoleUpdate,
  logGuildUpdate,
} = require('../utils/logs');
const { PSG_BLUE, COINS_PER_MESSAGE_INTERVAL, MIN_MESSAGE_LENGTH } = require('../config/settings');

function setupEvents(client) {

  // ==================== READY ====================
  client.once('clientReady', async () => {
    initFiles();
    console.log(`🔴🔵 Bot PSG connecté en tant que ${client.user.tag}`);
    console.log(`📊 Serveurs : ${client.guilds.cache.size}`);

    for (const guild of client.guilds.cache.values()) {
      initServerConfig(String(guild.id), guild.name);
    }

    try {
      const {REST, Routes, MessageFlags } = require('discord.js');
      const { TOKEN } = require('../config/settings');
      const rest = new REST().setToken(TOKEN);
      const commands = buildCommandsJSON(client);
      const data = await rest.put(
        Routes.applicationCommands(client.user.id),
        { body: commands },
      );
      console.log(`✅ ${data.length} commande(s) slash synchronisée(s)`);
      console.log('📝 Système de logs activé');
      console.log('⚡ Système de mini-jeu activé');
      console.log(`🔒 Anti-spam: longueur min = ${MIN_MESSAGE_LENGTH} caractères`);
    } catch (e) {
      console.error('❌ Erreur de synchronisation:', e.message);
    }

    // Démarrer la boucle mini-jeu (toutes les minutes)
    setInterval(async () => {
      for (const guild of client.guilds.cache.values()) {
        const guildId = String(guild.id);
        const channelId = getMinigameChannel(guildId);
        if (!channelId) continue;

        try {
          const nextTime = getNextMinigameTime(guildId);
          if (Date.now() >= nextTime.getTime()) {
            console.log(`⚡ Mini-jeu déclenché sur ${guild.name}`);
            const { spawnMinigame } = require('../commands/minigame');
            await spawnMinigame(client, guildId);
          }
        } catch (e) {
          console.error(`❌ Erreur mini-jeu pour ${guild.name}:`, e.message);
        }
      }
    }, 60000);
  });

  // ==================== GUILD JOIN ====================
  client.on('guildCreate', (guild) => {
    initServerConfig(String(guild.id), guild.name);
    console.log(`✅ Configuration créée pour ${guild.name} (${guild.id})`);
  });

  // ==================== MEMBRES ====================
  client.on('guildMemberAdd', async (member) => {
    await logMemberJoin(member);
    getUserData(String(member.guild.id), String(member.id)); // init utilisateur
  });

  client.on('guildMemberRemove', async (member) => {
    await logMemberLeave(member);
  });

  client.on('guildMemberUpdate', async (oldMember, newMember) => {
    await logMemberUpdate(oldMember, newMember);
  });

  // ==================== MESSAGES ====================
  client.on('messageDelete', async (message) => {
    await logMessageDelete(message);
  });

  client.on('messageUpdate', async (oldMessage, newMessage) => {
    await logMessageEdit(oldMessage, newMessage);
  });

  client.on('messageDeleteBulk', async (messages) => {
    const first = messages.first();
    if (first) await logBulkDelete(messages, first.channel);
  });

  // Système de coins par message
  client.on('messageCreate', async (message) => {
    if (message.author.bot) return;
    if (!message.guild) return;
    if (message.content.startsWith('/')) return;

    const guildId = String(message.guild.id);
    const userId = String(message.author.id);
    const channelId = String(message.channel.id);

    if (isCoinsDisabledChannel(guildId, channelId)) return;

    const clean = message.content.trim();
    if (clean.length < MIN_MESSAGE_LENGTH) return;

    const userData = getUserData(guildId, userId);
    userData.messages++;

    if (userData.messages % COINS_PER_MESSAGE_INTERVAL === 0) {
      userData.coins++;
      console.log(`💰 ${message.author.username} a gagné 1 coin sur ${message.guild.name} (${clean.length} car.)`);
    }

    saveUserData(guildId, userId, userData);
  });

  // ==================== VOCAL ====================
  client.on('voiceStateUpdate', async (oldState, newState) => {
    await logVoiceState(newState.member, oldState, newState);
  });

  // ==================== SALONS ====================
  client.on('channelCreate', async (channel) => {
    await logChannelCreate(channel);
  });

  client.on('channelDelete', async (channel) => {
    await logChannelDelete(channel);
  });

  client.on('channelUpdate', async (oldChannel, newChannel) => {
    await logChannelUpdate(oldChannel, newChannel);
  });

  // ==================== RÔLES ====================
  client.on('roleCreate', async (role) => {
    await logRoleCreate(role);
  });

  client.on('roleDelete', async (role) => {
    await logRoleDelete(role);
  });

  client.on('roleUpdate', async (oldRole, newRole) => {
    await logRoleUpdate(oldRole, newRole);
  });

  // ==================== SERVEUR ====================
  client.on('guildUpdate', async (oldGuild, newGuild) => {
    await logGuildUpdate(oldGuild, newGuild);
  });
}

// Définitions des slash commands pour la synchronisation API
function buildCommandsJSON() {
  const { ApplicationCommandOptionType } = require('discord.js');

  return [
    { name: 'solde', description: 'Consulte ton solde de PSG Coins' },
    { name: 'packs', description: 'Voir les packs disponibles et acheter avec des boutons' },
    {
      name: 'collection',
      description: 'Voir ta collection de cartes ou celle d\'un autre membre',
      options: [{ name: 'membre', description: '(Optionnel) Le membre dont tu veux voir la collection', type: ApplicationCommandOptionType.User, required: false }],
    },
    {
      name: 'addcoins',
      description: '[ADMIN] Ajouter des PSG Coins à un membre',
      options: [
        { name: 'membre', description: 'Le membre qui va recevoir les coins', type: ApplicationCommandOptionType.User, required: true },
        { name: 'montant', description: 'Nombre de PSG Coins à ajouter', type: ApplicationCommandOptionType.Integer, required: true },
      ],
    },
    {
      name: 'removecoins',
      description: '[ADMIN] Retirer des PSG Coins à un membre',
      options: [
        { name: 'membre', description: 'Le membre qui va perdre les coins', type: ApplicationCommandOptionType.User, required: true },
        { name: 'montant', description: 'Nombre de PSG Coins à retirer', type: ApplicationCommandOptionType.Integer, required: true },
      ],
    },
    {
      name: 'setcoins',
      description: '[ADMIN] Définir le solde exact d\'un membre',
      options: [
        { name: 'membre', description: 'Le membre dont tu veux modifier le solde', type: ApplicationCommandOptionType.User, required: true },
        { name: 'montant', description: 'Nouveau solde en PSG Coins', type: ApplicationCommandOptionType.Integer, required: true },
      ],
    },
    {
      name: 'give',
      description: '[ADMIN] Donner une carte à un membre',
      options: [
        { name: 'carte_id', description: "L'ID de la carte à donner (ex: gk_donnarumma_basic)", type: ApplicationCommandOptionType.String, required: true },
        { name: 'membre', description: 'Le membre qui va recevoir la carte', type: ApplicationCommandOptionType.User, required: true },
        { name: 'raison', description: '(Optionnel) Raison ou message pour le membre', type: ApplicationCommandOptionType.String, required: false },
      ],
    },
    { name: 'config', description: '[OWNER] Configurer le bot de manière interactive' },
  ];
}

module.exports = { setupEvents };