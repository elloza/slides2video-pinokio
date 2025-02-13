import streamlit as st


if __name__ == "__main__":
    # Configuración de página debe ir ANTES de cualquier otro comando de Streamlit
    st.set_page_config(
        page_title="Slides2Video",
        page_icon="📄",
        layout="wide"
    )

    # Definición de páginas
    home = st.Page("home.py", title="🏠 Inicio 🏠", icon=":material/home:")
    slides_to_video = st.Page("slides_to_video.py", title="📄 Slides to video 🎞️")
    video_to_video = st.Page("video_to_video.py", title="🎞️ Video to video 🎞️")
    slides_to_podcast = st.Page("slides_to_podcast.py", title="📄 Slides to podcast 🎙️")

    # Navegación con secciones
    pg = st.navigation({
        "Inicio":[home],
        "Herramientas": [slides_to_video, video_to_video, slides_to_podcast]
    })
    
    # Ejecutar la página seleccionada
    pg.run()
