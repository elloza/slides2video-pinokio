import streamlit as st

st.sidebar.title("Slides2Video")

# Información en la barra lateral
st.sidebar.markdown("""
    ### Proyecto de Innovación Docente
    **Convocatoria 2024/2025**

    Desarrollado por:  
    **Álvaro Lozano Murciego**  
    Universidad de Salamanca
""")

# Encabezado principal
st.write("# Slides2Video: Innovación Docente con IA 🎥✨")

# Descripción principal
st.markdown("""
    ## Descripción 📋

    El proyecto busca automatizar la creación de material audiovisual a partir de material docente ya existente. Todos
    esto apoyandose en modelos de Inteligencia Artificial.🤖📚 Estos modelos se utilizan en diferentes etapas de la herramienta y en algunos casos son modelos abiertos y otros son APIs de terceros privadas con un coste pero habitualmente con un
    free tier que permite utilizar la herramienta 🌐🔗
            
    Se presentan varias herramientas, siendo la primera de ellas y objetivo principal de este proyecto, la que permite crear videos a partir de presentaciones de diapositivas. 
    El sistema, a partir de una presentación de diapositivas (con notas del orador o no), genera un video con la narración de las notas del orador y la presentación de las 
    diapositivas en un idioma objetivo. 🌐🎤 Para más información de los requisitos para utilizar esta herramienta consutad la documentación.
""")

# Diseño columnas 3
col1, col2, col3 = st.columns([1,3,1])

with col2:
    st.image("PID-SoloSlides.png", caption="Arquitectura del Sistema", use_container_width=True)
