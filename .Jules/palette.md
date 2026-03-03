## 2024-05-15 - Streamlit Loading States
**Learning:** Streamlit apps block the UI during long-running Python operations (like running PowerShell scripts). Users don't know if the button click registered or if the app is frozen.
**Action:** Wrap long-running operations in `with st.spinner("Analyzing...")` to provide immediate visual feedback. Adding tooltips (`help="description"`) to buttons also clarifies what the diagnostic will do before clicking.
