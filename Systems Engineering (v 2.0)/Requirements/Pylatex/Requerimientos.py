import csv
from collections import defaultdict
from pylatex import Document, Section, Subsection, Package, NoEscape, LongTable, MultiColumn

# Crear documento
doc = Document("Requerimientos")

# Paquetes de LaTeX necesarios
doc.packages.append(Package('inputenc', options='utf8'))
doc.packages.append(Package('fontenc', options='T1'))
doc.packages.append(Package('babel', options='spanish'))
doc.packages.append(Package('array'))
doc.packages.append(Package('float'))
doc.packages.append(Package('geometry', options='letterpaper,top=1.5cm,bottom=1.5cm,left=2.5cm,right=1.5cm'))

# Función para limpiar caracteres problemáticos
def limpiar_texto(cell):
    if cell is None:
        return ""
    return (cell.replace(" ", " ")   # espacio fino invisible → espacio normal
                .replace("±", "$\\pm$")
                .replace("°", "$^{\\circ}$")
                .replace("²", "$^2$")
                .replace("cm^2", "cm$^2$")
                .replace("%", "\\%")
                .replace("&", "\\&")
                .replace("_", "\\_")
                .replace("#", "\\#")
                .replace("{", "\\{")
                .replace("}", "\\}")
                )

# Clasificación dinámica por prefijo
clasificados = defaultdict(list)

# Leer CSV y clasificar
with open("requerimientos.csv", newline='', encoding='utf-8') as csvfile:
    reader = csv.DictReader(csvfile, delimiter=';')
    for row in reader:
        ident = limpiar_texto(row.get("Identificador"))
        desc = limpiar_texto(row.get("Descripción del requerimiento"))
        previo = limpiar_texto(row.get("RequisitoPrevio"))
        prefijo = ident.split("-")[0] if ident else "SIN_PREFIJO"
        clasificados[prefijo].append((ident, desc, previo))

# Descripciones por categoría
descripciones = {
    "R.SH": "Requerimientos de Stakeholders: necesidades generales.",
    "R.AVMS": "Requerimientos de variables medidas y especificaciones ambientales.",
    "R.PDS": "Requerimientos del sistema de potencia y energía.",
    "R.COMS": "Requerimientos de comunicaciones y transmisión de datos.",
    "R.CPU": "Requerimientos del procesamiento central y firmware.",
    "R.DT": "Requerimientos de sensores de temperatura seca.",
    "R.GB": "Requerimientos de sensores de temperatura de globo.",
    "R.UV": "Requerimientos de sensores de radiación ultravioleta.",
    "R.WS": "Requerimientos de sensores de velocidad del viento.",
    "R.STR": "Requerimientos de la estructura física del sistema.",
    "R.SDPS": "Requerimientos del servidor en la nube y procesamiento de datos.",
    "R.UICS": "Requerimientos de la interfaz de usuario y alertas."
}

# Función para subsección con tabla

def agregar_subseccion(doc, prefijo, requerimientos, primera=False):
    # Solo insertar salto de página si no es la primera subsección
    if not primera:
        doc.append(NoEscape(r"\newpage"))
    
    with doc.create(Subsection(f"Categoría {prefijo}")):
        descripcion = descripciones.get(prefijo, "Descripción no definida para esta categoría.")
        doc.append(descripcion + "\n\n")
        
        with doc.create(LongTable('|p{2cm}|p{9cm}|p{2.5cm}|')) as tabular:
            # Encabezado (se repite en todas las páginas)
            tabular.add_hline()
            tabular.add_row(("ID", "Descripción del requerimiento", "Requisito previo"))
            tabular.add_hline()
            tabular.end_table_header()
            
            # Pie de tabla (se repite en todas las páginas excepto la última)
            tabular.add_hline()
            tabular.add_row([MultiColumn(3, align='|r|', data="Continúa en la siguiente página...")])
            tabular.add_hline()
            tabular.end_table_footer()
            
            # Pie final (solo en la última página)
            tabular.add_hline()
            tabular.add_row([MultiColumn(3, align='|r|', data="Fin de la tabla")])
            tabular.add_hline()
            tabular.end_table_last_footer()
            
            # Filas de requerimientos
            for req in requerimientos:
                tabular.add_row(req)
                tabular.add_hline()


# Sección principal
with doc.create(Section("Lista de Requerimientos")):
    for i, (prefijo, reqs) in enumerate(clasificados.items()):
        agregar_subseccion(doc, prefijo, reqs, primera=(i==0))

# Generar archivo .tex (compilar luego con pdflatex)
doc.generate_pdf(clean_tex=False)
