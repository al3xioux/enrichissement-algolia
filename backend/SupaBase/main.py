import os
import sys
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()



url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)


def get_all_categories_lvl0():
    response = supabase.table('Instruction categories lvl0').select('*').execute()
    return response.data

def get_instruction_categories_lvl0():
    response = supabase.table('Instruction categories lvl0').select('instruction').execute()
    return [item['instruction'] for item in response.data if 'instruction' in item]

def get_nom_categories_lvl0():
    response = supabase.table('Instruction categories lvl0').select('Nom').execute()
    return [item['Nom'] for item in response.data if 'Nom' in item]

def get_instruction_by_nom(nom):
    response = supabase.table('Instruction categories lvl0').select('instruction').eq('Nom', nom).execute()
    if response.data and 'instruction' in response.data[0]:
        return response.data[0]['instruction']
    return None

def update_instruction_category_lvl0(nom_original, nouveau_nom=None, nouvelle_instruction=None):
    update_data = {}
    if nouveau_nom is not None:
        update_data['Nom'] = nouveau_nom
    if nouvelle_instruction is not None:
        update_data['instruction'] = nouvelle_instruction
    if not update_data:
        return None  # Rien à mettre à jour
    response = supabase.table('Instruction categories lvl0').update(update_data).eq('Nom', nom_original).execute()
    return response.data

