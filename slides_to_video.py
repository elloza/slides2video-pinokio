import streamlit as st
# Removed heavy imports here

def load_heavy_modules():

    my_bar = st.progress(0, text="Cargando módulos, por favor espera...")
    global detect_file_type, get_file_stats, reset_state, init_session_state, get_language_options
    global extract_pdf_slides, extract_pptx_slides, get_file_bytes, get_vlm
    global get_tts_provider, Translator
    global merge_slides_to_video
    # Loading File Utils
    my_bar.progress(10, text="Cargando FileUtils...")
    from utils.FileUtils import (
        detect_file_type, get_file_stats, reset_state, init_session_state,
        get_language_options, extract_pdf_slides, extract_pptx_slides, get_file_bytes
    )
    my_bar.progress(35, text="Cargando VLMUtils...")
    from utils.VLMUtils import get_vlm
    my_bar.progress(60, text="Cargando TTSUtils...")
    from utils.TTSUtils import get_tts_provider
    my_bar.progress(75, text="Cargando TranlationUtils...")
    from utils.TranlationUtils import Translator
    my_bar.progress(90, text="Cargando VideoUtils...")
    my_bar.progress(100, text="Módulos cargados!")

    # Ocultar la barra de progreso y el texto
    my_bar.empty()


import time
import threading
import queue
from utils.VideoUtils import merge_slides_to_video


# Función para el Paso 1: Subir Presentación
def step_upload():
    col1, col2 = st.columns([3, 2])
    with col1:
        st.write("#### Sube tu presentación")
        uploaded_file = st.file_uploader(
            "Arrastra o selecciona tu archivo",
            type=['pdf', 'pptx'],
            help="PDF o PPTX (solo PPTX admite notas del orador)",
            key="file_uploader"
        )
        if uploaded_file:
            file_type = detect_file_type(uploaded_file)
            if file_type:
                stats = get_file_stats(file_type, uploaded_file)
                if stats:
                    st.session_state.uploaded_file = uploaded_file
                    st.session_state.file_type = file_type
                    st.session_state.file_stats = stats
                    st.success("✅ Archivo cargado correctamente")
                    if file_type == 'pdf':
                        st.session_state.slides_images = extract_pdf_slides(uploaded_file)
                        st.session_state.slides_notes = ["" for _ in st.session_state.slides_images]
                    else:
                        st.session_state.slides_images, st.session_state.slides_notes = extract_pptx_slides(uploaded_file)
        if st.session_state.uploaded_file and st.button("✨ Siguiente ✨", use_container_width=True):
            st.session_state.step += 1
            st.rerun()
    with col2:
        # ...Información y resumen del documento...
        st.markdown("""
        <div style="font-size:14px;">
            <h4>Información</h4>
            <p>
                👋 <strong>Proceso de conversión</strong><br><br>
                1. Sube tu presentación (PDF/PPTX)<br>
                2. Configura las notas del orador<br>
                3. Configura el audio con IA<br>
                4. Genera y descarga el video
            </p>
        </div>
        """, unsafe_allow_html=True)
        if st.session_state.uploaded_file and st.session_state.file_stats:
            st.markdown("<div style='font-size:14px;'><h4>📊 Resumen del documento</h4></div>", unsafe_allow_html=True)
            for key, value in st.session_state.file_stats.items():
                st.markdown(f"<div style='font-size:14px;'><strong>{key}:</strong> {value}</div>", unsafe_allow_html=True)
            if st.session_state.file_type == 'pdf':
                st.warning("⚠️ Los archivos PDF no contienen notas del orador")

