import sys
import os
from dotenv import load_dotenv
from algoliasearch.exceptions import AlgoliaException
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

load_dotenv()

from GET.main import get_algolia_client


def post_new_attribute_for_product(index_name, object_id, attribute_name, value):
    """
    Ajoute un attribut à un produit en une seule requête sur Algolia.

    Args:
        index_name (str): Nom de l'index Algolia.
        object_id (str): ID du produit à mettre à jour.
        attribute_name (str): Nom de l'attribut à ajouter.
        value (str): Valeur de l'attribut à ajouter.

    Returns:
        bool: True si la mise à jour a réussi, False sinon.
    """

    client = get_algolia_client()
    index = client.init_index(index_name)

    response = index.partial_update_object({
        "objectID": object_id,
        attribute_name: value
    })
    return True

def post_new_value_for_product(index_name, product_id, field_name, new_value):
    """
    Ajoute une valeur à un champ d'un produit en une seule requête sur Algolia.

    Args:
        index_name (str): Nom de l'index Algolia.
        product_id (str): ID du produit à mettre à jour.
        field_name (str): Nom du champ à mettre à jour.
        new_value (str): Nouvelle valeur à ajouter.

    Returns:
        bool: True si la mise à jour a réussi, False sinon.
    """

    try:
        client = get_algolia_client()
        index = client.init_index(index_name)
        
        # Mise à jour du produit
        index.partial_update_object({
            'objectID': product_id,
            field_name: new_value
        })
        
        return True
    except Exception as e:
        print(f"Erreur lors de la mise à jour du produit : {str(e)}")
        return False

def post_new_field_to_products(index_name, products, field_name, default_value=""):
    """
    Ajoute un champ à plusieurs produits en une seule requête batch sur Algolia.

    Args:
        index_name (str): Nom de l'index Algolia.
        products (list): Liste de produits (chacun avec un objectID).
        field_name (str): Nom du champ à ajouter.
        default_value (str): Valeur par défaut du champ.

    Returns:
        int: Nombre de produits mis à jour.
    """

    client = get_algolia_client()
    index = client.init_index(index_name)

    if not products:
        return 0

    updates = []
    for product in products:
        updates.append({
            'objectID': product['objectID'],
            field_name: default_value
        })

    try:
        response = index.partial_update_objects(updates, {'createIfNotExists': True})
        if isinstance(response, dict) and 'taskID' in response:
            index.wait_task(response['taskID'])
        return len(updates)
    except AlgoliaException as e:
        print(f"Erreur lors de la mise à jour batch : {e}")
        return 0


""" post_new_field_to_products("prod_raja_fr_ai_assistant_emballage_product_algolia_fr", [{"objectID": "OFF_FR_491"},{"objectID": "LOCGYR60"}], "test", "test") """