import streamlit as st
import sys
import os
import json
import time
import pandas as pd
import io

st.set_page_config(
    page_title="Enrichissement Algolia",
    layout="wide"
)

# -------------------------------------------------
# Imports locaux (backend)
# -------------------------------------------------

# Ajouter le dossier parent au sys.path pour pouvoir importer les modules backend
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.GET.main import (
    get_algolia_indexes_name,
    get_categories_lvl0_name,
    get_categories_lvl1_name,
    get_categories_lvl2_name,
    get_product_by_id,
    get_products_by_category_lvl2,
    get_algolia_fields,
)
from backend.POST.main import post_new_field_to_products
from backend.agent.main import enrichir_champ_batch, enrichir_champ_batch_excel
from backend.SupaBase.main import (
    get_nom_instructions_categories_lvl0,
    get_instruction_by_nom,
    get_instruction_juge_by_nom,
)
from openai import OpenAI

# -------------------------------------------------
# Session state & authentification
# -------------------------------------------------

if "products" not in st.session_state:
    st.session_state.products = None
if "custom_fields" not in st.session_state:
    st.session_state.custom_fields = set()

SESSION_TIMEOUT = 30 * 60  # 30 minutes (en secondes)


def check_password():
    """Affiche un petit formulaire de connexion et gère la durée de session."""
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
    if "login_time" not in st.session_state:
        st.session_state.login_time = None

    # Déconnexion automatique après timeout
    if st.session_state.logged_in:
        if st.session_state.login_time and (time.time() - st.session_state.login_time > SESSION_TIMEOUT):
            st.session_state.logged_in = False
            st.session_state.login_time = None
            st.warning("Session expirée, veuillez vous reconnecter.")
            st.rerun()

    # Formulaire de login si non authentifié
    if not st.session_state.logged_in:
        with st.form("login_form"):
            password = st.text_input("Mot de passe", type="password")
            if st.form_submit_button("Se connecter"):
                if password == os.getenv("PASSWORD"):
                    st.session_state.logged_in = True
                    st.session_state.login_time = time.time()
                    st.success("Connexion réussie !")
                    st.rerun()
                else:
                    st.error("Mot de passe incorrect")
        st.stop()
    else:
        if st.button("Déconnexion"):
            st.session_state.logged_in = False
            st.session_state.login_time = None
            st.rerun()


check_password()

# -------------------------------------------------
# Helpers
# -------------------------------------------------

def clean_category_name(category: str | None):
    if not category:
        return None
    parts = category.split(" > ")
    return parts[-1] if len(parts) > 1 else category


def get_full_category_path(category_name: str, all_categories: list[str]):
    return next((cat for cat in all_categories if clean_category_name(cat) == category_name), None)


def filter_categories_by_parent(categories: list[str], parent_category: str | None):
    if not parent_category:
        return []
    return [cat for cat in categories if cat.startswith(parent_category)]


def extract_object_id(prod):
    d = prod.model_dump() if hasattr(prod, "model_dump") else prod
    for key in [
        "objectID",
        "objectId",
        "_objectID",
        "_objectId",
        "object_id",
    ]:
        if key in d:
            return d[key]
    return None


# -------------------------------------------------
# Mise en page / CSS minimal
# -------------------------------------------------

st.title("🔄 Enrichissement Algolia")

st.markdown(
    """
    <style>
        .block-container {padding-right: 2rem;}
        .stButton>button {width: 100%;}
        .product-card {border: 1px solid #e0e0e0;border-radius: 10px;padding: 15px;margin-bottom: 15px;background-color: white;}
        .product-card:hover {box-shadow: 0 4px 8px rgba(0,0,0,0.1);}    
    </style>
    """,
    unsafe_allow_html=True,
)

# -------------------------------------------------
# Sidebar — Recherche & import de produits
# -------------------------------------------------

