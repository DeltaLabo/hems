\LoadClass[a4paper,10pt]{article}

\usepackage[utf8]{inputenc}
\usepackage[T1]{fontenc}
\usepackage[backend=bibtex,style=ieee]{biblatex}
\usepackage{csquotes}
\usepackage[english]{babel}
\usepackage[left=2cm,right=2cm,top=2cm,bottom=2cm]{geometry}
\usepackage{enumitem}
\usepackage{fontawesome}
\usepackage{titlesec}
\usepackage{parskip}
\usepackage{hyperref}
\usepackage{xcolor}
\usepackage{helvet}
\renewcommand{\familydefault}{\sfdefault}
\usepackage{array}
\usepackage[absolute,overlay]{textpos}
\usepackage{graphicx}
\usepackage{import}

% Colors
\definecolor{primary}{RGB}{0,0,0}
\definecolor{secondary}{RGB}{64,64,64}
\definecolor{DarkCyan}{RGB}{0,139,139}

% Section titles
\titleformat{\section}
  {\color{primary}\Large\bfseries}
  {\thesection.}
  {0.8em}
  {}
  [\titlerule]

% Hyperlinks
\hypersetup{
    colorlinks=true,
    linkcolor=primary,
    urlcolor=secondary
}
