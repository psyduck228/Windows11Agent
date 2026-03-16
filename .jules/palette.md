## 2024-05-15 - Streamlit Loading States
**Learning:** Streamlit apps block the UI during long-running Python operations (like running PowerShell scripts). Users don't know if the button click registered or if the app is frozen.
**Action:** Wrap long-running operations in `with st.spinner("Analyzing...")` to provide immediate visual feedback. Adding tooltips (`help="description"`) to buttons also clarifies what the diagnostic will do before clicking.
## 2024-05-24 - Accurate Toast Feedback
**Learning:** Blindly showing a success toast (`st.toast('Analysis complete!', icon='✅')`) when a backend process actually fails or is rate-limited creates confusing, contradictory signals for the user. They see 'Success' but the output says 'Error'.
**Action:** Always check the result or status of the backend operation before displaying feedback, and use the appropriate toast variation (success vs. failure) to match the actual outcome.
## 2024-05-31 - Contextual Disabled States
**Learning:** Disabling buttons without explaining *why* they are disabled (e.g., a 'Clear Chat' button when the chat is already empty) leaves users confused about whether the app is broken or if they just can't perform the action right now.
**Action:** When conditionally disabling an interactive element, dynamically update its tooltip (`help`) to explicitly explain the disabled state to the user.
## 2024-06-05 - Synchronous UI State Clutter
**Learning:** Pre-populating output state strings (e.g., `st.session_state["output"] = "Analyzing..."`) before blocking calls in Streamlit is a UX anti-pattern because the UI won't redraw until the script finishes. Instead of acting as an intermediate loading state, the text permanently clutters the final rendered output.
**Action:** Remove manual state string assignments before blocking operations and rely on `st.spinner` for visual feedback. Directly assign the result to the state instead of appending.
## 2024-06-15 - Destructive Action Confirmation
**Learning:** Users can easily misclick destructive buttons like "Clear Chat History" leading to immediate, unrecoverable data loss without any friction.
**Action:** Always place destructive actions behind a confirmation dialog or popover to prevent accidental loss of state.

## 2024-06-25 - Enhance Visibility of Application State Errors
**Learning:** Rendering diagnostic script failures as default code output (`st.code`) obfuscates the failure state, confusing users who expect a distinct error visualization. Using consistent instructions (like using identical placeholders for different UI components requesting the same action) reduces cognitive load.
**Action:** Always conditionally render operational failures (e.g., outputs starting with 'Error:' or 'Execution Failed:') using visually distinct error components like `st.error(..., icon="❌")` instead of plain code blocks, and extract repetitive UI strings into global constants for consistent messaging across different components.

## 2024-06-25 - Keyboard Accessibility and Power User Shortcuts
**Learning:** Frequent actions like triggering main diagnostic tools benefit significantly from keyboard shortcuts, which drastically improves accessibility for users reliant on keyboard navigation and enhances UX for power users.
**Action:** Use Streamlit's `shortcut` parameter on frequent or primary `st.button`s to provide keyboard accessibility hints (e.g., `shortcut="Shift+1"`).
