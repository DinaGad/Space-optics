\NeedsTeXFormat{LaTeX2e}
\ProvidesClass{KAIST-slide}[A KAIST LaTeX Slide Template]
%-----------------------------------------------------------------------------------------------
%For 4:3 slides: \LoadClass{beamer}
\LoadClass[aspectratio=1610]{beamer}
\RequirePackage{calc}
\RequirePackage{environ}
\RequirePackage{svg}
\RequirePackage{tikz}
\usetikzlibrary{positioning}
%-----------------------------------------------------------------------------------------------
% Font: https://tug.org/FontCatalogue/texgyreheros/
% TODO: Maybe find a better font sometime later.
\RequirePackage{tgheros}
\renewcommand*\familydefault{\sfdefault}
\RequirePackage[T1]{fontenc}
\RequirePackage{background} % Ensure compatibility with legacy package
%\usepackage{atbegshi} % Use LaTeX-native functionality instead
%-----------------------------------------------------------------------------------------------
% Color
\definecolor{kaist-gold}{RGB}{206, 184, 144}
\definecolor{kaist-dust}{RGB}{234, 216, 158}
\definecolor{kaist-field}{RGB}{220, 184, 68}
\definecolor{kaist-rush}{RGB}{218, 170, 0}
\definecolor{kaist-aged}{RGB}{142, 111, 62}
\definecolor{kaist-steam}{RGB}{196, 191, 192}
\definecolor{kaist-railway-gray}{RGB}{157, 151, 149}
\definecolor{kaist-cool-gray}{RGB}{111, 114, 123}
\definecolor{kaist-steel}{RGB}{85, 89, 96}
%-----------------------------------------------------------------------------------------------
%Disable navigation symbols
\setbeamertemplate{navigation symbols}{}
%-----------------------------------------------------------------------------------------------
% Draw background
\setbeamertemplate{background canvas}{
    \begin{tikzpicture}[remember picture,overlay,shift=(current page.north west)]
    \begin{scope}[x={(current page.north east)},y={(current page.south west)}]
        \draw[kaist-field,line width=.5pt] (0.01,0) -- (0.01,0.95);
        \draw[kaist-field,line width=.5pt] (0.995,1) -- (0.995,0.35);
        \draw[kaist-field,line width=.5pt] (0.665,1) -- (0.665,0.84);
        \fill[teal] (0.0150,0) rectangle (1,0.08);
    \end{scope}
    \end{tikzpicture}
}
%-----------------------------------------------------------------------------------------------
% Customize Margin
\setbeamersize{text margin left=.16\paperwidth,text margin right=.10\paperwidth}
%-----------------------------------------------------------------------------------------------
% Customize title
\setbeamercolor{frametitle}{fg=kaist-dust}
\newlength{\titlevspace}
\setlength{\titlevspace}{\dimexpr.11\paperheight - 30pt\relax}
\setbeamertemplate{frametitle}{\vspace*{\titlevspace}
    \fontsize{12}{14}\fontseries{bc}\fontshape{}\selectfont\insertframetitle}
%-----------------------------------------------------------------------------------------------
% Customize footnote
\newcommand{\slidelogo}{}
\newcommand{\slidefoot}{}
\setbeamertemplate{footline}
{
    \hspace*{.2\paperwidth}
    \includesvg[width=.05\paperwidth,keepaspectratio]{\slidelogo}
    \makebox[.3\paperwidth][c]{\slidefoot}
    \hspace*{.05\paperwidth}
    \insertdate\hspace{.1\paperwidth}\insertframenumber
    \vspace*{.03\paperheight}
}
%-----------------------------------------------------------------------------------------------
% Customize enumerate/itemize style
% \setbeamerfont*{enumerate item}{series=\bfseries}
% \setbeamerfont*{enumerate subitem}{series=\bfseries}
% \setbeamerfont*{enumerate subsubitem}{series=\bfseries}
% \setbeamercolor*{enumerate item}{fg=black}
% \setbeamercolor*{enumerate subitem}{fg=black}
% \setbeamercolor*{enumerate subsubitem}{fg=black}

