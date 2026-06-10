# 🎥 KiliCasa 3D Pipeline — Dashboard de Prétraitement (PoC)

Ce dépôt contient le module de **prétraitement** et l'**interface utilisateur** (Dashboard) du projet **KiliCasa**.
L'application est développée en Python avec **Streamlit** et conçue pour s'exécuter sur une VM (Datalia) afin de **nettoyer, standardiser et filtrer** les données avant leur injection dans le pipeline de reconstruction 3D (**COLMAP / Gaussian Splatting**).

---

## 🚀 Architecture Globale (Hybrid Cloud)

| Étage | Matériel | Rôle |
|-------|----------|------|
| **1. VM Locale / Edge** | CPU | Interface Streamlit, ingestion des données (vidéos/photos), extraction de trames (FFmpeg), filtrage lourd (OpenCV). |
| **2. Google Colab** | GPU T4 | Calculs lourds d'IA, triangulation spatiale (COLMAP), rendu 3D (Gaussian Splatting). |

Ce dépôt couvre **l'étage 1** : tout ce qui prépare les images avant le GPU.

---

## ✨ Fonctionnalités Validées (Sprint 1)

### 📹 1. Module Vidéo — *Exigence EF-007*
- **Discrétisation temporelle :** extraction automatique de trames à un framerate optimisé (2 FPS par défaut) via un appel système bas niveau `FFmpeg`.
- **Élimination de la redondance :** réduction drastique du volume de données pour préserver la VRAM du GPU.

### 📸 2. Module Photos & Standardisation — *Exigences EF-004 & EF-006*
- **Nettoyage RGPD / EXIF :** suppression native de toutes les métadonnées (coordonnées GPS, constructeur) lors de la lecture des buffers d'images.
- **Sécurisation Anti-OOM (Out Of Memory) :** downscaling intelligent des images ultra-haute résolution (4K/8K) vers une dimension maximale standardisée (1920 px).
- **Interpolation Lanczos4 :** utilisation de l'algorithme `INTER_LANCZOS4` (OpenCV) pour réduire la taille sans perte de netteté sur les bordures et les textures.

### 🔍 3. Filtre Anti-Flou — *Exigence EF-008*
- **Analyse fréquentielle :** calcul de la **Variance du Laplacien** sur chaque image (conversion Grayscale préalable pour optimiser la complexité spatiale).
- **Routage dynamique :** les images sous le seuil de tolérance (Δf < 250) sont isolées dans un dossier de rejet pour éviter les échecs de triangulation 3D.

---

## 📁 Structure du Projet

```
kilicasa-3d-pipelin/
├── app.py              # Dashboard Streamlit (UI + orchestration)
├── pipeline.py         # VideoPreprocessor : ffmpeg + OpenCV (cœur métier)
├── storage.py          # Adapter de stockage (Local / Drive / S3)
├── requirements.txt    # Dépendances Python
├── redame.md           # Ce fichier
└── data/               # Généré à l'exécution
    ├── inputs/            # Vidéos uploadées
    ├── frames_extracted/  # Trames extraites + nettes conservées
    ├── frames_rejected/   # Trames floues rejetées
    ├── photos_input/      # Photos uploadées (mode Lot de Photos)
    ├── photos_processed/  # Photos nettes + redimensionnées
    └── photos_rejected/   # Photos floues rejetées
```

> Le stockage repose sur un **design pattern Adapter** (`StorageManager`). On peut basculer
> du backend local vers Google Drive / S3 sans toucher au reste du code.

---

## 🛠️ Prérequis

- **Python 3.9+**
- **FFmpeg** installé au niveau système (requis pour le mode Vidéo) :
  ```bash
  sudo apt update && sudo apt install -y ffmpeg
  ffmpeg -version   # vérification
  ```

---

## ⚙️ Installation et Lancement 

```bash
# 1. Créer et activer l'environnement virtuel
python3 -m venv venv
source venv/bin/activate

# 2. Installer les dépendances Python
pip install -r requirements.txt

# 3. Lancer le dashboard
streamlit run app.py
```

L'interface est ensuite accessible sur **http://localhost:8501**.
Sur une VM distante, ajoute `--server.address 0.0.0.0` et ouvre le port 8501.

---

## 🖥️ Utilisation du Dashboard

1. **Choisir le type d'entrée** en haut de la page : `Vidéo` ou `Lot de Photos`.
2. **Régler les paramètres** dans la barre latérale :
   - *Seuil de netteté* (Variance du Laplacien) — commun aux deux modes.
   - *Frames par seconde* — mode Vidéo uniquement.
   - *Dimension max* — mode Photos uniquement.
3. **Uploader** la source (une vidéo, ou plusieurs photos).
4. **Lancer le prétraitement** : la barre de progression suit chaque étape.
5. **Consulter les résultats** : métriques (traitées / conservées / rejetées) et aperçu des images conservées.

---

## 🧩 Pile Technique

| Composant | Usage |
|-----------|-------|
| **Streamlit** | Interface web du dashboard |
| **FFmpeg** | Extraction de trames vidéo |
| **OpenCV** (`opencv-python`) | Détection de flou + redimensionnement Lanczos4 |
| **Python `abc`** | Interface Adapter du stockage |

---

