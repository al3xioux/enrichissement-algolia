import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
import os
from openai import OpenAI
from typing import Dict, Any
import json
from backend.POST.main import post_new_value_for_product
import re

def enrichir_champ_batch(index_name, produits, champ_cible, prompt_user, openai_client, model="gpt-4o-mini", system_instruction=None, judge_instruction=None, excel_file=None):
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
        judge_instruction (str, optionnel): Prompt système pour le juge. Si None, on utilise le prompt juge par défaut.
        excel_file (str, optionnel): Fichier Excel à utiliser pour l'enrichissement.
    Returns:
        int: Nombre de produits enrichis.
    """
    nb_success = 0
    # Détection des champs sources dans le prompt utilisateur (tous les @champs)
    champs_sources = set(re.findall(r"@([a-zA-Z0-9_]+)", prompt_user))
    champs_sources_str = ', '.join(champs_sources)
    if system_instruction is not None:
        prompt_systeme = system_instruction.format(
            champ_a_enrichir=champ_cible,
            champs_sources=champs_sources_str,
            post_new_value_for_product="post_new_value_for_product",
            excel_file=excel_file
        )
    else:
        prompt_systeme = f"Tu es un assistant d'enrichissement de données produit. Tu dois générer une valeur pertinente pour le champ '{champ_cible}' à partir des champs sources : {champs_sources_str}. Un excel peut être donner pour aider à la génération de la valeur."
    for produit in produits:
        prod_dict = produit.model_dump() if hasattr(produit, 'model_dump') else produit
        prompt = prompt_user
        for champ in champs_sources:
            valeur = str(prod_dict.get(champ, ""))
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
            print(f"Erreur OpenAI pour le produit {prod_dict.get('objectID', prod_dict.get('object_id', ''))}: {e}")
            valeur_enrichie = ""
        # Jugement de la valeur enrichie
        try:
            prompt_jugement = (
                f"Voici un produit : {json.dumps(prod_dict, ensure_ascii=False)}.\n"
                f"Le champ à enrichir est : '{champ_cible}'.\n"
                f"Le prompt utilisateur était : '{prompt_user}'.\n"
                f"La valeur générée est : '{valeur_enrichie}'.\n"
                "En tant qu'expert, si la valeur générée est cohérente, pertinente et utile pour ce champ, réponds uniquement par «OK». Sinon, réécris la valeur de façon correcte et pertinente pour ce champ."
            )
            if judge_instruction is not None:
                prompt_systeme_juge = judge_instruction
            else:
                prompt_systeme_juge = "Tu es un expert en data quality et enrichissement de données produit."
            response_jugement = openai_client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": prompt_systeme_juge},
                    {"role": "user", "content": prompt_jugement}
                ]
            )
            jugement = response_jugement.choices[0].message.content.strip()
            print(f"[DEBUG JUGEMENT] Prompt envoyé :\n{prompt_jugement}\nRéponse du juge : {jugement}")
            if jugement.strip().upper() == "OK":
                valeur_finale = valeur_enrichie
            else:
                valeur_finale = jugement
        except Exception as e:
            print(f"Erreur lors du jugement de la valeur enrichie : {e}")
            valeur_finale = valeur_enrichie
        success = post_new_value_for_product(index_name, prod_dict.get("objectID", prod_dict.get("object_id", "")), champ_cible, valeur_finale)
        if success:
            nb_success += 1
    return nb_success



""" # Exemple de produits (à adapter avec tes vrais produits)
produits = [
    {"objectID": "2702RET", "name": "Chariot de rétention porte-fût 45/54 litres 113x61,1x99 cm", "shortDescription": " Pour le déplacement de 2 fûts de 200 litres. Conforme à la norme EN 1757-3. Maniable : équipé de 4 roues Ø 12,5 cm, dont 2 pivotantes avec frein. Bac étanche. Caillebotis, grille de 31 x 31 mm. En acier finition époxy bleu. "},
    {"objectID": "CHARETG2F", "name": "Chariot de rétention 220 litres", "shortDescription": " Pour le stockage et le déplacement en position verticale de fûts contenant des liquides toxiques ou polluants. Caillebotis amovible. Conforme à la norme EN 1757-3. Maniable : équipé de 4 roues en caoutchouc dont 2 pivotantes avec frein. En acier galvanisé. "}
]


openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

print(enrichir_champ_batch(
    index_name="prod_raja_fr_ai_assistant_emballage_product_algolia_fr",
    produits=produits,
    champ_cible="motcle2",
    prompt_user="Génère une liste de 3 mots clés à partir de @name et de @shortDescription.",
    openai_client=openai_client
)) """