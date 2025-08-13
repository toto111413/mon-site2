# app.py — Version 100% SQLite (compatible Streamlit Cloud)
import streamlit as st
import random
import json
import sqlite3
from typing import Dict, Optional

# =========================
# Création de la table SQLite
# =========================
def init_db():
    conn = sqlite3.connect("sauvegarde.db")
    c = conn.cursor()
    c.execute("""
    CREATE TABLE IF NOT EXISTS sauvegarde (
        joueur TEXT PRIMARY KEY,
        points INTEGER
    )
    """)
    conn.commit()
    conn.close()

init_db()

# =========================
# Fonctions SQLite
# =========================
def load_or_create_user_by_name_sqlite(name: str):
    conn = sqlite3.connect("sauvegarde.db")
    c = conn.cursor()
    c.execute("SELECT joueur, points FROM sauvegarde WHERE joueur = ?", (name,))
    row = c.fetchone()
    if row:
        st.session_state.points = row[1]
    else:
        c.execute("INSERT INTO sauvegarde (joueur, points) VALUES (?, ?)", (name, st.session_state.points))
        conn.commit()
    conn.close()

def save_current_user_sqlite():
    if "player_name" not in st.session_state or not st.session_state.player_name:
        return
    conn = sqlite3.connect("sauvegarde.db")
    c = conn.cursor()
    c.execute("UPDATE sauvegarde SET points = ? WHERE joueur = ?", 
              (st.session_state.points, st.session_state.player_name))
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

def award_points(points_gain=0, reason=None):
    bonus = 1 if st.session_state.has_hat else 0
    total = points_gain + bonus
    st.session_state.points += total
    if reason:
        st.success(f"+{total} points ({reason})")
    save_current_user_sqlite()

# =========================
# Initialisation du state
# =========================
if "points" not in st.session_state: st.session_state.points = 0
if "consumables" not in st.session_state:
    st.session_state.consumables = {"indice_pendu": 0, "aide_mastermind": 0, "rejouer": 0, "boost_animal": 0}
if "has_hat" not in st.session_state: st.session_state.has_hat = False
if "inventory_list" not in st.session_state: st.session_state.inventory_list = []
if "pet" not in st.session_state: st.session_state.pet = "none"
if "pet_xp" not in st.session_state: st.session_state.pet_xp = 0
if "secret" not in st.session_state: st.session_state.secret = random.randint(1, 20)

# =========================
# Connexion joueur
# =========================
st.sidebar.header("Joueur")
player_name = st.sidebar.text_input("Ton pseudo (obligatoire pour sauvegarder)")

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

# =========================
# Accueil
# =========================
if tab == "Accueil":
    st.header("🏠 Accueil")
    st.write("Bienvenue ! Renseigne ton pseudo dans la barre latérale pour sauvegarder ta progression.")

# =========================
# Jeux
# =========================
elif tab == "Jeux":
    st.header("🎮 Jeux")
    if st.button("Gagner 5 points (test)"):
        award_points(5, "Test")

# =========================
# Boutique
# =========================
elif tab == "Boutique":
    st.header("🛒 Boutique")
    st.write(f"Points disponibles : **{st.session_state.points}**")
    if st.button("Acheter 🎩 Chapeau magique (10 pts)"):
        if st.session_state.points >= 10:
            st.session_state.points -= 10
            st.session_state.has_hat = True
            save_current_user_sqlite()
            st.success("Chapeau acheté !")
        else:
            st.error("Pas assez de points.")

# =========================
# Animal
# =========================
elif tab == "Animal":
    st.header("🐶 Animal virtuel")
    st.write(f"Statut : {st.session_state.pet}")
    st.write(f"XP : {st.session_state.pet_xp}")

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

    # Affichage du top 20
    if rows:
        max_points = max(points for _, points in rows)
        for i, (joueur, points) in enumerate(rows, start=1):
            medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}ᵉ"
            st.write(f"{medal} **{joueur}** — {points} points")
            st.progress(points / max_points)
    else:
        st.info("Aucun joueur enregistré pour l’instant.")
        max_points = 0

    # Afficher la position du joueur connecté même s'il n'est pas dans le top 20
    me_name = st.session_state.get("player_name", None)
    if me_name:
        save_current_user_sqlite()  # Sauvegarde pour être sûr que c'est en DB
        cur.execute("SELECT points FROM sauvegarde WHERE joueur = ?", (me_name,))
        me_row = cur.fetchone()
        if me_row:
            me_points = me_row[0]
            cur.execute("SELECT COUNT(*) + 1 FROM sauvegarde WHERE points > ?", (me_points,))
            me_rank = cur.fetchone()[0]
        else:
            cur.execute("INSERT INTO sauvegarde (joueur, points) VALUES (?, 0)", (me_name,))
            conn.commit()
            me_points = 0
            me_rank = None

        if me_name not in top_names:
            st.markdown("---")
            st.subheader("📌 Ta position")
            me_badge = "🥇" if me_rank == 1 else "🥈" if me_rank == 2 else "🥉" if me_rank == 3 else f"{me_rank}ᵉ"
            st.write(f"{me_badge} **{me_name}** — {me_points} points")
            if max_points > 0:
                st.progress(me_points / max_points)
            else:
                st.progress(0)

    conn.close()


            # Surligne ma ligne si je suis dedans
    if me_name and joueur == me_name:
        st.markdown(f"**{badge} {joueur} — {points} points**")
    else:
        st.write(f"{badge} {joueur} — {points} points")

        st.progress(points, max_points)

        # Si je ne suis pas dans le top 20 mais j’ai un rang : affiche ma ligne perso
        top_names = {j for j, _ in rows}
        if me_name and (me_points is not None) and (me_name not in top_names):
            st.markdown("---")
            st.subheader("Ta position")
            me_badge = "🥇" if me_rank == 1 else ("🥈" if me_rank == 2 else ("🥉" if me_rank == 3 else ordinal_fr(me_rank)))
            st.markdown(f"**{me_badge} {me_name} — {me_points} points**")
            st.progress((me_points / max_points) if max_points else 0.0)
        else:
            st.info("Aucun joueur enregistré pour l’instant.")


# =========================
# Footer
# =========================
st.markdown("---")
if st.button("💾 Sauvegarder maintenant"):
    save_current_user_sqlite()
    st.success("Progression sauvegardée.")

