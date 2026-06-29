import streamlit as st

# Vérification du mot de passe admin
password = st.sidebar.text_input("Mot de passe Admin", type="password")
if password == "TCM2026!": # Vous pourrez choisir le mot de passe que vous voulez ici
    st.sidebar.success("Mode Administrateur Activé")
    # Tout votre code de l'espace administration actuel se range ici...import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, time

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(page_title="TCM - Tennis Club Manage", page_icon="🎾", layout="wide")

# --- CONNEXION BASE DE DONNÉES ---
conn = sqlite3.connect('tcm_club.db', check_same_thread=False)
cursor = conn.cursor()

# Création des tables si elles n'existent pas
cursor.execute('''
CREATE TABLE IF NOT EXISTS membres (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nom TEXT NOT NULL,
    prenom TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS reservations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    terrain TEXT NOT NULL,
    date TEXT NOT NULL,
    heure TEXT NOT NULL,
    membre_id INTEGER,
    FOREIGN KEY(membre_id) REFERENCES membres(id)
)
''')
conn.commit()

# --- CONFIGURATION DU CLUB ---
TERRAINS = [f"Extérieur {i}" for i in range(1, 7)] + [f"Intérieur {i}" for i in range(1, 3)]
HEURES = [f"{h:02d}:00" for h in range(8, 22)] # De 08:00 à 22:00

# --- TITRE PRINCIPAL ---
st.title("🎾 Tennis Club Manage (TCM)")
st.subheader("Système de réservation des terrains")

# --- NAVIGATION ---
menu = st.sidebar.radio("Navigation", ["📆 Réserver un terrain", "👤 Espace Administration"])

# ----------------------------------------------------
# 📆 PAGE : RÉSERVATION
# ----------------------------------------------------
if menu == "📆 Réserver un terrain":
    st.header("Faire une réservation")
    
    # 1. Sélection du membre
    membres_df = pd.read_sql_query("SELECT id, prenom || ' ' || nom as complet FROM membres", conn)
    
    if membres_df.empty:
        st.warning("⚠️ Aucun membre enregistré. Veuillez vous rendre dans l'Espace Administration pour ajouter des membres.")
    else:
        liste_membres = membres_df['complet'].tolist()
        membre_selectionne = st.selectbox("Qui réserve ?", liste_membres)
        membre_id = int(membres_df[membres_df['complet'] == membre_selectionne]['id'].values[0])
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            date_choisie = st.date_input("Choisir une date", datetime.today())
        with col2:
            terrain_choisi = st.selectbox("Choisir un terrain", TERRAINS)
        with col3:
            heure_choisie = st.selectbox("Choisir une heure (Créneau d'1h)", HEURES)
            
        if st.button("Confirmer la réservation", type="primary"):
            # Vérification si le terrain est déjà pris à cette date et heure
            cursor.execute(
                "SELECT * FROM reservations WHERE terrain=? AND date=? AND heure=?", 
                (terrain_choisi, str(date_choisie), heure_choisie)
            )
            existe = cursor.fetchone()
            
            if existe:
                st.error(f"❌ Désolé, le **{terrain_choisi}** est déjà réservé à **{heure_choisie}** le {date_choisie}.")
            else:
                cursor.execute(
                    "INSERT INTO reservations (terrain, date, heure, membre_id) VALUES (?, ?, ?, ?)",
                    (terrain_choisi, str(date_choisie), heure_choisie, membre_id)
                )
                conn.commit()
                st.success(f"✅ Réservation validée pour {membre_selectionne} : {terrain_choisi} à {heure_choisie} le {date_choisie}.")

    # Affichage du planning du jour
    st.write("---")
    st.subheader("📅 Planning des réservations")
    date_planning = st.date_input("Voir le planning du :", datetime.today(), key="planning_date")
    
    query = """
        SELECT r.terrain, r.heure, (m.prenom || ' ' || m.nom) as joueur 
        FROM reservations r 
        JOIN membres m ON r.membre_id = m.id 
        WHERE r.date = ?
    """
    res_df = pd.read_sql_query(query, conn, params=(str(date_planning),))
    
    if res_df.empty:
        st.info("Aucune réservation pour cette journée. Tous les terrains sont libres ! 🎾")
    else:
        st.dataframe(res_df, use_container_width=True, hide_index=True)

# ----------------------------------------------------
# 👤 PAGE : ADMINISTRATION
# ----------------------------------------------------
elif menu == "👤 Espace Administration":
    st.header("Gestion du club (Admin)")
    
    tab1, tab2 = st.tabs(["➕ Ajouter un membre", "📋 Liste des membres"])
    
    with tab1:
        st.subheader("Enregistrer un nouveau membre")
        with st.form("ajout_membre"):
            nom = st.text_input("Nom")
            prenom = st.text_input("Prénom")
            email = st.text_input("Adresse Email")
            
            submit = st.form_submit_button("Ajouter le membre")
            
            if submit:
                if nom and prenom and email:
                    try:
                        cursor.execute("INSERT INTO membres (nom, prenom, email) VALUES (?, ?, ?)", (nom, prenom, email))
                        conn.commit()
                        st.success(f"Le membre **{prenom} {nom}** a été ajouté avec succès !")
                    except sqlite3.IntegrityError:
                        st.error("❌ Cet email est déjà utilisé par un autre membre.")
                else:
                    st.warning("⚠️ Veuillez remplir tous les champs.")
                    
    with tab2:
        st.subheader("Membres inscrits au TCM")
        membres_complets = pd.read_sql_query("SELECT id, prenom, nom, email FROM membres", conn)
        if membres_complets.empty:
            st.info("Aucun membre inscrit pour le moment.")
        else:
            st.dataframe(membres_complets, use_container_width=True, hide_index=True)
