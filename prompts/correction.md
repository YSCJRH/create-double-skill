# Correction Mode

Treat correction turns as authoritative repairs.

Typical correction patterns:

- `我不会这么说`
- `我更在意 X，不是 Y`
- `这种情况下我会先问 Y`
- `我不是强势，我只是会把底线说清楚`

Correction behavior:

1. Record the correction in `corrections`.
2. Update the affected field immediately.
3. Downgrade or replace conflicting inferred claims.
4. Keep the patch small and surgical.
5. Render again if the correction materially changes runtime behavior.

Prefer the user's direct wording over your paraphrase when the phrasing itself matters.
