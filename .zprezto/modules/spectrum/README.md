Spectrum
========

Provides for easier use of 256 colors and effects.

To learn more about text formatting, read [A Guide to 256 Color Codes][1].

Variables
---------

  - `BG` provides background colors.
  - `FG` provides foreground colors.
  - `FX` provides effects.

### Background and Foreground

Terminals support 8, 16, 88, and 256 colors. Check if a terminal supports 256
colors with `tput colors` before use.

The following colors are supported.

- 0 to 255
- black
- red
- green
- yellow
- blue
- magenta
- cyan
- white

### Effects

Though there are many effects, most terminals support at least bold formatting.

**Not all effects work on all terminals; use them sparingly.**

| Enable                    | Disable                      |
| ------------------------- | ---------------------------- |
|                           | none                         |
|                           | normal                       |
| bold                      | no-bold                      |
| faint                     | no-faint                     |
| standout                  | no-standout                  |
| underline                 | no-underline                 |
| blink                     | no-blink                     |
| fast-blink                | no-fast-blink                |
| reverse                   | no-reverse                   |
| conceal                   | no-conceal                   |
| strikethrough             | no-strikethrough             |
| gothic                    | no-gothic                    |
| double-underline          | no-double-underline          |
| proportional              | no-proportional              |
| overline                  | no-overline                  |
|                           |                              |
|                           | no-border                    |
| border-rectangle          | no-border-rectangle          |
| border-circle             | no-border-circle             |
|                           |                              |
|                           | no-ideogram-marking          |
| underline-or-right        | no-underline-or-right        |
| double-underline-or-right | no-double-underline-or-right |
| overline-or-left          | no-overline-or-left          |
| double-overline-or-left   | no-double-overline-or-left   |
| stress                    | no-stress                    |
|                           |                              |
|                           | font-default                 |
| font-first                | no-font-first                |
| font-second               | no-font-second               |
| font-third                | no-font-third                |
| font-fourth               | no-font-fourth               |
| font-fifth                | no-font-fifth                |
| font-sixth                | no-font-sixth                |
| font-seventh              | no-font-seventh              |
| font-eigth                | no-font-eigth                |
| font-ninth                | no-font-ninth                |

### Plain Text

Use `$BG[none]`, `$FG[none]`, or `$FX[none]` to turn off formatting.

Authors
-------

*The authors of this module should be contacted via the [issue tracker][2].*

  - [P.C. Shyamshankar](https://github.com/sykora)
  - [Sorin Ionescu](https://github.com/sorin-ionescu)

[1]: http://lucentbeing.com/writing/archives/a-guide-to-256-color-codes/
[2]: https://github.com/sorin-ionescu/prezto/issues
