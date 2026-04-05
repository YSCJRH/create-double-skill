# Interview Mode

Ask one question at a time.

The adaptive `start` flow now chooses a track first, then picks questions by depth.

## Global Rules

- Keep the first visible success lightweight.
- Prefer values, decision model, and boundaries before biography.
- Use follow-up questions only when the user wants a more specific double.
- If an answer is too weak to write confidently, keep it as an `unknown`, not an inferred fact.
- When the user gives a correction that answers a pending question, do not ask that question again.

## Track Guidance

### `general`

Use when the user wants a broad self-model.

Question priority:

1. `values.priorities`
2. `decision_model.default_questions`
3. `interaction_style.boundary_style`
4. `interaction_style.support_style`
5. `voice.tone`
6. `interaction_style.disagreement_style`
7. `anchor_examples`

### `work`

Use when the user wants a double that helps with work, collaboration, review, or delivery decisions.

Question priority:

1. work priorities
2. first clarification question on a fuzzy task
3. how they reset expectations or set boundaries at work
4. disagreement / review style
5. speed vs risk tradeoff bias
6. communication structure in work contexts
7. one real work tradeoff example

### `self-dialogue`

Use when the user wants a double for reflection, inner dialogue, or getting unstuck.

Question priority:

1. what they most want to protect when overwhelmed
2. the first question they ask to get clear
3. where self-kindness ends and self-deception begins
4. what kind of support actually helps
5. recurring self-sabotage or blind spots
6. phrases that feel fake, manipulative, or useless
7. one real example of pulling themselves back from confusion

### `external`

Use when the user wants a double for public-facing communication or interacting with other people.

Question priority:

1. what they most want to protect in outward expression
2. what they confirm before replying or speaking publicly
3. how they set boundaries when pushed too far
4. how others describe their outward tone
5. whether they lead with context, conclusions, or boundaries
6. phrases they deliberately avoid
7. one real example of managing tone or boundaries with others

## Depth Guidance

- `quick`
  ask only the 3 base questions, render, allow one correction, then offer 2 more follow-ups
- `standard`
  ask the 3 base questions plus 2 follow-ups before rendering
- `deep`
  ask the 3 base questions plus 4 follow-ups, and make sure at least one of them yields an `anchor_example`

## Good Questions

- ask for a real tradeoff
- ask for one concrete sentence they would or would not use
- ask how they act under pressure or discomfort
- ask for one example that reveals a repeated pattern

## Bad Questions

- broad life history dumps
- multiple unrelated questions in one turn
- trivia that does not change the runtime double
