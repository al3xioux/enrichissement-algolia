import streamlit as st
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.GET.main import get_algolia_indexes_name, get_categories_lvl0_name, get_categories_lvl1_name, get_categories_lvl2_name, get_product_by_id, get_products_by_category_lvl2, get_algolia_fields
from backend.POST.main import post_new_field_to_products
from backend.agent.main import enrichir_champ_batch
from backend.SupaBase.main import get_nom_categories_lvl0, get_instruction_by_nom
from openai import OpenAI

# Initialisation de la session state si elle n'existe pas
if 'products' not in st.session_state:
    st.session_state.products = None

def clean_category_name(category):
    """Nettoie le nom de la catégorie pour n'afficher que le dernier niveau"""
    if not category:
        return None
    parts = category.split(' > ')
    return parts[-1] if len(parts) > 1 else category

def get_full_category_path(category_name, all_categories):
    """Trouve le chemin complet d'une catégorie"""
    return next((cat for cat in all_categories if clean_category_name(cat) == category_name), None)

def filter_categories_by_parent(categories, parent_category):
    """Filtre les catégories pour ne garder que celles qui appartiennent à la catégorie parente"""
    if not parent_category:
        return []
    return [cat for cat in categories if cat.startswith(parent_category)]




# Configuration de la page
st.set_page_config(
    page_title="Enrichissement Algolia",
    layout="wide"
)
# Titre de l'application
st.title("🔄 Enrichissement Algolia")
# Configuration du style pour une meilleure présentation
st.markdown("""
    <style>
        .block-container {
            padding-right: 2rem;
        }
        .stButton>button {
            width: 100%;
        }
        .product-card {
            border: 1px solid #e0e0e0;
            border-radius: 10px;
            padding: 15px;
            margin-bottom: 15px;
            background-color: white;
        }
        .product-card:hover {
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        }
    </style>
""", unsafe_allow_html=True)



# Sidebar
with st.sidebar:
    st.header("Recherche de produit")

    indexes_name = get_algolia_indexes_name()
    index_name = st.selectbox(
        "Index Algolia",
        indexes_name,
        help="Sélectionnez l'index Algolia à enrichir"
    )

    # Catégories niveau 0
    category_lvl0_name = get_categories_lvl0_name(index_name)
    category_lvl0_clean = [clean_category_name(cat) for cat in category_lvl0_name]
    category_lvl0 = st.selectbox(
        "Catégorie niveau 0",
        category_lvl0_clean,
        help="Sélectionnez une catégorie d'enrichissement"
    )

    # Catégories niveau 1
    if category_lvl0:
        # Trouver la catégorie complète correspondante
        category_lvl0_full = get_full_category_path(category_lvl0, category_lvl0_name)
        category_lvl1_name = get_categories_lvl1_name(index_name, category_lvl0_full)
        # Filtrer les catégories niveau 1 pour ne garder que celles qui appartiennent à la catégorie niveau 0
        category_lvl1_name = filter_categories_by_parent(category_lvl1_name, category_lvl0_full)
        category_lvl1_clean = [clean_category_name(cat) for cat in category_lvl1_name]
        category_lvl1 = st.selectbox(
            "Catégorie niveau 1",
            category_lvl1_clean,
            help="Sélectionnez une sous-catégorie d'enrichissement"
        )
    else:
        category_lvl1 = None
        category_lvl1_name = []

    # Catégories niveau 2
    if category_lvl1:
        # Trouver la catégorie complète correspondante
        category_lvl1_full = get_full_category_path(category_lvl1, category_lvl1_name)
        category_lvl2_name = get_categories_lvl2_name(index_name, category_lvl1_full)
        # Filtrer les catégories niveau 2 pour ne garder que celles qui appartiennent à la catégorie niveau 1
        category_lvl2_name = filter_categories_by_parent(category_lvl2_name, category_lvl1_full)
        category_lvl2_clean = [clean_category_name(cat) for cat in category_lvl2_name]
        category_lvl2 = st.selectbox(
            "Catégorie niveau 2",
            category_lvl2_clean,
            help="Sélectionnez une sous-catégorie d'enrichissement"
        )
    else:
        category_lvl2 = None
        category_lvl2_name = []

    product_id = st.text_input(
        "ID du produit",
        placeholder="Entrez l'ID du produit...",
        help="Entrez l'identifiant unique du produit à rechercher"
    )

    if st.button("Lancer la recherche"):
        if product_id:
            st.session_state.products = get_product_by_id(index_name, product_id)
        elif category_lvl2:
            category_lvl2_full = get_full_category_path(category_lvl2, category_lvl2_name)
            st.session_state.products = get_products_by_category_lvl2(index_name, category_lvl2_full)
        else:
            st.warning("Veuillez sélectionner une catégorie ou entrer un ID de produit")
            st.session_state.products = None

# Colonnes principales
col_produit, col_ia = st.columns([2, 1])

