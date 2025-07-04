"""Fonctions utilitaires pour la récupération de données dans Algolia."""

from algoliasearch.search.client import SearchClientSync
import os
from dotenv import load_dotenv

load_dotenv()

def get_algolia_client():
    """Crée un client Algolia à partir des variables d'environnement."""

    app_id = os.getenv("ALGOLIA_APP_ID")
    api_key = os.getenv("ALGOLIA_API_KEY")
    return SearchClientSync(app_id, api_key)


def get_algolia_indexes_name():
    """Retourne la liste des noms d'index disponibles sur Algolia."""

    client = get_algolia_client()
    response = client.list_indices()
    items = response.items if hasattr(response, 'items') else []
    return [item.name for item in items]


def get_categories_lvl0_name(index_name):
    """Renvoie les catégories de niveau 0 pour un index donné."""

    client = get_algolia_client()
    results = client.search_single_index(index_name, {
        'query': '',
        'facets': ['categories.lvl0'],
        'maxValuesPerFacet': 100
    })
    facets = getattr(results, 'facets', {}) or {}
    categories_lvl0 = facets.get('categories.lvl0', {})
    return list(categories_lvl0.keys())


def get_categories_lvl1_name(index_name, category_lvl0):
    """Renvoie les catégories de niveau 1 pour une catégorie de niveau 0."""

    client = get_algolia_client()
    category_lvl0 = category_lvl0.strip()
    escaped_category = category_lvl0.replace('"', '\"')
    results = client.search_single_index(index_name, {
        'query': '',
        'facets': ['categories.lvl1'],
        'filters': f'categories.lvl0:"{escaped_category}"',
        'maxValuesPerFacet': 100
    })
    facets = getattr(results, 'facets', {}) or {}
    categories_lvl1 = facets.get('categories.lvl1', {})
    return list(categories_lvl1.keys())


def get_categories_lvl2_name(index_name, category_lvl1):
    """Renvoie les catégories de niveau 2 pour une catégorie de niveau 1."""

    client = get_algolia_client()
    category_lvl1 = category_lvl1.strip()
    escaped_category = category_lvl1.replace('"', '\"')
    results = client.search_single_index(index_name, {
        'query': '',
        'facets': ['categories.lvl2'],
        'filters': f'categories.lvl1:"{escaped_category}"',
        'maxValuesPerFacet': 100
    })
    facets = getattr(results, 'facets', {}) or {}
    categories_lvl2 = facets.get('categories.lvl2', {})
    return list(categories_lvl2.keys())


def get_product_by_id(index_name, product_id):
    """Récupère un produit par son identifiant."""

    client = get_algolia_client()
    results = client.search_single_index(index_name, {
        'query': '',
        'filters': f'objectID:{product_id}',
        'attributesToRetrieve': ['name', 'objectID', 'MotsCles', 'shortDescription', 'longDescription', 'ProductImageLink']
    })
    hits = getattr(results, 'hits', []) or []
    return hits[0] if hits else None

def get_products_by_category_lvl1(index_name, category_lvl1):
    """Récupère les produits associés à une catégorie de niveau 1."""

    client = get_algolia_client()
    results = client.search_single_index(index_name, {
        'query': '',
        'filters': f'categories.lvl1:"{category_lvl1}"',
        'hitsPerPage': 100,
        'attributesToRetrieve': ['name', 'objectID', 'MotsCles', 'shortDescription', 'longDescription', 'ProductImageLink']
    })
    hits = getattr(results, 'hits', []) or []
    return hits

def get_products_by_category_lvl2(index_name, category_lvl2):
    """Récupère les produits associés à une catégorie de niveau 2."""

    client = get_algolia_client()
    results = client.search_single_index(index_name, {
        'query': '',
        'filters': f'categories.lvl2:"{category_lvl2}"',
        'hitsPerPage': 100,
        'attributesToRetrieve': ['name', 'objectID', 'MotsCles', 'shortDescription', 'longDescription', 'ProductImageLink']
    })
    hits = getattr(results, 'hits', []) or []
    return hits

def get_algolia_fields(index_name):
    """
    Récupère tous les champs disponibles dans un index Algolia en parcourant plusieurs produits.
    Args:
        index_name (str): Nom de l'index Algolia.
    Returns:
        list: Liste des noms de champs disponibles.
    """
    client = get_algolia_client()
    results = client.search_single_index(index_name, {
        'query': '',
        'hitsPerPage': 20,  # Prend les 20 premiers produits
        'attributesToRetrieve': ['*']
    })
    hits = getattr(results, 'hits', []) or []
    champs = set()
    for prod in hits:
        champs.update(prod.model_dump().keys())
    return list(champs)