with st.sidebar:
    st.header("Recherche de produit")

    indexes_name = get_algolia_indexes_name()
    index_name = st.selectbox("Index Algolia", indexes_name)

    # --- Catégorie niveau 0 ---
    category_lvl0_name = get_categories_lvl0_name(index_name)
    category_lvl0 = st.selectbox(
        "Catégorie niveau 0",
        [clean_category_name(c) for c in category_lvl0_name],
    )

    # --- Catégorie niveau 1 ---
    if category_lvl0:
        cat_lvl0_full = get_full_category_path(category_lvl0, category_lvl0_name)
        category_lvl1_name = filter_categories_by_parent(
            get_categories_lvl1_name(index_name, cat_lvl0_full), cat_lvl0_full
        )
        category_lvl1 = st.selectbox(
            "Catégorie niveau 1",
            [clean_category_name(c) for c in category_lvl1_name],
        )
    else:
        category_lvl1, category_lvl1_name = None, []

    # --- Catégorie niveau 2 ---
    if category_lvl1:
        cat_lvl1_full = get_full_category_path(category_lvl1, category_lvl1_name)
        category_lvl2_name = filter_categories_by_parent(
            get_categories_lvl2_name(index_name, cat_lvl1_full), cat_lvl1_full
        )
        category_lvl2 = st.selectbox(
            "Catégorie niveau 2",
            [clean_category_name(c) for c in category_lvl2_name],
        )
    else:
        category_lvl2, category_lvl2_name = None, []

    # --- Recherche directe par ID ---
    product_id = st.text_input("ID du produit", placeholder="Entrez l'ID du produit…")

    if st.button("Lancer la recherche"):
        if product_id:
            st.session_state.products = get_product_by_id(index_name, product_id)
        elif category_lvl2:
            cat_lvl2_full = get_full_category_path(category_lvl2, category_lvl2_name)
            st.session_state.products = get_products_by_category_lvl2(index_name, cat_lvl2_full)
        else:
            st.warning("Veuillez sélectionner une catégorie ou entrer un ID de produit")
            st.session_state.products = None

    # --- Import Excel/CSV de produits (affecte excel_products_df dans la session) ---
    st.markdown("---")
    st.subheader("Importer un fichier Excel ou CSV de produits")
    excel_file_import = st.file_uploader(
        "Importer un fichier (xlsx, xls ou csv)",
        type=["xlsx", "xls", "csv"],
        key="excel_import_produits",
    )
    if excel_file_import is not None:
        try:
            if excel_file_import.name.lower().endswith(".csv"):
                df_excel = pd.read_csv(excel_file_import)
            else:
                df_excel = pd.read_excel(excel_file_import)
            st.session_state.excel_products_df = df_excel
            st.success(f"{len(df_excel)} ligne(s) importée(s).")
        except Exception as e:
            st.error(f"Erreur lors de la lecture du fichier : {e}")

# -------------------------------------------------
# Colonnes principales (produits & IA)
# -------------------------------------------------

col_prod, col_ia = st.columns([2, 1])

# --------- Colonne de gauche : aperçu produits ---------

with col_prod:
    st.header("Détails du produit")

    def show_product_card(prod):
        d = prod.model_dump() if hasattr(prod, "model_dump") else prod
        col1, col2 = st.columns([2, 1])
        with col1:
            st.markdown(f"**object_id :** {d.get('object_id', 'N/A')}")
            st.markdown(f"**name :** {d.get('name', 'N/A')}")
            if d.get("shortDescription"):
                st.markdown(f"**shortDescription :** {d.get('shortDescription')}")
        with col2:
            img_url = d.get("ProductImageLink")
            if isinstance(img_url, list):
                img_url = img_url[0]
            elif isinstance(img_url, dict):
                img_url = next(iter(img_url.values()), None)
            if img_url and isinstance(img_url, str) and img_url.startswith("http"):
                st.image(img_url, width=150)
            else:
                st.write("Image non disponible")
        st.divider()

    # Aperçu des produits importés via Excel (si présent)
    if hasattr(st.session_state, "excel_products_df"):
        st.subheader("Produits importés depuis Excel")
        df_excel = st.session_state.excel_products_df
        for idx, row in df_excel.iterrows():
            champs = list(row.index)
            st.markdown(f"**Produit {idx + 1}**")
            for ch in champs[:3]:
                st.write(f"{ch}: {row[ch]}")
            st.divider()

    # Produits issus de la recherche Algolia
    if st.session_state.products is not None:
        if isinstance(st.session_state.products, list):
            st.subheader(f"{len(st.session_state.products)} produit(s) trouvé(s)")
            for p in st.session_state.products:
                show_product_card(p)
        else:
            show_product_card(st.session_state.products)
    elif not hasattr(st.session_state, "excel_products_df"):
        st.info("Aucun produit sélectionné ou importé.")

