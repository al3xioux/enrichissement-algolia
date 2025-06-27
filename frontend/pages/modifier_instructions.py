import streamlit as st
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from backend.SupaBase.main import get_all_instructions_categories_lvl0, update_instruction_category_lvl0, post_instruction_category_lvl0

st.title("🔧 Administration des instructions")

# Récupération des instructions
categories = get_all_instructions_categories_lvl0()

if not categories:
    st.warning("Aucune instruction trouvée dans la base de données.")
    st.stop()

# Sélection d'une catégorie à éditer
noms = [cat['Nom'] for cat in categories]
nom_selectionne = st.selectbox("Sélectionnez une catégorie à modifier", noms)

categorie = next((cat for cat in categories if cat['Nom'] == nom_selectionne), None)

if categorie:
    with st.form("edit_instruction_form"):
        nouveau_nom = st.text_input("Nom de la catégorie", value=categorie.get('Nom', ''))
        nouvelle_instruction = st.text_area("Instruction", value=categorie.get('Instruction', ''), height=300)
        nouvelle_instruction_juge = st.text_area("Instruction Juge", value=categorie.get('Instruction_juge', ''), height=200)
        submit = st.form_submit_button("Enregistrer les modifications")
        if submit:
            result = update_instruction_category_lvl0(
                nom_original=nom_selectionne,
                nouveau_nom=nouveau_nom,
                nouvelle_instruction=nouvelle_instruction,
                nouvelle_instruction_juge=nouvelle_instruction_juge
            )
            if result:
                st.success("✅ Modifications enregistrées avec succès !")
            else:
                st.error("❌ Échec de la mise à jour ou aucune modification détectée.")

    with st.form("add_instruction_form"):
        nouveau_nom = st.text_input("Nom de la catégorie")
        nouvelle_instruction = st.text_area("Instruction")
        nouvelle_instruction_juge = st.text_area("Instruction Juge")
        submit = st.form_submit_button("Ajouter la catégorie")
        if submit:
            result = post_instruction_category_lvl0(nouveau_nom, nouvelle_instruction, nouvelle_instruction_juge)
            if result:
                st.success("✅ Catégorie ajoutée avec succès !")
            else:
                st.error("❌ Échec de l'ajout de la catégorie.")