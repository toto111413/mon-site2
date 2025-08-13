# app.py — Version 100% SQLite (compatible Streamlit Cloud)
import streamlit as st
import random
import json
import sqlite3
from typing import Dict, Optional

# =========================
# Base SQLite (une seule table "sauvegarde")
# =========================
def init_db():
    conn = sqlite3.connect("sauvegarde.db", check_same_thread=False)
    c = conn.cursor()
    c.execute("""
    CREATE TABLE IF NOT EXISTS sauvegarde (
        joueur TEXT PRIMARY KEY,
        points INTEGER DEFAULT 0,
        consumables TEXT DEFAULT '{}',           -- JSON dict
        has_hat INTEGER DEFAULT 0,               -- 0/1
        inventory_list TEXT DEFAULT '[]',        -- JSON list
        achievements TEXT DEFAULT '[]',          -- JSON list
        pet TEXT DEFAULT 'none',                 -- none/egg/puppy/adult/legend
        pet_xp INTEGER DEFAULT 0
    )
    """)
    conn.commit()
    conn.close()

init_db()

def _row_to_state(row):
    # row: (joueur, points, consumables, has_hat, inventory_list, achievements, pet, pet_xp)
    return {
        "name": row[0],
        "points": int(row[1] or 0),
        "consumables": json.loads(row[2] or "{}"),
        "has_hat": bool(row[3] or 0),
        "inventory_list": json.loads(row[4] or "[]"),
        "achievements": set(json.loads(row[5] or "[]")),
        "pet": row[6] or "none",
        "pet_xp": int(row[7] or 0),
    }

def load_or_create_user_by_name_sqlite(name: str):
    conn = sqlite3.connect("sauvegarde.db", check_same_thread=False)
    c = conn.cursor()
    c.execute("""SELECT joueur, points, consumables, has_hat, inventory_list, achievements, pet, pet_xp
                 FROM sauvegarde WHERE joueur=?""", (name,))
    row = c.fetchone()
    if row:
        data = _row_to_state(row)
        st.session_state.points = data["points"]
        st.session_state.consumables = data["consumables"]
        st.session_state.has_hat = data["has_hat"]
        st.session_state.inventory_list = data["inventory_list"]
        st.session_state.achievements = data["achievements"]
        st.session_state.pet = data["pet"]
        st.session_state.pet_xp = data["pet_xp"]
    else:
        # créer une ligne par défaut
        c.execute("""INSERT INTO sauvegarde (joueur, points, consumables, has_hat, inventory_list, achievements, pet, pet_xp)
                     VALUES (?, 0, '{}', 0, '[]', '[]', 'none', 0)""", (name,))
        conn.commit()
    conn.close()

def save_current_user_sqlite():
    if not st.session_state.get("player_name"):
        return
    conn = sqlite3.connect("sauvegarde.db", check_same_thread=False)
    c = conn.cursor()
    c.execute("""
    UPDATE sauvegarde
    SET points=?, consumables=?, has_hat=?, inventory_list=?, achievements=?, pet=?, pet_xp=?
    WHERE joueur=?
    """, (
        int(st.session_state.points),
        json.dumps(st.session_state.consumables),
        1 if st.session_state.has_hat else 0,
        json.dumps(st.session_state.inventory_list),
        json.dumps(sorted(list(st.session_state.achievements))),
        st.session_state.pet,
        int(st.session_state.pet_xp),
        st.session_state.player_name
    ))
    conn.commit()
    conn.close()

# =========================
# App config
# =========================
st.set_page_config(page_title="Mon site de jeux", page_icon="🌐", layout="wide")
st.markdown("<h1 style='text-align:center'>Bienvenue sur mon site de jeux ✨</h1>", unsafe_allow_html=True)

# =========================
# Helpers / State
# =========================
def inventory_display_list():
    items = []
    if st.session_state.has_hat:
        items.append("🎩 Chapeau magique")
    for k, v in (st.session_state.consumables or {}).items():
        if v > 0:
            nice = {
                "indice_pendu": "💡 Indice Pendu",
                "aide_mastermind": "🎯 Aide Mastermind",
                "rejouer": "🔄 Rejouer",
                "boost_animal": "🚀 Boost Animal"
            }.get(k, k)
            items.append(f"{nice} x{v}")
    if st.session_state.pet != "none":
        pet_name = {
            "egg": "🥚 Œuf de compagnon",
            "puppy": "🐶 Compagnon (chiot)",
            "adult": "🐕 Compagnon (adulte)",
            "legend": "🐕‍🦺✨ Compagnon (légendaire)"
        }.get(st.session_state.pet, "Animal virtuel")
        items.append(pet_name)
    return items

