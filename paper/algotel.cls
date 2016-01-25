%%  Copyright (c) 1997, Russel Winder.
%%  With DMTCS-specific alterations by Jeremy Thompson (September 1997)
%%                                     Jens Gustedt (October 1998)
%%  With AlgoTel-specific alterations by =C9ric Fleury (Mars 2000)
%%
\def \fileversion{v1.3}
\def \filedate{1997/05/09}
\def \docdate{\filedate}
\newcommand \journalacronym{algotel}
\newif \if@@draft
\NeedsTeXFormat{LaTeX2e}
\usepackage{ifthen}
\DeclareOption{11pt}{\ClassError{\journalacronym}{Option `11pt' not supported}{}}
\DeclareOption{12pt}{\ClassError{\journalacronym}{Option `12pt' not supported}{}}
\DeclareOption{twocolumn}{\ClassError{\journalacronym}{Option `twocolumn' not supported}{}}
\newcommand{\reftexRun}{}\newcommand{\href}[2]{#2}
\DeclareOption{pdftex}{\renewcommand{\reftexRun}{\RequirePackage[pdftex]{hyperref}}}
\newcommand{\timesRun}{\RequirePackage{times}\RequirePackage{mathptm}}
\DeclareOption{notimes}{\renewcommand{\timesRun}{}}
\DeclareOption*{\PassOptionsToClass{\CurrentOption}{article}}
\ProcessOptions
\LoadClass{article}
\RequirePackage{latexsym}
\timesRun
\reftexRun
\renewcommand\figurename{Fig.}
\renewcommand\tablename{Tab.}
\setlength \textheight{22cm}
\setlength \textwidth{15cm}
\setlength \headsep{1cm}
\setlength \footskip{2cm}
\setlength \headheight{0cm}
\setlength \oddsidemargin{0.96cm}
\setlength \evensidemargin{0.96cm}
\setlength \textfloatsep{13\p@ \@plus 2\p@ \@minus 4\p@}
\setlength \dbltextfloatsep{13\p@ \@plus 2\p@ \@minus 4\p@}
\setlength \parskip{\z@ \@plus 1\p@}
\setlength \parindent{10\p@}
\setlength \topsep{4\p@ \@plus 2\p@ \@minus 1\p@}
\setlength \partopsep{2\p@ \@plus 1\p@ \@minus 1\p@}
\def \title{\@ifnextchar[{\@gettitletwo}{\@gettitleone}}
\def \@gettitleone#1{\@gettitletwo[#1]{#1}}
\def \@gettitletwo[#1]#2{{%
    \gdef \@title{#2}%
    \def \thanks##1{\relax}%
    \def \\{\unskip \space \ignorespaces}%
    \xdef \@titlehead{#1}%
}}
\newcommand \addressmark[1]{%
    \if@marksrequired%
        $^{#1}$%
    \fi%
}
\newif \if@marksrequired
\def \author{\@ifnextchar[{\@getauthortwo}{\@getauthorone}}
\def \@getauthorone#1{\@getauthortwo[#1]{#1}}
\def \@getauthortwo[#1]#2{{%
    \global \@marksrequiredtrue%
    \global \let \latexand \and%
    \gdef \and{\unskip \space \@authorand \space \ignorespaces}%
    \gdef \@author{\if@@draft \strut \else #2\fi}%
    \def \thanks##1{\relax}%
    \def \\{\unskip \space \ignorespaces}%
    \@marksrequiredfalse%
    \xdef \@authorhead{\if@@draft \space \else #1\fi}%
}}
\def \@authorand{and}
\newcommand \address[1]{\gdef \@address{\if@@draft \strut \else #1\fi}}
\def \@firsthead{\relax}
\def \@keywords{\relax}
\newcommand \keywords[1]{\gdef \@keywords{#1}}
\newcommand \@afterabstract@keywords[1]{%
    \gdef \@keywords{#1}%
    \@dokeywords%
}
\newcommand \@dokeywords{%
    {\small \noindent \textbf{Keywords:} \@keywords \par}%
    \vspace{10\p@}%
    \hrule \@height 1\p@%
    \vspace{10\p@}%
    \global \let \keywords \@gobbleone%
}
\newcommand \trykeywords{%
    \if \relax \@keywords%
        \global \let \keywords \@afterabstract@keywords%
        \vspace{10\p@}%
        \hrule \@height 1\p@%
        \vspace{10\p@}%
    \else%
        \@dokeywords%
    \fi%
}
\renewcommand \part{}
\renewcommand \section{\@startsection {section}{1}{\z@}%
    {-10\p@ \@plus -3\p@ \@minus -2\p@}{6\p@ \@plus 1\p@ \@minus 1\p@}{\sffamily\Large}}
\renewcommand \subsection{\@startsection{subsection}{2}{\z@}%
    {-8\p@ \@plus -2\p@ \@minus -2\p@}{5\p@ \@plus 1\p@ \@minus 1\p@}{\sffamily\large\itshape}}
\renewcommand \subsubsection{\@startsection{subsubsection}{3}{\z@}%
    {-6\p@ \@plus -1 pt \@minus -1\p@}{4\p@ \@plus 1\p@ \@minus 1\p@}{\sffamily\large\itshape}}
\renewcommand \paragraph{\@startsection{paragraph}{4}{\z@}%
    {6\p@ \@plus 1\p@ \@minus -2\p@}{-1em}{\normalsize\bfseries}}
\renewcommand \subparagraph{\@startsection{subparagraph}{4}{\parindent}%
    {6\p@ \@plus 1\p@ \@minus 2\p@}{-1em}{\normalsize\bfseries}}
\renewcommand \appendix{%
    \par%
    \setcounter{section}{0}%
    \setcounter{subsection}{0}%
    \gdef \thesection{\Alph{section}}%
}
\renewcommand \footnoterule{\kern-3\p@ \hrule \@height 0.8\p@ \kern 2.2\p@}
\long \def \@makefntext#1{\hangindent 7\p@$^{\textrm{\@thefnmark}}$ #1}
\renewcommand \thefootnote{\fnsymbol{footnote}}
\long \def \@makecaption#1#2{%
    \vskip \abovecaptionskip%
    \small%
    \sbox \@tempboxa{\textbf{#1:} #2}%
    \ifdim \wd \@tempboxa > \hsize%
        \textbf{#1:} #2%
        \par%
    \else%
        \global \@minipagefalse%
        \hb@xt@ \hsize{\hfil \box\@tempboxa \hfil}%
    \fi%
    \vskip \belowcaptionskip%
}
\renewcommand \maketitle{\par%
    \begingroup%
        \def \thefootnote{\fnsymbol{footnote}}%
        \def \@makefnmark{\hb@xt@ \z@{$\m@th^{\@thefnmark}$\hss}}%
        \long \def \@makefntext##1{\parindent 1em\noindent
            \hb@xt@ 1.8em{\hss $\m@th^{\@thefnmark}$}##1}%
        \setcounter{footnote}{1}%
        \newpage%
        \global \@topnum \z@%
        \@maketitle%
        \thispagestyle{first}%
        \@thanks%
    \endgroup%
    \global \let \maketitle \relax%
    \global \let \@maketitle \relax%
    \gdef \@thanks{}%
    \gdef \@address{}%
    \gdef \@author{}%
    \gdef \@title{}%
    \global \let \thanks \relax%
}
\newenvironment{titlesp}{%
    \list{}{\leftmargin \z@}\item[]%
}{\endlist}
\def \@maketitle{%
    \newpage%
    \null%
    \begin{titlesp}%
        {\sffamily \raggedright \hyphenpenalty\@M \huge \textit{\@title} \par}%
        \vspace{16\p@}%
        {\Large \@author \par}%
        \vspace{6\p@}%
        {\small \itshape \@address \par}%
        \vspace{6\p@}%
        \vspace{8\p@}%
        \hrule \@height 1\p@%
\vspace{2\p@}%
    \end{titlesp}%
}
\renewenvironment{abstract}{%
    \begin{titlesp}%
        \small%
}{%
    \end{titlesp}%
    \trykeywords%
}
\newcommand \noabstract{\trykeywords}
\def \ps@first{%
    \let \@mkboth \@gobbletwo%
    \def \@oddhead{\normalfont \@firsthead \hss}%
    \def \@oddfoot{%
        \vbox to \z@{%
            \hb@xt@ \textwidth{\footnotesize%
              \hss}%
            \if@@draft \@typesetdetails \fi%
            \vss%
        }%
    }%
    \let \@evenhead \@oddhead%
    \let \@evenfoot \@oddfoot%
    \let \sectionmark \@gobble%
    \let \subsectionmark \@gobble%
}
\def \ps@journal{%
    \let \@mkboth \@gobbletwo%
    \def \@oddhead{%
\normalsize%
\ifodd \c@page%
    \textit{\@titlehead} \hfill% \textrm{\thepage}%
\else%
            %\textrm{\thepage}
            \hfill \textit{\@authorhead}%
        \fi%
    }
    \def \@oddfoot{\vbox to \z@{\if@@draft \@typesetdetails \fi \vss}}%
    \let \@evenhead \@oddhead%
    \let \@evenfoot \@oddfoot%
    \let \sectionmark \@gobble%
    \let \subsectionmark \@gobble%
}
\pagestyle{journal}
\let \ps@plain \ps@journal
\let \ps@myheadings \ps@journal
\let \ps@headings \ps@journal
\flushbottom
\newcommand{\qed}{\hfill$\Box$}
\endinput
%%
%% End of file `dmtcs.cls'.

