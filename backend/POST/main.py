import sys
import os
from dotenv import load_dotenv
import json
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
    body = {
        "objectID": object_id,
        attribute_name: value
    }
    response = client.partial_update_object(index_name, body, {'createIfNotExists': True})
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
        dict: Réponse Algolia nettoyée si la mise à jour a réussi, None sinon.
    """

    try:
        client = get_algolia_client()
        response = client.partial_update_object(
            index_name=index_name,
            object_id=product_id,
            attributes_to_update={
                field_name: new_value,
            },
            create_if_not_exists=True
        )
        # Attendre la fin de la tâche si possible
        task_id = response.get('taskID') if isinstance(response, dict) else None
        if task_id:
            client.wait_for_task(index_name, task_id)
        # Nettoyage de la réponse pour éviter les problèmes de sérialisation
        return json.loads(json.dumps(response))
    except Exception as e:
        print(f"Erreur lors de la mise à jour du produit : {str(e)}")
        return None

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
    if not products:
        return 0

    updates = []
    for product in products:
        updates.append({
            'objectID': product['objectID'],
            field_name: default_value
        })
    print(f"[DEBUG] Updates envoyés à Algolia : {updates}")
    try:
        response = client.partial_update_objects(index_name, updates, {'createIfNotExists': True})
        # En v4, il faut utiliser wait_for_task
        if hasattr(response, 'task_id'):
            client.wait_for_task(index_name, response.task_id)
        return len(updates)
    except Exception as e:
        print(f"Erreur lors de la mise à jour batch : {e}")
        return 0


""" post_new_field_to_products("prod_raja_fr_ai_assistant_emballage_product_algolia_fr", [{"objectID": "OFF_FR_491"},{"objectID": "LOCGYR60"}], "test", "test") """