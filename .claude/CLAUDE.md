# User Environment

## Global Tools

- **Playwright** - Global install only (not a local package). Use exclusively via `npx playwright` CLI. All browsers installed.
- **ImageMagick** - Available via `magick` command.

## Preferences

### Communication

- Be ruthlessly concise: no intros, preambles, or filler.
- If clarification is needed: ask 3-4 concrete options.
- If the prompt seems `rambling`/`voice-to-text-written`: ask all questions at once, then wait.
- If the prompt seems `typed`: use `AskUserQuestionTool`.

### Behavior

- Don't ask "would you like me to implement X?" - just do it.
- Never add `Co-Authored-By` or `🤖 Generated with` lines to commits or PRs.

## Voice-to-Text Processing

When input is rambling:

1. Synthesize the core point first
2. Flag if something important got buried
3. Ask clarifying questions if needed (concrete options, not open-ended)
4. Don't ask "did you mean X?" - just proceed with the best interpretation

## Dev Workflow

- Prefer hooks and skills for repeatable patterns
- Use Haiku for cheap checks, Sonnet for judgment, Opus for synthesis
- Separate shared config (settings.json) from personal (settings.local.json)
- When setting up new patterns: explain the tradeoffs, then just do it
