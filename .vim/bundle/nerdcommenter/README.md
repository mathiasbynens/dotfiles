# NERD Commenter

Comment functions so powerful—no comment necessary.

## Installation

### Via Plugin Manager (Recommended)

#### [Vim-Plug](https://github.com/junegunn/vim-plug)

1. Add `Plug 'scrooloose/nerdcommenter'` to your vimrc file.
2. Reload your vimrc or restart
3. Run `:PlugInstall`

#### [Vundle](https://github.com/VundleVim/Vundle.vim) or similar

1. Add `Plugin 'scrooloose/nerdcommenter'` to your vimrc file.
2. Reload your vimrc or restart
3. Run `:BundleInstall`

#### [NeoBundle](https://github.com/Shougo/neobundle.vim)

1. Add `NeoBundle 'scrooloose/nerdcommenter'` to your vimrc file.
2. Reload your vimrc or restart
3. Run `:NeoUpdate``

#### [Pathogen](https://github.com/tpope/vim-pathogen)

```sh
cd ~/.vim/bundle
git clone https://github.com/scrooloose/nerdcommenter.git
```

### Manual Installation

#### Unix

(For Neovim, change `~/.vim/` to `~/.config/nvim/`.)

```sh
curl -fLo ~/.vim/plugin/NERD_Commenter.vim --create-dirs \
  https://raw.githubusercontent.com/scrooloose/nerdcommenter/master/plugin/NERD_commenter.vim
curl -fLo ~/.vim/doc/NERD_Commenter.txt --create-dirs \
  https://raw.githubusercontent.com/scrooloose/nerdcommenter/master/doc/NERD_commenter.txt
```

#### Windows (PowerShell)

```powershell
md ~\vimfiles\plugin
md ~\vimfiles\doc
$pluguri = 'https://raw.githubusercontent.com/scrooloose/nerdcommenter/master/plugin/NERD_commenter.vim'
$docsuri = 'https://raw.githubusercontent.com/scrooloose/nerdcommenter/master/doc/NERD_commenter.txt'
(New-Object Net.WebClient).DownloadFile($pluguri, $ExecutionContext.SessionState.Path.GetUnresolvedProviderPathFromPSPath("~\vimfiles\plugin\NERD_commenter.vim"))
(New-Object Net.WebClient).DownloadFile($docsuri, $ExecutionContext.SessionState.Path.GetUnresolvedProviderPathFromPSPath("~\vimfiles\doc\NERD_commenter.txt"))
```

### Post Installation

Make sure that you have filetype plugins enabled, as the plugin makes use of **|commentstring|** where possible (which is usually set in a filetype plugin). See **|filetype-plugin-on|** for details, but the short version is make sure this line appears in your vimrc:

```sh
filetype plugin on
```

## Usage

### Documentation

Please see the vim help system for full documentation of all options: `:help nerdcommenter`

### Settings

Several settings can be added to your vimrc to change the default behavior. Some examples:

```vim
" Add spaces after comment delimiters by default
let g:NERDSpaceDelims = 1

" Use compact syntax for prettified multi-line comments
let g:NERDCompactSexyComs = 1

" Align line-wise comment delimiters flush left instead of following code indentation
let g:NERDDefaultAlign = 'left'

" Set a language to use its alternate delimiters by default
let g:NERDAltDelims_java = 1

" Add your own custom formats or override the defaults
let g:NERDCustomDelimiters = { 'c': { 'left': '/**','right': '*/' } }

" Allow commenting and inverting empty lines (useful when commenting a region)
let g:NERDCommentEmptyLines = 1

" Enable trimming of trailing whitespace when uncommenting
let g:NERDTrimTrailingWhitespace = 1
```

### Default mappings

The following key mappings are provided by default (there is also a menu provided that contains menu items corresponding to all the below mappings):

Most of the following mappings are for normal/visual mode only. The **|NERDComInsertComment|** mapping is for insert mode only.

  * `[count]<leader>cc` **|NERDComComment|**

    Comment out the current line or text selected in visual mode.

  * `[count]<leader>cn` **|NERDComNestedComment|**

    Same as <leader>cc but forces nesting.

  * `[count]<leader>c<space>` **|NERDComToggleComment|**

    Toggles the comment state of the selected line(s). If the topmost selected line is commented, all selected lines are uncommented and vice versa.

  * `[count]<leader>cm` **|NERDComMinimalComment|**

    Comments the given lines using only one set of multipart delimiters.

  * `[count]<leader>ci` **|NERDComInvertComment|**

    Toggles the comment state of the selected line(s) individually.

  * `[count]<leader>cs` **|NERDComSexyComment|**

    Comments out the selected lines with a pretty block formatted layout.

  * `[count]<leader>cy` **|NERDComYankComment|**

    Same as <leader>cc except that the commented line(s) are yanked first.

  * `<leader>c$` **|NERDComEOLComment|**

    Comments the current line from the cursor to the end of line.

  * `<leader>cA` **|NERDComAppendComment|**

    Adds comment delimiters to the end of line and goes into insert mode between them.

  * **|NERDComInsertComment|**

    Adds comment delimiters at the current cursor position and inserts between. Disabled by default.

  * `<leader>ca` **|NERDComAltDelim|**

    Switches to the alternative set of delimiters.

  * `[count]<leader>cl`  
    `[count]<leader>cb` **|NERDComAlignedComment|**

    Same as **|NERDComComment|** except that the delimiters are aligned down the left side (`<leader>cl`) or both sides (`<leader>cb`).

  * `[count]<leader>cu` **|NERDComUncommentLine|**

    Uncomments the selected line(s).
