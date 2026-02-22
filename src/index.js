// src/index.js - Point d'entrée du bot PSG Dream League (Node.js)
const { Client, GatewayIntentBits, Partials } = require('discord.js');
const fs = require('fs');

console.log('🔍 Vérification de l\'environnement...');
console.log(`📁 Dossier de travail: ${process.cwd()}`);
console.log(`🟢 Node.js version: ${process.version}`);

const { TOKEN, DATA_DIR, PACKS_DIR } = require('./config/settings');
console.log(`🔑 Token détecté: ${TOKEN.slice(0, 10)}...`);

const { setupEvents } = require('./handlers/events');
const { setupCommands } = require('./handlers/commands');
const { setupAutoReminder } = require('./commands/auto_reminder');

// Créer les dossiers nécessaires
fs.mkdirSync(DATA_DIR, { recursive: true });
fs.mkdirSync(PACKS_DIR, { recursive: true });
console.log('✅ Dossiers créés/vérifiés');

// Créer le client Discord
const client = new Client({
  intents: [
    GatewayIntentBits.Guilds,
    GatewayIntentBits.GuildMembers,
    GatewayIntentBits.GuildMessages,
    GatewayIntentBits.MessageContent,
    GatewayIntentBits.GuildVoiceStates,
    GatewayIntentBits.GuildMessageReactions,
    GatewayIntentBits.DirectMessages,
  ],
  partials: [Partials.Message, Partials.Channel, Partials.Reaction, Partials.GuildMember],
});

console.log('\n🔴🔵 Initialisation du bot PSG...');

// Setup des événements, commandes et rappels
setupEvents(client);
console.log('✅ Événements configurés');

setupCommands(client);
console.log('✅ Commandes configurées');

setupAutoReminder(client);
console.log('✅ Système de rappel automatique configuré');

// Connexion
console.log('\n📋 Connexion à Discord...');
client.login(TOKEN).catch((error) => {
  if (error.code === 'TokenInvalid' || error.message?.includes('TOKEN_INVALID')) {
    console.error('\n❌ ERREUR DE CONNEXION: Token invalide');
    console.error('\n🔧 Solutions:');
    console.error('1. Vérifie que ton fichier .env contient bien DISCORD_TOKEN=...');
    console.error('2. Va sur https://discord.com/developers/applications');
    console.error('3. Reset ton token et copie-le dans .env');
    console.error('4. Vérifie qu\'il n\'y a pas d\'espaces avant/après le token');
  } else {
    console.error('\n❌ ERREUR INATTENDUE:', error.message);
  }
  process.exit(1);
});

// Gestion des erreurs non capturées
process.on('unhandledRejection', (reason, promise) => {
  console.error('⚠️ Rejet non géré:', reason);
});

process.on('uncaughtException', (error) => {
  console.error('💥 Exception non capturée:', error);
});

module.exports = { client };
