# Router

Route each incoming turn into exactly one label:

- `answer`: the user is answering the current question
- `freeform`: the user is volunteering self-description or examples
- `correction`: the user is repairing prior language, values, or behavior
- `switch_mode`: the user is explicitly changing collection mode
- `finish`: the user wants a draft generated now

Interpret in this order:

1. Hard control phrases:
   - `继续提问` -> `switch_mode`, mode becomes `interview`
   - `我自己说` -> `switch_mode`, mode becomes `freeform`
   - `我要改一下` -> `switch_mode`, mode becomes `correction`
   - `先生成看看` -> `finish`
2. Explicit repair language:
   - `我不会这么说`
   - `我不会这样说`
   - `我更在意`
   - `这种情况下我会先问`
   - `不是这个意思`
3. Dense self-description:
   - multiple sentences
   - multiple examples
   - clear value or style statements not tied to the last question
4. Default to `answer` only when the turn is directly answering the active question.

Keep the route stable unless there is a strong reason to change it. Mixed turns should prefer the most consequential label:

- correction beats answer
- finish beats everything
- switch_mode beats answer/freeform when explicit
