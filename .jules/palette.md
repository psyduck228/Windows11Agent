## 2024-05-15 - Streamlit Loading States
**Learning:** Streamlit apps block the UI during long-running Python operations (like running PowerShell scripts). Users don't know if the button click registered or if the app is frozen.
**Action:** Wrap long-running operations in `with st.spinner("Analyzing...")` to provide immediate visual feedback. Adding tooltips (`help="description"`) to buttons also clarifies what the diagnostic will do before clicking.
## 2024-05-24 - Accurate Toast Feedback
**Learning:** Blindly showing a success toast (`st.toast('Analysis complete!', icon='✅')`) when a backend process actually fails or is rate-limited creates confusing, contradictory signals for the user. They see 'Success' but the output says 'Error'.
**Action:** Always check the result or status of the backend operation before displaying feedback, and use the appropriate toast variation (success vs. failure) to match the actual outcome.
