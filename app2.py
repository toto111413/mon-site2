# app.py — Version 100% SQLite (compatible Streamlit Cloud)
import streamlit as st
import random
import json
import sqlite3
from typing import Dict, Optional

# =========================
# Base de données (SQLite)
# =========================
def get_conn():
    # check_same_thread=False pour usage dans Streamlit
    return sqlite3.connect("sauvegarde.db", check_same_thread=False)

def db_init():
    conn = get_conn()
    cur = conn.cursor()
    # Table des utilisateurs avec toutes les colonnes nécessaires
    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        name TEXT PRIMARY KEY,
        points INTEGER NOT NULL DEFAULT 0,
        consumables TEXT NOT NULL DEFAULT '{}',      -- JSON dict
        has_hat INTEGER NOT NULL DEFAULT 0,          -- 0/1
        inventory_list TEXT NOT NULL DEFAULT '[]',   -- JSON list
        achievements TEXT NOT NULL DEFAULT '[]',     -- JSON list
        pet TEXT NOT NULL DEFAULT 'none',
        pet_xp INTEGER NOT NULL DEFAULT 0
    )
    """)
    conn.commit()
    conn.close()

def db_get_user(name: str) -> Optional[Dict]:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT name, points, consumables, has_hat, inventory_list, achievements, pet, pet_xp
        FROM users WHERE name=?
    """, (name,))
    row = cur.fetchone()
    conn.close()
    if not row:
        return None
    try:
        return {
            "name": row[0],
            "points": int(row[1] or 0),
            "consumables": json.loads(row[2] or "{}"),
            "has_hat": bool(row[3]),
            "inventory_list": json.loads(row[4] or "[]"),
            "achievements": set(json.loads(row[5] or "[]")),
            "pet": row[6] or "none",
            "pet_xp": int(row[7] or 0),
        }
    except Exception:
        # Si jamais mauvaise donnée, on revient à un état par défaut
        return {
            "name": name,
            "points": 0,
            "consumables": {},
            "has_hat": False,
            "inventory_list": [],
            "achievements": set(),
            "pet": "none",
            "pet_xp": 0,
        }

