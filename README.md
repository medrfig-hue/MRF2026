# Le Cahier des Nombres

Jeu de maths et de lecture pour enfants de 5 à 10 ans (**Grande Section**, **CP**, **CE1**, **CE2** et **CM1**), dans une seule page web : ouvrez `index.html` dans un navigateur, sur ordinateur, tablette ou téléphone. Aucune installation.

## Grande Section

En GS, l'enfant ne lit pas encore : chaque consigne est lue à voix haute automatiquement, et les réponses sont des images, des points ou des chiffres jusqu'à 10.

- **Maths (7 jeux)** : compter jusqu'à 10, ajouter, faire 5 et 10, le plus et le moins, le train des nombres (aussi à l'envers), les formes (rond, carré, triangle, rectangle), les suites logiques.
- **Langage et lecture (6 jeux)** : lettres capitales, taper les syllabes, les rimes, le premier son, le même mot, écouter une phrase et montrer l'image.

## Maths : 11 jeux

| Jeu | CP | CE1 | CE2 | CM1 |
| --- | --- | --- | --- | --- |
| Compter | objets et boîtes de 10, jusqu'à 20 | jusqu'à 60 | objets en rangées (multiplication) | fractions (bandes, fraction d'une quantité) |
| Additions | jusqu'à 20, puis dizaines | jusqu'à 100, avec retenue | jusqu'à 1000, aide « opération posée » | jusqu'à 100 000, décimaux |
| Soustractions | objets barrés, jusqu'à 20 | jusqu'à 100 | jusqu'à 1000, aide « opération posée » | jusqu'à 100 000, décimaux |
| Aller à 10 / 100 / 1000 | compléments à 10 et 20 | à la dizaine et à 100 | à 100, à la centaine et à 1000 | à 10 000, au millier, à 1 (décimaux) |
| Le crocodile | comparer `<` `>` `=` jusqu'à 100 | jusqu'à 1000 | jusqu'à 999 999, décimaux (3,5 et 3,45), fractions |
| Dizaines / Centaines / Milliers | barres de 10 et cubes | plaques, barres, cubes | milliers, chiffre des centaines… | nombres en lettres, chiffre des dixièmes… |
| Le train | suites de nombres | de 2 en 2, 5, 10, 100, à rebours | de 25, 50, 250, 1000, + 9, + 11 | de 1 000, 10 000, 0,1, 0,25… |
| Doubles et moitiés | doubles jusqu'à 10 | jusqu'à 100 | jusqu'à 1000 | moitiés décimales, tiers, quarts |
| Groupes / Tables / Diviser | compter des paquets | tables de 2, 3, 4, 5, 10 | tables de 2 à 9, × 10, × 100, 43 × 4, division exacte | 234 × 6, 23 × 14, division avec reste |
| La monnaie | pièces et billets en euros | compter et rendre la monnaie | centimes, jusqu'à 250 €, rendre sur 50 / 100 € | mesures : longueurs, masses, contenances, durées |
| Problèmes | petites histoires (ajout, retrait) | écart, multiplication, partage | deux étapes, partage, « combien de boîtes », prix | reste d'une division, fractions, périmètre |

## Lecture et français : 13 jeux

Le sélecteur **Maths / Lecture** de l'accueil affiche les jeux de la matière choisie.

| Jeu | CP | CE1 | CE2 | CM1 |
| --- | --- | --- | --- | --- |
| Les lettres | majuscules ↔ minuscules (b, d, p, q…), alphabet | | | |
| Les syllabes | assembler (m + a), première syllabe, compter les syllabes | | | |
| Les sons | entendre ou, on, an, in, oi, ch, o | écrire eau, ain, en, oi, m devant b et p, lettres muettes | | |
| Mot et image | lire un mot, trouver l'image ; trouver le mot bien écrit | repérer le mot bien écrit | | |
| Phrases | comprendre une ou deux phrases (images) | choisir la phrase dans le bon ordre | | |
| Un, une, des | | un/une, le/la/l', pluriels en s, x, aux | | |
| Histoires | | lire un court texte et répondre | textes plus longs, questions de déduction | textes longs, déductions (horaires, causes) |
| Le dictionnaire | | ordre alphabétique | 2e et 3e lettre | |
| Homophones | | | a/à, et/est, son/sont, on/ont, ces/ses | ou/où, ce/se, c'est/s'est |
| Conjugaison | | | présent, imparfait, futur | passé composé, verbes irréguliers |
| Les accords | | | accorder l'adjectif | participe passé avec être |
| Nature des mots | | | nom, verbe, adjectif | déterminant, pronom |
| Synonymes, contraires | | | le sens des mots | préfixes, familles de mots |

Les consignes peuvent être lues à voix haute, sans jamais lire la réponse ni le texte à déchiffrer.

## Fiches à imprimer (PDF)

Le dossier [`fiches/`](fiches/) contient une fiche par niveau et par volet : `gs-maths.pdf`, `gs-lecture.pdf`, `cp-maths.pdf`, … `cm1-lecture.pdf`. Les fiches de Grande Section sont illustrées et faites pour être lues par un adulte. Chacune propose deux pages d'exercices, une page de petits problèmes (maths) ou de textes à comprendre (lecture), puis un corrigé pour les parents. L'accueil du jeu donne le lien vers les fiches du niveau choisi.

Pour fabriquer une autre série (autres nombres, autres mots), avec Node.js, `pip install reportlab pillow` et la police Noto Color Emoji (pour les images de GS) :

```
python3 tools/fiches.py --serie 2
```

Les mots, phrases et histoires viennent du jeu lui-même (`tools/donnees.js` les lit dans `index.html`). Police : [Andika](https://software.sil.org/andika/) (SIL Open Font License, voir `tools/fonts/OFL.txt`).

## Comment ça marche

- 10 questions par partie. Une étoile quand la réponse est trouvée du premier coup.
- En cas d'erreur : une aide visuelle et un indice, puis un second essai. Après deux erreurs, la solution est expliquée.
- La difficulté s'adapte : elle monte après 3 réussites d'affilée et baisse après 2 échecs.
- Toutes les 10 étoiles, un nouvel autocollant rejoint l'album.
- Option « Lire à voix haute » pour les enfants qui lisent encore difficilement.
- Un espace parents montre le taux de réussite par jeu.
- Les progrès sont enregistrés dans le navigateur (localStorage), sur l'appareil uniquement.
