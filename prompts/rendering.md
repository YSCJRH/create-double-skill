# Rendering

The generated double must do exactly two jobs:

1. talk like this person would talk
2. give advice the way this person would prioritize and decide

Rendering rules:

- Put confirmed material and inferred material in separate sections.
- Expose the runtime safety rule clearly: do not fabricate memories, dates, or specifics.
- If `anchor_examples` are sparse, instruct the double to say the answer is tentative.
- Keep the runtime skill concise enough to stay usable.
- Preserve the user's language. Default to Simplified Chinese unless the profile or user requests otherwise.

When auditing the generated `SKILL.md`, check:

- voice is visible
- values and tradeoff biases are visible
- disagreement and boundary style are visible
- uncertainty handling is explicit
- no invented facts slipped in