def add_consumable(key, count=1):
    st.session_state.consumables[key] = st.session_state.consumables.get(key, 0) + count

def consume_item(key):
    if st.session_state.consumables.get(key, 0) > 0:
        st.session_state.consumables[key] -= 1
        return True
    return False

def check_legend_success():
    if (st.session_state.pet_xp >= 1000) and (not st.session_state.get("legend_awarded", False)):
        st.session_state.achievements.add("🏆 Légende vivante")
        st.session_state.points += 20
        st.session_state.legend_awarded = True
        st.balloons()
        st.success("🏆 Succès débloqué : Légende vivante ! +20 points")
        save_current_user_sqlite()

def evolve_pet_if_needed():
    if st.session_state.pet == "egg" and st.session_state.pet_xp >= 10:
        st.session_state.pet = "puppy"
        st.session_state.achievements.add("Naissance du compagnon")
        st.success("🐣 Ton œuf a éclos en chiot !")
    elif st.session_state.pet == "puppy" and st.session_state.pet_xp >= 30:
        st.session_state.pet = "adult"
        st.session_state.achievements.add("Compagnon adulte")
        st.success("🐶 Ton chiot est devenu adulte !")
    elif st.session_state.pet == "adult" and st.session_state.pet_xp >= 100:
        st.session_state.pet = "legend"
        st.session_state.achievements.add("Compagnon légendaire")
        st.success("👑 Ton compagnon est devenu légendaire !")
    check_legend_success()
    save_current_user_sqlite()

def award_points(points_gain=0, reason=None):
    bonus = 1 if st.session_state.has_hat else 0
    total = points_gain + bonus
    st.session_state.points += total
    if reason:
        st.success(f"+{total} points ({reason})")
    # suites / séries de victoires (succès simples)
    if points_gain > 0:
        st.session_state.total_wins += 1
        st.session_state.consecutive_wins += 1
    else:
        st.session_state.consecutive_wins = 0
    if st.session_state.total_wins >= 5:
        st.session_state.achievements.add("Vainqueur x5")
    if st.session_state.consecutive_wins >= 3:
        st.session_state.achievements.add("Série de 3 victoires")
    # pet XP
    if st.session_state.pet != "none":
        st.session_state.pet_xp += points_gain
        evolve_pet_if_needed()
    # déblocage mini-jeu secret
    if st.session_state.points >= 100:
        st.session_state.secret_unlocked = True
    save_current_user_sqlite()

# =========================
# Initialisation State (défauts)
# =========================
if "points" not in st.session_state: st.session_state.points = 0
if "consumables" not in st.session_state:
    st.session_state.consumables = {"indice_pendu": 0, "aide_mastermind": 0, "rejouer": 0, "boost_animal": 0}
if "has_hat" not in st.session_state: st.session_state.has_hat = False
if "inventory_list" not in st.session_state: st.session_state.inventory_list = []
if "achievements" not in st.session_state: st.session_state.achievements = set()
if "pet" not in st.session_state: st.session_state.pet = "none"
if "pet_xp" not in st.session_state: st.session_state.pet_xp = 0
if "legend_awarded" not in st.session_state: st.session_state.legend_awarded = False
if "total_wins" not in st.session_state: st.session_state.total_wins = 0
if "consecutive_wins" not in st.session_state: st.session_state.consecutive_wins = 0
if "secret" not in st.session_state: st.session_state.secret = random.randint(1, 20)
if "secret_unlocked" not in st.session_state: st.session_state.secret_unlocked = False

# Pendu
if "mot_secret" not in st.session_state:
    st.session_state.mot_secret = random.choice(["python","famille","ordinateur","jeu","tom","arcade","chat","pizza","robot","streamlit"])
if "lettres_trouvees" not in st.session_state: st.session_state.lettres_trouvees = []
if "erreurs" not in st.session_state: st.session_state.erreurs = 0
if "pendu_hint_used" not in st.session_state: st.session_state.pendu_hint_used = False
if "pendu_lost" not in st.session_state: st.session_state.pendu_lost = False

