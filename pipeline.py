import os
import subprocess
import cv2
import shutil

class VideoPreprocessor:
    """Orchestre le prétraitement d'une vidéo : extraction puis filtrage."""

    def extract_frames_ffmpeg(self, video_path, output_folder, fps=2):
        """Extrait les frames de la vidéo via ffmpeg.

        Args:
            video_path: chemin vers la vidéo source.
            output_folder: dossier où les images seront sauvegardées.
            fps: nombre d'images extraites par seconde (défaut: 2).
        """
        print(f"Début de l'extraction des frames depuis : {video_path}")
        
        # S'assurer que le dossier de sortie existe
        os.makedirs(output_folder, exist_ok=True)
        
        # La commande FFmpeg
        command = [
            'ffmpeg',
            '-y',                             # Écrase les fichiers existants si on relance
            '-i', video_path,                 # Fichier d'entrée
            '-vf', f'fps={fps}',              # Filtre de framerate
            '-qscale:v', '2',                 # Haute qualité jpeg
            f'{output_folder}/frame_%04d.jpg' # Format de sortie
        ]
        
        try:
            # Exécution de la commande dans le terminal de la VM
            subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            print("Extraction FFmpeg terminée avec succès.")
        except subprocess.CalledProcessError as e:
            print(f" Erreur FFmpeg : {e.stderr.decode()}")
            raise e

    def filter_blurry_frames_opencv(self, folder_path, rejected_folder, threshold=250.0):
        """Filtre les frames floues d'un dossier via OpenCV.

        Args:
            folder_path: dossier contenant les frames extraites.
            rejected_folder: dossier où déplacer les images floues.
            threshold: seuil de netteté (Variance du Laplacien).
        """
        print("Analyse de netteté en cours avec OpenCV...")
        
        # Créer le dossier des rejets s'il n'existe pas
        os.makedirs(rejected_folder, exist_ok=True)
        
        blurry_count = 0
        sharp_count = 0
        
        # Parcourir toutes les images du dossier
        for filename in os.listdir(folder_path):
            if filename.lower().endswith(('.jpg', '.jpeg', '.png')):
                file_path = os.path.join(folder_path, filename)
                
                # 1. Lecture de l'image
                image = cv2.imread(file_path)
                if image is None:
                    continue
                
                # 2. Conversion en niveaux de gris (Grayscale)
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
                
                # 3. Calcul de la variance du Laplacien (Score de netteté)
                fm = cv2.Laplacian(gray, cv2.CV_64F).var()
                
                # 4. Tri : si c'est inférieur au seuil, on déplace (rejette)
                if fm < threshold:
                    shutil.move(file_path, os.path.join(rejected_folder, filename))
                    blurry_count += 1
                else:
                    sharp_count += 1
                    
        print(f"✅ Filtrage terminé : {sharp_count} nettes conservées, {blurry_count} floues rejetées.")

        # On retourne les stats pour les afficher plus tard dans le Dashboard Streamlit
        return sharp_count, blurry_count

    def process_photos_batch(self, input_folder, output_folder, rejected_folder, max_dimension=1920, threshold=250.0):
        """Traite un lot de photos : Filtre le flou, redimensionne (Anti-OOM) et nettoie les EXIF.

        Args:
            input_folder: dossier contenant les photos originales.
            output_folder: dossier pour les photos prêtes pour la 3D.
            rejected_folder: dossier pour les photos floues.
            max_dimension: Taille maximale (largeur ou hauteur) pour éviter le crash GPU.
        """
        print(f"Début du traitement du lot de photos depuis : {input_folder}")
        
        os.makedirs(output_folder, exist_ok=True)
        os.makedirs(rejected_folder, exist_ok=True)
        
        sharp_count = 0
        blurry_count = 0
        
        for filename in os.listdir(input_folder):
            if filename.lower().endswith(('.jpg', '.jpeg', '.png')):
                file_path = os.path.join(input_folder, filename)
                
                # 1. Lecture de l'image (cv2.imread ignore automatiquement les données EXIF !)
                image = cv2.imread(file_path)
                if image is None:
                    continue
                
                # 2. Détection de flou (Variance du Laplacien)
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
                fm = cv2.Laplacian(gray, cv2.CV_64F).var()
                
                if fm < threshold:
                    # L'image est floue, on la rejette
                    shutil.copy(file_path, os.path.join(rejected_folder, filename))
                    blurry_count += 1
                else:
                    # L'image est nette, on vérifie sa taille
                    h, w = image.shape[:2]
                    
                    # 3. Redimensionnement IA (Upscaling down / Downsampling)
                    if max(h, w) > max_dimension:
                        scale = max_dimension / max(h, w)
                        new_w, new_h = int(w * scale), int(h * scale)
                        # INTER_LANCZOS4 est le meilleur algorithme mathématique pour réduire la taille sans perdre les détails
                        image = cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_LANCZOS4)
                    
                    # 4. Sauvegarde de l'image standardisée
                    cv2.imwrite(os.path.join(output_folder, filename), image)
                    sharp_count += 1
                    
        print(f" Traitement photos terminé : {sharp_count} nettes/redimensionnées, {blurry_count} rejetées.")
        return sharp_count, blurry_count
   