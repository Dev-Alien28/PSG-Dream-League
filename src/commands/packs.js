// src/commands/packs.js - Boutique de packs avec boutons
const {EmbedBuilder, ActionRowBuilder, ButtonBuilder, ButtonStyle, AttachmentBuilder, MessageFlags } = require('discord.js');
const {
  getUserData, saveUserData, loadPackCards,
  canClaimFreePack, claimFreePack, getFreePackCooldown,
} = require('../utils/database');
const { checkChannelPermission, getAllowedChannel } = require('../utils/permissions');
const { PSG_BLUE, PSG_RED, PACKS_CONFIG, CARD_TYPES, PSG_FOOTER_ICON } = require('../config/settings');
const { getRarityColor, getRarityEmoji, getRarityCardImage, formatCardStats, weightedRandom } = require('../utils/cardHelpers');

const fs = require('fs');
const path = require('path');

// ─── Helpers image ────────────────────────────────────────────────────────────

// ✅ __dirname = src/commands/ → '..' remonte à src/ → + imagePath = src/images/cards/Carte_X.png
function getCardImageFile(card) {
  const imagePath = card.image || '';
  if (imagePath.startsWith('http://') || imagePath.startsWith('https://')) return null;

  const absolutePath = path.join(__dirname, '..', imagePath);
  if (imagePath && fs.existsSync(absolutePath)) {
    try {
      const filename = path.basename(absolutePath);
      return new AttachmentBuilder(absolutePath, { name: filename });
    } catch (e) {
      console.error(`❌ Erreur lecture image ${absolutePath}:`, e);
      return null;
    }
  }
  return null;
}

function getCardImageUrlLocal(card) {
  const imagePath = card.image || '';
  if (imagePath && (imagePath.startsWith('http://') || imagePath.startsWith('https://'))) {
    if (imagePath.length <= 2048) return imagePath;
  }
  return null;
}

// ─── Commande /packs ──────────────────────────────────────────────────────────

async function packsCommand(interaction) {
  if (!checkChannelPermission(interaction, 'packs')) {
    const allowedChannel = getAllowedChannel(interaction.guildId, 'packs', interaction.client);
    const embed = new EmbedBuilder().setTitle('❌ Salon non autorisé').setColor(PSG_RED);
    if (allowedChannel) {
      embed.setDescription(`Cette commande ne peut pas être utilisée dans ce salon.\n\n➡️ **Utilise plutôt :** ${allowedChannel}`);
    } else {
      embed.setDescription("Cette commande ne peut pas être utilisée dans ce salon.\n\nAucun salon n'est configuré. Contacte un administrateur avec `/config`.");
    }
    return interaction.reply({ embeds: [embed], flags: MessageFlags.Ephemeral });
  }

  const guildId = interaction.guildId;
  const userId = interaction.user.id;
  const userData = getUserData(guildId, userId);

  const embed = new EmbedBuilder()
    .setTitle('🎁 BOUTIQUE PSG - PACKS DISPONIBLES')
    .setDescription('Clique sur un bouton ci-dessous pour acheter un pack !\nChaque pack contient **1 carte exclusive** avec des taux de drop différents.\n\u200b')
    .setColor(PSG_BLUE)
    .setFooter({
      text: `Ton solde : ${userData.coins} PSG Coins • ${interaction.guild.name} • Expire dans 1 min`,
      iconURL: PSG_FOOTER_ICON,
    });

  const packEntries = Object.entries(PACKS_CONFIG).filter(([k]) => k !== 'pack_event');

  for (let i = 0; i < packEntries.length; i++) {
    const [packKey, packInfo] = packEntries[i];
    let extraInfo = '';
    if (packKey === 'free_pack') {
      if (canClaimFreePack(guildId, userId)) {
        extraInfo = '\n✅ **Disponible maintenant !**';
      } else {
        const cooldown = getFreePackCooldown(guildId, userId);
        const hours = Math.floor(cooldown / 3600);
        const minutes = Math.floor((cooldown % 3600) / 60);
        extraInfo = `\n⏰ Disponible dans **${hours}h${String(minutes).padStart(2, '0')}m**`;
      }
    }
    const value = `${packInfo.description}${extraInfo}${i < packEntries.length - 1 ? '\n\u200b' : ''}`;
    embed.addFields({ name: `${packInfo.emoji} **${packInfo.nom}**`, value, inline: false });
  }

  // Boutons
  const rows = [];
  let row = new ActionRowBuilder();
  let btnCount = 0;

  for (const [packKey, packInfo] of packEntries) {
    if (btnCount === 5) {
      rows.push(row);
      row = new ActionRowBuilder();
      btnCount = 0;
    }
    const style = packKey === 'free_pack' ? ButtonStyle.Success : ButtonStyle.Primary;
    const btn = new ButtonBuilder()
      .setCustomId(`buy_pack_${packKey}_${userId}`)
      .setLabel(`${packInfo.emoji} ${packInfo.nom} - ${packInfo.prix} 🪙`)
      .setStyle(style);
    row.addComponents(btn);
    btnCount++;
  }
  if (btnCount > 0) rows.push(row);

  // ✅ Chemin absolu pour Boite.png
  const boitePath = path.join(__dirname, '..', 'images', 'Boite.png');
  const replyOptions = { embeds: [embed], components: rows, flags: MessageFlags.Ephemeral };

  if (fs.existsSync(boitePath)) {
    const file = new AttachmentBuilder(boitePath, { name: 'Boite.png' });
    embed.setImage('attachment://Boite.png');
    replyOptions.files = [file];
  }

  await interaction.reply(replyOptions);

  // Auto-suppression après 60 secondes
  setTimeout(async () => {
    try {
      await interaction.deleteReply();
    } catch { /* déjà supprimé */ }
  }, 60000);
}