with col_produit:
    st.header("Détails du produit")
    
    def show_product_card(prod):
        col1, col2 = st.columns([2, 1])
        with col1:
            st.markdown(f"**ID :** {prod.get('objectID', 'Non disponible')}")
            st.markdown(f"**Nom :** {prod.get('name', 'Non disponible')}")
            if prod.get('shortDescription'):
                st.markdown(f"**Description courte :** {prod.get('shortDescription')}")
        with col2:
            image_url = prod.get('ProductImageLink')
            if image_url:
                if isinstance(image_url, list):
                    image_url = image_url[0]
                elif isinstance(image_url, dict):
                    image_url = next(iter(image_url.values()), None)
                
                if image_url and isinstance(image_url, str) and image_url.startswith('http'):
                    st.image(image_url, width=150)
                else:
                    st.write("Image non disponible")
            else:
                st.write("Image non disponible")
        st.divider()

    if st.session_state.products is not None:
        if isinstance(st.session_state.products, list):
            st.subheader(f"{len(st.session_state.products)} produit(s) trouvé(s)")
            for prod in st.session_state.products:
                show_product_card(prod)
        else:
            show_product_card(st.session_state.products)
    else:
        st.info("Aucun produit sélectionné. Veuillez rechercher un produit par son ID ou sélectionner une catégorie.")

with col_ia:
    st.header("Assistant Enrichissement")
    
    with st.form("creation_champ"):
        new_field = st.text_input(
            "Nouveau champ",
            placeholder="Entrez le nom du champ...",
            help="Nom du champ à créer pour l'enrichissement"
        )
        default_value = st.text_input(
            "Valeur par défaut",
            placeholder="Valeur initiale du champ...",
            help="Valeur par défaut pour le nouveau champ"
        )
        submitted_field = st.form_submit_button("Créer le champ")

        if submitted_field:
            if new_field and st.session_state.products is not None:
                status_container = st.empty()
                status_container.info("Traitement des produits en cours...")

                try:
                    # Préparation des produits pour l'API
                    products_to_update = []
                    if isinstance(st.session_state.products, list):
                        products_to_update = [{"objectID": prod.get('objectID')} for prod in st.session_state.products]
                    else:
                        products_to_update = [{"objectID": st.session_state.products.get('objectID')}]

                    # Appel de la version batch
                    updated_count = post_new_field_to_products(
                        index_name, 
                        products_to_update, 
                        new_field, 
                        default_value
                    )

                    if updated_count > 0:
                        # Ajout du champ custom à la session pour la solution hybride
                        if 'custom_fields' not in st.session_state:
                            st.session_state.custom_fields = set()
                        st.session_state.custom_fields.add(new_field)
                        status_container.success(f"✅ Le champ '{new_field}' a été ajouté à {updated_count} produit(s) avec la valeur : '{default_value}'")
                    else:
                        status_container.warning("⚠️ Aucun produit n'a été mis à jour.")
                except Exception as e:
                    st.error(f"Erreur lors de la mise à jour : {str(e)}")
            else:
                st.warning("⚠️ Veuillez remplir tous les champs et sélectionner des produits avant de créer un nouveau champ.")
    
    with st.form("form_enrichissement"):
        # Récupérer les champs disponibles pour l'index sélectionné
        available_fields = get_algolia_fields(index_name) if index_name else []
        # Fusionner avec les champs custom créés pendant la session
        custom_fields = list(st.session_state.get('custom_fields', set()))
        all_fields = sorted(set(available_fields + custom_fields))
        
        target_field = st.selectbox(
            "Champ à enrichir",
            options=all_fields,
            help="Sélectionnez le champ à enrichir"
        )

        instructions_lvl0 = st.selectbox(
            "Instruction catégorie 0",
            options= get_nom_categories_lvl0(),
            help="Sélectionnez l'instruction à utiliser"
        )
        source_fields = st.text_area(
            "Prompt",
            placeholder="@nom, @longDescription",
            help="Prompt + champs sources"
        )
        envoyer = st.form_submit_button("Enrichir")
        
        if envoyer and target_field and source_fields:
            # Récupérer l'instruction système liée à la catégorie sélectionnée
            instruction_systeme = get_instruction_by_nom(instructions_lvl0)  # 'instruction' est la catégorie sélectionnée
            # Récupération des produits à enrichir
            if isinstance(st.session_state.products, list):
                produits = st.session_state.products
            else:
                produits = [st.session_state.products]
            # Initialisation du client OpenAI
            openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            # Appel de l'agent avec l'instruction système
            nb = enrichir_champ_batch(
                index_name=index_name,
                produits=produits,
                champ_cible=target_field,
                prompt_user=source_fields,
                openai_client=openai_client,
                system_instruction=instruction_systeme
            )
            st.success(f"{nb} produit(s) enrichi(s) avec succès !")
