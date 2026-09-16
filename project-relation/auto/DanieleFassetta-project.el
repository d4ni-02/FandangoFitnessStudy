;; -*- lexical-binding: t; -*-

(TeX-add-style-hook
 "DanieleFassetta-project"
 (lambda ()
   (TeX-add-to-alist 'LaTeX-provided-class-options
                     '(("IEEEtran" "conference")))
   (TeX-add-to-alist 'LaTeX-provided-package-options
                     '(("biblatex" "backend=biber" "sorting=none") ("hyperref" "") ("cite" "") ("amsmath" "") ("amssymb" "") ("amsfonts" "") ("algorithmic" "") ("graphicx" "") ("textcomp" "") ("xcolor" "") ("tabularray" "") ("url" "") ("placeins" "") ("dblfloatfix" "")))
   (add-to-list 'LaTeX-verbatim-macros-with-braces-local "url")
   (add-to-list 'LaTeX-verbatim-macros-with-braces-local "path")
   (add-to-list 'LaTeX-verbatim-macros-with-delims-local "url")
   (add-to-list 'LaTeX-verbatim-macros-with-delims-local "path")
   (TeX-run-style-hooks
    "latex2e"
    "IEEEtran"
    "IEEEtran10"
    "cite"
    "amsmath"
    "amssymb"
    "amsfonts"
    "algorithmic"
    "graphicx"
    "textcomp"
    "xcolor"
    "tabularray"
    "url"
    "placeins"
    "dblfloatfix")
   (TeX-add-symbols
    "BibTeX")
   (LaTeX-add-labels
    "fig:fig1"
    "sec:res_quest"
    "eq:fitness"
    "sec:meth"
    "eq:delta"
    "tbl:valid_solutions_all"
    "fig:fig2"
    "tbl:grammar_coverage"
    "sec:stats"
    "tbl:a12_scores")
   (LaTeX-add-bibliographies
    "references"))
 :latex)

