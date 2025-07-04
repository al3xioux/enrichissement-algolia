"""Fonctions de lecture et d'écriture des instructions stockées dans Supabase."""

import os
import sys
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()



url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)


def get_all_instructions_categories_lvl0():
    """Récupère toutes les colonnes de la table des instructions niveau 0."""

    response = supabase.table('Instruction_categories_lvl0').select('*').execute()
    return response.data

def get_instructions_categories_lvl0():
    """Liste uniquement la colonne "Instruction" de la table."""

    response = supabase.table('Instruction_categories_lvl0').select('Instruction').execute()
    return [item['Instruction'] for item in response.data if 'Instruction' in item]

def get_nom_instructions_categories_lvl0():
    """Récupère la liste des noms d'instructions niveau 0."""

    response = supabase.table('Instruction_categories_lvl0').select('Nom').execute()
    return [item['Nom'] for item in response.data if 'Nom' in item]

def get_instruction_by_nom(nom):
    """Retourne l'instruction associée à un nom de catégorie."""

    response = supabase.table('Instruction_categories_lvl0').select('Instruction').eq('Nom', nom).execute()
    if response.data and 'Instruction' in response.data[0]:
        return response.data[0]['Instruction']
    return None

def get_instructions_juge_categories_lvl0():
    """Liste la colonne "Instruction_juge" de la table."""

    response = supabase.table('Instruction_categories_lvl0').select('Instruction_juge').execute()
    return [item['Instruction_juge'] for item in response.data if 'Instruction_juge' in item]

def get_instruction_juge_by_nom(nom):
    """Récupère l'instruction juge à partir du nom de catégorie."""

    response = supabase.table('Instruction_categories_lvl0').select('Instruction_juge').eq('Nom', nom).execute()
    if response.data and 'Instruction_juge' in response.data[0]:
        return response.data[0]['Instruction_juge']
    return None

def update_instruction_category_lvl0(nom_original, nouveau_nom=None, nouvelle_instruction=None, nouvelle_instruction_juge=None):
    """Met à jour une instruction existante identifiée par son nom."""

    update_data = {}
    if nouveau_nom is not None:
        update_data['Nom'] = nouveau_nom
    if nouvelle_instruction is not None:
        update_data['Instruction'] = nouvelle_instruction
    if nouvelle_instruction_juge is not None:
        update_data['Instruction_juge'] = nouvelle_instruction_juge
    if not update_data:
        return None  # Rien à mettre à jour
    response = supabase.table('Instruction_categories_lvl0').update(update_data).eq('Nom', nom_original).execute()
    return response.data

def post_instruction_category_lvl0(nom, instruction, instruction_juge):
    """Insère une nouvelle instruction niveau 0 dans la base."""

    response = supabase.table('Instruction_categories_lvl0').insert({'Nom': nom, 'Instruction': instruction, 'Instruction_juge': instruction_juge}).execute()
    return response.data
