## `announce` — Envoyer une annonce par message privé

Permet d'envoyer une annonce importante aux membres du bot via leurs messages privés (DM).

**Commande :**
```bash
announce
```

La commande ne prend aucun argument. Elle lance un assistant interactif dans la console.

### Déroulement

**1. Choisir la portée**
- `[1] Guild` : tous les membres d'un serveur.
- `[2] Role` : tous les membres possédant un rôle.
- `[3] User` : un membre précis.
- `[Q]` : annuler.

**2. Choisir la cible**

Une liste numérotée des serveurs, rôles ou membres disponibles s'affiche.

Saisir le numéro correspondant à la cible souhaitée.

- `Q` : annuler et quitter la commande.

**3. Saisir le titre**

Entrer le titre de l'annonce sur une seule ligne (256 caractères maximum).

- `Q` : annuler.

**4. Saisir le contenu**

Entrer le corps du message. Plusieurs lignes sont acceptées.

- `.` sur une ligne seule : terminer la saisie.
- `/cancel` : annuler l'annonce.

Le contenu est limité à 4096 caractères.

**5. Vérifier et confirmer**

Un aperçu de l'annonce et le nombre de destinataires s'affichent.

- `Y` : confirmer et envoyer l'annonce.
- `N` ou `Q` : annuler sans envoyer.

**6. Résultat**

Les messages privés sont envoyés séquentiellement. Un récapitulatif indique le nombre d'envois réussis et échoués.

Les membres ayant désactivé les messages privés ou pour lesquels l'envoi échoue sont ignorés, et l'envoi continue pour les autres.

### Exemples

**Annoncer à tous les membres d'un serveur :**
```text
announce
> 1 - Guild
> 1 - Mon serveur
> Titre : Maintenance prévue
> Contenu :
Bonjour à tous,
Une maintenance est prévue demain à 20h.
.
> Y
```

**Annoncer à un rôle précis :**
```text
announce
> 2 - Role
> 3 - Administrateurs
> Titre : Réunion importante
> Contenu :
Une réunion est prévue prochainement.
Merci de rester disponibles.
.
> Y
```

**Annuler une annonce :**
```text
> /cancel
```
ou, lors de la confirmation :
```text
> N
```

### ⚠️ Précautions

- La console étant partagée, **attendez qu'elle soit libre avant de lancer `announce`**. Ne lancez pas plusieurs commandes interactives simultanément et ne saisissez rien pendant qu'un autre utilisateur utilise la console.
- Vérifiez attentivement la cible, le titre et le contenu avant de confirmer.
- Une fois l'envoi confirmé, il n'est plus possible de l'annuler.
- Les bots et le compte du bot lui-même sont exclus des destinataires.
- L'accès aux membres nécessite l'intention privilégiée `Server Members Intent` activée dans la configuration du bot et sur le portail développeur Discord.