# Mastermind
if "mastermind_secret" not in st.session_state:
    couleurs = ["Rouge","Bleu","Vert","Jaune","Orange","Violet"]
    st.session_state.mastermind_secret = [random.choice(couleurs) for _ in range(4)]
if "mastermind_attempts" not in st.session_state: st.session_state.mastermind_attempts = 6
if "mastermind_hint_used" not in st.session_state: st.session_state.mastermind_hint_used = False
if "mastermind_lost" not in st.session_state: st.session_state.mastermind_lost = False

# Mots mélangés
if "mot_original" not in st.session_state:
    mots = ["python","france","ordinateur","Papick","programmation","robot"]
    st.session_state.mot_original = random.choice(mots)
    mel = list(st.session_state.mot_original)
    random.shuffle(mel)
    st.session_state.mot_melange = "".join(mel)
    st.session_state.mots_attempts = 3
if "mots_lost" not in st.session_state: st.session_state.mots_lost = False

# Trésor (mini-jeu secret)
if "treasure_pos" not in st.session_state:
    st.session_state.treasure_pos = (random.randint(0,3), random.randint(0,3))
if "treasure_attempts" not in st.session_state: st.session_state.treasure_attempts = 6
if "treasure_found" not in st.session_state: st.session_state.treasure_found = False

# =========================
# Connexion joueur (sidebar)
# =========================
st.sidebar.header("Joueur")
player_name = st.sidebar.text_input("Ton pseudo (obligatoire pour sauvegarder)", key="player_name_input")

if player_name:
    if "player_name" not in st.session_state or st.session_state.player_name != player_name:
        st.session_state.player_name = player_name
        load_or_create_user_by_name_sqlite(player_name)
        st.success(f"Bienvenue {player_name} — progression chargée.")
else:
    st.sidebar.info("Entrez un pseudo pour activer la sauvegarde.")

# =========================
# Navigation
# =========================
tab = st.sidebar.selectbox(
    "Navigation",
    ["Accueil", "Jeux internes", "Jeux externes", "Boutique", "Animal", "Succès", "Classement"]
)

# Top status bar
st.markdown(f"**💰 Points : {st.session_state.points} • Inventaire : {', '.join(inventory_display_list()) or 'Aucun'}**")

# =========================
# Pages
# =========================
if tab == "Accueil":
    st.header("🏠 Accueil")
    st.write("Bienvenue ! Renseigne ton **pseudo** dans la barre latérale pour charger / sauvegarder ta progression.")
    st.write("- Le mini-jeu secret se débloque à **100 points**.")
    st.write("Amuse-toi !")

