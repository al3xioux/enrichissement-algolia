# Enrichissement Algolia

Ce projet propose une interface Streamlit permettant d'enrichir des produits stockés dans un index Algolia à l'aide de l'API OpenAI. Les instructions utilisées pour l'enrichissement sont centralisées dans Supabase.

## Architecture du dépôt

- **backend** : fonctions Python pour interagir avec Algolia, Supabase et l'API OpenAI
  - `GET` : récupération des données (indexes, catégories, produits...)
  - `POST` : mise à jour des produits (création de champs ou ajout de valeurs)
  - `SupaBase` : gestion des instructions stockées dans Supabase
  - `agent` : logique d'enrichissement en lot via OpenAI
- **frontend** : application Streamlit
  - `app.py` : interface principale pour rechercher des produits et lancer l'enrichissement
  - `pages/modifier_instructions.py` : page d'administration des instructions dans Supabase
- **requirements.txt** : dépendances Python nécessaires pour exécuter l'application

## Installation rapide

1. Créez un environnement virtuel Python puis installez les dépendances :
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```
2. Renseignez les variables d'environnement utilisées par l'application :
   - `ALGOLIA_APP_ID` et `ALGOLIA_API_KEY`
   - `SUPABASE_URL` et `SUPABASE_KEY`
   - `OPENAI_API_KEY`
   - `PASSWORD` (mot de passe simple pour se connecter à l'application Streamlit)

## Lancement de l'interface

Exécutez la commande suivante :
```bash
streamlit run frontend/app.py
```
Vous pourrez alors rechercher des produits, créer de nouveaux champs ou les enrichir via OpenAI.

La page "Administration des instructions" est accessible depuis le menu latéral de Streamlit et permet d'ajouter ou de modifier les instructions utilisées par l'agent.