def db_upsert_user(state: Dict):
    # state attendu: keys name, points, consumables, has_hat, inventory_list, achievements, pet, pet_xp
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO users (name, points, consumables, has_hat, inventory_list, achievements, pet, pet_xp)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(name) DO UPDATE SET
            points=excluded.points,
            consumables=excluded.consumables,
            has_hat=excluded.has_hat,
            inventory_list=excluded.inventory_list,
            achievements=excluded.achievements,
            pet=excluded.pet,
            pet_xp=excluded.pet_xp
    """, (
        state["name"],
        int(state.get("points", 0)),
        json.dumps(state.get("consumables", {})),
        1 if state.get("has_hat", False) else 0,
        json.dumps(state.get("inventory_list", [])),
        json.dumps(list(state.get("achievements", []))),
        state.get("pet", "none"),
        int(state.get("pet_xp", 0)),
    ))
    conn.commit()
    conn.close()

# =========================
# App config
# =========================
st.set_page_config(page_title="Mon site de jeux", page_icon="🌐", layout="wide")
st.markdown("<h1 style='text-align:center'>Bienvenue sur mon site de jeux ✨</h1>", unsafe_allow_html=True)

# =========================
# Helpers UI / State
# =========================
def inventory_display_list():
    items = []
    if st.session_state.has_hat:
        items.append("🎩 Chapeau magique")
    for k, v in st.session_state.consumables.items():
        if v > 0:
            name = {
                "indice_pendu": "💡 Indice Pendu",
                "aide_mastermind": "🎯 Aide Mastermind",
                "rejouer": "🔄 Rejouer",
                "boost_animal": "🚀 Boost Animal"
            }.get(k, k)
            items.append(f"{name} x{v}")
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

def get_state_for_saving(name: str):
    return {
        "name": name,
        "points": st.session_state.points,
        "consumables": st.session_state.consumables,
        "has_hat": st.session_state.has_hat,
        "inventory_list": st.session_state.inventory_list,
        "achievements": list(st.session_state.achievements),
        "pet": st.session_state.pet,
        "pet_xp": st.session_state.pet_xp
    }

def save_current_user():
    if "player_name" not in st.session_state or not st.session_state.player_name:
        return
    db_upsert_user(get_state_for_saving(st.session_state.player_name))

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
    save_current_user()

def check_legend_success():
    if (st.session_state.pet_xp >= 1000) and (not st.session_state.legend_awarded):
        st.session_state.achievements.add("🏆 Légende vivante")
        st.session_state.points += 20
        st.session_state.legend_awarded = True
        st.balloons()
        st.success("🏆 Succès débloqué : Légende vivante ! +20 points")
        save_current_user()

def award_points(points_gain=0, reason=None):
    bonus = 1 if st.session_state.has_hat else 0
    total = points_gain + bonus
    st.session_state.points += total
    if reason:
        st.success(f"+{total} points ({reason})")
    if points_gain > 0:
        st.session_state.total_wins += 1
        st.session_state.consecutive_wins += 1
    else:
        st.session_state.consecutive_wins = 0
    if st.session_state.total_wins >= 5:
        st.session_state.achievements.add("Vainqueur x5")
    if st.session_state.consecutive_wins >= 3:
        st.session_state.achievements.add("Série de 3 victoires")
    if st.session_state.pet != "none":
        st.session_state.pet_xp += points_gain
        evolve_pet_if_needed()
    if st.session_state.points >= 100:
        st.session_state.secret_unlocked = True
    save_current_user()

# =========================
# Initialisation
# =========================
db_init()

# State par défaut
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
    mots = ["python","streamlit","ordinateur","arcade","programmation","robot"]
    st.session_state.mot_original = random.choice(mots)
    melange = list(st.session_state.mot_original)
    random.shuffle(melange)
    st.session_state.mot_melange = "".join(melange)
    st.session_state.mots_attempts = 3
if "mots_lost" not in st.session_state: st.session_state.mots_lost = False

# Trésor
if "treasure_pos" not in st.session_state:
    st.session_state.treasure_pos = (random.randint(0,3), random.randint(0,3))
if "treasure_attempts" not in st.session_state: st.session_state.treasure_attempts = 6
if "treasure_found" not in st.session_state: st.session_state.treasure_found = False

# =========================
# Sidebar & Navigation
# =========================
st.sidebar.header("Joueur")
player_name = st.sidebar.text_input("Ton pseudo (pour sauvegarder)", key="player_name_input")

if player_name:
    if "player_name" not in st.session_state or st.session_state.player_name != player_name:
        st.session_state.player_name = player_name
        # Charger depuis la DB si déjà existant, sinon créer une ligne avec l'état courant
        existing = db_get_user(player_name)
        if existing:
            st.session_state.points = existing["points"]
            st.session_state.consumables = existing["consumables"]
            st.session_state.has_hat = existing["has_hat"]
            st.session_state.inventory_list = existing["inventory_list"]
            st.session_state.achievements = set(existing["achievements"])
            st.session_state.pet = existing["pet"]
            st.session_state.pet_xp = existing["pet_xp"]
            st.success(f"Bienvenue {player_name} — progression chargée.")
        else:
            db_upsert_user(get_state_for_saving(player_name))
            st.success(f"Bienvenue {player_name} — nouveau profil créé.")
else:
    st.sidebar.info("Entre un pseudo pour activer la sauvegarde.")

tab = st.sidebar.selectbox("Navigation", ["Accueil", "Jeux internes", "Jeux externes", "Boutique", "Animal", "Succès"])

st.markdown(f"**💰 Points : {st.session_state.points} • Inventaire : {', '.join(inventory_display_list()) or 'Aucun'}**")

# =========================
# Pages
# =========================
if tab == "Accueil":
    st.header("🏠 Accueil")
    st.write("Bienvenue ! Renseigne ton **pseudo** dans la barre latérale pour charger / sauvegarder ta progression.")
    st.write("- Le mini-jeu secret se débloque à 100 points.")
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
                save_current_user()
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
                save_current_user()
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
                    save_current_user()
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
                    save_current_user()
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
            save_current_user()

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
                    save_current_user()
            else:
                if st.button("Recommencer"):
                    st.session_state.mot_secret = random.choice(["python","famille","ordinateur","jeu","tom","arcade","chat","pizza","robot","streamlit"])
                    st.session_state.lettres_trouvees = []
                    st.session_state.erreurs = 0
                    st.session_state.pendu_hint_used = False
                    st.session_state.pendu_lost = False
                    save_current_user()

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
                save_current_user()
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
                            save_current_user()
                    else:
                        if st.button("Recommencer"):
                            st.session_state.mastermind_secret = [random.choice(couleurs) for _ in range(4)]
                            st.session_state.mastermind_attempts = 6
                            st.session_state.mastermind_hint_used = False
                            st.session_state.mastermind_lost = False
                            save_current_user()

        # Aide Mastermind (consommable)
        if st.session_state.consumables.get("aide_mastermind",0) > 0 and not st.session_state.mastermind_hint_used:
            if st.button("🎯 Utiliser Aide Mastermind (révèle une position)"):
                idx = random.randrange(4)
                couleur_reelle = st.session_state.mastermind_secret[idx]
                st.session_state.mastermind_hint_used = True
                consume_item("aide_mastermind")
                st.info(f"🎯 Indice : position {idx+1} = **{couleur_reelle}**")
                save_current_user()

    # Mots mélangés
    elif game == "Mots mélangés":
        st.subheader("🔀 Mots mélangés")
        st.write(f"Mot mélangé : **{st.session_state.mot_melange}**")
        proposition = st.text_input("Votre réponse :")
        if st.button("Valider"):
            if (proposition or "").lower() == st.session_state.mot_original:
                award_points(5, "Mots mélangés gagné")
                st.session_state.achievements.add("Décodeur")
                mots = ["python","streamlit","ordinateur","arcade","programmation","robot"]
                st.session_state.mot_original = random.choice(mots)
                melange = list(st.session_state.mot_original)
                random.shuffle(melange)
                st.session_state.mot_melange = "".join(melange)
                st.session_state.mots_attempts = 3
                st.session_state.mots_lost = False
                save_current_user()
            else:
                st.session_state.mots_attempts -= 1
                st.warning(f"Incorrect ! Essais restants : {st.session_state.mots_attempts}")
                if st.session_state.mots_attempts <= 0:
                    st.error(f"Perdu ! Le mot était : {st.session_state.mot_original}")
                    st.session_state.mots_lost = True
                    if st.session_state.consumables.get("rejouer",0) > 0:
                        if st.button("🔄 Utiliser Rejouer (consomme 1)"):
                            consume_item("rejouer")
                            mots = ["python","france","ordinateur","Papick","programmation","robot"]
                            st.session_state.mot_original = random.choice(mots)
                            melange = list(st.session_state.mot_original)
                            random.shuffle(melange)
                            st.session_state.mot_melange = "".join(melange)
                            st.session_state.mots_attempts = 3
                            st.session_state.mots_lost = False
                            st.success("Rejouer utilisé : nouvelle partie.")
                            save_current_user()
                    else:
                        if st.button("Recommencer"):
                            mots = ["python","streamlit","ordinateur","arcade","programmation","robot"]
                            st.session_state.mot_original = random.choice(mots)
                            melange = list(st.session_state.mot_original)
                            random.shuffle(melange)
                            st.session_state.mot_melange = "".join(melange)
                            st.session_state.mots_attempts = 3
                            st.session_state.mots_lost = False
                            save_current_user()

    # Mini-jeu secret
    elif game == "Mini-jeu secret":
        if not st.session_state.secret_unlocked:
            st.info("Mini-jeu secret débloqué à 100 points.")
        else:
            st.subheader("🔒 Mini-jeu secret : Trouve le trésor")
            st.write("Tu as 6 essais pour trouver le trésor caché dans une grille 4x4.")
            st.write(f"Essais restants : {st.session_state.treasure_attempts}")
            x = st.slider("Choisis X", 0, 3, 0, key="tre_x_internal")
            y = st.slider("Choisis Y", 0, 3, 0, key="tre_y_internal")
            if st.button("Creuser"):
                if (x,y) == st.session_state.treasure_pos:
                    award_points(20, "Trésor trouvé")
                    st.success("💎 Tu as trouvé le trésor !")
                    st.session_state.treasure_pos = (random.randint(0,3), random.randint(0,3))
                    st.session_state.treasure_attempts = 6
                    st.session_state.treasure_found = False
                    save_current_user()
                else:
                    st.session_state.treasure_attempts -= 1
                    st.warning("Rien ici...")
                    if st.session_state.treasure_attempts <= 0:
                        st.error(f"Fin des essais ! Le trésor était en {st.session_state.treasure_pos}")
                        if st.button("Recommencer la chasse"):
                            st.session_state.treasure_pos = (random.randint(0,3), random.randint(0,3))
                            st.session_state.treasure_attempts = 6
                            st.session_state.treasure_found = False
                            save_current_user()

elif tab == "Jeux externes":
    st.header("🌐 Jeux externes")
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

elif tab == "Boutique":
    st.header("🛒 Boutique")
    st.write(f"Points disponibles : **{st.session_state.points}**")
    st.subheader("Articles disponibles")

    SHOP = [
        {"key":"pet_egg","nom":"🥚 Œuf de compagnon","prix":15,"desc":"Éclosion puis compagnon évolutif.","consumable":False},
        {"key":"chapeau","nom":"🎩 Chapeau magique","prix":10,"desc":"Permanent : +1 point bonus par victoire.","consumable":False},
        {"key":"indice_pendu","nom":"💡 Indice Pendu","prix":8,"desc":"Révèle une lettre au Pendu (1x).","consumable":True},
        {"key":"aide_mastermind","nom":"🎯 Aide Mastermind","prix":8,"desc":"Révèle la couleur correcte d'une position (1x).","consumable":True},
        {"key":"rejouer","nom":"🔄 Rejouer","prix":12,"desc":"Recommence une partie perdue (1x).","consumable":True},
        {"key":"boost_animal","nom":"🚀 Boost Animal","prix":10,"desc":"+10 XP compagnon (1x).","consumable":True}
    ]

    for art in SHOP:
        c1, c2 = st.columns([3,1])
        with c1:
            st.write(f"**{art['nom']}** - {art['prix']} pts")
            st.caption(art["desc"])
        with c2:
            if art["key"] == "pet_egg":
                if st.session_state.pet != "none":
                    st.button("Acheté", key="bought_pet")
                else:
                    if st.button("Acheter", key="buy_pet"):
                        if st.session_state.points >= art["prix"]:
                            st.session_state.points -= art["prix"]
                            st.session_state.pet = "egg"
                            if art["nom"] not in st.session_state.inventory_list:
                                st.session_state.inventory_list.append(art["nom"])
                            st.success("🥚 Tu as adopté un œuf ! Va voir la page Animal.")
                            save_current_user()
                        else:
                            st.error("Pas assez de points.")
            elif art["key"] == "chapeau":
                if st.session_state.has_hat:
                    st.button("Acheté", key="bought_hat")
                else:
                    if st.button("Acheter", key="buy_hat"):
                        if st.session_state.points >= art["prix"]:
                            st.session_state.points -= art["prix"]
                            st.session_state.has_hat = True
                            if art["nom"] not in st.session_state.inventory_list:
                                st.session_state.inventory_list.append(art["nom"])
                            st.success("🎩 Chapeau acheté ! (+1 point bonus par victoire)")
                            save_current_user()
                        else:
                            st.error("Pas assez de points.")
            else:
                cnt = st.session_state.consumables.get(art["key"],0)
                st.write(f"x{cnt}")
                if st.button("Acheter", key=f"buy_{art['key']}"):
                    if st.session_state.points >= art["prix"]:
                        st.session_state.points -= art["prix"]
                        add_consumable(art["key"],1)
                        if art["nom"] not in st.session_state.inventory_list:
                            st.session_state.inventory_list.append(art["nom"])
                        st.success(f"{art['nom']} ajouté à ton inventaire.")
                        save_current_user()
                    else:
                        st.error("Pas assez de points.")

    st.markdown("---")
    st.subheader("Inventaire détaillé")
    inv = inventory_display_list()
    if inv:
        for i in inv:
            st.write("•", i)
    else:
        st.write("Aucun objet possédé.")

elif tab == "Animal":
    st.header("🐶 Animal virtuel")
    visuals = {
        "none": "Tu n'as pas d'animal. Achète l'œuf dans la boutique.",
        "egg": "🥚 (œuf)",
        "puppy": "🐶 (chiot)",
        "adult": "🐕 (adulte)",
        "legend": "🐕‍🦺✨ (légendaire)"
    }
    st.write(f"Statut : **{visuals.get(st.session_state.pet, 'none')}**")
    st.write(f"XP du compagnon : {st.session_state.pet_xp}")
    if st.session_state.pet != "none":
        if st.button("Caresser (+1 pet XP)"):
            st.session_state.pet_xp += 1
            evolve_pet_if_needed()
            save_current_user()
            st.success("❤️ Le compagnon est content.")
    if st.session_state.consumables.get("boost_animal",0) > 0:
        if st.button("🚀 Utiliser Boost Animal (+10 pet XP)"):
            consume_item("boost_animal")
            st.session_state.pet_xp += 10
            evolve_pet_if_needed()
            save_current_user()
            st.success("Boost Animal utilisé (+10 pet XP).")
    st.markdown("---")
    st.write("Ton compagnon gagne de l'XP quand tu gagnes des parties (égal au nombre de points gagnés).")

elif tab == "Succès":
    st.header("🏆 Succès débloqués")
    if st.session_state.achievements:
        for a in sorted(st.session_state.achievements):
            st.write("•", a)
    else:
        st.write("Aucun succès débloqué pour le moment. Joue pour en obtenir !")

# =========================
# Footer / Sauvegarde
# =========================
st.markdown("---")
if st.button("💾 Sauvegarder maintenant"):
    save_current_user()
    st.success("Progression sauvegardée dans la base locale (SQLite).")

st.caption("Version SQLite : onglets, boutique, animal virtuel, succès, et sauvegarde locale persistante.")



