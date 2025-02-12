import streamlit as st
import inspect
import textwrap


# state(key) - Return the value of st.session_state[key] or False
# -------------------------------------------------------------------------------
def state(key):
    try:
        if st.session_state[key]:
            return st.session_state[key]
        else:
            return False
    except Exception as e:
        # st.exception(f"Exception: {e}")
        return False


# show_session( ) - Display st.session_state 
# -------------------------------------------------------------------------------
def show_session( ):
    """Showing the st.session_state."""
    show_session = st.sidebar.checkbox("Show session_state", True)
    if show_session:
        # Showing the st.session_state.
        st.markdown("## Session State")
        st.write("st.session_state object:", st.session_state)


# show_code( ) - Display the named code 
# -------------------------------------------------------------------------------
def show_code(main):
    """Showing the page code."""
    show_code = st.sidebar.checkbox("Show code", True)
    if show_code:
        # Showing the code of the demo.
        st.markdown("## Code")
        sourcelines, _ = inspect.getsourcelines(main)
        st.code(textwrap.dedent("".join(sourcelines[1:])))