# --------- Colonne de droite : assistant IA ---------

with col_ia:
    st.header("Assistant Enrichissement")

    # 1️⃣ Formulaire de création d'un champ ---------------------------------

    with st.expander("Ajouter un champ", expanded=False):
        with st.form("creation_champ"):
            new_field = st.text_input("Nouveau champ", placeholder="Nom du champ…")
            default_value = st.text_input("Valeur par défaut", placeholder="Valeur initiale…")
            create_click = st.form_submit_button("Créer le champ")

        if create_click:
            # --- Cas 1 : Excel importé -------------------------------------
            if new_field and hasattr(st.session_state, "excel_products_df"):
                df_excel = st.session_state.excel_products_df
                if new_field not in df_excel.columns:
                    df_excel[new_field] = default_value
                    # On stocke le DataFrame enrichi dans une variable de session dédiée
                    st.session_state.excel_products_df_enriched = df_excel.copy()
                    st.session_state.excel_products_df = df_excel

                    # Export pour téléchargement
                    tmp_output = io.BytesIO()
                    df_excel.to_excel(tmp_output, index=False, engine="xlsxwriter")
                    tmp_output.seek(0)

                    st.success(f"✅ Le champ '{new_field}' a été ajouté au fichier importé.")
                    st.session_state.tmp_excel_enrichi = tmp_output
                else:
                    st.warning(f"⚠️ Le champ '{new_field}' existe déjà dans le fichier importé.")

            # --- Cas 2 : produits Algolia présents ------------------------
            elif new_field and st.session_state.products is not None:
                status = st.empty()
                status.info("Ajout du champ en cours…")

                try:
                    prods_to_update = (
                        [{"objectID": extract_object_id(p)} for p in st.session_state.products]
                        if isinstance(st.session_state.products, list)
                        else [{"objectID": extract_object_id(st.session_state.products)}]
                    )

                    updated_count = post_new_field_to_products(
                        index_name=index_name,
                        products=prods_to_update,
                        new_field=new_field,
                        default_value=default_value,
                    )

                    if updated_count > 0:
                        st.session_state.custom_fields.add(new_field)
                        status.success(
                            f"✅ Champ '{new_field}' ajouté à {updated_count} produit(s) avec la valeur '{default_value}'."
                        )
                    else:
                        status.warning("⚠️ Aucun produit n'a été mis à jour.")
                except Exception as exc:
                    status.error(f"Erreur : {exc}")
            else:
                st.warning(
                    "Veuillez renseigner un nom de champ et sélectionner/charger des produits avant de créer le champ."
                )

    # 2️⃣ Formulaire d'enrichissement --------------------------------------

    with st.form("form_enrichissement"):
        # --- Détermination des champs disponibles ------------------------
        # Utiliser le DataFrame enrichi s'il existe, sinon celui de base
        if hasattr(st.session_state, "excel_products_df_enriched"):
            all_fields = list(st.session_state.excel_products_df_enriched.columns)
        elif hasattr(st.session_state, "excel_products_df"):
            all_fields = list(st.session_state.excel_products_df.columns)
        else:
            available_fields = get_algolia_fields(index_name) if index_name else []
            all_fields = sorted(set(available_fields + list(st.session_state.custom_fields)))

        target_field = st.selectbox("Champ à enrichir", options=all_fields)

        instructions_lvl0 = st.selectbox(
            "Instruction catégorie 0",
            options=get_nom_instructions_categories_lvl0(),
        )

        # Index de destination (uniquement si pas d'Excel importé)
        if not hasattr(st.session_state, "excel_products_df"):
            target_index = st.selectbox("Index de destination", options=get_algolia_indexes_name())
        else:
            target_index = index_name  # pas utilisé mais requis dans l'appel de l'agent

        # 📂 Uploader Excel spécifique à l'enrichissement (placé DANS le form)
        excel_file = st.file_uploader(
            "Fichier Excel pour enrichissement (optionnel)",
            type=["xlsx", "xls", "csv"],
            key="excel_for_enrichissement",
            help="Permet d'enrichir directement un fichier sans passer par l'index",
        )

        st.markdown("**Prompt**")
        source_fields = st.text_area("Prompt", "")

        envoyer = st.form_submit_button("Enrichir")

        # ------------------ Traitement de l'enrichissement --------------
        if envoyer and target_field and source_fields:
            # On supprime l'ancien buffer de téléchargement avant de lancer l'enrichissement
            if hasattr(st.session_state, "tmp_excel_enrichi"):
                del st.session_state.tmp_excel_enrichi

            # Récupération des instructions système & juge
            instruction_systeme = get_instruction_by_nom(instructions_lvl0)
            instruction_juge = get_instruction_juge_by_nom(instructions_lvl0)

            # Récupération des produits à enrichir
            if hasattr(st.session_state, "excel_products_df_enriched"):
                df_excel = st.session_state.excel_products_df_enriched
            elif hasattr(st.session_state, "excel_products_df"):
                df_excel = st.session_state.excel_products_df
            else:
                df_excel = None
            if isinstance(st.session_state.products, list):
                produits = st.session_state.products
            elif st.session_state.products is not None:
                produits = [st.session_state.products]
            else:
                produits = []

            # Client OpenAI
            openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

            # Appel de l'agent (mode Algolia ou Excel)
            try:
                if excel_file is not None:
                    # Enrichissement direct d'un fichier Excel/CSV -------------------
                    try:
                        if excel_file.name.lower().endswith(".csv"):
                            df_uploaded = pd.read_csv(excel_file)
                        else:
                            df_uploaded = pd.read_excel(excel_file)
                        produits_excel = df_uploaded.to_dict(orient="records")
                        nb = len(produits_excel)
                        produits_enrichis = enrichir_champ_batch_excel(
                            produits=produits_excel,
                            champ_cible=target_field,
                            prompt_user=source_fields,
                            openai_client=openai_client,
                            system_instruction=instruction_systeme,
                            judge_instruction=instruction_juge,
                        )
                        st.success(f"{nb} ligne(s) enrichie(s) dans le fichier ⚡️")
                        # Générer le fichier Excel enrichi et bouton de téléchargement
                        df_enrichi = pd.DataFrame(produits_enrichis)
                        tmp_output = io.BytesIO()
                        df_enrichi.to_excel(tmp_output, index=False, engine="xlsxwriter")
                        tmp_output.seek(0)
                        st.session_state.tmp_excel_enrichi = tmp_output
                    except Exception as exc:
                        st.error(f"Erreur lors de la lecture du fichier : {exc}")
                elif df_excel is not None:
                    # Enrichissement du DataFrame Excel enrichi ou de base ----------
                    produits_excel = df_excel.to_dict(orient="records")
                    nb = len(produits_excel)
                    produits_enrichis = enrichir_champ_batch_excel(
                        produits=produits_excel,
                        champ_cible=target_field,
                        prompt_user=source_fields,
                        openai_client=openai_client,
                        system_instruction=instruction_systeme,
                        judge_instruction=instruction_juge,
                        excel_file=excel_file
                    )
                    st.success(f"{nb} ligne(s) enrichie(s) dans le fichier ⚡️")
                    # Générer le fichier Excel enrichi et bouton de téléchargement
                    df_enrichi = pd.DataFrame(produits_enrichis)
                    tmp_output = io.BytesIO()
                    df_enrichi.to_excel(tmp_output, index=False, engine="xlsxwriter")
                    tmp_output.seek(0)
                    st.session_state.tmp_excel_enrichi = tmp_output
                else:
                    # Enrichissement des produits Algolia ----------------------------
                    nb = enrichir_champ_batch(
                        index_name=target_index,
                        produits=produits,
                        champ_cible=target_field,
                        prompt_user=source_fields,
                        openai_client=openai_client,
                        system_instruction=instruction_systeme,
                        judge_instruction=instruction_juge,
                        excel_file=excel_file
                    )
                    st.success(f"{nb} produit(s) enrichi(s) avec succès !")
            except Exception as exc:
                st.error(f"Erreur durant l'enrichissement : {exc}")

    # Affichage du bouton de téléchargement juste sous le formulaire d'enrichissement
    if hasattr(st.session_state, "tmp_excel_enrichi"):
        st.download_button(
            "Télécharger le fichier enrichi",
            data=st.session_state.tmp_excel_enrichi,
            file_name="produits_enrichis.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
