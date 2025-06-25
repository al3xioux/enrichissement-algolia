import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
import os
from openai import OpenAI
from typing import Dict, Any
import json
from backend.POST.main import post_new_value_for_product
import re

def enrichir_champ_batch(index_name, produits, champ_cible, prompt_user, openai_client, model="gpt-4o-mini", system_instruction=None):
    """
    Enrichit un champ pour une liste de produits en utilisant un prompt utilisateur libre et l'API OpenAI.
    Args:
        index_name (str): Nom de l'index Algolia.
        produits (list): Liste de produits (dicts avec objectID et champs).
        champ_cible (str): Champ à enrichir.
        prompt_user (str): Prompt utilisateur avec des @champs.
        openai_client (OpenAI): Client OpenAI déjà configuré.
        model (str): Modèle OpenAI à utiliser.
        system_instruction (str, optionnel): Prompt système à utiliser. Si None, on utilise le prompt par défaut.
    Returns:
        int: Nombre de produits enrichis.
    """
    nb_success = 0
    # Détection des champs sources dans le prompt utilisateur (tous les @champs)
    champs_sources = set(re.findall(r"@([a-zA-Z0-9_]+)", prompt_user))
    champs_sources_str = ', '.join(champs_sources)
    if system_instruction is not None:
        prompt_systeme = system_instruction
    else:
        prompt_systeme = system_instruction.format(
            champ_a_enrichir=champ_cible,
            champs_sources=champs_sources_str,
            post_new_value_for_product="post_new_value_for_product"
        )
    for produit in produits:
        prompt = prompt_user
        for champ in champs_sources:
            valeur = str(produit.get(champ, ""))
            prompt = prompt.replace(f"@{champ}", valeur)
        # Appel OpenAI avec prompt système + prompt utilisateur
        try:
            response = openai_client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": prompt_systeme},
                    {"role": "user", "content": prompt}
                ]
            )
            valeur_enrichie = response.choices[0].message.content.strip()
        except Exception as e:
            print(f"Erreur OpenAI pour le produit {produit.get('objectID')}: {e}")
            valeur_enrichie = ""
        print(f"Mise à jour {produit['objectID']} : {champ_cible} = {valeur_enrichie}")
        success = post_new_value_for_product(index_name, produit["objectID"], champ_cible, valeur_enrichie)
        print(f"Résultat Algolia : {success}")
        if success:
            nb_success += 1
    return nb_success

""" # Exemple de produits (à adapter avec tes vrais produits)
produits = [
    {"objectID": "2702RET", "name": "Chariot de rétention porte-fût 45/54 litres 113x61,1x99 cm", "shortDescription": " Pour le déplacement de 2 fûts de 200 litres. Conforme à la norme EN 1757-3. Maniable : équipé de 4 roues Ø 12,5 cm, dont 2 pivotantes avec frein. Bac étanche. Caillebotis, grille de 31 x 31 mm. En acier finition époxy bleu. "},
    {"objectID": "CHARETG2F", "name": "Chariot de rétention 220 litres", "shortDescription": " Pour le stockage et le déplacement en position verticale de fûts contenant des liquides toxiques ou polluants. Caillebotis amovible. Conforme à la norme EN 1757-3. Maniable : équipé de 4 roues en caoutchouc dont 2 pivotantes avec frein. En acier galvanisé. "}
]

champ_cible = "motcle2"
prompt_user = "Génère une liste de 3 mots clés à partir du nom (@name) et de la description courte (@shortDescription)."

openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

nb = enrichir_champ_batch(
    index_name="prod_raja_fr_ai_assistant_emballage_product_algolia_fr",
    produits=produits,
    champ_cible=champ_cible,
    prompt_user=prompt_user,
    openai_client=openai_client
)

print(f"{nb} produits enrichis !") """