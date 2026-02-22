// src/commands/minigame.js - Mini-jeu Joueur Fuyard
const {EmbedBuilder, ActionRowBuilder, ButtonBuilder, ButtonStyle, MessageFlags } = require('discord.js');
const { loadPackCards, addCardToUser, getMinigameChannel, setMinigameChannel, scheduleNextMinigame, getNextMinigameTime } = require('../utils/database');
const { PSG_BLUE, PSG_RED, MINIGAME_CONFIG, PACKS_CONFIG, PSG_FOOTER_ICON } = require('../config/settings');
const { getRarityEmoji, getCardTypeEmoji, formatCardStats, getCardImageUrl, weightedRandom } = require('../utils/cardHelpers');
const { OWNER_ID } = require('../utils/permissions');

const PSG_QUESTIONS = [
  { question: "En quelle année le PSG a-t-il été fondé ?", answers: ["1970", "1965", "1975", "1980"], correct: 0 },
  { question: "Quel joueur détient le record de buts au PSG ?", answers: ["Zlatan Ibrahimović", "Edinson Cavani", "Kylian Mbappé", "Pauleta"], correct: 1 },
  { question: "Quel est le surnom du PSG ?", answers: ["Les Rouges", "Les Parisiens", "Les Bleus", "Les Princes"], correct: 1 },
  { question: "En quelle année le PSG a-t-il atteint sa première finale de Ligue des Champions ?", answers: ["2015", "2018", "2020", "2021"], correct: 2 },
  { question: "Quel est le nom du stade du PSG ?", answers: ["Stade de France", "Parc des Princes", "Stade Vélodrome", "Allianz Riviera"], correct: 1 },
  { question: "Qui est le président actuel du PSG ?", answers: ["Jean-Michel Aulas", "Nasser Al-Khelaïfi", "Frank McCourt", "Vincent Labrune"], correct: 1 },
  { question: "Quel joueur brésilien légendaire a porté le maillot du PSG ?", answers: ["Ronaldo", "Ronaldinho", "Rivaldo", "Romário"], correct: 1 },
  { question: "Quelle est la capacité du Parc des Princes ?", answers: ["45 000", "48 000", "50 000", "55 000"], correct: 1 },
  { question: "En quelle année le Qatar a-t-il racheté le PSG ?", answers: ["2009", "2011", "2013", "2015"], correct: 1 },
  { question: "Quel est le rival historique du PSG ?", answers: ["Lyon", "Marseille", "Monaco", "Lille"], correct: 1 },
  { question: "Qui est l'entraîneur du PSG depuis 2023 ?", answers: ["Thomas Tuchel", "Mauricio Pochettino", "Luis Enrique", "Christophe Galtier"], correct: 2 },
  { question: "Quel gardien italien joue au PSG ?", answers: ["Gianluigi Buffon", "Gianluigi Donnarumma", "Salvatore Sirigu", "Mattia Perin"], correct: 1 },
  { question: "En quelle année Neymar a-t-il rejoint le PSG ?", answers: ["2016", "2017", "2018", "2019"], correct: 1 },
  { question: "Combien a coûté le transfert de Neymar au PSG ?", answers: ["200 millions", "222 millions", "250 millions", "300 millions"], correct: 1 },
  { question: "Quel défenseur marocain joue au PSG ?", answers: ["Achraf Hakimi", "Hakim Ziyech", "Noussair Mazraoui", "Romain Saïss"], correct: 0 },
  { question: "Quel pays représente Marquinhos ?", answers: ["Argentine", "Brésil", "Portugal", "Espagne"], correct: 1 },
  { question: "En quelle année le PSG a-t-il remporté son premier titre de champion de France ?", answers: ["1986", "1990", "1994", "1998"], correct: 0 },
];

// Stockage en mémoire des mini-jeux actifs
const activeMinigames = new Map(); // guildId → { answered, winner, timeout }

