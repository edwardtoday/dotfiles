(when (>= emacs-major-version 24)
  (require 'package)
  (package-initialize)
  (add-to-list 'package-archives '("melpa" . "http://melpa.milkbox.net/packages/") t)
)

(when (not package-archive-contents)
  (package-refresh-contents))

(defvar my-packages '(starter-kit starter-kit-bindings ido-ubiquitous magit exec-path-from-shell auto-complete color-theme)
  "A list of packages to ensure are installed at launch.")

(dolist (p my-packages)
  (when (not (package-installed-p p))
    (package-install p)))

(setq custom-file (concat esk-user-dir "/custom.el"))
(load custom-file)

(when (memq window-system '(mac ns))
  (exec-path-from-shell-initialize))

(require 'color-theme)
(load-file "~/.emacs.d/elpa/color-theme-ir-black-1.0.1/color-theme-ir-black.el")
(color-theme-ir-black)

(require 'auto-complete)
(require 'auto-complete-config)

(add-to-list 'load-path "~/.emacs.d/doxymacs/")
(require 'doxymacs)
(defun my-doxymacs-font-lock-hook ()
  (if (or (eq major-mode 'c-mode) (eq major-mode 'c++-mode))
      (doxymacs-font-lock)))
(add-hook 'font-lock-mode-hook 'my-doxymacs-font-lock-hook)
(add-hook 'c-mode-common-hook'doxymacs-mode)
(add-hook 'c++-mode-common-hook 'doxymacs-mode)

(setq doxymacs-file-comment-template
 '("///" > n
   "/// " (doxymacs-doxygen-command-char) "file   "
   (if (buffer-file-name)
       (file-name-nondirectory (buffer-file-name))
     "") > n
   "/// " (doxymacs-doxygen-command-char) "author " (user-full-name)
   "<qingpei@sansi.com>"
   > n
   "/// " (doxymacs-doxygen-command-char) "date   " (current-time-string) > n
   "/// " > n
   "/// " (doxymacs-doxygen-command-char) "brief  " (p "Brief description of this file: ") > n
   "/// " > n
   "/// " p > n
   "///" > n))

(ac-config-default)