elif tab == "Jeux internes":
    st.header("🎮 Jeux internes")
    game = st.selectbox("Choisis un jeu :", ["Devine le nombre", "Pierre-Papier-Ciseaux", "Pendu", "Mastermind", "Mots mélangés", "Mini-jeu secret"])

    # Devine le nombre
    if game == "Devine le nombre":
        st.subheader("🎲 Devine le nombre")
        guess = st.number_input("Entrez un nombre entre 1 et 20", min_value=1, max_value=20, step=1, key="guess_input")
        if st.button("Vérifier", key="btn_verify_guess"):
            if guess == st.session_state.secret:
                award_points(5, "Devine le nombre gagné")
                st.session_state.secret = random.randint(1, 20)
            elif guess < st.session_state.secret:
                st.info("C'est plus grand !")
            else:
                st.info("C'est plus petit !")

    # Pierre-Papier-Ciseaux
    elif game == "Pierre-Papier-Ciseaux":
        st.subheader("✂️ Pierre-Papier-Ciseaux")
        choix = st.radio("Faites votre choix :", ["Pierre", "Papier", "Ciseaux"], key="ppc_choice")
        if st.button("Jouer", key="btn_ppc"):
            bot = random.choice(["Pierre", "Papier", "Ciseaux"])
            st.write(f"L'ordinateur a choisi : {bot}")
            if choix == bot:
                st.info("Égalité ! 🤝")
            elif (choix == "Pierre" and bot == "Ciseaux") or \
                 (choix == "Papier" and bot == "Pierre") or \
                 (choix == "Ciseaux" and bot == "Papier"):
                award_points(2, "Chifoumi gagné")
            else:
                st.error("Perdu 😢")

    # Pendu
    elif game == "Pendu":
        st.subheader("🪢 Pendu amélioré")
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

        # Indice Pendu (consommable)
        if st.session_state.consumables.get("indice_pendu",0) > 0 and not st.session_state.pendu_hint_used:
            if st.button("💡 Utiliser Indice Pendu (révèle une lettre)"):
                remaining = [c for c in set(st.session_state.mot_secret) if c not in st.session_state.lettres_trouvees]
                if remaining:
                    chosen = random.choice(remaining)
                    st.session_state.lettres_trouvees.append(chosen)
                    st.session_state.pendu_hint_used = True
                    consume_item("indice_pendu")
                    st.success(f"💡 Indice utilisé : la lettre **{chosen}** a été révélée.")
                    save_current_user_sqlite()
                else:
                    st.info("Aucune lettre restante à révéler.")

        lettre = st.text_input("Proposez une lettre :", max_chars=1, key="pendu_input")
        if st.button("Proposer la lettre"):
            l = (lettre or "").lower()
            if not l or not l.isalpha():
                st.warning("⚠️ Entrez une lettre valide.")
            else:
                if l in st.session_state.lettres_trouvees:
                    st.warning("⚠️ Lettre déjà proposée.")
                elif l in st.session_state.mot_secret:
                    st.session_state.lettres_trouvees.append(l)
                    st.success(f"✅ La lettre **{l}** est dans le mot !")
                    save_current_user_sqlite()
                else:
                    st.session_state.erreurs += 1
                    st.error(f"❌ La lettre **{l}** n'est pas dans le mot.")

        # Gagné
        if "_" not in mot_affiche:
            award_points(3, "Pendu gagné")
            st.session_state.achievements.add("Maître du mot")
            st.session_state.mot_secret = random.choice(["python","famille","ordinateur","jeu","tom","arcade","chat","pizza","robot","streamlit"])
            st.session_state.lettres_trouvees = []
            st.session_state.erreurs = 0
            st.session_state.pendu_hint_used = False
            st.session_state.pendu_lost = False
            save_current_user_sqlite()

        # Perdu
        if st.session_state.erreurs >= len(pendu_etapes)-1:
            st.error(f"💀 Pendu ! Le mot était **{st.session_state.mot_secret}**.")
            st.session_state.pendu_lost = True
            if st.session_state.consumables.get("rejouer",0) > 0:
                if st.button("🔄 Utiliser Rejouer (consomme 1)"):
                    consume_item("rejouer")
                    st.session_state.mot_secret = random.choice(["python","famille","ordinateur","jeu","tom","arcade","chat","pizza","robot","streamlit"])
                    st.session_state.lettres_trouvees = []
                    st.session_state.erreurs = 0
                    st.session_state.pendu_hint_used = False
                    st.session_state.pendu_lost = False
                    st.success("La partie a été réinitialisée (Rejouer utilisé).")
                    save_current_user_sqlite()
            else:
                if st.button("Recommencer"):
                    st.session_state.mot_secret = random.choice(["python","famille","ordinateur","jeu","tom","arcade","chat","pizza","robot","streamlit"])
                    st.session_state.lettres_trouvees = []
                    st.session_state.erreurs = 0
                    st.session_state.pendu_hint_used = False
                    st.session_state.pendu_lost = False
                    save_current_user_sqlite()

    # Mastermind
    elif game == "Mastermind":
        st.subheader("🎯 Mastermind")
        couleurs = ["Rouge","Bleu","Vert","Jaune","Orange","Violet"]
        choix = [st.selectbox(f"Couleur {i+1}", couleurs, key=f"mm_color_{i}") for i in range(4)]
        if st.button("Vérifier combinaison"):
            bien_places = sum([c == s for c, s in zip(choix, st.session_state.mastermind_secret)])
            mal_places = sum(min(choix.count(c), st.session_state.mastermind_secret.count(c)) for c in couleurs) - bien_places
            st.write(f"Bien placés : {bien_places} | Mal placés : {mal_places}")
            if bien_places == 4:
                award_points(8, "Mastermind gagné")
                st.session_state.achievements.add("Maître du code")
                st.session_state.mastermind_secret = [random.choice(couleurs) for _ in range(4)]
                st.session_state.mastermind_attempts = 6
                st.session_state.mastermind_hint_used = False
                st.session_state.mastermind_lost = False
                save_current_user_sqlite()
            else:
                st.session_state.mastermind_attempts -= 1
                if st.session_state.mastermind_attempts <= 0:
                    st.error(f"Perdu ! La combinaison était : {st.session_state.mastermind_secret}")
                    st.session_state.mastermind_lost = True
                    if st.session_state.consumables.get("rejouer",0) > 0:
                        if st.button("🔄 Utiliser Rejouer (consomme 1)"):
                            consume_item("rejouer")
                            st.session_state.mastermind_secret = [random.choice(couleurs) for _ in range(4)]
                            st.session_state.mastermind_attempts = 6
                            st.session_state.mastermind_hint_used = False
                            st.session_state.mastermind_lost = False
                            st.success("Rejouer utilisé : nouvelle combinaison.")
                            save_current_user_sqlite()
                    else:
                        if st.button("Recommencer"):
                            st.session_state.mastermind_secret = [random.choice(couleurs) for _ in range(4)]
                            st.session_state.mastermind_attempts = 6
                            st.session_state.mastermind_hint_used = False
                            st.session_state.mastermind_lost = False
                            save_current_user_sqlite()

        
                # Aide Mastermind (consommable)
        if st.session_state.consumables.get("aide_mastermind", 0) > 0 and not st.session_state.mastermind_hint_used:
            if st.button("🎯 Utiliser Aide Mastermind (révèle une position)"):
                idx = random.randrange(4)
                couleur_reelle = st.session_state.mastermind_secret[idx]
                st.session_state.mastermind_hint_used = True
                consume_item("aide_mastermind")
                st.info(f"🎯 Indice : position {idx+1} = **{couleur_reelle}**")
                save_current_user_sqlite()

    # Mots mélangés
    elif game == "Mots mélangés":
        st.subheader("🔀 Mots mélangés")
        # état initial si besoin
        if "mot_original" not in st.session_state:
            mots = ["python", "france", "ordinateur", "Papick", "programmation", "robot"]
            st.session_state.mot_original = random.choice(mots)
            mel = list(st.session_state.mot_original)
            random.shuffle(mel)
            st.session_state.mot_melange = "".join(mel)
            st.session_state.mots_attempts = 3
        if "mots_lost" not in st.session_state:
            st.session_state.mots_lost = False

        st.write(f"Mot mélangé : **{st.session_state.mot_melange}**")
        proposition = st.text_input("Votre réponse :", key="mots_input")
        if st.button("Valider", key="mots_valider"):
            if (proposition or "").lower() == st.session_state.mot_original:
                award_points(5, "Mots mélangés gagné")
                st.session_state.achievements = st.session_state.get("achievements", set())
                st.session_state.achievements.add("Décodeur")
                mots = ["python", "france", "ordinateur", "Papick", "programmation", "robot"]
                st.session_state.mot_original = random.choice(mots)
                mel = list(st.session_state.mot_original)
                random.shuffle(mel)
                st.session_state.mot_melange = "".join(mel)
                st.session_state.mots_attempts = 3
                st.session_state.mots_lost = False
                save_current_user_sqlite()
            else:
                st.session_state.mots_attempts -= 1
                st.warning(f"Incorrect ! Essais restants : {st.session_state.mots_attempts}")
                if st.session_state.mots_attempts <= 0:
                    st.error(f"Perdu ! Le mot était : {st.session_state.mot_original}")
                    st.session_state.mots_lost = True
                    if st.session_state.consumables.get("rejouer", 0) > 0:
                        if st.button("🔄 Utiliser Rejouer (consomme 1)", key="mots_rejouer_btn"):
                            consume_item("rejouer")
                            mots = ["python", "france", "ordinateur", "Papick", "programmation", "robot"]
                            st.session_state.mot_original = random.choice(mots)
                            mel = list(st.session_state.mot_original)
                            random.shuffle(mel)
                            st.session_state.mot_melange = "".join(mel)
                            st.session_state.mots_attempts = 3
                            st.session_state.mots_lost = False
                            st.success("Rejouer utilisé : nouvelle partie.")
                            save_current_user_sqlite()
                    else:
                        if st.button("Recommencer", key="mots_restart_btn"):
                            mots = ["python", "france", "ordinateur", "Papick", "programmation", "robot"]
                            st.session_state.mot_original = random.choice(mots)
                            mel = list(st.session_state.mot_original)
                            random.shuffle(mel)
                            st.session_state.mot_melange = "".join(mel)
                            st.session_state.mots_attempts = 3
                            st.session_state.mots_lost = False
                            save_current_user_sqlite()

    # Mini-jeu secret
    elif game == "Mini-jeu secret":
        # déblocage à 100 pts (pas besoin de flag si tu préfères)
        secret_unlocked = st.session_state.get("secret_unlocked", False) or (st.session_state.points >= 100)
        if not secret_unlocked:
            st.info("Mini-jeu secret débloqué à 100 points.")
        else:
            st.subheader("🔒 Mini-jeu secret : Trouve le trésor")
            # état initial si besoin
            if "treasure_pos" not in st.session_state:
                st.session_state.treasure_pos = (random.randint(0, 3), random.randint(0, 3))
            if "treasure_attempts" not in st.session_state:
                st.session_state.treasure_attempts = 6
            if "treasure_found" not in st.session_state:
                st.session_state.treasure_found = False

            st.write("Tu as 6 essais pour trouver le trésor caché dans une grille 4x4.")
            st.write(f"Essais restants : {st.session_state.treasure_attempts}")
            x = st.slider("Choisis X", 0, 3, 0, key="tre_x_internal")
            y = st.slider("Choisis Y", 0, 3, 0, key="tre_y_internal")
            if st.button("Creuser", key="tre_dig_btn"):
                if (x, y) == st.session_state.treasure_pos:
                    award_points(20, "Trésor trouvé")
                    st.success("💎 Tu as trouvé le trésor !")
                    st.session_state.treasure_pos = (random.randint(0, 3), random.randint(0, 3))
                    st.session_state.treasure_attempts = 6
                    st.session_state.treasure_found = False
                    save_current_user_sqlite()
                else:
                    st.session_state.treasure_attempts -= 1
                    st.warning("Rien ici...")
                    if st.session_state.treasure_attempts <= 0:
                        st.error(f"Fin des essais ! Le trésor était en {st.session_state.treasure_pos}")
                        if st.button("Recommencer la chasse", key="tre_restart_btn"):
                            st.session_state.treasure_pos = (random.randint(0, 3), random.randint(0, 3))
                            st.session_state.treasure_attempts = 6
                            st.session_state.treasure_found = False
                            save_current_user_sqlite()



