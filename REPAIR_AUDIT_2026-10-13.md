# Repair audit — 2026-10-13

This update keeps the V41 project and the existing grammar/SRS tables. It changes only the V2 content and the V2 review/menu rendering.

- All 209 lessons and 1,017 grammar cards now contain an explicit `answer_form` value. Cards without a speech-level ending say that no speech-level ending is required; cards ending in 해요체/합니다체/plain forms identify the relevant form.
- Negative base-form hints now resolve to the lexical predicate. For example, `보존하지 않으면` points to `보존하다`, `좋아하지 않을까 봐` to `좋아하다`, and `지명하지 않았거든요` to `지명하다`; they no longer point to `않다`.
- The lesson browser labels the first filter as HTSK level/unit, then filters by topic and grammar point.
- Grammar translations now highlight an English meaning cue for the common HTSK patterns where that cue is explicitly present in the English translation. The Korean cloze remains authoritative; translations without a reliable cue are not falsely colored in full.
- Vocabulary translations retain target-word highlighting for the TOPIK, themed, and music queues.

Validation: Python compilation passes; all 209 lesson files load; all 1,017 cards have a prompt, answer, hint, explanation and answer-form instruction; vocabulary seed validation remains unchanged.
