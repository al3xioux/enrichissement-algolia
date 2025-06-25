from algoliasearch.search_client import SearchClient
import os
from dotenv import load_dotenv

load_dotenv()

def get_algolia_client():
    app_id = os.getenv("ALGOLIA_APP_ID")
    api_key = os.getenv("ALGOLIA_API_KEY")

    return SearchClient.create(app_id, api_key)


def get_algolia_indexes_name():
    client = get_algolia_client()
    response = client.list_indices()
    items = response.get("items", [])
    return [item.get("name") for item in items]


def get_categories_lvl0_name(index_name):
    client = get_algolia_client()
    index = client.init_index(index_name)

    results = index.search('', {
        'facets': ['categories.lvl0'],
        'maxValuesPerFacet': 100
    })

    categories_lvl0 = results.get('facets', {}).get('categories.lvl0', {})
    return list(categories_lvl0.keys())


def get_categories_lvl1_name(index_name, category_lvl0):
    client = get_algolia_client()
    index = client.init_index(index_name)
    
    # Nettoyage et échappement de la catégorie
    category_lvl0 = category_lvl0.strip()
    escaped_category = category_lvl0.replace('"', '\\"')

    results = index.search('', {
        'facets': ['categories.lvl1'],
        'filters': f'categories.lvl0:"{escaped_category}"',
        'maxValuesPerFacet': 100
    })

    categories_lvl1 = results.get('facets', {}).get('categories.lvl1', {})
    return list(categories_lvl1.keys())


def get_categories_lvl2_name(index_name, category_lvl1):
    client = get_algolia_client()
    index = client.init_index(index_name)
    
    # Nettoyage et échappement de la catégorie
    category_lvl1 = category_lvl1.strip()
    escaped_category = category_lvl1.replace('"', '\\"')

    results = index.search('', {
        'facets': ['categories.lvl2'],
        'filters': f'categories.lvl1:"{escaped_category}"',
        'maxValuesPerFacet': 100
    })

    categories_lvl2 = results.get('facets', {}).get('categories.lvl2', {})
    return list(categories_lvl2.keys())


def get_product_by_id(index_name, product_id):
    client = get_algolia_client()
    index = client.init_index(index_name)

    results = index.search('', {
            'filters': f'objectID:{product_id}',
            'attributesToRetrieve': ['name', 'objectID', 'MotsCles', 'shortDescription', 'longDescription', 'ProductImageLink']
        })
    return results.get('hits', [])[0]

def get_products_by_category_lvl1(index_name, category_lvl1):
    client = get_algolia_client()
    index = client.init_index(index_name)
    results = index.search('', {
        'filters': f'categories.lvl1:"{category_lvl1}"',
        'hitsPerPage': 100,
        'attributesToRetrieve': ['name', 'objectID', 'MotsCles', 'shortDescription', 'longDescription', 'ProductImageLink']
    })
    return results.get('hits', [])

def get_products_by_category_lvl2(index_name, category_lvl2):
    client = get_algolia_client()
    index = client.init_index(index_name)
    results = index.search('', {
        'filters': f'categories.lvl2:"{category_lvl2}"',
        'hitsPerPage': 100,
        'attributesToRetrieve': ['name', 'objectID', 'MotsCles', 'shortDescription', 'longDescription', 'ProductImageLink']
    })
    return results.get('hits', [])

def get_algolia_fields(index_name):
    """
    Récupère tous les champs disponibles dans un index Algolia en parcourant plusieurs produits.
    Args:
        index_name (str): Nom de l'index Algolia.
    Returns:
        list: Liste des noms de champs disponibles.
    """
    client = get_algolia_client()
    index = client.init_index(index_name)
    # Récupérer un échantillon de produits pour extraire les champs
    results = index.search('', {
        'hitsPerPage': 20,  # Prend les 20 premiers produits
        'attributesToRetrieve': ['*']
    })
    champs = set()
    for prod in results.get('hits', []):
        champs.update(prod.keys())
    return list(champs)