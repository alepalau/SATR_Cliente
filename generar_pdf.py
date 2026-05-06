# -*- coding: utf-8 -*-
# Copyright (C) 2026  Alejandro Javier Palau <alepalau@codice.net.ar>
#
# Este programa es software libre: puedes redistribuirlo y/o modificarlo 
# bajo los términos de la Licencia Pública General GNU publicada por 
# la Free Software Foundation, ya sea la versión 3 de la Licencia, o 
# (a tu elección) cualquier versión posterior.
#
# Este programa se distribuye con la esperanza de que sea útil, 
# pero SIN NINGUNA GARANTÍA; incluso sin la garantía implícita de 
# COMERCIALIZACIÓN o APTITUD PARA UN PROPÓSITO PARTICULAR. 
# Para más detalles, consulta la Licencia Pública General GNU.
#
# Deberías haber recibido una copia de la Licencia Pública General GNU 
# junto con este programa. Si no, consulta <https://gnu.org>.

from weasyprint import HTML

# Leer plantilla
with open("plantilla.html", "r", encoding="utf-8") as f:
    html = f.read()

# Reemplazar datos dinámicos
html = html.replace("{{chofer}}", "Juan Pérez")
html = html.replace("{{fecha}}", "25/03/2026")

# Generar PDF
HTML(string=html, base_url=".").write_pdf("reporte.pdf")

print("PDF generado!")