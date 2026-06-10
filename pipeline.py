import os
import subprocess
import cv2
import shutil

class VideoPreprocessor:
    """Orchestre le prétraitement d'une vidéo ou de photos : extraction, flou et overlap."""

    def extract_frames_ffmpeg(self, video_path, output_folder, fps=2):
        """Extrait des frames d'une vidéo via FFmpeg à la cadence demandée (fps).

        Args:
            video_path (str): Chemin du fichier vidéo source.
            output_folder (str): Dossier de destination des frames extraites.
            fps (int): Nombre de frames à extraire par seconde.

        Returns:
            int: Le nombre de frames extraites.
        """
        print(f"Extraction des frames depuis : {video_path} (fps={fps})")
        os.makedirs(output_folder, exist_ok=True)

        # Nettoyer les anciennes frames pour repartir sur un dossier propre
        for old_file in os.listdir(output_folder):
            if old_file.lower().endswith(('.jpg', '.jpeg', '.png')):
                os.remove(os.path.join(output_folder, old_file))

        output_pattern = os.path.join(output_folder, "frame_%04d.jpg")
        command = [
            "ffmpeg",
            "-i", video_path,
            "-vf", f"fps={fps}",
            "-qscale:v", "2",  # Haute qualité JPEG (2 = quasi sans perte)
            "-y",              # Écrase les fichiers existants sans demander
            output_pattern,
        ]

        result = subprocess.run(command, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"FFmpeg a échoué : {result.stderr}")

        frame_count = len([
            f for f in os.listdir(output_folder)
            if f.lower().endswith(('.jpg', '.jpeg', '.png'))
        ])
        print(f"✅ Extraction terminée : {frame_count} frames générées.")
        return frame_count

    def check_overlap_orb(self, img1_path, img2_path, min_good_matches=40):
        """Calcule le chevauchement (overlap) entre deux images consécutives via l'algorithme ORB.
        
        Returns:
            bool: True si l'overlap est suffisant, False sinon.
            int: Le nombre de points de correspondance trouvés.
        """
        img1 = cv2.imread(img1_path, cv2.IMREAD_GRAYSCALE)
        img2 = cv2.imread(img2_path, cv2.IMREAD_GRAYSCALE)
        
        if img1 is None or img2 is None:
            return False, 0

        # 1. Initialiser le détecteur ORB (Ultra rapide sur CPU)
        orb = cv2.ORB_create(nfeatures=500)

        # 2. Trouver les points clés et les descripteurs
        kp1, des1 = orb.detectAndCompute(img1, None)
        kp2, des2 = orb.detectAndCompute(img2, None)

        if des1 is None or des2 is None:
            return False, 0

        # 3. Créer un Brute-Force Matcher avec la distance de Hamming (adaptée à ORB)
        bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
        
        # Matcher les descripteurs
        matches = bf.match(des1, des2)
        
        # Trier les correspondances par distance (les meilleures en premier)
        matches = sorted(matches, key=lambda x: x.distance)
        
        # Filtrer les bonnes correspondances (distance faible = forte ressemblance)
        good_matches = [m for m in matches if m.distance < 45]
        
        # Si le nombre de points communs est suffisant, l'overlap est validé
        is_ok = len(good_matches) >= min_good_matches
        return is_ok, len(good_matches)

    # Résolution de référence pour la mesure de flou. La variance du Laplacien est
    # très sensible à la taille (une même image nette donne une variance ~30x plus
    # faible en 4K qu'en 720p). On normalise donc toujours à cette taille AVANT de
    # mesurer, indépendamment du downscale anti-OOM, pour que le seuil reste stable.
    BLUR_REFERENCE_DIM = 1280

    def _laplacian_variance(self, gray):
        """Mesure la netteté (variance du Laplacien) à une résolution de référence fixe."""
        h, w = gray.shape[:2]
        if max(h, w) > self.BLUR_REFERENCE_DIM:
            scale = self.BLUR_REFERENCE_DIM / max(h, w)
            gray = cv2.resize(gray, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_AREA)
        return cv2.Laplacian(gray, cv2.CV_64F).var()

    def filter_blurry_frames_opencv(self, folder_path, rejected_folder, threshold=250.0, max_dimension=1920):
        """Filtre les frames floues ET vérifie l'overlap consécutif."""
        print("Analyse de netteté et de chevauchement en cours...")
        os.makedirs(rejected_folder, exist_ok=True)
        
        blurry_count = 0
        low_overlap_count = 0
        sharp_count = 0
        
        # Trier les images pour les analyser dans l'ordre chronologique
        filenames = sorted([f for f in os.listdir(folder_path) if f.lower().endswith(('.jpg', '.jpeg', '.png'))])
        
        last_valid_img_path = None
        
        for filename in filenames:
            file_path = os.path.join(folder_path, filename)
            
            # 1. Check Flou
            image = cv2.imread(file_path)
            if image is None:
                continue
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            fm = self._laplacian_variance(gray)

            if fm < threshold:
                shutil.move(file_path, os.path.join(rejected_folder, filename))
                blurry_count += 1
                continue
                
            # 2. Check Overlap avec la dernière image valide conservée
            if last_valid_img_path is not None:
                is_overlap_ok, match_score = self.check_overlap_orb(last_valid_img_path, file_path)
                if not is_overlap_ok:
                    shutil.move(file_path, os.path.join(rejected_folder, filename))
                    low_overlap_count += 1
                    continue
            
            # Si l'image passe les deux filtres, elle devient la référence
            last_valid_img_path = file_path
            sharp_count += 1
                    
        print(f"✅ Filtrage terminé : {sharp_count} valides, {blurry_count} floues, {low_overlap_count} mauvais overlap.")
        return sharp_count, blurry_count, low_overlap_count

    def process_photos_batch(self, input_folder, output_folder, rejected_folder, max_dimension=1920, threshold=250.0):
        """Traite un lot de photos : Filtre le flou, l'overlap, redimensionne et nettoie les EXIF."""
        print(f"Début du traitement du lot de photos depuis : {input_folder}")
        os.makedirs(output_folder, exist_ok=True)
        os.makedirs(rejected_folder, exist_ok=True)
        
        sharp_count = 0
        blurry_count = 0
        low_overlap_count = 0
        
        filenames = sorted([f for f in os.listdir(input_folder) if f.lower().endswith(('.jpg', '.jpeg', '.png'))])
        last_valid_img_path = None
        
        for filename in filenames:
            file_path = os.path.join(input_folder, filename)
            image = cv2.imread(file_path)
            if image is None:
                continue
                
            # 1. Check Flou (mesuré sur version normalisée pour stabilité du seuil)
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            fm = self._laplacian_variance(gray)

            if fm < threshold:
                shutil.copy(file_path, os.path.join(rejected_folder, filename))
                blurry_count += 1
                continue
            
            # 2. Check Dimension & Downscaling
            h, w = image.shape[:2]
            if max(h, w) > max_dimension:
                scale = max_dimension / max(h, w)
                new_w, new_h = int(w * scale), int(h * scale)
                image = cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_LANCZOS4)
            
            # Sauvegarde temporaire dans output pour pouvoir tester l'overlap
            temp_output_path = os.path.join(output_folder, filename)
            cv2.imwrite(temp_output_path, image)
            
            # 3. Check Overlap
            if last_valid_img_path is not None:
                is_overlap_ok, _ = self.check_overlap_orb(last_valid_img_path, temp_output_path)
                if not is_overlap_ok:
                    os.remove(temp_output_path) # On supprime du dossier valide
                    shutil.copy(file_path, os.path.join(rejected_folder, filename))
                    low_overlap_count += 1
                    continue
                    
            last_valid_img_path = temp_output_path
            sharp_count += 1
                    
        return sharp_count, blurry_count, low_overlap_count