## 2026-03-04 - [Disable input when unuseable]
**Learning:** [Disabling form inputs when they are inactive provides crucial affordance that they cannot currently be used, rather than relying solely on placeholder text which some users might miss or screen readers might deprioritize compared to a disabled state attribute.]
**Action:** [Always use the disabled attribute when an input element's functionality relies on an unmet precondition, even if the placeholder text attempts to explain it.]

## 2026-03-05 - [Visual Scannability in Action Lists]
**Learning:** [Text-heavy control panels can cause cognitive fatigue. Adding simple icon affordances to primary action buttons significantly improves scannability and helps users quickly identify the desired diagnostic tool without reading every label.]
**Action:** [Use the `icon` parameter on Streamlit buttons when presenting a group of related but distinct actions to improve visual hierarchy and reduce cognitive load.]

## 2026-03-06 - [Context Reset Affordance in SPAs]
**Learning:** [In single-page diagnostic applications, users can experience cognitive overload from long, continuous conversational histories. Providing a clear, localized reset affordance (like a Clear Chat button) improves user control and reduces context fatigue.]
**Action:** [Always include a localized context-reset control in continuous chat interfaces to allow users to start fresh without refreshing the entire application.]

## 2024-05-24 - Accessible Completion Feedback for Long-Running Tasks
**Learning:** While Streamlit's `st.spinner` provides adequate visual feedback during long-running synchronous operations (like executing PowerShell scripts), it lacks clear auditory completion signals. Screen reader users may not realize when the script has finished and the UI has updated, as the newly populated code block might not be immediately announced.
**Action:** Always pair `st.spinner` with `st.toast()` upon completion for long-running actions. Streamlit implements toasts using ARIA live regions (`role="status"` or `role="alert"`), ensuring that the completion state is actively announced to screen reader users alongside the visual pop-up.