% \setbeamercolor*{itemize item}{fg=black}
% \setbeamercolor*{itemize subitem}{fg=black}
% \setbeamercolor*{itemize subsubitem}{fg=black}
% \setbeamertemplate{itemize items}[square]
%-----------------------------------------------------------------------------------------------
% Customize block style:
\setbeamercolor{block body}{bg=kaist-aged}
\setbeamercolor{block title}{bg=kaist-aged, fg=white}
\setbeamercolor{block body example}{bg=kaist-steam}
\setbeamercolor{block title example}{bg=kaist-steel, fg=white}
\setbeamercolor{block body alerted}{bg=alerted text.fg!10}
\setbeamercolor{block title alerted}{bg=alerted text.fg!20}
%-----------------------------------------------------------------------------------------------
% Customize figure tyle:
\setbeamercolor{caption name}{fg=kaist-field}
%-----------------------------------------------------------------------------------------------
% Customize title page style
\setbeamercolor*{title}{fg=kaist-field}
\setbeamerfont*{title}{size={\fontsize{17}{22}}, series=\fontseries{bc}, shape=\fontshape{}}
\setbeamercolor*{subtitle}{fg=cyan}
\setbeamerfont*{subtitle}{size={\fontsize{12}{16}}, series=\fontseries{bc}, shape=\fontshape{}}
\setbeamercolor*{author}{fg=blue}
\setbeamerfont*{author}{size={\fontsize{12}{14}}, series=\fontseries{bc}, shape=\fontshape{}}
\defbeamertemplate*{title page}{customized}[1][]
{
    \usebeamerfont{title}\usebeamercolor[fg]{title}
    \inserttitle\par
    \bigskip
    \usebeamerfont{subtitle}\usebeamercolor[fg]{subtitle}
    \hfill\insertsubtitle\par
    \bigskip
    \usebeamerfont{author}\usebeamercolor[fg]{author}
    \insertauthor\par
    \insertinstitute\par
    \insertdate\par
}
%-----------------------------------------------------------------------------------------------
\newcommand{\titlelogo}{}
\NewEnviron{titleframe}[1]{
    {
        \setbeamertemplate{background canvas}{
            \begin{tikzpicture}[remember picture,overlay,shift=(current page.north west)]
            \begin{scope}[x={(current page.north east)},y={(current page.south west)}]
                \fill[white] (0,0) rectangle (1,1);
                \draw[kaist-cool-gray,line width=.5pt] (0.1,0) -- (0.1,0.95);
                \draw[kaist-cool-gray,line width=.5pt] (0.9,1) -- (0.9,0.25);
                \draw[kaist-cool-gray,line width=.5pt] (0.70,1) -- (0.70,0.82);
            \end{scope}
            \end{tikzpicture}
        }
        \setbeamercolor{footline}{fg=white}
        \setbeamertemplate{footline}{
            \hspace*{.12\paperwidth}
            \includesvg[width=.3\paperwidth,keepaspectratio]{\titlelogo}
            \makebox[.3\paperwidth][c]{\slidefoot}
            \hspace*{.025\paperwidth}
            \insertdate\hspace{.03\paperwidth}\insertframenumber
            \vspace*{.06\paperheight}
        }
        \setbeamertemplate{frametitle}{\vspace*{.25\paperheight}
            \fontsize{24}{30}\fontseries{bc}\fontshape{it}\selectfont\insertframetitle}
        \setbeamercolor{normal text}{fg=white}
        \setbeamercolor{item}{fg=white}
        \begin{frame}{#1}
            \usebeamercolor[fg]{normal text}
            \BODY
        \end{frame}
    }
}
%-----------------------------------------------------------------------------------------------
% Customize other page styles:
\NewEnviron{notitleframe}{
    {
        \setbeamertemplate{background canvas}{
            \begin{tikzpicture}[remember picture,overlay,shift=(current page.north west)]
            \begin{scope}[x={(current page.north east)},y={(current page.south west)}]
                \draw[kaist-gold,line width=.5pt] (0.1,0) -- (0.1,0.95);
                \draw[kaist-gold,line width=.5pt] (0.9,1) -- (0.9,0.25);
                \draw[kaist-gold,line width=.5pt] (0.72,1) -- (0.72,0.84);
            \end{scope}
            \end{tikzpicture}
        }
        \begin{frame}
            \usebeamercolor[fg]{normal text}
            \BODY
        \end{frame}
    }
}