# Función para el Paso 2: Configurar Notas
def step_configure_notes():

    PROMPT_DEFAULT = "Eres un experto profesor en TEMA. Se te presenta una diapositiva de tu clase y tienes que generar las explicaciones en primera persona del singular o del plural, explicando el tema del que tratan. Solo contesta con la explicación, nada más, y como si se tratara de una explicación hablada a ellos en clase."

    col_config, col_preview = st.columns(2)
    with col_config:
        languages = get_language_options()
        notes = st.session_state.slides_notes  # Directamente de la sesión
        has_notes = any(note for note in notes)
        st.write("### Selección de operación:")
        notes_mode = st.selectbox(
            "Operación a realizar", 
            options=["Traducir notas", "Generar notas"], 
            index=0 if has_notes else 1, 
            key='notes_mode'
        )
        if notes_mode == "Traducir notas":
            st.write("### Traducir notas existentes")
            source_lang = st.selectbox("Idioma original", options=languages.keys(), format_func=lambda x: languages[x], key='source_lang')
            target_lang = st.selectbox("Idioma destino", options=languages.keys(), format_func=lambda x: languages[x], key='target_lang')
            language_bcp47 = {"en": "eng_Latn", "es": "spa_Latn", "fr": "fra_Latn", "de": "deu_Latn",
                              "ro": "ron_Latn", "it": "ita_Latn", "pt": "por_Latn", "nl": "nld_Latn",
                              "pl": "pol_Latn", "ar": "arb_Arab"}
            src_bcp47, tgt_bcp47 = language_bcp47.get(source_lang, source_lang), language_bcp47.get(target_lang, target_lang)
        else:
            st.write("### Generar notas")
            # Configuración de VLM para generación de notas
            st.write("#### Configuración de VLM")
            vlm_model = st.selectbox(
                "Modelo de VLM",
                options=["Gemini 2.0","LLMStudio"],
                key="vlm_model"
            )
            if vlm_model == "LLMStudio":
                # Guardar URL y Model Identifier en la sesión
                st.session_state.vlm_model_url = st.text_input(
                    "URL del modelo VLM",
                    value=st.session_state.get("vlm_model_url", "http://localhost:1234/v1"),
                    help="URL del modelo de visión y lenguaje para generar las notas"
                )

                col1, col2,= st.columns([1,1])

                with col1:
                    st.session_state.vlm_model_id = st.text_input(
                        "Model Identifier VLM",
                        value=st.session_state.get("vlm_model_id", "qwen2-vl-7b-instruct"),
                        help="Identifier del modelo VLM"
                    )

                with col2:
                    st.number_input("Maxtokens", min_value=1, value=500, step=1, key="max_tokens", help="Número máximo de tokens en la respuesta generada por el modelo")

                st.session_state.user_prompt = st.text_area(
                    "Rol del orador (Prompt)",
                    value=PROMPT_DEFAULT,
                    help="Define cómo se generarán las notas",
                    height=100
                )

            elif vlm_model == "Gemini 2.0":
                st.write("#### Configuración de Gemini 2.0")

                col1, col2, col3, col4 = st.columns([2,1,1,1])
                with col1:
                    api_key = st.text_input("API Key *", type="password", key="gemini_api_key")
                with col2:
                    # Se solicita también el identificador del modelo, en el caso de Gemini no hay URL
                    model_id = st.text_input("Model Identifier", value=st.session_state.get("gemini_model_id", "gemini-2.0-flash"), key="gemini_model_id")
                with col3:
                    # Usar un key distinto, asignando el valor a una variable local
                    st.number_input("Reqtime(ms)", min_value=0, value=0, step=100, key="gem_wait_time", help="Tiempo de espera entre solicitudes a la API de Gemini (en milisegundos)")
                with col4:
                    st.number_input("Maxtokens", min_value=1, value=500, step=1, key="max_tokens", help="Número máximo de tokens en la respuesta generada por el modelo")

                st.session_state.user_prompt = st.text_area(
                    "Rol del orador (Prompt)",
                    value=PROMPT_DEFAULT,
                    help="Define cómo se generarán las notas",
                    height=100
                )
                
    with col_preview:
        st.write("### Preview de Diapositivas")
        col1, col2, col3 = st.columns([1,3,1])
        num_slides = len(st.session_state.slides_images)
        slide_number = st.number_input("Diapositiva", min_value=1, max_value=num_slides, value=1, step=1)
        slide_index = slide_number - 1
        with col2:
            st.image(st.session_state.slides_images[slide_index], caption=f"Diapositiva {slide_number}", use_container_width=True)
        note = st.session_state.slides_notes[slide_index]
        st.session_state.slides_notes[slide_index] = st.text_area(f"Notas para la diapositiva {slide_number}", value=note, height=68)
        # Nuevos botones de generación de notas en el preview
        if notes_mode == "Generar notas":
            col_gen1, col_gen2 = st.columns(2)
            with col_gen1:
                if st.button("Generar Nota", key="gen_current_note", use_container_width=True):
                    with st.spinner("Generando nota para la diapositiva..."):
                        if st.session_state.vlm_model == "LLMStudio":
                            vlm = get_vlm("LLMStudio", st.session_state.vlm_model_url, st.session_state.vlm_model_id)
                        else:  # Gemini 2.0
                            if not st.session_state.get("gemini_api_key"):
                                st.error("Por favor ingresa la API Key para Gemini 2.0")
                                st.stop()
                            model_id = st.session_state.get("gemini_model_id", "gemini-2.0-flash")
                            vlm = get_vlm("Gemini 2.0", "", model_id, st.session_state.gemini_api_key)
                        st.session_state.slides_notes[slide_index] = vlm.process_single_slide(
                            st.session_state.slides_images[slide_index],
                            st.session_state.user_prompt,
                            st.session_state.max_tokens  # se pasa max_tokens
                        )
                        st.success("✅ Nota generada correctamente")
                    st.rerun()

            with col_gen2:
                if st.button("Generar Notas para todas", key="gen_all_notes", use_container_width=True):
                    if st.session_state.vlm_model == "LLMStudio":
                        vlm = get_vlm("LLMStudio", st.session_state.vlm_model_url, st.session_state.vlm_model_id)
                    else:
                        if not st.session_state.get("gemini_api_key"):
                            st.error("Por favor ingresa la API Key para Gemini 2.0")
                            st.stop()
                        base_url = st.session_state.get("gemini_base_url", "http://localhost:1234/v1")
                        model_id = st.session_state.get("gemini_model_id", "gemini-default")
                        vlm = get_vlm("Gemini 2.0", base_url, model_id, st.session_state.gemini_api_key)
                    all_notes = []
                    total = len(st.session_state.slides_images)
                    progress_bar = st.progress(0)
                    for idx, image in enumerate(st.session_state.slides_images):
                        note = vlm.process_single_slide(
                            image,
                            st.session_state.user_prompt,
                            st.session_state.max_tokens  # se pasa max_tokens
                        )
                        all_notes.append(note)
                        progress_bar.progress((idx + 1) / total)
                        if st.session_state.vlm_model == "Gemini 2.0":
                            # Recuperar el valor usando el key modificado
                            gem_wait_time = st.session_state.get("gem_wait_time", 0)
                            time.sleep(gem_wait_time / 1000)
                    st.session_state.slides_notes = all_notes
                    st.success("✅ Notas generadas correctamente")
                    st.rerun()
        else:  # Modo "Traducir notas"
            if st.button("Traducir Nota", key="trans_current_note", use_container_width=True):
                note = st.session_state.slides_notes[slide_index]
                if note.strip():
                    with st.spinner("Traduciendo nota..."):
                        # Actualizar en el texto del spinner que se está descargando el modelo en el spinner
                        with st.spinner("Descargando modelo de traducción..."):
                            translator_instance = Translator()
                        translated = translator_instance.translate_notes(src_bcp47, tgt_bcp47, note)
                        st.session_state.slides_notes[slide_index] = translated
                    st.success("✅ Nota traducida")
                    # Asegurarse que se refresca el renderizado del cuadro con las notas
                    st.rerun()
                    
                else:
                    st.info("No hay nota para traducir en esta diapositiva.")
            if st.button("Traducir todas las notas", key="trans_all_notes", use_container_width=True):
                progress_bar = st.progress(0)
                progress_text = st.empty()
                translated_notes = []
                total = len(st.session_state.slides_notes)
                for idx, n in enumerate(st.session_state.slides_notes):
                    if not n.strip():
                        translated_notes.append("")
                        continue
                    progress_bar.progress((idx + 1) / total)
                    progress_text.text(f"Traduciendo diapositiva {idx + 1} de {total}")
                    translator_instance = Translator()
                    translated_notes.append(translator_instance.translate_notes(src_bcp47, tgt_bcp47, n))
                progress_bar.progress(1.0)
                progress_text.empty()
                st.session_state.slides_notes = translated_notes
                st.success("✅ Todas las notas traducidas correctamente")
                st.rerun()

        col_nav1, col_nav2 = st.columns([1, 1])
        with col_nav1:
            if st.button("⬅️ Atrás", use_container_width=True):
                st.session_state.step -= 1
                st.rerun()
        with col_nav2:
            if st.button("✨ Siguiente ✨", use_container_width=True):
                st.session_state.step += 1
                st.rerun()

