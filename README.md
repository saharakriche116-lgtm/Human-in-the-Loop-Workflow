# Project 3: Human-in-the-Loop Workflow (CV Extraction)

Ce projet implémente un système d'extraction d'informations (CVs) assisté par l'IA. Il repose sur le concept Human-in-the-Loop : l'IA propose une extraction, l'humain corrige les erreurs , et le système se réentraine pour s'améliorer.

![alt text](image.png)
![alt text](image-1.png)

## Fonctionnalités Clés
- **Ingestion :** Upload de fichiers PDF (CVs)
- **Extraction Hybride :** Utilisation de Regex pour préremplir les champs
- **Correction Humaine :** Interface "Split-Screen" (PDF à gauche , Formulaire des champs extraite à droite)
- **Apprentissage Continu :** Pipeline de reentrainement (Scikit-Learn) basé sur les corrections validées
- **Métriques :** Suivi du temps de corrrection moyen et de la precision du modèle pour vérifier si le modèle est en train d'apprendre avec MLflow

---

## Prérequis
Avant le lancement du projet, il faut s'assurez d'avoir installé :
* **Python** (3.8 ou plus récent)
* **Node.js** (v14 ou plus récent) & **npm**
* **Git**


---

## Installation & Lancement

Le projet est divisé en deux dossiers : `backend` (API Python) et `frontend` (React Interface). il faut lancer deux terminaux séparés :

### 1️⃣ Installation du Backend (Terminal 1)

On doit allez dans le dossier backend et installez les dépendances Python

```bash
# 1. Naviguer vers le backend
cd backend

# 2. Créer un environnement virtuel 
# Windows :
python -m venv venv
venv\Scripts\activate
# Mac/Linux :
python3 -m venv venv
source venv/bin/activate

# 3. Installer les librairies nécessaires
pip install fastapi uvicorn sqlalchemy scikit-learn pandas pdfplumber python-multipart joblib

# 4. Démarrer le serveur API
uvicorn main:app --reload
```

### 2️⃣ Installation du Frontend (Terminal 2)

On doit allez dans le dossier frontend et installez les dépendances Node

```bash
# 1. Naviguer vers le frontend
cd frontend

# 2. Installer les paquets
npm install

# 3. Lancer l'interface
npm run dev
```
L'application est maintenant accessible sur http://localhost:5173 comme il est indiqué dans le terminal 

---

## Guide d'utilisation (Workflow)
Pour tester le cycle d'apprentissage complet :

* **Upload** : Sur la page d'accueil comme mentionné ci dessus , cliquez sur "Choisir un fichier" et sélectionnez un CV au format PDF

* **Correction** : Le document apparait dans la liste avec un statut "Pending" On Clique donc sur "Corriger"

* **Validation** : L'IA tente de remplir les champs (nom, email, skills...)
* Corrigez les erreurs ou ajoutez des champs manquants 
* Cliquez sur "Valider et Enregistrer"

* **Ré-entraînement** : Après avoir corrigé des CVs variés, cliquez sur le bouton "Ré-entraîner l'IA" en haut à droite pour réentrainer le modèle pour qu'il peut predire mieux dans la prochaine fois

* **Visualisation** dans MLflow pour voir les métriques d'amélioration

---

## Structure du Projet

```bash
/project-root
│
├── /backend
│   ├── main.py              # API FastAPI & Routes
│   ├── extraction_engine.py # Logique d'extraction (Regex/PDF parsing)
│   ├── train_model.py       # Pipeline ML (Scikit-Learn)
│   ├── hitl.db              # Base de données SQLite (générée auto)
│   └── model_hitl.pkl       # Modèle IA sauvegardee (généré auto)
│
├── /frontend
│   ├── src/App.jsx          # Interface Principale (Logique React)
│   └── package.json         # Dépendances JS
│
└── README.md                # Documentation
```