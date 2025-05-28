# Here are all the important parameters for the snow profile processing

LABELS = {
    "not_labelled": 0,
    "surface": 1,
    "ground": 2,
    "pp": 3,
    "ppgp": 4,
    "df": 5,
    "rg": 6,
    "fc": 7,
    "dh": 8,
    "sh": 9,
    "fcxr": 10,
    "mf": 11,
    "mfcr": 12,
    "if": 13
}

LABELS_LONG = {
    0: "Not labelled",
    1: "Surface",
    2: "Ground",
    3: "Precip. particles",  #new wording from json "Precipitation particles",
    4: "Graupel",
    5: "Decomp. / fragm.",  #new wording from json "Decomposing and fragmented\nprecipitation particles",
    6: "Rounded grains",
    7: "Faceted crystals",
    8: "Depth hoar",
    9: "Surface hoar",
    10: "Rounding faceted particles",
    11: "Melt forms",
    12: "Melt-freeze crust",
    13: "Ice formations"
}

COLORS = {
    0: "dimgray",
    1: "chocolate",
    2: "darkslategrey",
    3: "#00FF00",
    4: "#808080",
    5: "#228B22",
    6: "#FFB6C1",
    7: "#ADD8E6",
    8: "#0000FF",
    9: "#FF00FF",
    10: "#D6C7D4", # mixture of fc and rg
    11: "#FF0000",
    12: "#890000", # mixture of mf (red) and stripes (C40000) should be changed in red with vertical stripes
    13: "#00FFFF"
}