async function spawnMinigame(client, guildId) {
  const channelId = getMinigameChannel(guildId);
  if (!channelId) return;

  const guild = client.guilds.cache.get(guildId);
  if (!guild) return;

  const channel = guild.channels.cache.get(channelId);
  if (!channel) return;

  const questionData = PSG_QUESTIONS[Math.floor(Math.random() * PSG_QUESTIONS.length)];
  const labels = ['A', 'B', 'C', 'D'];

  const embed = new EmbedBuilder()
    .setTitle('⚡ JOUEUR FUYARD APPARU !')
    .setDescription(`Un joueur légendaire vient d'apparaître ! Réponds correctement et rapidement pour gagner une carte exclusive !\n\n**❓ ${questionData.question}**`)
    .setColor(0xFFD700)
    .addFields(
      { name: '⏱️ Temps', value: `${MINIGAME_CONFIG.timeout} secondes`, inline: true },
      { name: '🏆 Récompense', value: 'Carte Légendaire/Épique', inline: true },
    )
    .setFooter({ text: "Première bonne réponse gagne !", iconURL: PSG_FOOTER_ICON });

  const buttons = questionData.answers.map((answer, i) =>
    new ButtonBuilder()
      .setCustomId(`minigame_answer_${guildId}_${i}`)
      .setLabel(`${labels[i]}. ${answer}`)
      .setStyle(ButtonStyle.Primary),
  );

  const row = new ActionRowBuilder().addComponents(buttons);
  const message = await channel.send({ embeds: [embed], components: [row] });

  // Initialiser l'état du mini-jeu
  activeMinigames.set(guildId, {
    answered: new Set(),
    winner: null,
    questionData,
    message,
    guildId,
    client,
  });

  // Timeout automatique
  const timeout = setTimeout(async () => {
    const state = activeMinigames.get(guildId);
    if (!state || state.winner) return;

    // Désactiver les boutons
    const disabledButtons = questionData.answers.map((answer, i) =>
      new ButtonBuilder()
        .setCustomId(`minigame_answer_${guildId}_${i}`)
        .setLabel(`${labels[i]}. ${answer}`)
        .setStyle(i === questionData.correct ? ButtonStyle.Success : ButtonStyle.Secondary)
        .setDisabled(true),
    );
    const disabledRow = new ActionRowBuilder().addComponents(disabledButtons);

    const endEmbed = new EmbedBuilder()
      .setTitle('⏰ Temps écoulé !')
      .setDescription(`Personne n'a trouvé la bonne réponse à temps !\n\n**✅ Réponse correcte :** ${questionData.answers[questionData.correct]}`)
      .setColor(PSG_RED);

    try {
      await message.edit({ embeds: [endEmbed], components: [disabledRow] });
    } catch { /* message supprimé */ }

    activeMinigames.delete(guildId);
    scheduleNextMinigame(guildId);
  }, MINIGAME_CONFIG.timeout * 1000);

  activeMinigames.get(guildId).timeout = timeout;
}

async function handleMinigameAnswer(interaction) {
  const parts = interaction.customId.split('_');
  const guildId = parts[2];
  const answerIndex = parseInt(parts[3], 10);

  const state = activeMinigames.get(guildId);
  if (!state) {
    return interaction.reply({ content: '❌ Ce mini-jeu est terminé.', flags: MessageFlags.Ephemeral });
  }

  if (state.answered.has(interaction.user.id)) {
    return interaction.reply({ content: '❌ Tu as déjà répondu !', flags: MessageFlags.Ephemeral });
  }
  state.answered.add(interaction.user.id);

  if (answerIndex === state.questionData.correct) {
    if (state.winner) {
      return interaction.reply({ content: `✅ Bonne réponse mais ${state.winner} était plus rapide !`, flags: MessageFlags.Ephemeral });
    }

    // Premier gagnant !
    state.winner = interaction.user;
    clearTimeout(state.timeout);

    // Désactiver les boutons
    const labels = ['A', 'B', 'C', 'D'];
    const disabledButtons = state.questionData.answers.map((answer, i) =>
      new ButtonBuilder()
        .setCustomId(`minigame_answer_${guildId}_${i}`)
        .setLabel(`${labels[i]}. ${answer}`)
        .setStyle(i === state.questionData.correct ? ButtonStyle.Success : ButtonStyle.Secondary)
        .setDisabled(true),
    );
    const disabledRow = new ActionRowBuilder().addComponents(disabledButtons);
    await interaction.update({ components: [disabledRow] });

    // Donner la récompense
    await giveMinigameReward(interaction, guildId, state.questionData);
    activeMinigames.delete(guildId);
    scheduleNextMinigame(guildId);
  } else {
    return interaction.reply({ content: '❌ Mauvaise réponse ! Dommage...', flags: MessageFlags.Ephemeral });
  }
}

