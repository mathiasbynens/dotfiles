Prompt
======

Loads prompt [themes][1].

Settings
--------

To select a prompt theme, add the following to *zpreztorc*, and replace **name**
with the name of the theme you wish to load. Setting it to **random** will load
a random theme.

    zstyle ':prezto:module:prompt' theme 'name'

Theming
-------

A prompt theme is an autoloadable function file with a special name,
`prompt_name_setup`, placed anywhere in `$fpath`, but for the purpose of this
project, themes **should** be placed in the *modules/prompt/functions*
directory.

### Theme Functions

There are three theme functions, a setup function, a help function, and
a preview function. The setup function **must** always be defined. The help
function and the preview functions are optional.

#### prompt_name_setup

This function is called by the `prompt` function to install the theme. This
function may define other functions as necessary to maintain the prompt,
including a function that displays help or a function used to preview it.

**Do not call this function directly.**

The most basic example of this function can be seen below.

    function prompt_name_setup {
      PROMPT='%m%# '
      RPROMPT=''
    }

#### prompt_name_help

If the `prompt_name_setup` function is customizable via parameters, a help
function **should** be defined. The user will access it via `prompt -h name`.

The most basic example of this function can be seen below.

    function prompt_name_help {
      cat <<EOH
    This prompt is color-scheme-able. You can invoke it thus:

      prompt theme [<color1>] [<color2>]

    where the color is for the left-hand prompt.
    EOH
    }

#### prompt_name_preview

If the `prompt_name_setup` function is customizable via parameters, a preview
function **should** be defined. The user will access it via `prompt -p name`.

The most basic example of this function can be seen below.

    function prompt_name_preview {
      if (( $# > 0 )); then
        prompt_preview_theme theme "$@"
      else
        prompt_preview_theme theme red green blue
        print
        prompt_preview_theme theme yellow magenta black
      fi
    }

### Hook Functions

There are many Zsh [hook][2] functions, but mostly the *precmd* hook will be
used.

#### prompt_name_precmd

This hook is called before the prompt is displayed and is useful for getting
information to display in a prompt.

When calling functions to get information to display in a prompt, do not assume
that all the dependencies have been loaded. Always check for the availability of
a function before you calling it.

**Do not register hook functions. They will be registered by the `prompt` function.**

The most basic example of this function can be seen below.

    function prompt_name_precmd {
      if (( $+functions[git-info] )); then
        git-info
      fi
    }

Authors
-------

*The authors of this module should be contacted via the [issue tracker][3].*

  - [Sorin Ionescu](https://github.com/sorin-ionescu)

[1]: http://zsh.sourceforge.net/Doc/Release/User-Contributions.html#Prompt-Themes
[2]: http://zsh.sourceforge.net/Doc/Release/Functions.html#Hook-Functions
[3]: https://github.com/sorin-ionescu/prezto/issues