# ---------------------------
# PAGE: CLASSEMENT
# ---------------------------
elif tab == "Classement":
    st.header("🏆 Classement des joueurs")

    conn = sqlite3.connect("sauvegarde.db")
    cur = conn.cursor()

    # Récupérer le top 20
    cur.execute("""
        SELECT joueur, MAX(points) as pts
        FROM sauvegarde
        GROUP BY joueur
        ORDER BY pts DESC
        LIMIT 20
    """)
    rows = cur.fetchall()
    top_names = [r[0] for r in rows]

    # Trouver le score maximum (évite division par zéro)
    max_points = max((points for _, points in rows), default=0)

    # Affichage du top 20
    if rows:
        for i, (joueur, points) in enumerate(rows, start=1):
            medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}ᵉ"
            if max_points > 0:
                st.progress(points / max_points)
            else:
                st.progress(0)
            st.write(f"{medal} **{joueur}** — {points} points")
    else:
        st.info("Aucun joueur enregistré pour l’instant.")

    # Afficher la position du joueur connecté
    me_name = st.session_state.get("player_name", None)
    if me_name:
        save_current_user_sqlite()
        cur.execute("SELECT points FROM sauvegarde WHERE joueur = ?", (me_name,))
        me_row = cur.fetchone()
        if me_row:
            me_points = me_row[0]
            cur.execute("SELECT COUNT(*) + 1 FROM sauvegarde WHERE points > ?", (me_points,))
            me_rank = cur.fetchone()[0]
        else:
            cur.execute("INSERT INTO sauvegarde (joueur, points) VALUES (?, 0)", (me_name,))
            conn.commit()
            me_points, me_rank = 0, None

        if me_name not in top_names:
            st.markdown("---")
            st.subheader("📌 Ta position")
            me_badge = "🥇" if me_rank == 1 else "🥈" if me_rank == 2 else "🥉" if me_rank == 3 else f"{me_rank}ᵉ"
            if max_points > 0:
                st.progress(me_points / max_points)
            else:
                st.progress(0)
            st.write(f"{me_badge} **{me_name}** — {me_points} points")

    conn.close()


# =========================
# Footer
# =========================
st.markdown("---")
if st.button("💾 Sauvegarder maintenant"):
    save_current_user_sqlite()
    st.success("Progression sauvegardée.")

