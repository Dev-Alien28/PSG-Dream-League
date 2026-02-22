// src/utils/permissions.js - Gestion des permissions par serveur (Enmap)
const {
  initServerConfig,
  loadServerConfig,
  saveServerConfig,
} = require('./database');

const OWNER_ID = '878724920987766796';

// ==================== PERMISSIONS SALONS ====================

function checkChannelPermission(interaction, commandName) {
  const config = loadServerConfig(interaction.guildId);
  if (!config) return true;

  const allowedChannels = config.channels?.[commandName] || [];
  if (!allowedChannels.length) return true;

  return allowedChannels.map(String).includes(String(interaction.channelId));
}

function getAllowedChannel(guildId, commandName, client) {
  const config = loadServerConfig(String(guildId));
  if (!config) return null;

  const channelIds = config.channels?.[commandName] || [];
  if (!channelIds.length) return null;

  const guild = client?.guilds?.cache?.get(String(guildId));
  if (!guild) return null;

  for (const channelId of channelIds) {
    const channel = guild.channels.cache.get(String(channelId));
    if (channel) return channel;
  }
  return null;
}

// ==================== PERMISSIONS RÔLES ====================

function checkRolePermission(interaction, permissionType) {
  if (interaction.user.id === OWNER_ID) return true;
  if (interaction.user.id === interaction.guild?.ownerId) return true;

  const config = loadServerConfig(interaction.guildId);

  const nativeCheck = () => {
    const perms = interaction.member?.permissions;
    if (permissionType === 'admin') return perms?.has('Administrator') ?? false;
    if (permissionType === 'moderator') return perms?.has('ModerateMembers') || perms?.has('Administrator') || false;
    return false;
  };

  if (!config) return nativeCheck();

  const allowedRoles = config.roles?.[permissionType] || [];
  if (!allowedRoles.length) return nativeCheck();

  const userRoleIds = interaction.member?.roles?.cache?.map(r => String(r.id)) || [];
  const hasRole = allowedRoles.some(roleId => userRoleIds.includes(String(roleId)));

  return hasRole || nativeCheck();
}

// ==================== GESTION SALONS ====================

function addChannelPermission(guildId, commandName, channelId) {
  const config = loadServerConfig(guildId);
  if (!config) return false;
  if (!config.channels[commandName]) config.channels[commandName] = [];
  if (!config.channels[commandName].includes(String(channelId))) {
    config.channels[commandName].push(String(channelId));
    saveServerConfig(guildId, config);
    return true;
  }
  return false;
}

function removeChannelPermission(guildId, commandName, channelId) {
  const config = loadServerConfig(guildId);
  if (!config) return false;
  const idx = (config.channels[commandName] || []).indexOf(String(channelId));
  if (idx !== -1) {
    config.channels[commandName].splice(idx, 1);
    saveServerConfig(guildId, config);
    return true;
  }
  return false;
}

function getAllowedChannels(guildId, commandName) {
  const config = loadServerConfig(guildId);
  return config?.channels?.[commandName] || [];
}

// ==================== GESTION RÔLES ====================

function addRolePermission(guildId, permissionType, roleId) {
  const config = loadServerConfig(guildId);
  if (!config) return false;
  if (!config.roles[permissionType]) config.roles[permissionType] = [];
  if (!config.roles[permissionType].includes(String(roleId))) {
    config.roles[permissionType].push(String(roleId));
    saveServerConfig(guildId, config);
    return true;
  }
  return false;
}

function removeRolePermission(guildId, permissionType, roleId) {
  const config = loadServerConfig(guildId);
  if (!config) return false;
  const idx = (config.roles[permissionType] || []).indexOf(String(roleId));
  if (idx !== -1) {
    config.roles[permissionType].splice(idx, 1);
    saveServerConfig(guildId, config);
    return true;
  }
  return false;
}

function getAllowedRoles(guildId, permissionType) {
  const config = loadServerConfig(guildId);
  return config?.roles?.[permissionType] || [];
}

// ==================== SALONS SANS COINS ====================

function getNoCoinsChannels(guildId) {
  const config = loadServerConfig(guildId);
  return config?.no_coins_channels || [];
}

function addNoCoinsChannel(guildId, channelId) {
  const config = loadServerConfig(guildId);
  if (!config) return false;
  if (!config.no_coins_channels) config.no_coins_channels = [];
  if (!config.no_coins_channels.includes(String(channelId))) {
    config.no_coins_channels.push(String(channelId));
    saveServerConfig(guildId, config);
    return true;
  }
  return false;
}

function removeNoCoinsChannel(guildId, channelId) {
  const config = loadServerConfig(guildId);
  if (!config) return false;
  const idx = (config.no_coins_channels || []).indexOf(String(channelId));
  if (idx !== -1) {
    config.no_coins_channels.splice(idx, 1);
    saveServerConfig(guildId, config);
    return true;
  }
  return false;
}

function isCoinsDisabledChannel(guildId, channelId) {
  return getNoCoinsChannels(guildId).includes(String(channelId));
}

module.exports = {
  OWNER_ID,
  initServerConfig,   // ré-exporté pour rétrocompatibilité
  loadServerConfig,   // ré-exporté pour rétrocompatibilité
  saveServerConfig,   // ré-exporté pour rétrocompatibilité
  checkChannelPermission,
  getAllowedChannel,
  checkRolePermission,
  addChannelPermission,
  removeChannelPermission,
  getAllowedChannels,
  addRolePermission,
  removeRolePermission,
  getAllowedRoles,
  getNoCoinsChannels,
  addNoCoinsChannel,
  removeNoCoinsChannel,
  isCoinsDisabledChannel,
};