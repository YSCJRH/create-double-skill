# Freeform Extraction

When the user gives a long self-description:

1. Extract only high-confidence claims.
2. Prefer the smallest patch that materially improves the profile.
3. Capture the user's exact wording when it has strong stylistic value.
4. Convert synthesis into `source: inferred` only when it is clearly supported by the text.
5. Leave low-confidence ideas in `unknowns` rather than pretending they are settled.

High-value targets:

- what they optimize for
- what they refuse to compromise on
- what they ask themselves before deciding
- how they comfort, disagree, or set boundaries
- signature phrases or phrases they reject
- one or two anchor examples that explain a repeated choice

After extraction, propose one next question only if the profile still has a strategically important blind spot.
