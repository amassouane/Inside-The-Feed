# Questions probables du professeur — réponses courtes

### Pourquoi TF-IDF et pas des embeddings (BERT, etc.) ?
Parce que l'objectif est pédagogique : TF-IDF est **entièrement explicable**. Chaque score se décompose
en contributions de termes. Les embeddings géreraient mieux les synonymes (`foot`/`football`),
mais ils fonctionnent comme une boîte noire et demandent un modèle téléchargé.

### Pourquoi le cosinus et pas la distance euclidienne ?
Le cosinus compare des **directions**, indépendamment de la longueur des textes.
Comme nos vecteurs sont normalisés, le cosinus est un simple produit scalaire, donc décomposable par terme.

### Comment calculez-vous l'idf exactement ?
`idf(t) = ln((1 + n) / (1 + df(t))) + 1`. C'est le paramètre par défaut de scikit-learn (`smooth_idf=True`),
que nous écrivons explicitement dans `make_vectorizer()`. Un test vérifie la formule sur nos 40 posts.

### Pourquoi faire la moyenne des likes pour le profil ?
C'est la méthode la plus simple : le profil est le « centre » des contenus aimés.
Limite : tous les likes pèsent pareil, sans tenir compte de l'ancienneté ni de l'intensité.
On l'observe avec p10, dont le terme rare `désert` passe en tête du profil.

### Les scores sont faibles (0,15) : est-ce un problème ?
Non. Les textes sont courts et chacun contient beaucoup de mots uniques, donc les vecteurs se recouvrent peu.
Seul l'**ordre** compte pour le classement. Le score n'est pas une probabilité.

### Pourquoi les pâtes apparaissent-elles dans un feed football ?
À cause du seul mot `rapide` (« attaquant rapide », « recette rapide »). C'est de la polysémie :
le modèle compte des mots, il ne comprend pas le sens. Nous le montrons volontairement.

### La catégorie est-elle utilisée dans le calcul ?
Non. Seuls le titre, la description et les hashtags sont vectorisés. La catégorie sert à l'affichage,
au feed initial équilibré et à la règle d'exploration, qui n'est pas du NLP.

### Comment marche l'exploration ? Est-ce aléatoire ?
Non, elle est déterministe. On réserve `arrondi(8 × p)` places. On prend les thèmes absents du top 8,
dans un ordre fixe, et on choisit à tour de rôle le meilleur post non aimé de chaque thème.
Les scores ne sont pas modifiés.

### Quelle différence avec le filtrage collaboratif ?
Le collaboratif utilise les **autres utilisateurs** (« ceux qui ont aimé X ont aussi aimé Y ») et ignore le texte.
Il découvre des goûts inattendus, mais il lui faut beaucoup d'utilisateurs et il souffre aussi du cold start.
Les systèmes réels sont **hybrides**.

### Est-ce que c'est ainsi que fonctionne TikTok ?
Non, et nous ne le prétendons pas. Les plateformes utilisent des modèles appris sur des milliards d'interactions
(temps de visionnage, partages…), des embeddings et des objectifs d'engagement. Nous illustrons une **brique**
de base : la similarité de contenu.

### Votre démo prouve-t-elle l'existence des bulles de filtre ?
Non. Un utilisateur fictif et 40 posts ne permettent aucune conclusion scientifique. Il faudrait de vrais utilisateurs,
une durée, une mesure de diversité et un groupe témoin. Nous montrons seulement qu'un feed peut se **spécialiser**
selon les likes.

### Comment gérez-vous le cold start ?
Sans like, il n'y a pas de profil. Nous affichons un feed initial équilibré (un post par thème, à tour de rôle),
déterministe et **explicitement marqué comme non personnalisé**.

### Comment améliorer le modèle ?
Lemmatisation (`joueur`/`joueurs`), dictionnaire de synonymes, n-grammes, embeddings sémantiques,
pondération temporelle des likes, signaux négatifs (« pas intéressé »), passage à un système hybride.

### Comment savez-vous que vos résultats sont justes ?
44 tests automatiques : normalisation, formule idf, cosinus = produit scalaire, somme des contributions = score,
exclusion des posts aimés, absence de doublons, règles d'exploration, et chaque effet annoncé dans la démo
(par exemple « p09 passe de la 5e à la 2e place »). Si les données changent, les tests échouent.

### Pourquoi Streamlit ?
Interface interactive en Python pur, en local et sans serveur web à écrire. Les calculs sont séparés de l'interface
(`recommender/` n'importe pas Streamlit) : on peut les réutiliser ailleurs.

### Combien de temps prendrait le calcul avec un million de posts ?
La matrice TF-IDF est creuse, et le produit profil × matrice reste rapide (une multiplication creuse).
En production, on utiliserait plutôt une recherche de plus proches voisins approximative et une étape de pré-sélection
de candidats avant le classement.
