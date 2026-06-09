"""Dashboard interne de test — KiliCasa 3D Pipeline.

Interface Streamlit pour prétraiter une source d'images en vue de la
reconstruction 3D. Deux modes d'entrée :

- **Vidéo** : extraction de frames (ffmpeg) puis filtrage de netteté (OpenCV).
- **Lot de Photos** : filtrage de netteté + redimensionnement (anti-OOM) via OpenCV.
"""

from pathlib import Path
import streamlit as st
from pipeline import VideoPreprocessor
from storage import LocalStorageAdapter

# --------------------------------------------------------------------------- #
# Configuration de la page
# --------------------------------------------------------------------------- #
st.set_page_config(
    page_title="KiliCasa Pipeline",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Habillage CSS ULTRA-PREMIUM (SaaS Look)
st.markdown("""
<style>
/* Cacher les éléments par défaut de Streamlit */
#MainMenu {visibility: hidden;}
header {visibility: hidden;}
footer {visibility: hidden;}

/* Reset global */
.stApp {
    background-color: #fafbfc;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
}

.block-container {
    max-width: 1200px;
    padding-top: 2rem !important;
    padding-bottom: 2rem !important;
}

/* Le Hero Header (Style Vercel/Stripe) */
.hero-container {
    background: linear-gradient(180deg, #ffffff 0%, #f8fafc 100%);
    border: 1px solid #e2e8f0;
    border-radius: 16px;
    padding: 2.5rem;
    margin-bottom: 2rem;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03);
    text-align: center;
}

.hero-title {
    font-size: 2.5rem;
    font-weight: 800;
    letter-spacing: -0.025em;
    color: #0f172a;
    margin: 0 0 0.5rem 0;
}

.hero-sub {
    color: #64748b;
    font-size: 1.1rem;
    font-weight: 400;
    margin-bottom: 1.5rem;
}

.hero-badge {
    background: #f1f5f9;
    color: #334155;
    padding: 0.35rem 0.75rem;
    border-radius: 9999px;
    font-size: 0.75rem;
    font-weight: 600;
    letter-spacing: 0.05em;
    text-transform: uppercase;
    border: 1px solid #cbd5e1;
}

/* Style des bouttons primaires */
div.stButton > button {
    background-color: #0f172a;
    color: #ffffff;
    border-radius: 8px;
    font-weight: 600;
    padding: 0.5rem 1rem;
    border: 1px solid #0f172a;
    transition: all 0.2s ease-in-out;
    width: 100%;
}

div.stButton > button:hover {
    background-color: #ffffff;
    color: #0f172a;
    border: 1px solid #0f172a;
    box-shadow: 0 4px 12px rgba(15, 23, 42, 0.15);
    transform: translateY(-1px);
}

/* Style de la zone d'upload (Drag & Drop) */
[data-testid="stFileUploadDropzone"] {
    background-color: #ffffff;
    border: 2px dashed #cbd5e1;
    border-radius: 12px;
    padding: 2rem;
    transition: border-color 0.2s ease;
}

[data-testid="stFileUploadDropzone"]:hover {
    border-color: #0f172a;
    background-color: #f8fafc;
}

/* Métriques (Cards de résultat) */
[data-testid="stMetric"] {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 12px;
    padding: 1.5rem;
    box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06);
    text-align: center;
}

[data-testid="stMetricValue"] {
    color: #0f172a;
    font-size: 2.5rem;
    font-weight: 800;
    font-variant-numeric: tabular-nums;
}

[data-testid="stMetricLabel"] {
    color: #64748b;
    font-weight: 500;
    font-size: 0.9rem;
    text-transform: uppercase;
    letter-spacing: 0.025em;
}

/* Typography des sous-titres */
h3 {
    font-size: 1.25rem !important;
    font-weight: 700 !important;
    color: #1e293b !important;
    padding-bottom: 0.5rem;
    border-bottom: 2px solid #f1f5f9;
    margin-bottom: 1.5rem !important;
}

/* Etapes de progression */
.step-item {
    padding: 0.75rem 1rem;
    border-radius: 8px;
    margin-bottom: 0.5rem;
    font-size: 0.95rem;
    font-weight: 500;
    display: flex;
    align-items: center;
    gap: 0.75rem;
}
.step-done {
    background-color: #f0fdf4;
    color: #166534;
    border: 1px solid #bbf7d0;
}
.step-active {
    background-color: #eff6ff;
    color: #1d4ed8;
    border: 1px solid #bfdbfe;
    animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
}
.step-pending {
    background-color: #f8fafc;
    color: #94a3b8;
    border: 1px solid #e2e8f0;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: .7; }
}

/* Sidebar Customization */
section[data-testid="stSidebar"] {
    background-color: #ffffff;
    border-right: 1px solid #e2e8f0;
}
section[data-testid="stSidebar"] .stSlider {
    padding-bottom: 1.5rem;
}

</style>
""", unsafe_allow_html=True)

# --------------------------------------------------------------------------- #
# En-tête (Hero Section)
# --------------------------------------------------------------------------- #
st.markdown(
    """
    <div class="hero-container">
        <h1 class="hero-title">KiliCasa Core</h1>
        <p class="hero-sub">Moteur de prétraitement et de standardisation pour l'analyse spatiale 3D.</p>
        <span class="hero-badge">Environnement de Test CPU</span>
    </div>
    """,
    unsafe_allow_html=True,
)

# Initialisation des classes métiers
storage = LocalStorageAdapter(base_dir="data")
storage.init_structure()
preprocessor = VideoPreprocessor()

# Tabs au lieu du st.radio pour un look plus "Logiciel"
tab1, tab2 = st.tabs(["🎥 Traitement Vidéo", "📸 Traitement Photos (Batch)"])

# --------------------------------------------------------------------------- #
# Helpers UI
# --------------------------------------------------------------------------- #
def render_steps(placeholder, steps, current):
    """Affiche la liste des étapes avec un design SaaS."""
    html_content = ""
    for idx, label in enumerate(steps):
        if idx < current:
            html_content += f'<div class="step-item step-done">✓ {label}</div>'
        elif idx == current:
            html_content += f'<div class="step-item step-active">⚡ {label}</div>'
        else:
            html_content += f'<div class="step-item step-pending">○ {label}</div>'
    placeholder.markdown(html_content, unsafe_allow_html=True)

def render_results(sharp_count, blurry_count, preview_dir, kept_label="Images Nettes"):
    """Affiche les métriques avec des cards modernes."""
    st.markdown("<br>", unsafe_allow_html=True)
    total = sharp_count + blurry_count
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Analysé", total)
    col2.metric(kept_label, sharp_count)
    
    delta_str = f"-{(blurry_count / total * 100):.0f}% rejeté" if total else "0"
    col3.metric("Flou Détecté", blurry_count, delta=delta_str, delta_color="inverse")

    kept = sorted(Path(preview_dir).glob("*.jpg")) + sorted(Path(preview_dir).glob("*.png"))
    if kept:
        st.markdown("<br><h3>Aperçu du Dataset Validé</h3>", unsafe_allow_html=True)
        preview = kept[:4] # On affiche juste 4 pour que ce soit clean
        cols = st.columns(4)
        for idx, img_path in enumerate(preview):
            cols[idx].image(str(img_path), use_container_width=True)

# --------------------------------------------------------------------------- #
# Panneau Latéral (Settings)
# --------------------------------------------------------------------------- #
with st.sidebar:
    st.markdown("### ⚙️ Configuration")
    threshold = st.slider(
        "Seuil de Tolérance (Laplacien)",
        min_value=50.0, max_value=600.0, value=250.0, step=10.0,
        help="Niveau de détection du Motion Blur."
    )
    
    fps = st.slider(
        "Échantillonnage Vidéo (FPS)",
        min_value=1, max_value=10, value=2,
        help="Nombre de trames extraites par seconde."
    )
    
    max_dimension = st.slider(
        "Downscaling Anti-OOM (px)",
        min_value=720, max_value=4096, value=1920, step=128,
        help="Résolution maximale pour éviter la saturation VRAM."
    )
    st.divider()
    st.caption("Datalia Edge Server · v1.0")

# --------------------------------------------------------------------------- #
# TAB 1 : Mode VIDÉO
# --------------------------------------------------------------------------- #
with tab1:
    left, right = st.columns([1.2, 1], gap="large")

    with left:
        st.markdown("### Source Vidéo")
        uploaded_video = st.file_uploader("Glissez votre fichier MP4 ici", type=["mp4", "mov"], key="video_uploader", label_visibility="collapsed")
        
        if uploaded_video is not None:
            st.video(uploaded_video)

    with right:
        st.markdown("### Moteur de Traitement")
        launch_video = st.button("Lancer l'extraction", key="btn_video", disabled=uploaded_video is None)
        status_zone_v = st.container()
        steps_placeholder_v = st.empty()

    if launch_video and uploaded_video is not None:
        extracted_dir = str(storage.get_path("frames_extracted"))
        rejected_dir = str(storage.get_path("frames_rejected"))
        steps = ["Ingestion du fichier", "Discrétisation FFmpeg", "Filtre Fréquentiel (OpenCV)", "Dataset Prêt"]
        
        sharp_count = blurry_count = 0
        success = False
        
        try:
            render_steps(steps_placeholder_v, steps, 0)
            saved_path = storage.save_file(uploaded_video, uploaded_video.name, subdir="inputs")
            
            render_steps(steps_placeholder_v, steps, 1)
            preprocessor.extract_frames_ffmpeg(str(saved_path), extracted_dir, fps=fps)
            
            render_steps(steps_placeholder_v, steps, 2)
            sharp_count, blurry_count = preprocessor.filter_blurry_frames_opencv(extracted_dir, rejected_dir, threshold=threshold)
            
            render_steps(steps_placeholder_v, steps, 3)
            success = True
        except Exception as exc:
            status_zone_v.error(f"Erreur d'exécution : {exc}")

        if success:
            render_results(sharp_count, blurry_count, extracted_dir)

# --------------------------------------------------------------------------- #
# TAB 2 : Mode LOT DE PHOTOS
# --------------------------------------------------------------------------- #
with tab2:
    left, right = st.columns([1.2, 1], gap="large")

    with left:
        st.markdown("### Source Photos")
        uploaded_photos = st.file_uploader("Glissez vos photos ici", type=["jpg", "jpeg", "png"], accept_multiple_files=True, key="photo_uploader", label_visibility="collapsed")
        
        if uploaded_photos:
            st.info(f"📁 {len(uploaded_photos)} fichiers mis en attente.")

    with right:
        st.markdown("### Moteur de Traitement")
        launch_photos = st.button("Lancer la standardisation", key="btn_photos", disabled=not uploaded_photos)
        status_zone_p = st.container()
        steps_placeholder_p = st.empty()

    if launch_photos and uploaded_photos:
        photos_input_dir = str(storage.get_path("photos_input"))
        photos_output_dir = str(storage.get_path("photos_processed"))
        photos_rejected_dir = str(storage.get_path("photos_rejected"))
        
        steps = ["Mise en cache", "Nettoyage EXIF & Downscaling", "Dataset Prêt"]
        
        sharp_count = blurry_count = 0
        success = False
        
        try:
            render_steps(steps_placeholder_p, steps, 0)
            for photo in uploaded_photos:
                storage.save_file(photo, photo.name, subdir="photos_input")
                
            render_steps(steps_placeholder_p, steps, 1)
            sharp_count, blurry_count = preprocessor.process_photos_batch(
                photos_input_dir, photos_output_dir, photos_rejected_dir, max_dimension=max_dimension, threshold=threshold
            )
            
            render_steps(steps_placeholder_p, steps, 2)
            success = True
        except Exception as exc:
            status_zone_p.error(f"Erreur d'exécution : {exc}")

        if success:
            render_results(sharp_count, blurry_count, photos_output_dir, kept_label="Photos Valides")