// ─── Achat d'un pack ──────────────────────────────────────────────────────────

async function buyPack(interaction, packKey) {
  const guildId = interaction.guildId;
  const userId = interaction.user.id;
  const userData = getUserData(guildId, userId);
  const packInfo = PACKS_CONFIG[packKey];

  if (!packInfo) {
    return interaction.reply({ content: '❌ Pack inconnu.', flags: MessageFlags.Ephemeral });
  }

  // ── Pack gratuit ──
  if (packKey === 'free_pack') {
    if (!canClaimFreePack(guildId, userId)) {
      const cooldown = getFreePackCooldown(guildId, userId);
      const hours = Math.floor(cooldown / 3600);
      const minutes = Math.floor((cooldown % 3600) / 60);
      return interaction.reply({
        embeds: [
          new EmbedBuilder()
            .setTitle('⏰ Pack gratuit indisponible')
            .setDescription(`Tu as déjà réclamé ton pack gratuit !\n\n**Prochain pack dans :** ${hours}h ${minutes}m`)
            .setColor(PSG_RED)
            .setFooter({ text: 'Le pack gratuit se recharge toutes les 24 heures' }),
        ],
        flags: MessageFlags.Ephemeral,
      });
    }
    claimFreePack(guildId, userId);

  // ── Solde insuffisant ──
  } else if (userData.coins < packInfo.prix) {
    return interaction.reply({
      embeds: [
        new EmbedBuilder()
          .setTitle('❌ Solde insuffisant')
          .setDescription("Tu n'as pas assez de PSG Coins pour acheter ce pack !")
          .setColor(PSG_RED)
          .addFields(
            { name: '💰 Prix du pack', value: `${packInfo.prix} 🪙`, inline: true },
            { name: '💎 Ton solde', value: `${userData.coins} 🪙`, inline: true },
            { name: '❗ Il te manque', value: `${packInfo.prix - userData.coins} 🪙`, inline: true },
          )
          .setFooter({ text: 'Contacte un administrateur pour obtenir des PSG Coins !' }),
      ],
      flags: MessageFlags.Ephemeral,
    });
  }

  // ── Charger les cartes ──
  const allCards = loadPackCards(packKey);
  if (!allCards.length) {
    return interaction.reply({
      embeds: [
        new EmbedBuilder()
          .setTitle('❌ Erreur')
          .setDescription('Aucune carte disponible dans ce pack. Contacte un administrateur.')
          .setColor(PSG_RED),
      ],
      flags: MessageFlags.Ephemeral,
    });
  }

  // ── Tirage pondéré ──
  const chosenRarity = weightedRandom(packInfo.drop_rates);
  const cardsOfRarity = allCards.filter(c => c.rareté === chosenRarity);
  const card = cardsOfRarity.length
    ? cardsOfRarity[Math.floor(Math.random() * cardsOfRarity.length)]
    : allCards[Math.floor(Math.random() * allCards.length)];

  // ── Déduire coins & sauvegarder ──
  const freshData = getUserData(guildId, userId);
  if (packKey !== 'free_pack') freshData.coins -= packInfo.prix;
  freshData.collection.push(card);
  saveUserData(guildId, userId, freshData);

  // ── Construire l'embed ──
  const typeEmoji = CARD_TYPES[card.type]?.emoji || '🎴';
  const embed = new EmbedBuilder()
    .setTitle(`🎁 ${packInfo.emoji} ${packInfo.nom} ouvert !`)
    .setDescription(`# 🎴 ${card.nom}`)
    .setColor(getRarityColor(card.rareté))
    .addFields(
      { name: `${typeEmoji} Type`, value: card.type ? card.type.charAt(0).toUpperCase() + card.type.slice(1) : 'Joueur', inline: true },
      { name: '🎲 Chance de drop', value: `${packInfo.drop_rates[card.rareté] ?? '?'}%`, inline: true },
      { name: '\u200b', value: '\u200b', inline: true },
      { name: '📊 Statistiques', value: formatCardStats(card), inline: false },
      { name: '💰 Nouveau solde', value: `${freshData.coins} 🪙`, inline: true },
      { name: '🎴 Collection', value: `${freshData.collection.length} cartes`, inline: true },
    )
    .setFooter({ text: `Paris Saint-Germain • ${interaction.guild.name}`, iconURL: PSG_FOOTER_ICON });

  const mentionContent = `🎉 ${interaction.user} a obtenu une carte !`;

  // ── Gestion image : priorité fichier local > URL > thumbnail par rareté ──
  const imageFile = getCardImageFile(card);

  if (imageFile) {
    embed.setImage(`attachment://${imageFile.name}`);
    return interaction.reply({ content: mentionContent, embeds: [embed], files: [imageFile] });
  }

  const cardImageUrl = getCardImageUrlLocal(card);
  if (cardImageUrl) {
    embed.setImage(cardImageUrl);
  } else {
    embed.setThumbnail(getRarityCardImage(card.rareté || 'Basic'));
  }

  return interaction.reply({ content: mentionContent, embeds: [embed] });
}

module.exports = { packsCommand, buyPack };