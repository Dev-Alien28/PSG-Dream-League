// src/commands/admin.js - Commandes admin (addcoins, removecoins, setcoins)
const {EmbedBuilder, MessageFlags } = require('discord.js');
const { getUserData, saveUserData } = require('../utils/database');
const { checkRolePermission } = require('../utils/permissions');
const { PSG_BLUE, PSG_RED, PSG_FOOTER_ICON } = require('../config/settings');

const PSG_LOGO = PSG_FOOTER_ICON;

function buildFooter(guild) {
  return { text: `Paris Saint-Germain • ${guild.name}`, iconURL: PSG_LOGO };
}

async function addCoinsCommand(interaction, membre, montant) {
  if (!checkRolePermission(interaction, 'admin')) {
    return interaction.reply({
      embeds: [new EmbedBuilder().setTitle('❌ Accès refusé').setDescription("Tu n'as pas les permissions administrateur pour utiliser cette commande.").setColor(PSG_RED)],
      flags: MessageFlags.Ephemeral,
    });
  }

  const guildId = interaction.guildId;
  const userId = membre.id;
  const userData = getUserData(guildId, userId);
  const ancienSolde = userData.coins;
  userData.coins += montant;
  saveUserData(guildId, userId, userData);

  const embed = new EmbedBuilder()
    .setTitle('✅ PSG Coins ajoutés!')
    .setDescription(`Tu as ajouté **${montant} PSG Coins** à ${membre}!`)
    .setColor(PSG_BLUE)
    .addFields(
      { name: '💰 Ancien solde', value: `${ancienSolde} 🪙`, inline: true },
      { name: '💎 Nouveau solde', value: `${userData.coins} 🪙`, inline: true },
    )
    .setFooter(buildFooter(interaction.guild));

  await interaction.reply({ embeds: [embed] });

  try {
    const notifEmbed = new EmbedBuilder()
      .setTitle('💰 Tu as reçu des PSG Coins!')
      .setDescription(`Un administrateur de **${interaction.guild.name}** t'a ajouté **${montant} PSG Coins**!`)
      .setColor(PSG_BLUE)
      .addFields({ name: '💎 Nouveau solde', value: `${userData.coins} 🪙`, inline: false })
      .setFooter(buildFooter(interaction.guild));
    await membre.send({ embeds: [notifEmbed] });
  } catch { /* DM désactivés */ }
}

async function removeCoinsCommand(interaction, membre, montant) {
  if (!checkRolePermission(interaction, 'admin')) {
    return interaction.reply({
      embeds: [new EmbedBuilder().setTitle('❌ Accès refusé').setDescription("Tu n'as pas les permissions administrateur pour utiliser cette commande.").setColor(PSG_RED)],
      flags: MessageFlags.Ephemeral,
    });
  }

  const guildId = interaction.guildId;
  const userId = membre.id;
  const userData = getUserData(guildId, userId);

  if (userData.coins < montant) {
    return interaction.reply({
      embeds: [new EmbedBuilder()
        .setTitle('⚠️ Attention')
        .setDescription(`${membre} n'a que **${userData.coins} PSG Coins** sur ce serveur.\n\nTu essaies d'en retirer **${montant}**. Veux-tu vraiment mettre son solde à 0?`)
        .setColor(PSG_RED)
        .addFields(
          { name: '💰 Solde actuel', value: `${userData.coins} 🪙`, inline: true },
          { name: '⛔ Montant à retirer', value: `${montant} 🪙`, inline: true },
        )],
      flags: MessageFlags.Ephemeral,
    });
  }

  const ancienSolde = userData.coins;
  userData.coins -= montant;
  saveUserData(guildId, userId, userData);

  const embed = new EmbedBuilder()
    .setTitle('✅ PSG Coins retirés!')
    .setDescription(`Tu as retiré **${montant} PSG Coins** à ${membre}!`)
    .setColor(PSG_BLUE)
    .addFields(
      { name: '💰 Ancien solde', value: `${ancienSolde} 🪙`, inline: true },
      { name: '💎 Nouveau solde', value: `${userData.coins} 🪙`, inline: true },
    )
    .setFooter(buildFooter(interaction.guild));

  await interaction.reply({ embeds: [embed] });

  try {
    const notifEmbed = new EmbedBuilder()
      .setTitle('⚠️ Des PSG Coins ont été retirés')
      .setDescription(`Un administrateur de **${interaction.guild.name}** t'a retiré **${montant} PSG Coins**.`)
      .setColor(PSG_RED)
      .addFields({ name: '💎 Nouveau solde', value: `${userData.coins} 🪙`, inline: false })
      .setFooter(buildFooter(interaction.guild));
    await membre.send({ embeds: [notifEmbed] });
  } catch { /* DM désactivés */ }
}

async function setCoinsCommand(interaction, membre, montant) {
  if (!checkRolePermission(interaction, 'admin')) {
    return interaction.reply({
      embeds: [new EmbedBuilder().setTitle('❌ Accès refusé').setDescription("Tu n'as pas les permissions administrateur pour utiliser cette commande.").setColor(PSG_RED)],
      flags: MessageFlags.Ephemeral,
    });
  }

  const guildId = interaction.guildId;
  const userId = membre.id;
  const userData = getUserData(guildId, userId);
  const ancienSolde = userData.coins;
  userData.coins = montant;
  saveUserData(guildId, userId, userData);

  const embed = new EmbedBuilder()
    .setTitle('✅ Solde modifié!')
    .setDescription(`Tu as défini le solde de ${membre} à **${montant} PSG Coins** sur ce serveur!`)
    .setColor(PSG_BLUE)
    .addFields(
      { name: '💰 Ancien solde', value: `${ancienSolde} 🪙`, inline: true },
      { name: '💎 Nouveau solde', value: `${montant} 🪙`, inline: true },
    )
    .setFooter(buildFooter(interaction.guild));

  await interaction.reply({ embeds: [embed] });

  try {
    const notifEmbed = new EmbedBuilder()
      .setTitle('💰 Ton solde a été modifié')
      .setDescription(`Un administrateur de **${interaction.guild.name}** a défini ton solde à **${montant} PSG Coins**.`)
      .setColor(PSG_BLUE)
      .setFooter(buildFooter(interaction.guild));
    await membre.send({ embeds: [notifEmbed] });
  } catch { /* DM désactivés */ }
}

module.exports = { addCoinsCommand, removeCoinsCommand, setCoinsCommand };