# Función para el Paso 3: Configurar Audio
def step_configure_audio():
    # Asegurar que slides_notes_audios tenga la misma longitud que slides_notes
    if 'slides_notes_audios' not in st.session_state or len(st.session_state.slides_notes_audios) != len(st.session_state.slides_notes):
        st.session_state.slides_notes_audios = [None] * len(st.session_state.slides_notes)
    col_config_audio, col_preview_audio = st.columns(2)
    with col_config_audio:
        st.write("### Configurar Audio")
        tts_provider_selected = st.selectbox(
            "Proveedor de TTS",
            options=["xttsv2","elevenlabs"],
            key='tts_provider',
            index=1
        )
        
        if tts_provider_selected == 'xttsv2':
            st.write("### Configuración de XTTSv2")
            st.info("Modelo open source, sin necesidad de API Key. Pero hay que indicar el idioma y al usar este modelo aceptas https://coqui.ai/cpml.txt")
            # Spinner para cargar el modelo
            with st.spinner("Cargando modelo...descargando todo lo necesario..."):
                tts_client = get_tts_provider(tts_provider_selected)
            map_all_voices = tts_client.get_available_voices()
            voice_id = st.selectbox("Voz para la generación de audio", options=list(map_all_voices.keys()), format_func=lambda x: map_all_voices[x], key='selected_voice')
            # Language (de los disponibles por el tts provider)
            st.write("### Configuración de Idioma")
            languages = get_tts_provider(tts_provider_selected).get_available_languages()
            language = st.selectbox("Idioma", options=languages.keys(), format_func=lambda x: languages[x], key='language')
        elif tts_provider_selected == 'elevenlabs':
            st.write("### Configuración de ElevenLabs")
            st.write("API para generar audio a partir de texto.")
            api_key = st.text_input("Clave de API", type="password", key='elevenlabs_api_key')
            if not api_key:
                st.error("Por favor ingresa la Clave de API")
            if api_key:
                tts_client = get_tts_provider(tts_provider_selected, api_key)
                map_all_voices = tts_client.get_available_voices()
                selected_voice = st.selectbox(
                    "Selecciona la voz",
                    options=list(map_all_voices.keys()),
                    format_func=lambda x: map_all_voices[x]
                )
                st.session_state.selected_voice = selected_voice  # almacenar la voz seleccionada
                
        elif tts_provider_selected == 'chatterbox':
            st.write("### Configuración de Chatterbox TTS")
            st.info("Modelo open source, solo en inglés y si tienes una tarjeta gráfica NVIDIA")
            # Show a control for recording audio 
            st.write("### Grabación de audio de referencia")
            st.write("Puedes grabar un mensaje de voz para usarlo como referencia para la síntesis de voz.")
            reference_audio = st.audio_input("Graba un mensaje de voz")
            if reference_audio:
                st.audio(reference_audio, format="audio/wav")
            # Get the path to the audio file        
    with col_preview_audio:
        st.write("### Preview de Diapositivas con audio")
        num_slides = len(st.session_state.slides_images)
        slide_number = st.number_input("Diapositiva", min_value=1, max_value=num_slides, value=1, step=1)
        slide_index = slide_number - 1
        col_img, col_audio = st.columns([1, 1])
        with col_img:
            st.image(st.session_state.slides_images[slide_index], caption=f"Diapositiva {slide_number}", use_container_width=True)
        new_note = st.text_area(f"Notas para la diapositiva {slide_number}", value=st.session_state.slides_notes[slide_index], height=68)
        st.session_state.slides_notes[slide_index] = new_note
        
        with col_audio:
            if st.button("Generar audio para todas las diapositivas", key="gen_all_audio_btn"):
                provider = tts_provider_selected
                if provider == "elevenlabs":
                    api_key = st.session_state.get("elevenlabs_api_key", "")
                    if not api_key:
                        st.error("Por favor ingresa la Clave de API en la configuración.")
                        st.stop()
                    tts_client = get_tts_provider(provider, api_key)
                    voice_id = st.session_state.get("selected_voice", "default_voice")
                    language = st.session_state.get("language", "Spanish")
                
                elif provider == "chatterbox":
                    tts_client = get_tts_provider(provider, reference_voice=reference_audio)
                    voice_id = st.session_state.get("selected_voice", "default_voice")
                    language = st.session_state.get("language", "Spanish")

                progress_bar = st.progress(0)
                progress_text = st.empty()
                total = len(st.session_state.slides_notes)

                for idx, note in enumerate(st.session_state.slides_notes):
                    progress_bar.progress((idx + 1) / total)
                    progress_text.text(f"Generando audio para diapositiva {idx + 1} de {total}")
                    if note.strip():
                        st.session_state.slides_notes_audios[idx] = tts_client.synthesize_text(voice_id, note, language=language)
                progress_bar.empty()
                progress_text.empty()
                st.success("Todos los audios generados correctamente.")
                st.rerun()
            
            if new_note.strip() and st.button("Generar Audio", key=f"gen_audio_{slide_index}", use_container_width=True):
                provider = tts_provider_selected
                if provider == "elevenlabs":
                    api_key = st.session_state.get("elevenlabs_api_key", "")
                    if not api_key:
                        st.error("Por favor ingresa la Clave de API en la configuración.")
                        st.stop()
                    tts_client = get_tts_provider(provider, api_key)
                    voice_id = st.session_state.get("selected_voice")
                    language = st.session_state.get("language", "Spanish")
                elif provider == "xttsv2":
                    tts_client = get_tts_provider(provider)
                    voice_id = st.session_state.get("selected_voice")
                    language = st.session_state.get("language", "Spanish")
                else:
                    tts_client = get_tts_provider(provider,reference_voice=reference_audio)
                    voice_id = st.session_state.get("selected_voice", "default_voice")
                    language = st.session_state.get("language", "Spanish")
                
                st.session_state.slides_notes_audios[slide_index] = tts_client.synthesize_text(voice_id, new_note, language=language)
                st.success("Audio generado correctamente.")
                st.rerun()
                
            if st.session_state.slides_notes_audios[slide_index]:
                st.audio(st.session_state.slides_notes_audios[slide_index], format="audio/mp3")

        col_nav1, col_nav2 = st.columns([1, 1])
        with col_nav1:
            if st.button("⬅️ Atrás", use_container_width=True):
                st.session_state.step -= 1
                st.rerun()
        with col_nav2:
            if st.button("✨ Siguiente ✨", use_container_width=True):
                st.session_state.step += 1
                st.rerun()
            

