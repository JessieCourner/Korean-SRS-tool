# Mochi Hangul UI update — v12

## Changes

- Vocabulary review opens in a large in-app review dialog, matching the grammar review flow.
- Vocabulary answer grading uses the card loaded for the current prompt, avoiding an extra database read on every submission.
- Review results show a compact correct/retry status, the answer when needed, and a single Continue action.
- Enter and Space activate Continue after a review result.
- The English translation highlights the meaning currently being tested.
- Vocabulary progress uses a pastel bar with a clear card count and marker.
- The daily new-word count uses a number field instead of the low-contrast dropdown.
- Grammar review gives one free retry when the entered answer appears to use the same lexical word with a different grammar form. The hint explains the retry and the existing “Show a grammar hint” control remains available. The free retry does not call the SRS grading/update function; a subsequent submission is graded normally. To avoid false matches, the detector requires a two-syllable shared lexical prefix when the base form has at least two syllables.
- Review screens use shorter feedback to reduce visual noise.

## Data and validation

- The vocabulary and grammar content files are carried forward unchanged from v11.
- No production Supabase connection or data was modified.
- Python syntax compilation passed for the two changed modules; ZIP integrity was checked after packaging.
- No live-app or production import test was performed.
