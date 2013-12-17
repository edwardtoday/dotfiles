filetype off

set rtp+=~/.vim/bundle/vundle/
call vundle#rc()

" let Vundle manage Vundle
" required!
Bundle 'gmarik/vundle'

" My bundles here:
"
" original repos on GitHub
" a Git wrapper so awesome, it should be illegal
Bundle 'tpope/vim-fugitive'
" 用全新的方式在文档中高效的移动光标，革命性的突破
Bundle 'EasyMotion'
Bundle 'L9'
" quickly reach the buffer/file/command/bookmark/tag you want
Bundle 'FuzzyFinder'
" 相较于Command-T等查找文件的插件，ctrlp.vim最大的好处在于没有依赖，干净利落
Bundle 'ctrlp.vim'
" 在输入()，""等需要配对的符号时，自动帮你补全剩余半个
Bundle 'AutoClose'
" 神级插件，ZenCoding可以让你以一种神奇而无比爽快的感觉写HTML、CSS
Bundle 'ZenCoding.vim'
" 在()、""、甚至HTML标签之间快速跳转；
Bundle 'matchit.zip'
" 显示行末的空格；
Bundle 'ShowTrailingWhitespace'
" 自动识别文件编码；
Bundle 'FencView.vim'
" 必不可少，在VIM的编辑窗口树状显示文件目录
Bundle 'The-NERD-tree'
" NERD出品的快速给代码加注释插件，选中，`ctrl+h`即可注释多种语言代码；
Bundle 'The-NERD-Commenter'
" 解放生产力的神器，简单配置，就可以按照自己的风格快速输入大段代码。
Bundle 'UltiSnips'
" 让代码更加易于纵向排版，以=或,符号对齐
Bundle 'Tabular'
" 迄今位置最好的自动VIM自动补全插件了吧
Bundle 'Valloric/YouCompleteMe'
Bundle 'DoxygenToolkit.vim'

filetype plugin indent on     " required!

" Make Vim more useful
set nocompatible
" Use the OS clipboard by default (on versions compiled with `+clipboard`)
set clipboard=unnamed
" Enhance command-line completion
set wildmenu
" Allow cursor keys in insert mode
set esckeys
" Allow backspace in insert mode
set backspace=indent,eol,start
" Optimize for fast terminal connections
set ttyfast
" Add the g flag to search/replace by default
set gdefault
" Use UTF-8 without BOM
set encoding=utf-8 nobomb
" Change mapleader
let mapleader=","
" Don’t add empty newlines at the end of files
set binary
set noeol
" Centralize backups, swapfiles and undo history
set backupdir=~/.vim/backups
set directory=~/.vim/swaps
if exists("&undodir")
        set undodir=~/.vim/undo
endif

" Respect modeline in files
set modeline
set modelines=4
" Enable per-directory .vimrc files and disable unsafe commands in them
set exrc
set secure
" Enable line numbers
set number
" Enable syntax highlighting
syntax on
" Highlight current line
set cursorline
" Make tabs as wide as two spaces
set tabstop=2
" Show “invisible” characters
set lcs=tab:▸\ ,trail:·,eol:¬,nbsp:_
set list
" Highlight searches
set hlsearch
" Ignore case of searches
set ignorecase
" Highlight dynamically as pattern is typed
set incsearch
" Always show status line
set laststatus=2
" Enable mouse in all modes
set mouse=a
" Disable error bells
set noerrorbells
" Don’t reset cursor to start of line when moving around.
set nostartofline
" Show the cursor position
set ruler
" Don’t show the intro message when starting Vim
set shortmess=atI
" Show the current mode
set showmode
" Show the filename in the window titlebar
set title
" Show the (partial) command as it’s being typed
set showcmd
" Use relative line numbers
if exists("&relativenumber")
        set relativenumber
        au BufReadPost * set relativenumber
endif
" Start scrolling three lines before the horizontal window border
set scrolloff=3

" Strip trailing whitespace (,ss)
function! StripWhitespace()
        let save_cursor = getpos(".")
        let old_query = getreg('/')
        :%s/\s\+$//e
        call setpos('.', save_cursor)
        call setreg('/', old_query)
endfunction
noremap <leader>ss :call StripWhitespace()<CR>
" Save a file as root (,W)
noremap <leader>W :w !sudo tee % > /dev/null<CR>

if has('gui_running')
  set guifont=Droid\ Sans\ Mono\ 13
endif

let g:DoxygenToolkit_authorName="Pei Qing 卿培 edwardtoday@gmail.com"
