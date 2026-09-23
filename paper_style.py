"""
Matplotlib-Stil passend zur Copernicus-LaTeX-Vorlage (The Cryosphere, copernicus.cls v10.1.31).

Aus der Vorlage abgeleitet:
  - Schrift:        Times (copernicus.cls laedt \\usepackage{times}), Grundgroesse 10 pt
  - Bildunterschr.: \\small = 9 pt
  - Satzspiegel:    \\textwidth = 177 mm, im Endsatz zweispaltig mit \\columnsep = 7 mm
                    -> \\columnwidth = 85 mm
  - Farben:         identisch zu den TikZ-Workflow-Grafiken (fig_workflow2.tex)

Abweichend von einer reinen Kopiervorlage:
  - Tick-Richtung "in" statt "out" und geschlossener Rahmen (alle vier Spines
    sichtbar), damit der Stil zu den bereits bestehenden Paper-Abbildungen passt.

Verwendung:
    import matplotlib.pyplot as plt
    from paper_style import set_paper_style, figsize, C

    set_paper_style(usetex=True)            # oder usetex=False ohne LaTeX-Installation
    fig, ax = plt.subplots(figsize=figsize("text", 0.85, aspect=0.45))
    ax.plot(x, y, color=C["mainblue"])
    fig.savefig("fig_xyz.pdf")              # KEIN bbox_inches="tight", sonst aendert sich die Breite

In LaTeX dann mit genau der gleichen Breite einbinden:
    \\includegraphics[width=0.85\\textwidth]{figures/fig_xyz.pdf}
"""

import matplotlib as mpl

MM = 1 / 25.4  # mm -> inch

# Breiten aus copernicus.cls (Endsatz)
TEXTWIDTH_MM = 177.0     # figure*  / \textwidth
COLUMNWIDTH_MM = 85.0    # figure   / \columnwidth  (177 - 7) / 2

# Farben aus fig_workflow2.tex
C = {
    "mainblue":    "#5A7896",  # RGB 90,120,150
    "mainorange":  "#B47846",  # RGB 180,120,70
    "lightblue":   "#E6EEF5",  # RGB 230,238,245
    "lightorange": "#F5EBE1",  # RGB 245,235,225
    "lightgray":   "#F5F5F5",  # RGB 245,245,245
    "gray":        "#808080",  # entspricht TikZ black!50
    "black":       "#000000",
}


def figsize(width="column", frac=1.0, aspect=0.62):
    """Figurgroesse in Zoll.

    width:  "column" (85 mm), "text" (177 mm) oder eine Zahl in mm
    frac:   Anteil davon, z. B. 0.85 fuer width=0.85\\textwidth
    aspect: Hoehe / Breite
    """
    if width == "column":
        w = COLUMNWIDTH_MM
    elif width == "text":
        w = TEXTWIDTH_MM
    else:
        w = float(width)
    w *= frac
    return (w * MM, w * aspect * MM)


def set_paper_style(usetex=True):
    """Setzt die rcParams. usetex=True braucht eine lokale LaTeX-Installation
    und liefert exakt dieselben Schriften wie das Paper."""
    rc = {
        # --- Schriftgroessen: \small (9 pt) wie Bildunterschrift & TikZ-Grafiken
        "font.size": 9,
        "axes.labelsize": 9,
        "axes.titlesize": 9,
        "legend.fontsize": 8,
        "xtick.labelsize": 8,
        "ytick.labelsize": 8,
        "figure.titlesize": 9,

        # --- Linien & Achsen, dezent passend zu 10-pt-Text
        "axes.linewidth": 0.6,
        "axes.edgecolor": "black",
        "axes.labelcolor": "black",
        "axes.titleweight": "bold",
        "axes.spines.top": True,
        "axes.spines.right": True,
        "axes.prop_cycle": mpl.cycler(color=[C["mainblue"], C["mainorange"],
                                             "#6E8B5A", "#8C6E96", C["gray"]]),
        "lines.linewidth": 1.0,
        "lines.markersize": 3,
        "patch.linewidth": 0.6,
        "xtick.major.width": 0.6,
        "ytick.major.width": 0.6,
        "xtick.minor.width": 0.4,
        "ytick.minor.width": 0.4,
        "xtick.major.size": 3,
        "ytick.major.size": 3,
        "xtick.direction": "in",
        "ytick.direction": "in",
        "grid.linewidth": 0.4,
        "grid.color": "#D0D0D0",
        "legend.frameon": False,
        "legend.handlelength": 1.5,

        # --- Layout & Export
        "figure.constrained_layout.use": True,
        "savefig.dpi": 600,          # nur relevant fuer Rasterelemente/PNG
        "savefig.bbox": None,        # Breite bleibt exakt wie in figsize()
        "savefig.pad_inches": 0.01,
        "pdf.fonttype": 42,          # TrueType statt Type-3 einbetten
        "ps.fonttype": 42,
    }

    if usetex:
        rc.update({
            "text.usetex": True,
            "font.family": "serif",
            # dieselben Pakete wie copernicus.cls -> identische Glyphen
            "text.latex.preamble": r"\usepackage{times}"
                                   r"\usepackage{amsmath}\usepackage{siunitx}",
        })
    else:
        rc.update({
            "text.usetex": False,
            "font.family": "serif",
            "font.serif": ["Times New Roman", "TeX Gyre Termes", "Nimbus Roman",
                           "Times", "DejaVu Serif"],
            "mathtext.fontset": "stix",   # Times-aehnliche Formeln
        })

    mpl.rcParams.update(rc)


def panel_label(ax, label, x=-0.02, y=1.02):
    """(a), (b), ... wie im Fliesstext referenziert."""
    ax.text(x, y, f"({label})", transform=ax.transAxes,
            ha="right", va="bottom", fontsize=9, fontweight="bold")
