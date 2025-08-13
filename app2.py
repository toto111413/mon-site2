import streamlit as st
import random

# ---------------------------
# CONFIG PAGE
# ---------------------------
st.set_page_config(
    page_title="Mon Site Web",
    page_icon="🌐",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---------------------------
# INITIALISATIONS SESSION
# ---------------------------
if "points" not in st.session_state:
    st.session_state.points = 0

# consommables stockés par clé -> nombre d'exemplaires
if "consumables" not in st.session_state:
    st.session_state.consumables = {
        "indice_pendu": 0,      # 💡 Indice Pendu
        "aide_mastermind": 0,   # 🎯 Aide Mastermind
        "rejouer": 0,           # 🔄 Rejouer
        "boost_animal": 0       # 🚀 Boost Animal
    }

# chapeau permanent (non consommable)
if "has_hat" not in st.session_state:
    st.session_state.has_hat = False

# inventory_list used for display names (keeps unique names for purchased permanent items)
if "inventory_list" not in st.session_state:
    st.session_state.inventory_list = []

# achievements (successes)
if "achievements" not in st.session_state:
    st.session_state.achievements = set()

# pet state
if "pet" not in st.session_state:
    st.session_state.pet = "none"  # none, egg, puppy, adult, legend
if "pet_xp" not in st.session_state:
    st.session_state.pet_xp = 0

# track whether "Légende vivante" was already awarded
if "legend_awarded" not in st.session_state:
    st.session_state.legend_awarded = False  # --- AJOUT: succès unique flag

# secret mini-game unlocked by points
if "secret_unlocked" not in st.session_state:
    st.session_state.secret_unlocked = False

# stats for achievements
if "total_wins" not in st.session_state:
    st.session_state.total_wins = 0
if "consecutive_wins" not in st.session_state:
    st.session_state.consecutive_wins = 0

# per-game helper state initializations
# Devine le nombre
if "secret" not in st.session_state:
    st.session_state.secret = random.randint(1, 20)
# Pierre-Papier-Ciseaux doesn't need persistent state except stats handled above

# Pendu
if "mot_secret" not in st.session_state:
    st.session_state.mot_secret = random.choice(["python","famille","ordinateur","jeu","tom","arcade","chat","pizza","robot","streamlit"])
if "lettres_trouvees" not in st.session_state:
    st.session_state.lettres_trouvees = []
if "erreurs" not in st.session_state:
    st.session_state.erreurs = 0
if "pendu_hint_used" not in st.session_state:
    st.session_state.pendu_hint_used = False
if "pendu_lost" not in st.session_state:
    st.session_state.pendu_lost = False

# Mastermind
if "mastermind_secret" not in st.session_state:
    couleurs = ["Rouge","Bleu","Vert","Jaune","Orange","Violet"]
    st.session_state.mastermind_secret = [random.choice(couleurs) for _ in range(4)]
if "mastermind_attempts" not in st.session_state:
    st.session_state.mastermind_attempts = 6
if "mastermind_hint_used" not in st.session_state:
    st.session_state.mastermind_hint_used = False
if "mastermind_lost" not in st.session_state:
    st.session_state.mastermind_lost = False

# Mots mélangés
if "mot_original" not in st.session_state:
    mots = ["python","streamlit","ordinateur","arcade","programmation","robot"]
    st.session_state.mot_original = random.choice(mots)
    melange = list(st.session_state.mot_original)
    random.shuffle(melange)
    st.session_state.mot_melange = "".join(melange)
    st.session_state.mots_attempts = 3
if "mots_lost" not in st.session_state:
    st.session_state.mots_lost = False

# Mini-jeu secret (initial)
if "treasure_pos" not in st.session_state:
    st.session_state.treasure_pos = (random.randint(0,3), random.randint(0,3))
if "treasure_attempts" not in st.session_state:
    st.session_state.treasure_attempts = 6
if "treasure_found" not in st.session_state:
    st.session_state.treasure_found = False

# ---------------------------
# UTILITAIRES (points, pet, achievements)
# ---------------------------
def award_points(points_gain=0, reason=None):
    """Donne des points globaux, applique bonus chapeau, met à jour achievements/pet."""
    bonus = 1 if st.session_state.has_hat else 0
    total = points_gain + bonus
    st.session_state.points += total
    if reason:
        st.success(f"+{total} points ({reason})")
    # track wins if points_gain > 0 (not including hat bonus)
    if points_gain > 0:
        st.session_state.total_wins += 1
        st.session_state.consecutive_wins += 1
    else:
        st.session_state.consecutive_wins = 0
    # achievements
    if st.session_state.total_wins >= 5:
        st.session_state.achievements.add("Vainqueur x5")
    if st.session_state.consecutive_wins >= 3:
        st.session_state.achievements.add("Série de 3 victoires")
    # pet progression: pet gains pet_xp equal to points_gain (consumables that add to pet will add directly)
    if st.session_state.pet != "none":
        st.session_state.pet_xp += points_gain
        evolve_pet_if_needed()
    # unlock secret by points threshold
    if st.session_state.points >= 100:
        st.session_state.secret_unlocked = True
    # --- AJOUT: vérifier succès unique "Légende vivante" (1000 pet XP)
    check_legend_success()

def evolve_pet_if_needed():
    if st.session_state.pet == "egg" and st.session_state.pet_xp >= 10:
        st.session_state.pet = "puppy"
        st.session_state.achievements.add("Naissance du compagnon")
        st.success("🐣 Ton oeuf a éclos en chiot !")
    elif st.session_state.pet == "puppy" and st.session_state.pet_xp >= 30:
        st.session_state.pet = "adult"
        st.session_state.achievements.add("Compagnon adulte")
        st.success("🐶 Ton chiot est devenu adulte !")
    elif st.session_state.pet == "adult" and st.session_state.pet_xp >= 100:
        st.session_state.pet = "legend"
        st.session_state.achievements.add("Compagnon légendaire")
        st.success("👑 Ton compagnon est devenu légendaire !")
    # --- AJOUT: vérifier succès unique "Légende vivante" aussi quand évolutions se produisent
    check_legend_success()

def check_legend_success():
    """Vérifie si pet_xp atteint 1000 et donne le succès une seule fois."""
    if (st.session_state.pet_xp >= 1000) and (not st.session_state.legend_awarded):
        # --- AJOUT: déverrouille succès unique et récompense +20 points
        st.session_state.achievements.add("🏆 Légende vivante")
        st.session_state.points += 20
        st.session_state.legend_awarded = True
        st.balloons()
        st.success("🏆 Succès débloqué : Légende vivante ! +20 points")

def consume_item(key):
    """Consomme un exemplaire d'un consommable; s'assure que le compteur baisse."""
    if key in st.session_state.consumables and st.session_state.consumables[key] > 0:
        st.session_state.consumables[key] -= 1
        return True
    return False

def add_consumable(key, count=1):
    st.session_state.consumables[key] = st.session_state.consumables.get(key,0) + count

def inventory_display_list():
    """Return a readable list of owned items (chapeau + consumable counts)."""
    items = []
    if st.session_state.has_hat:
        items.append("🎩 Chapeau magique")
    # include pet if owned (egg or more) - if pet is not none and not already in inventory_list, show
    if st.session_state.pet != "none" and "Animal virtuel" not in st.session_state.inventory_list:
        # we add an entry to inventory_list when purchased (see shop logic) but keep it safe
        pass
    for k, v in st.session_state.consumables.items():
        if v > 0:
            name = {
                "indice_pendu": "💡 Indice Pendu",
                "aide_mastermind": "🎯 Aide Mastermind",
                "rejouer": "🔄 Rejouer",
                "boost_animal": "🚀 Boost Animal"
            }.get(k, k)
            items.append(f"{name} x{v}")
    # show egg/animal if owned and not using inventory_list
    if st.session_state.pet != "none":
        # show actual stage name
        pet_name = {
            "egg": "🥚 Œuf de compagnon (possédé)",
            "puppy": "🐶 Compagnon (chiot)",
            "adult": "🐕 Compagnon (adulte)",
            "legend": "🐕‍🦺✨ Compagnon (légendaire)"
        }.get(st.session_state.pet, "Animal virtuel")
        # ensure not duplicated
        if pet_name not in items:
            items.append(pet_name)
    return items

# ---------------------------
# BOUTIQUE : définition articles
# ---------------------------
# --- AJOUT: Œuf de compagnon en premier
ARTICLES = [
    {"key": "pet_egg", "nom": "🥚 Œuf de compagnon", "prix": 15, "desc": "Achetez un œuf qui éclos et devient un compagnon évolutif. (Unique)", "consumable": False, "special": "unlock_pet"},
    {"key": "chapeau", "nom": "🎩 Chapeau magique", "prix": 10, "desc": "Permanent : +1 point bonus par victoire (non consommable).", "consumable": False},
    {"key": "indice_pendu", "nom": "💡 Indice Pendu", "prix": 8, "desc": "Consommable: révèle une lettre dans le Pendu (1x).", "consumable": True},
    {"key": "aide_mastermind", "nom": "🎯 Aide Mastermind", "prix": 8, "desc": "Consommable: révèle la couleur correcte d'une position (1x).", "consumable": True},
    {"key": "rejouer", "nom": "🔄 Rejouer", "prix": 12, "desc": "Consommable: recommencer une partie perdue sans pénalité (1x).", "consumable": True},
    {"key": "boost_animal", "nom": "🚀 Boost Animal", "prix": 10, "desc": "Consommable: +10 points d'expérience pour l'animal (1x).", "consumable": True}
]

# ---------------------------
# MENU / HEADER
# ---------------------------
menu_items = ["Accueil", "Jeux externes", "Devine le nombre", "Pierre-Papier-Ciseaux", "Pendu", "Mastermind", "Mots mélangés", "Boutique", "Animal", "Succès"]
if st.session_state.secret_unlocked:
    menu_items.append("Mini-jeu secret")

menu = st.radio("🎮 Choisis une section :", menu_items)
st.markdown(f"**💰 Points : {st.session_state.points}**")
st.write("Inventaire :", ", ".join(inventory_display_list()) if inventory_display_list() else "Aucun article")

# ---------------------------
# PAGES / JEUX
# ---------------------------
# 1) ACCUEIL
if menu == "Accueil":
    st.markdown("<h1 style='text-align:center'>Bienvenue sur mon site de jeux ✨</h1>", unsafe_allow_html=True)
    name = st.text_input("Quel est votre nom ?")
    if name:
        st.success(f"Enchanté, {name} ! 😊")

# 2) JEUX EXTERNES
elif menu == "Jeux externes":
    st.header("🎮 Mes jeux externes")
    jeux = [
        {"titre": "cible", "desc": "As-tu le meilleur score ?", "lien": "https://zmwguswsyytnolqexffdfj.streamlit.app/"},
        {"titre": "RPG", "desc": "Combattez les monstres !", "lien": "https://je7erdurjykggnaagdzyzt.streamlit.app/"},
        {"titre": "Quiz", "desc": "Répondez aux questions", "lien": "https://hyu2irxjzdthppfbix6duf.streamlit.app/"},
        {"titre": "Dé", "desc": "Faites un grand total", "lien": "https://essaie-2-hcaltzcmtgndkwfuei7snk.streamlit.app/"},
        {"titre": "Morpion", "desc": "Jouez contre une IA", "lien": "https://essaie-p44xbuapphmrcwqw65nys44.streamlit.app/"}
    ]
    for j in jeux:
        st.subheader(j["titre"])
        st.write(j["desc"])
        st.markdown(f"[Voir le jeu]({j['lien']})")

# 3) DEVINE LE NOMBRE
elif menu == "Devine le nombre":
    st.header("🎲 Devine le nombre")
    if "secret" not in st.session_state:
        st.session_state.secret = random.randint(1, 20)
    guess = st.number_input("Entrez un nombre entre 1 et 20", min_value=1, max_value=20, step=1)
    if st.button("Vérifier"):
        if guess == st.session_state.secret:
            award_points(5, "Devine le nombre gagné")
            st.session_state.secret = random.randint(1, 20)
        elif guess < st.session_state.secret:
            st.info("C'est plus grand !")
            st.session_state.consecutive_wins = 0
        else:
            st.info("C'est plus petit !")
            st.session_state.consecutive_wins = 0

# 4) PIERRE-PAPIER-CISEAUX
elif menu == "Pierre-Papier-Ciseaux":
    st.header("✂️ Pierre-Papier-Ciseaux")
    choix = st.radio("Faites votre choix :", ["Pierre", "Papier", "Ciseaux"])
    if st.button("Jouer"):
        bot = random.choice(["Pierre", "Papier", "Ciseaux"])
        st.write(f"L'ordinateur a choisi : {bot}")
        if choix == bot:
            st.info("Égalité ! 🤝")
            st.session_state.consecutive_wins = 0
        elif (choix == "Pierre" and bot == "Ciseaux") or \
             (choix == "Papier" and bot == "Pierre") or \
             (choix == "Ciseaux" and bot == "Papier"):
            award_points(2, "Chifoumi gagné")
        else:
            st.error("Perdu 😢")
            st.session_state.consecutive_wins = 0

# 5) PENDU (with Indice Pendu consumable)
elif menu == "Pendu":
    st.header("🪢 Pendu amélioré")
    pendu_etapes = [
        "+---+\n    |\n    |\n    |\n   ===",
        "+---+\nO   |\n    |\n    |\n   ===",
        "+---+\nO   |\n|   |\n    |\n   ===",
        "+---+\nO   |\n/|  |\n    |\n   ===",
        "+---+\nO   |\n/|\\ |\n    |\n   ===",
        "+---+\nO   |\n/|\\ |\n/   |\n   ===",
        "+---+\nO   |\n/|\\ |\n/ \\ |\n   ==="
    ]

    mot_affiche = " ".join([l if l in st.session_state.lettres_trouvees else "_" for l in st.session_state.mot_secret])
    st.write(f"Mot à deviner : **{mot_affiche}**")
    st.code(pendu_etapes[st.session_state.erreurs])

    # If player owns Indice Pendu and not used in this partie, offer button
    if st.session_state.consumables.get("indice_pendu",0) > 0 and not st.session_state.pendu_hint_used:
        if st.button("💡 Utiliser Indice Pendu (révèle une lettre)"):
            # reveal one random unrevealed letter
            remaining = [c for c in set(st.session_state.mot_secret) if c not in st.session_state.lettres_trouvees]
            if remaining:
                chosen = random.choice(remaining)
                st.session_state.lettres_trouvees.append(chosen)
                st.session_state.pendu_hint_used = True
                consume_item("indice_pendu")
                st.success(f"💡 Indice utilisé : la lettre **{chosen}** a été révélée.")
            else:
                st.info("Aucune lettre restante à révéler.")
    # Letter propose
    lettre = st.text_input("Proposez une lettre :", max_chars=1)
    if st.button("Proposer la lettre"):
        l = lettre.lower()
        if not l or not l.isalpha():
            st.warning("⚠️ Entrez une lettre valide.")
        else:
            if l in st.session_state.lettres_trouvees:
                st.warning("⚠️ Lettre déjà proposée.")
            elif l in st.session_state.mot_secret:
                st.session_state.lettres_trouvees.append(l)
                st.success(f"✅ La lettre **{l}** est dans le mot !")
            else:
                st.session_state.erreurs += 1
                st.error(f"❌ La lettre **{l}** n'est pas dans le mot.")
    # Win
    if "_" not in mot_affiche:
        award_points(3, "Pendu gagné")
        st.session_state.achievements.add("Maître du mot")
        # reset round
        st.session_state.mot_secret = random.choice(["python","famille","ordinateur","jeu","tom","arcade","chat","pizza","robot","streamlit"])
        st.session_state.lettres_trouvees = []
        st.session_state.erreurs = 0
        st.session_state.pendu_hint_used = False
        st.session_state.pendu_lost = False
    # Lose
    if st.session_state.erreurs >= len(pendu_etapes)-1:
        st.error(f"💀 Pendu ! Le mot était **{st.session_state.mot_secret}**.")
        st.session_state.pendu_lost = True
        # show Rejouer option if owned
        if st.session_state.consumables.get("rejouer",0) > 0:
            if st.button("🔄 Utiliser Rejouer pour recommencer (consomme 1)"):
                consume_item("rejouer")
                st.session_state.mot_secret = random.choice(["python","famille","ordinateur","jeu","tom","arcade","chat","pizza","robot","streamlit"])
                st.session_state.lettres_trouvees = []
                st.session_state.erreurs = 0
                st.session_state.pendu_hint_used = False
                st.session_state.pendu_lost = False
                st.success("La partie a été réinitialisée (Rejouer utilisé).")
        else:
            if st.button("Recommencer manuellement"):
                st.session_state.mot_secret = random.choice(["python","famille","ordinateur","jeu","tom","arcade","chat","pizza","robot","streamlit"])
                st.session_state.lettres_trouvees = []
                st.session_state.erreurs = 0
                st.session_state.pendu_hint_used = False
                st.session_state.pendu_lost = False

# 6) MASTERMIND (with aide_mastermind consumable)
elif menu == "Mastermind":
    st.header("🎯 Mastermind")
    couleurs = ["Rouge","Bleu","Vert","Jaune","Orange","Violet"]
    # selectors
    choix = [st.selectbox(f"Couleur {i+1}", couleurs, key=f"color_{i}") for i in range(4)]
    if st.button("Vérifier combinaison"):
        bien_places = sum([c == s for c, s in zip(choix, st.session_state.mastermind_secret)])
        mal_places = sum(min(choix.count(c), st.session_state.mastermind_secret.count(c)) for c in couleurs) - bien_places
        st.write(f"Bien placés : {bien_places} | Mal placés : {mal_places}")
        if bien_places == 4:
            award_points(8, "Mastermind gagné")
            st.session_state.achievements.add("Maître du code")
            # reset
            st.session_state.mastermind_secret = [random.choice(couleurs) for _ in range(4)]
            st.session_state.mastermind_attempts = 6
            st.session_state.mastermind_hint_used = False
            st.session_state.mastermind_lost = False
        else:
            st.session_state.mastermind_attempts -= 1
            if st.session_state.mastermind_attempts <= 0:
                st.error(f"Perdu ! La combinaison était : {st.session_state.mastermind_secret}")
                st.session_state.mastermind_lost = True
                # offer Rejouer if owned
                if st.session_state.consumables.get("rejouer",0) > 0:
                    if st.button("🔄 Utiliser Rejouer pour recommencer Mastermind (consomme 1)"):
                        consume_item("rejouer")
                        st.session_state.mastermind_secret = [random.choice(couleurs) for _ in range(4)]
                        st.session_state.mastermind_attempts = 6
                        st.session_state.mastermind_hint_used = False
                        st.session_state.mastermind_lost = False
                        st.success("Rejouer utilisé : nouvelle combinaison générée.")
                else:
                    if st.button("Recommencer Mastermind"):
                        st.session_state.mastermind_secret = [random.choice(couleurs) for _ in range(4)]
                        st.session_state.mastermind_attempts = 6
                        st.session_state.mastermind_hint_used = False
                        st.session_state.mastermind_lost = False

    # aide Mastermind consumable: reveal a correct color at a random position if available and not used
    if st.session_state.consumables.get("aide_mastermind",0) > 0 and not st.session_state.mastermind_hint_used:
        if st.button("🎯 Utiliser Aide Mastermind (révèle une position correcte)"):
            # choose a random index
            idx = random.randrange(4)
            couleur_reelle = st.session_state.mastermind_secret[idx]
            st.session_state.mastermind_hint_used = True
            consume_item("aide_mastermind")
            st.info(f"🎯 Indice : à la position {idx+1}, la couleur est **{couleur_reelle}**")

# 7) MOTS MÉLANGÉS (with Rejouer consumable usage on loss)
elif menu == "Mots mélangés":
    st.header("🔀 Mots mélangés")
    st.write(f"Mot mélangé : **{st.session_state.mot_melange}**")
    proposition = st.text_input("Votre réponse :").lower()
    if st.button("Valider mot"):
        if proposition == st.session_state.mot_original:
            award_points(5, "Mots mélangés gagné")
            st.session_state.achievements.add("Décodeur")
            # reset
            mots = ["python","streamlit","ordinateur","arcade","programmation","robot"]
            st.session_state.mot_original = random.choice(mots)
            melange = list(st.session_state.mot_original)
            random.shuffle(melange)
            st.session_state.mot_melange = "".join(melange)
            st.session_state.mots_attempts = 3
            st.session_state.mots_lost = False
        else:
            st.session_state.mots_attempts -= 1
            st.warning(f"Incorrect ! Essais restants : {st.session_state.mots_attempts}")
            if st.session_state.mots_attempts <= 0:
                st.error(f"Perdu ! Le mot était : {st.session_state.mot_original}")
                st.session_state.mots_lost = True
                # offer Rejouer if present
                if st.session_state.consumables.get("rejouer",0) > 0:
                    if st.button("🔄 Utiliser Rejouer (consomme 1)"):
                        consume_item("rejouer")
                        mots = ["python","streamlit","ordinateur","arcade","programmation","robot"]
                        st.session_state.mot_original = random.choice(mots)
                        melange = list(st.session_state.mot_original)
                        random.shuffle(melange)
                        st.session_state.mot_melange = "".join(melange)
                        st.session_state.mots_attempts = 3
                        st.session_state.mots_lost = False
                        st.success("Rejouer utilisé : nouvelle partie lancée.")
                else:
                    if st.button("Recommencer manuellement"):
                        mots = ["python","streamlit","ordinateur","arcade","programmation","robot"]
                        st.session_state.mot_original = random.choice(mots)
                        melange = list(st.session_state.mot_original)
                        random.shuffle(melange)
                        st.session_state.mot_melange = "".join(melange)
                        st.session_state.mots_attempts = 3
                        st.session_state.mots_lost = False

# 8) BOUTIQUE (show counts, buy, consumables behaviour)
elif menu == "Boutique":
    st.header("🛒 Boutique")
    st.write(f"Points disponibles : **{st.session_state.points}**")
    st.subheader("Articles disponibles")
    for art in ARTICLES:
        col1, col2 = st.columns([3,1])
        with col1:
            st.write(f"**{art['nom']}** - {art['prix']} pts")
            st.caption(art['desc'])
        with col2:
            # For pet_egg and chapeau, show owned boolean; for consumables show count
            if art["key"] == "pet_egg":
                # --- AJOUT: Œuf de compagnon en premier et unique
                if st.session_state.pet != "none":
                    st.button("Acheté", key=f"bought_{art['key']}")
                else:
                    if st.button(f"Acheter", key=f"buy_{art['key']}"):
                        if st.session_state.points >= art["prix"]:
                            st.session_state.points -= art["prix"]
                            # unlock pet egg immediately
                            st.session_state.pet = "egg"
                            if art["nom"] not in st.session_state.inventory_list:
                                st.session_state.inventory_list.append(art["nom"])
                            st.success("🥚 Tu as adopté un oeuf ! Va voir la page Animal pour t'en occuper.")
                        else:
                            st.error("❌ Pas assez de points.")
            elif art["key"] == "chapeau":
                if st.session_state.has_hat:
                    st.button("Acheté", key=f"bought_{art['key']}")
                else:
                    if st.button(f"Acheter", key=f"buy_{art['key']}"):
                        if st.session_state.points >= art["prix"]:
                            st.session_state.points -= art["prix"]
                            st.session_state.has_hat = True
                            if art["nom"] not in st.session_state.inventory_list:
                                st.session_state.inventory_list.append(art["nom"])
                            st.success(f"✅ {art['nom']} acheté ! (permanent)")
                        else:
                            st.error("❌ Pas assez de points.")
            else:
                # consumable
                count = st.session_state.consumables.get(art["key"],0)
                st.write(f"x{count}")
                if st.button("Acheter", key=f"buy_{art['key']}"):
                    if st.session_state.points >= art["prix"]:
                        st.session_state.points -= art["prix"]
                        add_consumable(art["key"], 1)
                        if art["nom"] not in st.session_state.inventory_list:
                            st.session_state.inventory_list.append(art["nom"])
                        st.success(f"✅ {art['nom']} ajouté à votre inventaire (consommable).")
                    else:
                        st.error("❌ Pas assez de points.")

    st.markdown("---")
    st.subheader("Inventaire détaillé")
    inv = inventory_display_list()
    if inv:
        for i in inv:
            st.write("•", i)
    else:
        st.write("Aucun objet possédé.")

# 9) ANIMAL
elif menu == "Animal":
    st.header("🐶 Animal virtuel")
    visuals = {
        "none": "Tu n'as pas d'animal. Achète l'animal virtuel dans la boutique.",
        "egg": "🥚 (oeuf)",
        "puppy": "🐶 (chiot)",
        "adult": "🐕 (adulte)",
        "legend": "🐕‍🦺✨ (légendaire)"
    }
    st.write(f"Statut : **{visuals.get(st.session_state.pet, 'none')}**")
    st.write(f"Points gagnés pour le compagnon : {st.session_state.pet_xp}")
    if st.session_state.pet != "none":
        if st.button("Caresser (+1 pet point)"):
            st.session_state.pet_xp += 1
            evolve_pet_if_needed()
            st.success("❤️ Le compagnon est content.")
    # Boost Animal consumable usage
    if st.session_state.consumables.get("boost_animal",0) > 0:
        if st.button("🚀 Utiliser Boost Animal (+10 pet XP)"):
            consume_item("boost_animal")
            st.session_state.pet_xp += 10
            evolve_pet_if_needed()
            st.success("🚀 Boost Animal utilisé (+10 pet XP).")
    st.markdown("---")
    st.write("Les animaux gagnent de l'expérience lorsqu'on gagne des parties (dépend des jeux).")

# 10) SUCCÈS
elif menu == "Succès":
    st.header("🏆 Succès débloqués")
    if st.session_state.achievements:
        for a in sorted(st.session_state.achievements):
            st.write("•", a)
    else:
        st.write("Aucun succès débloqué... encore.")

# 11) MINI-JEU SECRET (unlocked by points)
elif menu == "Mini-jeu secret":
    st.header("🔒 Mini-jeu secret : Trouve le trésor")
    st.write("Tu as 6 essais pour trouver le trésor caché dans une grille 4x4.")
    st.write(f"Essais restants : {st.session_state.treasure_attempts}")
    x = st.slider("Choisis X", 0, 3, 0, key="tre_x")
    y = st.slider("Choisis Y", 0, 3, 0, key="tre_y")
    if st.button("Creuser"):
        if (x,y) == st.session_state.treasure_pos:
            award_points(20, "Trésor trouvé")
            st.session_state.treasure_found = True
            st.success("💎 Tu as trouvé le trésor !")
            # reset treasure for next time
            st.session_state.treasure_pos = (random.randint(0,3), random.randint(0,3))
            st.session_state.treasure_attempts = 6
            st.session_state.treasure_found = False
        else:
            st.session_state.treasure_attempts -= 1
            st.warning("Rien ici...")
            if st.session_state.treasure_attempts <= 0:
                st.error(f"Fin des essais ! Le trésor était en {st.session_state.treasure_pos}")
                # allow restart
                if st.button("Recommencer la chasse"):
                    st.session_state.treasure_pos = (random.randint(0,3), random.randint(0,3))
                    st.session_state.treasure_attempts = 6
                    st.session_state.treasure_found = False

# ---------------------------
# FOOTER
# ---------------------------
st.markdown("---")
st.caption("Boutique améliorée : objet Œuf en premier, consommables et effets intégrés — tout en Python pour Streamlit Cloud")