# Función para el Paso 4: Generar Video
def step_generate_video():
    st.write("### Generar Video")
    bloque1, bloque2 = st.columns(2)
    with bloque1:
        transition = st.selectbox(
            "Transición entre diapositivas",
            options=['fade', 'slide', 'none'],
            format_func=lambda x: 'Desvanecer' if x == 'fade' else 'Deslizar' if x == 'slide' else 'Ninguna',
            key='transition'
        )
        default_duration = st.number_input("Duración (segundos) para diapositivas sin audio", min_value=1.0, value=3.0, step=0.5, key="default_duration")
        transition_silence = st.number_input("Tiempo de silencio en transiciones (segundos)", min_value=0.0, value=0.0, step=0.5, key="transition_silence")
        fps = 1
        
        if st.button("🚀 Generar Video 🚀", use_container_width=True, type="primary"):
            
            st.write("### Generar Video")
            # Inicializar la cola de progreso
            progress_queue = queue.Queue()
            
            # Barra de progreso y estado
            progress_bar = st.progress(0)
            status_text = st.empty()

            slides_images = st.session_state.slides_images
            slides_audios = st.session_state.slides_notes_audios
            default_duration = st.session_state.default_duration
            fps = 1
            transition_silence = st.session_state.transition_silence

            # Variable compartida para almacenar el resultado
            video_output = {"path": None}
            output_file = "final_video.mp4"

            def run_video_generation():
                video_output["path"] = merge_slides_to_video(
                    slides_images,
                    slides_audios,
                    default_duration,
                    output_file,
                    fps,
                    transition_silence,
                    progress_queue
                )

            # Lanzar el hilo de generación de video
            thread = threading.Thread(target=run_video_generation, daemon=True)
            thread.start()

            # Leer la cola de progreso en el hilo principal
            while thread.is_alive():
                try:
                    status, progress = progress_queue.get(timeout=0.5)
                    progress_bar.progress(int(progress))
                    status_text.text(status+f" {progress:.2f}%")
                except queue.Empty:
                    pass  # Si la cola está vacía, continuar

            # Cuando el video esté listo, actualizar `st.session_state`
            if video_output["path"]:
                st.session_state.generated_video = video_output["path"]
                st.success("🎉 Video generado exitosamente 🚀")
            else:
                st.error("❌ No se pudo generar el video. 😢")

            # Ocultar la barra de progreso y el texto
            progress_bar.empty()
            status_text.empty()

    with bloque2:
        # Diseño 3 columnas con mas espacio en el medio
        col1, col2, col3 = st.columns([1, 8, 1])

        if st.session_state.get("generated_video"):
            with col2:
                with st.container():
                    video_bytes = get_file_bytes(st.session_state.generated_video)
                    st.video(video_bytes)
                    st.download_button(label="Descargar Video", data=video_bytes, file_name="final_video.mp4", mime="video/mp4", key="download_video", use_container_width=True)
    
    col_nav1, col_nav2 = st.columns([1, 1])
    with col_nav1:
        if st.button("⬅️ Atrás", use_container_width=True):
                st.session_state.step -= 1
                st.rerun()
    with col_nav2:
        if st.button("🔄 Volver al inicio y borrar información", use_container_width=True, type="primary"):
            # limpiar toda la sesión
            reset_state()
            st.rerun()

def main():
    load_heavy_modules()
    init_session_state()
    steps = ["📤 Subir Presentación", "✍️ Configurar Notas", "🎙️ Configurar Audio", "🎬 Generar Video"]
    st.markdown("## Convertir Presentación a Video 🎞️")
    st.progress(st.session_state.step / (len(steps) - 1))
    st.write(f"### Paso {st.session_state.step + 1}: {steps[st.session_state.step]}")
    if st.session_state.step == 0:
        step_upload()
    elif st.session_state.step == 1:
        step_configure_notes()
    elif st.session_state.step == 2:
        step_configure_audio()
    elif st.session_state.step == 3:
        step_generate_video()

#-----------------------------------------------------------------------
main()