async function giveMinigameReward(interaction, guildId, questionData) {
  const cards = loadPackCards('pack_event');
  if (!cards.length) {
    return interaction.followUp({ content: '❌ Erreur : Aucune carte disponible dans le pack événement.', flags: MessageFlags.Ephemeral });
  }

  const chosenRarity = weightedRandom(PACKS_CONFIG.pack_event.drop_rates);
  const cardsOfRarity = cards.filter(c => c.rareté === chosenRarity);
  const card = cardsOfRarity.length
    ? cardsOfRarity[Math.floor(Math.random() * cardsOfRarity.length)]
    : cards[Math.floor(Math.random() * cards.length)];

  addCardToUser(guildId, interaction.user.id, card);

  const embed = new EmbedBuilder()
    .setTitle('🎉 CARTE CAPTURÉE !')
    .setDescription(`**${interaction.user} a gagné la carte !**\n\n# 🎴 ${card.nom}`)
    .setColor(0xFFD700)
    .addFields(
      { name: '📊 Statistiques', value: formatCardStats(card), inline: false },
      { name: '🏆 Rareté', value: `${getRarityEmoji(card.rareté)} ${card.rareté}`, inline: true },
      { name: '✨ Type', value: `${getCardTypeEmoji(card.type)} ${card.type?.charAt(0).toUpperCase() + card.type?.slice(1)}`, inline: true },
    )
    .setFooter({ text: `Récompense mini-jeu • ${interaction.user.username}`, iconURL: interaction.user.displayAvatarURL() });

  const imageUrl = getCardImageUrl(card);
  if (imageUrl) embed.setImage(imageUrl);

  const endEmbed = new EmbedBuilder()
    .setTitle('🎉 GAGNANT !')
    .setDescription(`**${interaction.user} a capturé le joueur fuyard !**\n\nBonne réponse : ${questionData.answers[questionData.correct]}`)
    .setColor(0xFFD700);

  try {
    await state?.message?.edit({ embeds: [endEmbed] });
  } catch { /* ok */ }

  await interaction.followUp({ embeds: [embed] });
}

async function configMinigameCommand(interaction, salon) {
  if (interaction.user.id !== OWNER_ID) {
    return interaction.reply({
      embeds: [new EmbedBuilder().setTitle('❌ Accès refusé').setDescription('Seul le propriétaire du bot peut utiliser cette commande.').setColor(PSG_RED)],
      flags: MessageFlags.Ephemeral,
    });
  }

  const guildId = interaction.guildId;
  setMinigameChannel(guildId, salon.id);
  const nextTime = getNextMinigameTime(guildId);

  const embed = new EmbedBuilder()
    .setTitle('✅ Mini-jeu configuré')
    .setDescription(`Le mini-jeu **Joueur Fuyard** apparaîtra dans ${salon}`)
    .setColor(PSG_BLUE)
    .addFields(
      { name: '⏰ Prochaine apparition', value: `<t:${Math.floor(nextTime.getTime() / 1000)}:F>\n(<t:${Math.floor(nextTime.getTime() / 1000)}:R>)`, inline: false },
      { name: '📋 Intervalle', value: `Entre ${MINIGAME_CONFIG.min_interval_days} et ${MINIGAME_CONFIG.max_interval_days} jours`, inline: true },
      { name: '🕐 Heures d\'apparition', value: `Entre ${MINIGAME_CONFIG.start_hour}h et ${MINIGAME_CONFIG.end_hour}h`, inline: true },
    )
    .setFooter({ text: 'Paris Saint-Germain • Système événementiel', iconURL: PSG_FOOTER_ICON });

  return interaction.reply({ embeds: [embed] });
}

module.exports = { spawnMinigame, handleMinigameAnswer, configMinigameCommand, activeMinigames };