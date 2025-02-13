import streamlit as st
import base64

if __name__ == "__main__":
    # Configuración de página debe ir ANTES de cualquier otro comando de Streamlit
    st.set_page_config(
        page_title="Slides2Video",
        page_icon="favicon.ico",
        layout="wide"
    )

    # Mostrar el logo usando base64 en la sidebar
    with open("logo.png", "rb") as f:
        data = base64.b64encode(f.read()).decode("utf-8")

    st.sidebar.markdown(
        f"""
        <div style="display:table;margin-left:20%;">
            <img src="data:image/png;base64,{data}" width="100" height="100">
        </div>
        """,
        unsafe_allow_html=True,
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
