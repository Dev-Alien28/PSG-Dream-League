# 🔴🔵 PSG Dream League Bot

Bot Discord de collection de cartes PSG développé en Node.js avec discord.js v14.

---

## 📦 Installation

```bash
npm install
(il faut juste rajouter le .env )
npm start
```

---

## 🎮 Commandes

| Commande | Description | Accès |
|---|---|---|
| `/solde` | Voir son solde de PSG Coins | Tous |
| `/packs` | Ouvrir la boutique et acheter des packs | Tous |
| `/collection` | Voir sa collection de cartes (ou celle d'un membre) | Tous |
| `/addcoins` | Ajouter des coins à un membre | Admin |
| `/removecoins` | Retirer des coins à un membre | Admin |
| `/setcoins` | Définir le solde exact d'un membre | Admin |
| `/give` | Donner une carte à un membre | Admin |
| `/config` | Panneau de configuration interactif | Propriétaire |

---

## 📁 Structure

```
src/
├── index.js
├── config/
│   └── settings.js          
├── images/
│   ├─ boite.png
│   └─ cards/ 
	├─ Carte_1.png
	├─ Carte_2.png
	└─ Carte_3.png
├── commands/
│   ├── solde.js
│   ├── packs.js
│   ├── collection.js
│   ├── admin.js
│   ├── give.js
│   ├── config.js
│   ├── minigame.js          
│   └── auto_reminder.js     
├── handlers/
│   ├── commands.js          # Routeur slash commands + boutons/menus
│   └── events.js            # Événements Discord + coins par message
├── data/
│   ├── argent.json          # Soldes et collections (par serveur)
│   ├── event_state.json     # État du mini-jeu
│   ├── reminder_config.json # Config des rappels
│   ├── packs/               
│   └── servers/             # Config par serveur (salons, rôles, logs)
└── utils/
    ├── database.js          # Lecture/écriture JSON
    ├── permissions.js       # Permissions par rôle et salon
    ├── logs.js              # Logs Discord
    └── cardHelpers.js       # Utilitaires cartes (stats, couleurs, emojis)
```

---

## 🃏 Ajouter des cartes

Édite les fichiers JSON dans `data/packs/` :

| Fichier | Pack |
|---|---|
| `psg_start.json` | Pack principal (25 coins) |
| `free_pack.json` | Pack journalier gratuit |
| `pack_event.json` | Récompense mini-jeu |

Format d'une carte :

```json
{
  "id": "att_dembele_elite",
  "type": "joueur",
  "nom": "Ousmane Dembélé 25/26",
  "rareté": "Elite",
  "position": "Attaquant",
  "stats": { "frappe": 89, "technique": 92, "contrôle": 91 },
  "image": "images/cards/Carte_3.png"
}
```

Raretés disponibles : `Basic` · `Advanced` · `Elite` · `Unique` · `Legend`

---

## ⚙️ Configuration

Alien peut configuré mais on peut ajouter des personne c'est pour éviter de modifier des choses sans faire exprès
Lance `/config` dans Discord pour configurer par serveur :
- Salons autorisés par commande
- Rôles administrateurs
- Salon de logs
- Rappels automatiques
- Salons sans gains de coins