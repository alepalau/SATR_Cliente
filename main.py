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

import flet as ft
from datetime import datetime
import os
import shutil
import urllib.request
import json
import threading

def main(page: ft.Page):
    page.window_width = 400
    page.window_height = 850
    page.window_resizable = False
    page.title = "SATR"
    page.bgcolor = "#000000"
    page.theme_mode = "dark"
    page.padding = 0
    page.scroll = None

    lista_viajes = []
    lista_gastos = []
    edit_idx_v = -1
    edit_idx_g = -1
    drawer_visible = False
    pdf_menu_visible = False
    generar_visible = False
    tel_visible = False

    # ------------------ AUSPICIANTE ------------------

    _AUSPICIANTE_URL = "https://satr.codice.net.ar/auspiciante.json"
    _auspiciante = {"splash1": "", "splash2": "", "cierre": "", "segundos": 5}

    def descargar_auspiciante():
        try:
            req = urllib.request.urlopen(_AUSPICIANTE_URL, timeout=5)
            datos = json.loads(req.read().decode("utf-8"))
            _auspiciante["splash1"] = datos.get("splash1", "")
            _auspiciante["splash2"] = datos.get("splash2", "")
            _auspiciante["cierre"] = datos.get("cierre", "")
            _auspiciante["segundos"] = int(datos.get("segundos", 5))
        except:
            pass

    descargar_auspiciante()

    # ------------------ FUNCIONES ------------------

    JORNADA_FILE = "jornada_actual.json"

    def guardar_jornada():
        import json
        try:
            datos = {
                "chofer": ent_chofer.value,
                "patente": ent_patente.value,
                "km_ini": ent_km_ini.value,
                "km_fin": ent_km_fin.value,
                "hora_ini": ent_hora_ini.value,
                "hora_fin": ent_hora_fin.value,
                "p_age": ent_p_age.value,
                "p_cho": ent_p_cho.value,
                "viajes": lista_viajes,
                "gastos": lista_gastos,
            }
            with open(JORNADA_FILE, "w", encoding="utf-8") as f:
                json.dump(datos, f, ensure_ascii=False)
        except:
            pass

    def cargar_jornada():
        import json
        try:
            if not os.path.exists(JORNADA_FILE):
                return
            with open(JORNADA_FILE, "r", encoding="utf-8") as f:
                datos = json.load(f)
            lista_viajes.clear()
            lista_gastos.clear()
            lista_viajes.extend(datos.get("viajes", []))
            lista_gastos.extend(datos.get("gastos", []))
            ent_chofer.value = datos.get("chofer", "")
            ent_patente.value = datos.get("patente", "")
            ent_km_ini.value = datos.get("km_ini", "")
            ent_km_fin.value = datos.get("km_fin", "")
            ent_hora_ini.value = datos.get("hora_ini", "")
            ent_hora_fin.value = datos.get("hora_fin", "")
            ent_p_age.value = datos.get("p_age", "0")
            ent_p_cho.value = datos.get("p_cho", "0")
        except:
            try:
                os.remove(JORNADA_FILE)
            except:
                pass

    def abrir_menu(e):
        nonlocal drawer_visible
        drawer_visible = not drawer_visible
        drawer_container.visible = drawer_visible
        page.update()

    def toggle_pdf_menu(e):
        nonlocal pdf_menu_visible
        pdf_menu_visible = not pdf_menu_visible
        pdf_submenu.visible = pdf_menu_visible
        page.update()

    def toggle_generar(e):
        nonlocal generar_visible
        generar_visible = not generar_visible
        pdf_submenu_generar.visible = generar_visible
        page.update()

    def calcular_horas_trabajadas():
        """Devuelve (horas_float, texto_legible) o (0, '') si no hay datos."""
        try:
            hi = ent_hora_ini.value.strip()
            hf = ent_hora_fin.value.strip()
            if not hi or not hf:
                return 0, ""
            fmt = "%H:%M"
            t_ini = datetime.strptime(hi, fmt)
            t_fin = datetime.strptime(hf, fmt)
            delta = t_fin - t_ini
            if delta.total_seconds() < 0:
                delta_seg = delta.total_seconds() + 86400  # turno nocturno
            else:
                delta_seg = delta.total_seconds()
            horas_tot = delta_seg / 3600
            horas_int = int(delta_seg // 3600)
            minutos_int = int((delta_seg % 3600) // 60)
            texto = f"{horas_int}h {minutos_int:02d}m"
            return horas_tot, texto
        except:
            return 0, ""

    def formato_moneda(valor):
        s = f"{valor:,.2f}"
        return s.replace(",", "X").replace(".", ",").replace("X", ".")

    def formatear_entrada(e):
        try:
            valor_limpio = "".join(c for c in e.control.value if c in "0123456789")
            if valor_limpio:
                valor_int = int(valor_limpio)
                e.control.value = f"{valor_int:,}".replace(",", ".")
            else:
                e.control.value = ""
            page.update()
        except:
            e.control.value = ""
            page.update()

    def formatear_hora(e):
        """Agrega los dos puntos automáticamente mientras escribe la hora"""
        valor = "".join(c for c in e.control.value if c.isdigit())
        valor = valor[:4]
        if len(valor) >= 3:
            valor_formateado = f"{valor[:2]}:{valor[2:]}"
        else:
            valor_formateado = valor
        if valor_formateado != e.control.value:
            e.control.value = valor_formateado
            page.update()

    def cerrar_msg(dlg):
        dlg.open = False
        page.update()

    def mostrar_mensaje(texto):
        dlg = ft.AlertDialog(content=ft.Text(texto), actions=[ft.TextButton("OK", on_click=lambda e: cerrar_msg(dlg))])
        page.overlay.append(dlg)
        dlg.open = True
        page.update()

    def cargar_tel(clave, default=""):
        try:
            with open(f"tel_{clave}.txt", "r") as f:
                return f.read().strip()
        except:
            return default

    def guardar_tel(clave, valor):
        try:
            with open(f"tel_{clave}.txt", "w") as f:
                f.write(valor)
        except:
            pass

    def guardar_chofer(e):
        try:
            with open("chofer.txt", "w") as f:
                f.write(e.control.value)
        except:
            pass

    def abrir_link(url):
        async def _abrir(e):
            await page.launch_url(url)
        return _abrir

    def llamar(numero):
        async def _llamar(e):
            await page.launch_url(f"tel:{numero}")
        return _llamar

    # ------------------ PDF ------------------

    # Ruta de assets — confirmada en Android
    _ASSETS_DIR = "/data/user/0/com.codice.satr.satr_final/files/flet/app/assets"
    if not os.path.exists(_ASSETS_DIR):
        _ASSETS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")
    if not os.path.exists(_ASSETS_DIR):
        _ASSETS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets")

    import io
    def _img_buf(nombre):
        # Intentar JPEG primero (funciona sin Pillow), luego PNG
        nombre_jpg = nombre.replace(".png", ".jpg")
        for n in [nombre_jpg, nombre]:
            ruta = os.path.join(_ASSETS_DIR, n)
            if os.path.exists(ruta):
                return io.BytesIO(open(ruta, "rb").read())
        return None

    def generar_pdf():
        try:
            from fpdf import FPDF

            chofer = ent_chofer.value.upper()
            patente = ent_patente.value.upper()

            rec = sum(v["monto"] for v in lista_viajes)
            efectivo = sum(v["monto"] for v in lista_viajes if v["tipo"] == "EFECTIVO")
            transferencia = sum(v["monto"] for v in lista_viajes if v["tipo"] == "TRANSFERENCIA")

            c_age = (rec * (float(ent_p_age.value.replace(",", ".")) if ent_p_age.value else 0)) / 100
            g_cho = (rec * (float(ent_p_cho.value.replace(",", ".")) if ent_p_cho.value else 0)) / 100
            g_var = sum(g['monto'] for g in lista_gastos if g['desc'] not in ["AGENCIA", "CHOFER"])

            neto = rec - c_age - g_cho - g_var

            try:
                km_ini = float(ent_km_ini.value.replace(".", "")) if ent_km_ini.value else 0
                km_fin = float(ent_km_fin.value.replace(".", "")) if ent_km_fin.value else 0
                kms = km_fin - km_ini
                rendimiento = rec / kms if kms > 0 else 0
            except:
                kms = 0
                rendimiento = 0

            horas_float, horas_texto = calcular_horas_trabajadas()

            os.makedirs("pdfs", exist_ok=True)
            nombre = os.path.join("pdfs", f"SATR_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.pdf")

            class SATRDoc(FPDF):
                def header(self):
                    self.set_xy(10, 1)
                    self.set_font("Helvetica", "", 7)
                    self.set_text_color(100, 100, 100)
                    self.cell(0, 4, "satr.codice.net.ar", align="R", ln=True)
                    self.set_draw_color(187, 187, 187)
                    self.set_line_width(0.5)
                    self.line(10, 5, 200, 5)
                    try:
                        buf = _img_buf("membrete.png")
                        if buf:
                            self.image(buf, x=178, y=7, w=20, type="JPEG")
                    except Exception:
                        pass
                    try:
                        buf = _img_buf("fondoPDF.png")
                        if buf:
                            self.image(buf, x=55, y=100, w=100, type="JPEG")
                    except Exception:
                        pass
                    self.line(10, 30, 200, 30)
                    self.set_xy(10, 33)

                def footer(self):
                    self.set_draw_color(187, 187, 187)
                    self.set_line_width(0.5)
                    self.line(10, 255, 200, 255)
                    try:
                        buf = _img_buf("desarrollado.png")
                        if buf:
                            self.image(buf, x=60, y=258, w=80, type="JPEG")
                    except Exception:
                        pass
                    self.set_xy(10, 287)
                    self.set_font("Helvetica", "", 8)
                    self.set_text_color(100, 100, 100)
                    self.cell(0, 4, "codice.net.ar", align="C")

            pdf = SATRDoc()
            pdf.set_margins(10, 35, 10)
            pdf.set_auto_page_break(auto=True, margin=48)
            pdf.add_page()

            # Título
            pdf.set_font("Helvetica", "B", 16)
            pdf.set_text_color(0, 0, 0)
            pdf.cell(0, 10, "S.A.T.R. - REPORTE DE TURNO", align="C", ln=True)

            # Fecha
            pdf.set_font("Helvetica", "", 11)
            pdf.set_text_color(85, 85, 85)
            pdf.cell(0, 8, f"Fecha: {datetime.now().strftime('%d/%m/%Y')}", align="C", ln=True)
            pdf.ln(3)

            # Chofer y patente
            pdf.set_font("Helvetica", "B", 11)
            pdf.set_text_color(0, 0, 0)
            pdf.cell(0, 7, f"Chofer:   {chofer}", ln=True)
            pdf.cell(0, 7, f"Patente:  {patente}", ln=True)

            pdf.set_draw_color(187, 187, 187)
            pdf.line(10, pdf.get_y() + 2, 200, pdf.get_y() + 2)
            pdf.ln(6)

            # Función para fila de resumen
            def fila(label, valor, bold=False):
                pdf.set_font("Helvetica", "B" if bold else "", 11)
                pdf.cell(140, 7, label)
                pdf.cell(50, 7, f"$ {valor}", align="R", ln=True)

            fila("RECAUDACION TOTAL:", formato_moneda(rec))
            fila("EFECTIVO:", formato_moneda(efectivo))
            fila("TRANSFERENCIA:", formato_moneda(transferencia))
            fila("COMISION AGENCIA:", formato_moneda(c_age))
            fila("GANANCIA CHOFER:", formato_moneda(g_cho))
            fila("TOTAL DE GASTOS:", formato_moneda(g_var))

            pdf.set_draw_color(0, 0, 0)
            pdf.line(10, pdf.get_y() + 1, 200, pdf.get_y() + 1)
            pdf.ln(4)
            fila("NETO TITULAR:", formato_moneda(neto), bold=True)
            pdf.ln(4)

            # Km, horas y rendimiento
            pdf.set_font("Helvetica", "", 11)
            pdf.cell(0, 7, f"KILOMETROS RECORRIDOS: {formato_moneda(kms)}", ln=True)
            pdf.cell(0, 7, f"RENDIMIENTO POR KM: $ {formato_moneda(rendimiento)}", ln=True)
            if horas_texto:
                ganancia_x_hora = neto / horas_float if horas_float > 0 else 0
                pdf.cell(0, 7, f"HORAS TRABAJADAS: {horas_texto}", ln=True)
                pdf.cell(0, 7, f"GANANCIA PROMEDIO POR HORA: $ {formato_moneda(ganancia_x_hora)}", ln=True)
            pdf.ln(4)

            # Detalle viajes
            pdf.set_font("Helvetica", "B", 12)
            pdf.cell(0, 8, "Detalle de Viajes", ln=True)
            pdf.set_font("Helvetica", "", 10)
            for i, v in enumerate(lista_viajes, start=1):
                hora_str = f" [{v['hora']}]" if v.get('hora') else ""
                pdf.cell(0, 6, f"  Viaje {i}{hora_str} ({v['tipo']}): $ {formato_moneda(v['monto'])}", ln=True)

            pdf.ln(3)

            # Detalle gastos
            pdf.set_font("Helvetica", "B", 12)
            pdf.cell(0, 8, "Detalle de Gastos", ln=True)
            pdf.set_font("Helvetica", "", 10)
            for i, g in enumerate(lista_gastos, start=1):
                pdf.cell(0, 6, f"  Gasto {i} ({g['desc']}): $ {formato_moneda(g['monto'])}", ln=True)

            pdf.output(nombre)

            # Guardar JSON sidecar
            import json
            datos_jornada = {
                "fecha": datetime.now().strftime('%Y-%m-%d'),
                "chofer": chofer,
                "patente": patente,
                "recaudacion": rec,
                "efectivo": efectivo,
                "transferencia": transferencia,
                "comision_agencia": c_age,
                "gasto_chofer": g_cho,
                "gastos_varios": g_var,
                "neto": neto,
                "kms": kms,
                "horas_trabajadas": round(horas_float, 2),
            }
            nombre_json = nombre.replace(".pdf", ".json")
            with open(nombre_json, "w", encoding="utf-8") as fj:
                json.dump(datos_jornada, fj, ensure_ascii=False)

            # Copiar solo el PDF a Downloads (el JSON queda interno)
            nombre_base = os.path.basename(nombre)
            carpeta_downloads = "/storage/emulated/0/Download/SATR_PDFs"
            try:
                os.makedirs(carpeta_downloads, exist_ok=True)
                destino = os.path.join(carpeta_downloads, nombre_base)
                shutil.copy2(nombre, destino)
                ruta_final = destino
            except Exception:
                ruta_final = os.path.abspath(os.path.join("pdfs", nombre_base))

            def cerrar_dlg_pdf(dlg):
                dlg.open = False
                page.update()

            dlg_pdf = ft.AlertDialog(
                title=ft.Text("Reporte de turno", color="cyan", weight="bold"),
                content=ft.Column([
                    ft.Text("✓ Reporte generado", color="green", weight="bold", size=16),
                    ft.Text("Guardado en:", size=12),
                    ft.Text("Descargas → SATR_PDFs", color="cyan", size=12),
                    ft.Text(nombre_base, color="white", size=10),
                ], spacing=5),
                actions=[
                    ft.TextButton("Cerrar", on_click=lambda e: cerrar_dlg_pdf(dlg_pdf)),
                ]
            )
            page.overlay.append(dlg_pdf)
            dlg_pdf.open = True
            page.update()
        except Exception as ex:
            import traceback
            mostrar_mensaje(traceback.format_exc()[-400:])

    def generar_y_guardar_pdf(e):
        url_cierre = _auspiciante.get("cierre", "")
        if url_cierre:
            btn_cerrar_pub = ft.TextButton(
                "✕ Cerrar",
                visible=True,
                style=ft.ButtonStyle(color="white", bgcolor="#CC0000"),
            )
            pub_cierre = ft.Container(
                width=400,
                height=850,
                bgcolor="#000000",
                visible=True,
                content=ft.Stack([
                    ft.Image(src=url_cierre, width=400, height=850, fit="cover"),
                    ft.Container(
                        top=20,
                        right=10,
                        content=btn_cerrar_pub,
                    ),
                ])
            )
            def cerrar_publicidad(ev=None):
                page.overlay.remove(pub_cierre)
                page.update()
                generar_pdf()
            btn_cerrar_pub.on_click = cerrar_publicidad
            page.overlay.append(pub_cierre)
            page.update()
        else:
            generar_pdf()

    def abrir_pdf(nombre):
        nombre_base = os.path.basename(nombre)
        ruta_downloads = f"/storage/emulated/0/Download/SATR_PDFs/{nombre_base}"
        ruta_interna = os.path.abspath(os.path.join("pdfs", nombre_base))
        ruta_final = ruta_downloads if os.path.exists(ruta_downloads) else ruta_interna
        def _abrir(e):
            try:
                import subprocess
                subprocess.Popen([
                    "am", "start",
                    "-a", "android.intent.action.VIEW",
                    "-d", f"file://{ruta_final}",
                    "-t", "application/pdf"
                ])
            except Exception:
                mostrar_mensaje(f"Abrí el archivo desde:\nDescargas → SATR_PDFs\n\n{nombre_base}")
        return _abrir

    def buscar_pdf_por_fecha(e):
        def on_fecha_change(ev):
            valor = "".join(c for c in ev.control.value if c.isdigit())
            formateado = ""
            for i, c in enumerate(valor[:8]):
                if i == 2 or i == 4:
                    formateado += "-"
                formateado += c
            input_fecha.value = formateado
            page.update()

        def confirmar_fecha(ev):
            fecha_input = input_fecha.value.strip()
            resultados.controls.clear()
            try:
                partes = fecha_input.split("-")
                if len(partes) != 3 or len(partes[2]) != 4:
                    resultados.controls.append(ft.Text("Ingresá una fecha completa: DD-MM-YYYY"))
                    page.update()
                    return
                fecha_busqueda = f"{partes[2]}-{partes[1]}-{partes[0]}"
                carpeta = "/storage/emulated/0/Download/SATR_PDFs"
                if not os.path.exists(carpeta):
                    carpeta = os.path.abspath("pdfs")
                if not os.path.exists(carpeta):
                    resultados.controls.append(ft.Text("No hay PDFs guardados"))
                    page.update()
                    return
                archivos = os.listdir(carpeta)
                filtrados = [f for f in archivos if f.startswith(f"SATR_{fecha_busqueda}") and f.endswith(".pdf")]
                if not filtrados:
                    resultados.controls.append(ft.Text("No hay PDFs para esa fecha"))
                else:
                    for archivo in filtrados:
                        resultados.controls.append(
                            ft.TextButton(
                                archivo,
                                on_click=abrir_pdf(archivo)
                            )
                        )
                page.update()
            except Exception as ex:
                resultados.controls.append(ft.Text(f"Error: {ex}"))
                page.update()

        input_fecha = ft.TextField(
            label="Fecha (DD-MM-YYYY)",
            on_change=on_fecha_change,
            keyboard_type=ft.KeyboardType.NUMBER,
            max_length=10
        )
        resultados = ft.Column()

        dialog = ft.AlertDialog(
            title=ft.Text("Buscar PDF por fecha"),
            content=ft.Column([
                input_fecha,
                ft.ElevatedButton("Buscar", on_click=confirmar_fecha),
                resultados
            ], tight=True),
        )
        page.overlay.append(dialog)
        dialog.open = True
        page.update()

    def _estadisticas(e):
        import json

        def on_fecha_change_desde(ev):
            valor = "".join(c for c in ev.control.value if c.isdigit())
            formateado = ""
            for i, c in enumerate(valor[:8]):
                if i == 2 or i == 4:
                    formateado += "-"
                formateado += c
            input_desde.value = formateado
            page.update()

        def on_fecha_change_hasta(ev):
            valor = "".join(c for c in ev.control.value if c.isdigit())
            formateado = ""
            for i, c in enumerate(valor[:8]):
                if i == 2 or i == 4:
                    formateado += "-"
                formateado += c
            input_hasta.value = formateado
            page.update()

        def generar_reporte_estadisticas(desde_input, hasta_input, patente_filtro, resultados, dialog_estadisticas):
            try:
                def parsear_fecha(texto):
                    partes = texto.split("-")
                    if len(partes) != 3 or len(partes[2]) != 4:
                        return None
                    return f"{partes[2]}-{partes[1]}-{partes[0]}"

                fecha_desde = parsear_fecha(desde_input)
                fecha_hasta = parsear_fecha(hasta_input)

                if not fecha_desde or not fecha_hasta:
                    resultados.controls.append(ft.Text("Ingresá ambas fechas completas: DD-MM-YYYY"))
                    page.update()
                    return

                if fecha_desde > fecha_hasta:
                    resultados.controls.append(ft.Text("La fecha 'Desde' no puede ser mayor que 'Hasta'"))
                    page.update()
                    return

                carpeta_json = os.path.abspath("pdfs")
                if not os.path.exists(carpeta_json):
                    carpeta_json = "/storage/emulated/0/Download/SATR_PDFs"

                archivos_json = []
                if os.path.exists(carpeta_json):
                    archivos_json = [
                        f for f in os.listdir(carpeta_json)
                        if f.endswith(".json") and f.startswith("SATR_")
                    ]

                jornadas = []
                for archivo in archivos_json:
                    fecha_archivo = archivo.replace("SATR_", "")[:10]
                    if fecha_desde <= fecha_archivo <= fecha_hasta:
                        ruta = os.path.join(carpeta_json, archivo)
                        try:
                            with open(ruta, "r", encoding="utf-8") as fj:
                                datos = json.load(fj)
                                if patente_filtro == "" or datos.get("patente", "").upper() == patente_filtro:
                                    jornadas.append(datos)
                        except:
                            pass

                if not jornadas:
                    resultados.controls.append(ft.Text("No hay jornadas registradas en ese período"))
                    page.update()
                    return

                total_rec = sum(j["recaudacion"] for j in jornadas)
                total_ef = sum(j["efectivo"] for j in jornadas)
                total_tr = sum(j["transferencia"] for j in jornadas)
                total_age = sum(j["comision_agencia"] for j in jornadas)
                total_cho = sum(j["gasto_chofer"] for j in jornadas)
                total_var = sum(j["gastos_varios"] for j in jornadas)
                total_neto = sum(j["neto"] for j in jornadas)
                total_kms = sum(j["kms"] for j in jornadas)
                cant_jornadas = len(jornadas)

                os.makedirs("pdfs", exist_ok=True)
                sufijo_patente = f"_{patente_filtro}" if patente_filtro else ""
                nombre_estad = os.path.join("pdfs", f"SATR_Estadisticas_{fecha_desde}_{fecha_hasta}{sufijo_patente}.pdf")

                from fpdf import FPDF

                pdf = FPDF()
                pdf.add_page()

                def fmt(v):
                    s = f"{v:,.2f}"
                    return s.replace(",", "X").replace(".", ",").replace("X", ".")

                def fila_est(label, valor, color_val=(0,0,0), bold=False):
                    pdf.set_font("Helvetica", "B" if bold else "", 11)
                    pdf.set_text_color(0, 0, 0)
                    pdf.cell(0, 7, label, ln=False)
                    pdf.set_text_color(*color_val)
                    pdf.cell(0, 7, valor, ln=True, align="R")

                def linea_sep():
                    pdf.set_draw_color(187, 187, 187)
                    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
                    pdf.ln(3)

                pdf.set_font("Helvetica", "B", 18)
                pdf.cell(0, 10, "SATR - Estadisticas de periodo", ln=True)
                linea_sep()

                patente_texto = f"Patente: {patente_filtro}" if patente_filtro else "Todas las patentes"
                pdf.set_font("Helvetica", "", 10)
                pdf.cell(0, 7, f"Desde: {desde_input}  Hasta: {hasta_input}  {patente_texto}  Jornadas: {cant_jornadas}", ln=True)
                pdf.ln(3)

                pdf.set_font("Helvetica", "B", 13)
                pdf.cell(0, 8, "Recaudacion", ln=True)
                linea_sep()
                fila_est("Total recaudado:", f"$ {fmt(total_rec)}", (46,125,50), bold=True)
                fila_est("- Efectivo:", f"$ {fmt(total_ef)}")
                fila_est("- Transferencia:", f"$ {fmt(total_tr)}")
                pdf.ln(4)

                pdf.set_font("Helvetica", "B", 13)
                pdf.cell(0, 8, "Gastos", ln=True)
                linea_sep()
                fila_est("Comision agencia:", f"$ {fmt(total_age)}", (198,40,40))
                fila_est("Gastos chofer:", f"$ {fmt(total_cho)}", (198,40,40))
                fila_est("Gastos varios:", f"$ {fmt(total_var)}", (198,40,40))
                fila_est("Total gastos:", f"$ {fmt(total_age + total_cho + total_var)}", (198,40,40), bold=True)
                pdf.ln(4)

                pdf.set_font("Helvetica", "B", 13)
                pdf.cell(0, 8, "Resultado", ln=True)
                linea_sep()
                fila_est("Ganancia neta del periodo:", f"$ {fmt(total_neto)}", (46,125,50), bold=True)
                fila_est("Kilometros recorridos:", f"{fmt(total_kms)} km")

                pdf.output(nombre_estad)

                nombre_base = os.path.basename(nombre_estad)
                carpeta_downloads = "/storage/emulated/0/Download/SATR_Estadisticas"
                try:
                    os.makedirs(carpeta_downloads, exist_ok=True)
                    destino = os.path.join(carpeta_downloads, nombre_base)
                    shutil.copy2(nombre_estad, destino)
                    resultados.controls.append(ft.Text(f"✓ PDF generado con {cant_jornadas} jornadas", color="green"))
                    resultados.controls.append(ft.Text("Guardado en:\nDescargas → SATR_Estadisticas", color="cyan", size=12))
                except Exception:
                    resultados.controls.append(ft.Text(f"✓ PDF generado con {cant_jornadas} jornadas", color="green"))
                page.update()

            except Exception as ex:
                resultados.controls.append(ft.Text(f"Error: {ex}"))
                page.update()

        def calcular_estadisticas(ev):
            # Guardar los valores ingresados
            desde_input = input_desde.value.strip()
            hasta_input = input_hasta.value.strip()
            patente_filtro = input_patente.value.strip().upper()
            
            # Validar fechas básicas antes de mostrar publicidad
            def parsear_fecha_rapido(texto):
                partes = texto.split("-")
                if len(partes) != 3 or len(partes[2]) != 4:
                    return None
                return f"{partes[2]}-{partes[1]}-{partes[0]}"
            
            fecha_desde = parsear_fecha_rapido(desde_input)
            fecha_hasta = parsear_fecha_rapido(hasta_input)
            
            if not fecha_desde or not fecha_hasta:
                resultados.controls.append(ft.Text("Ingresá ambas fechas completas: DD-MM-YYYY"))
                page.update()
                return
            
            # Cerrar el diálogo de estadísticas
            dialog_estadisticas.open = False
            page.update()
            
            # Mostrar publicidad
            url_cierre = _auspiciante.get("cierre", "")
            if url_cierre:
                btn_cerrar_pub = ft.TextButton(
                    "✕ Cerrar",
                    visible=True,
                    style=ft.ButtonStyle(color="white", bgcolor="#CC0000"),
                )
                pub_cierre = ft.Container(
                    width=400,
                    height=850,
                    bgcolor="#000000",
                    visible=True,
                    content=ft.Stack([
                        ft.Image(src=url_cierre, width=400, height=850, fit="cover"),
                        ft.Container(
                            top=20,
                            right=10,
                            content=btn_cerrar_pub,
                        ),
                    ])
                )
                
                def cerrar_publicidad_y_generar(ev2=None):
                    page.overlay.remove(pub_cierre)
                    page.update()
                    # Crear nuevo diálogo para resultados
                    resultados_container = ft.Column()
                    dialog_resultados = ft.AlertDialog(
                        title=ft.Text("Estadísticas", color="cyan", weight="bold"),
                        content=ft.Container(
                            width=350,
                            height=400,
                            content=resultados_container,
                        ),
                        actions=[ft.TextButton("Cerrar", on_click=lambda x: cerrar_dialog_resultados(dialog_resultados))]
                    )
                    
                    def cerrar_dialog_resultados(dlg):
                        dlg.open = False
                        page.update()
                    
                    page.overlay.append(dialog_resultados)
                    dialog_resultados.open = True
                    page.update()
                    
                    # Generar el reporte
                    generar_reporte_estadisticas(desde_input, hasta_input, patente_filtro, resultados_container, dialog_resultados)
                    
                btn_cerrar_pub.on_click = cerrar_publicidad_y_generar
                page.overlay.append(pub_cierre)
                page.update()
            else:
                # Sin publicidad, mostrar resultados directamente
                resultados_container = ft.Column()
                dialog_resultados = ft.AlertDialog(
                    title=ft.Text("Estadísticas", color="cyan", weight="bold"),
                    content=ft.Container(
                        width=350,
                        height=400,
                        content=resultados_container,
                    ),
                    actions=[ft.TextButton("Cerrar", on_click=lambda x: cerrar_dialog_resultados(dialog_resultados))]
                )
                
                def cerrar_dialog_resultados(dlg):
                    dlg.open = False
                    page.update()
                
                page.overlay.append(dialog_resultados)
                dialog_resultados.open = True
                page.update()
                
                generar_reporte_estadisticas(desde_input, hasta_input, patente_filtro, resultados_container, dialog_resultados)

        input_desde = ft.TextField(
            label="Desde (DD-MM-YYYY)",
            on_change=on_fecha_change_desde,
            keyboard_type=ft.KeyboardType.NUMBER,
            max_length=10
        )
        input_hasta = ft.TextField(
            label="Hasta (DD-MM-YYYY)",
            on_change=on_fecha_change_hasta,
            keyboard_type=ft.KeyboardType.NUMBER,
            max_length=10
        )
        input_patente = ft.TextField(
            label="Patente (opcional)",
            hint_text="Dejar vacío para todas",
            capitalization=ft.TextCapitalization.CHARACTERS,
        )
        resultados = ft.Column()

        dialog_estadisticas = ft.AlertDialog(
            title=ft.Text("Estadísticas por período", color="cyan", weight="bold"),
            content=ft.Column([
                input_desde,
                input_hasta,
                input_patente,
                ft.ElevatedButton("Generar estadísticas", on_click=calcular_estadisticas),
                resultados
            ], tight=True),
        )
        page.overlay.append(dialog_estadisticas)
        dialog_estadisticas.open = True
        page.update()

    def abrir_tel_utiles(e):
        nonlocal tel_visible
        tel_visible = not tel_visible
        tel_submenu.visible = tel_visible
        page.update()

    def abrir_emergencias(e):
        emergencias = [
            ("Policía", "911"),
            ("Bomberos", "100"),
            ("Ambulancia / SAME", "107"),
            ("Defensa Civil", "103"),
        ]

        controles = [ft.Text("Emergencias", size=16, weight="bold", color="red")]
        for nombre, numero in emergencias:
            controles.append(
                ft.Row([
                    ft.Text(f"{nombre} — {numero}", expand=True),
                    ft.IconButton(
                        icon=ft.Icons.PHONE,
                        icon_color="green",
                        on_click=llamar(numero)
                    )
                ])
            )

        dialog = ft.AlertDialog(
            title=ft.Text("📞 Emergencias"),
            content=ft.Column(controles, tight=True),
            actions=[ft.TextButton("Cerrar", on_click=lambda e: cerrar_dialog(dialog))]
        )
        page.overlay.append(dialog)
        dialog.open = True
        page.update()

    def abrir_contacto_emergencia(e):
        numero_actual = cargar_tel("emergencia")
        campo = ft.TextField(
            label="Número de contacto",
            value=numero_actual,
            keyboard_type=ft.KeyboardType.PHONE,
        )

        def solo_guardar(ev):
            guardar_tel("emergencia", campo.value)
            cerrar_dialog(dialog)
            mostrar_mensaje("Número guardado")

        dialog = ft.AlertDialog(
            title=ft.Text("👤 Contacto de Emergencia"),
            content=ft.Column([campo], tight=True),
            actions=[
                ft.TextButton("Guardar", on_click=solo_guardar),
                ft.TextButton("Llamar", on_click=llamar(campo.value)),
                ft.TextButton("Cerrar", on_click=lambda e: cerrar_dialog(dialog)),
            ]
        )
        page.overlay.append(dialog)
        dialog.open = True
        page.update()

    def abrir_seguro(e):
        campos = {
            "comercial": ft.TextField(
                label="Comercial",
                value=cargar_tel("seguro_comercial"),
                keyboard_type=ft.KeyboardType.PHONE
            ),
            "siniestro": ft.TextField(
                label="Siniestro",
                value=cargar_tel("seguro_siniestro"),
                keyboard_type=ft.KeyboardType.PHONE
            ),
            "grua": ft.TextField(
                label="Grúa",
                value=cargar_tel("seguro_grua"),
                keyboard_type=ft.KeyboardType.PHONE
            ),
        }

        def guardar_seguro(ev):
            for clave, campo in campos.items():
                guardar_tel(f"seguro_{clave}", campo.value)
            cerrar_dialog(dialog)
            mostrar_mensaje("Números del seguro guardados")

        filas = [ft.Text("Seguro", size=16, weight="bold", color="cyan")]
        for clave, campo in campos.items():
            filas.append(
                ft.Row([
                    campo,
                    ft.IconButton(
                        icon=ft.Icons.PHONE,
                        icon_color="green",
                        on_click=llamar(campo.value)
                    )
                ])
            )

        dialog = ft.AlertDialog(
            title=ft.Text("🛡️ Seguro"),
            content=ft.Column(filas, tight=True),
            actions=[
                ft.TextButton("Guardar", on_click=guardar_seguro),
                ft.TextButton("Cerrar", on_click=lambda e: cerrar_dialog(dialog)),
            ]
        )
        page.overlay.append(dialog)
        dialog.open = True
        page.update()

    def abrir_acerca_de(e):
        def mostrar_acerca(ev):
            panel_acerca.visible = True
            panel_componentes.visible = False
            btn_acerca.style = ft.ButtonStyle(color="cyan")
            btn_componentes.style = ft.ButtonStyle(color="grey")
            page.update()

        def mostrar_componentes(ev):
            panel_acerca.visible = False
            panel_componentes.visible = True
            btn_acerca.style = ft.ButtonStyle(color="grey")
            btn_componentes.style = ft.ButtonStyle(color="cyan")
            page.update()

        btn_acerca = ft.TextButton("Acerca de", on_click=mostrar_acerca, style=ft.ButtonStyle(color="cyan"))
        btn_componentes = ft.TextButton("Componentes", on_click=mostrar_componentes, style=ft.ButtonStyle(color="grey"))

        panel_acerca = ft.Column([
            ft.Image(src="logoSATR.png", width=130, height=130, fit="contain"),
            ft.Text("SATR Cliente", size=18, weight="bold", color="white"),
            ft.Text("Versión 1.0.0", size=13, color="grey"),
            ft.Divider(),
            ft.Text(
                "Sistema de Administración de\nTaxis y Remises",
                size=13,
                text_align=ft.TextAlign.CENTER
            ),
            ft.Text("© 2026 Alejandro Javier Palau", size=12, color="grey"),
            ft.TextButton("Desarrollado por Códice",
                          on_click=abrir_link("http://codice.net.ar")
            ),
            ft.TextButton(
                "http://satr.codice.net.ar",
                on_click=abrir_link("http://satr.codice.net.ar")
            ),
            ft.TextButton(
                "Licencia GPLv3",
                on_click=abrir_link("https://www.gnu.org/licenses/gpl-3.0.html")
            ),
        ],
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        spacing=6,
        visible=True)

        panel_componentes = ft.Column([
            ft.Text("Componentes de terceros", size=14, weight="bold", color="white"),
            ft.Divider(),
            ft.Row([ft.Text("Flet", weight="bold", width=120), ft.Text("v0.83.0")]),
            ft.Row([ft.Text("fpdf2", weight="bold", width=120), ft.Text("v2.8.7")]),
            ft.Row([ft.Text("Pillow", weight="bold", width=120), ft.Text("v11.x")]),
            ft.Row([ft.Text("Python", weight="bold", width=120), ft.Text("v3.x")]),
        ], spacing=10, visible=False)

        dialog = ft.AlertDialog(
            title=ft.Text(""),
            content=ft.Container(
                width=300,
                height=520,
                content=ft.Column([
                    ft.Row([btn_acerca, ft.VerticalDivider(), btn_componentes]),
                    ft.Divider(),
                    panel_acerca,
                    panel_componentes,
                ], spacing=4)
            ),
            actions=[ft.TextButton("Cerrar", on_click=lambda e: cerrar_dialog(dialog))]
        )
        page.overlay.append(dialog)
        dialog.open = True
        page.update()

    def cerrar_dialog(dialog):
        dialog.open = False
        page.update()

    # ------------------ VIAJES ------------------

    tipo_pago = ft.RadioGroup(
        content=ft.Row([
            ft.Radio(value="EFECTIVO", label="Efectivo"),
            ft.Radio(value="TRANSFERENCIA", label="Transferencia"),
        ]),
        value="EFECTIVO"
    )

    def add_v(e):
        nonlocal edit_idx_v
        try:
            val = float(ent_monto_v.value.replace(".", ""))
            if edit_idx_v == -1:
                hora = datetime.now().strftime("%H:%M")
                lista_viajes.append({"monto": val, "tipo": tipo_pago.value, "hora": hora})
            else:
                hora_orig = lista_viajes[edit_idx_v].get("hora", "")
                lista_viajes[edit_idx_v] = {"monto": val, "tipo": tipo_pago.value, "hora": hora_orig}
                edit_idx_v = -1
                btn_add_v.text = "SUMAR"
            ent_monto_v.value = ""
            guardar_jornada()
            actualizar_interfaz()
        except:
            pass

    def preparar_edit_v(idx):
        nonlocal edit_idx_v
        edit_idx_v = idx
        ent_monto_v.value = f"{int(lista_viajes[idx]['monto']):,}".replace(",", ".")
        btn_add_v.text = "GUARDAR"
        page.update()

    def borrar_item(idx, es_v):
        if es_v:
            lista_viajes.pop(idx)
        else:
            lista_gastos.pop(idx)
        guardar_jornada()
        actualizar_interfaz()

    # ------------------ GASTOS ------------------

    def add_g(e):
        nonlocal edit_idx_g
        try:
            desc = ent_desc_g.value.upper() or "GASTO"
            val = float(ent_monto_g.value.replace(".", ""))
            if edit_idx_g == -1:
                lista_gastos.append({"desc": desc, "monto": val})
            else:
                lista_gastos[edit_idx_g] = {"desc": desc, "monto": val}
                edit_idx_g = -1
                btn_add_g.text = "CARGAR"
            ent_monto_g.value = ""
            ent_desc_g.value = ""
            guardar_jornada()
            actualizar_interfaz()
        except:
            pass

    def preparar_edit_g(idx):
        nonlocal edit_idx_g
        edit_idx_g = idx
        g = lista_gastos[idx]
        ent_desc_g.value = g["desc"]
        ent_monto_g.value = f"{int(g['monto']):,}".replace(",", ".")
        btn_add_g.text = "GUARDAR"
        page.update()

    # ------------------ COMISION ------------------

    def aplicar_comision(tipo):
        try:
            if tipo == "AGENCIA":
                float(ent_p_age.value.replace(",", "."))
                ent_p_cho.focus()
            else:
                float(ent_p_cho.value.replace(",", "."))
                ent_km_fin.focus()
            guardar_jornada()
            actualizar_interfaz()
        except:
            mostrar_mensaje("Error en %")

    # ------------------ UI ------------------

    def actualizar_interfaz():
        col_viajes.controls.clear()
        for i, v in enumerate(lista_viajes):
            col_viajes.controls.append(
                ft.Row([
                    ft.TextButton(f"$ {formato_moneda(v['monto'])} ({v['tipo']})",
                                  on_click=lambda e, idx=i: preparar_edit_v(idx)),
                    ft.TextButton("X", on_click=lambda e, idx=i: borrar_item(idx, True))
                ], alignment="spaceBetween")
            )

        col_gastos.controls.clear()
        for i, g in enumerate(lista_gastos):
            col_gastos.controls.append(
                ft.Row([
                    ft.TextButton(f"{g['desc']}: $ {formato_moneda(g['monto'])}",
                                  on_click=lambda e, idx=i: preparar_edit_g(idx)),
                    ft.TextButton("X", on_click=lambda e, idx=i: borrar_item(idx, False))
                ], alignment="spaceBetween")
            )

        rec = sum(v["monto"] for v in lista_viajes)
        efectivo = sum(v["monto"] for v in lista_viajes if v["tipo"] == "EFECTIVO")
        transferencia = sum(v["monto"] for v in lista_viajes if v["tipo"] == "TRANSFERENCIA")

        try:
            porc_age = float(ent_p_age.value.replace(",", "."))
        except:
            porc_age = 0
        try:
            porc_cho = float(ent_p_cho.value.replace(",", "."))
        except:
            porc_cho = 0

        c_age = (rec * porc_age) / 100
        g_cho = (rec * porc_cho) / 100
        g_var = sum(g['monto'] for g in lista_gastos if g['desc'] not in ["AGENCIA", "CHOFER"])

        lbl_resumen.value = (
            f"RECAUDACIÓN TOTAL: $ {formato_moneda(rec)}\n"
            f"EFECTIVO: $ {formato_moneda(efectivo)}\n"
            f"TRANSFERENCIA: $ {formato_moneda(transferencia)}\n"
            f"COMISIÓN AGENCIA: $ {formato_moneda(c_age)}\n"
            f"TOTAL DE GASTOS: $ {formato_moneda(g_var)}\n"
            f"GANANCIA CHOFER: $ {formato_moneda(g_cho)}\n"
            f"---------------------------\n"
            f"NETO TITULAR: $ {formato_moneda(rec - c_age - g_cho - g_var)}\n"
        )
        page.update()

    # ------------------ INPUTS ------------------

    ent_chofer = ft.TextField(label="Chofer", on_change=guardar_chofer)
    ent_patente = ft.TextField(label="Patente")
    ent_km_ini = ft.TextField(label="KM Ini", width=140, on_change=formatear_entrada, keyboard_type=ft.KeyboardType.NUMBER)
    ent_hora_ini = ft.TextField(label="Hora entrada", width=110, keyboard_type=ft.KeyboardType.NUMBER, hint_text="HH:MM", on_change=formatear_hora)
    ent_km_fin = ft.TextField(label="KM Fin", width=140, on_change=formatear_entrada, on_submit=lambda e: confirmar_km_fin(), keyboard_type=ft.KeyboardType.NUMBER)
    ent_hora_fin = ft.TextField(label="Hora salida", width=110, keyboard_type=ft.KeyboardType.NUMBER, hint_text="HH:MM", on_change=formatear_hora)
    ent_monto_v = ft.TextField(label="Importe $", width=170, on_change=formatear_entrada, keyboard_type=ft.KeyboardType.NUMBER)
    btn_add_v = ft.ElevatedButton("SUMAR", on_click=add_v)
    ent_desc_g = ft.TextField(label="Detalle Gasto")
    ent_monto_g = ft.TextField(label="Monto $", width=120, on_change=formatear_entrada, keyboard_type=ft.KeyboardType.NUMBER)
    btn_add_g = ft.ElevatedButton("CARGAR", on_click=add_g)
    ent_p_age = ft.TextField(label="% Agencia", value="0", width=110, on_submit=lambda e: aplicar_comision("AGENCIA"), keyboard_type=ft.KeyboardType.NUMBER)
    ent_p_cho = ft.TextField(label="% Chofer", value="0", width=110, on_submit=lambda e: aplicar_comision("CHOFER"), keyboard_type=ft.KeyboardType.NUMBER)
    lbl_resumen = ft.Text(size=15, weight="bold", color="yellow", font_family="monospace")
    col_viajes = ft.Column()
    col_gastos = ft.Column()

    def confirmar_km_fin():
        ent_km_fin.disabled = True
        page.update()
        ent_km_fin.disabled = False
        guardar_jornada()
        actualizar_interfaz()

    def confirmar_nueva_jornada(e):
        lista_viajes.clear()
        lista_gastos.clear()
        ent_chofer.value = ""
        ent_patente.value = ""
        ent_km_ini.value = ""
        ent_km_fin.value = ""
        ent_hora_ini.value = ""
        ent_hora_fin.value = ""
        try:
            os.remove(JORNADA_FILE)
        except:
            pass
        actualizar_interfaz()
        page.update()

    contenido = ft.Column(
        scroll="auto",
        expand=True,
        visible=False,
        controls=[
            ft.Text("SATR Cliente v1.0.0", size=20, weight="bold", color="white"),
            ft.Container(
                content=ft.Column([ent_chofer, ent_patente, ft.Row([ent_km_ini, ent_hora_ini])]),
                padding=10, bgcolor="#1A1A1A", border_radius=10
            ),
            ft.Container(
                content=ft.Column([ft.Text("VIAJES"), tipo_pago, ft.Row([ent_monto_v, btn_add_v]), col_viajes]),
                padding=10, bgcolor="#1A1A1A", border_radius=10
            ),
            ft.Container(
                content=ft.Column([ft.Text("GASTOS"), ent_desc_g, ft.Row([ent_monto_g, btn_add_g]), col_gastos]),
                padding=10, bgcolor="#1A1A1A", border_radius=10
            ),
            ft.Container(
                content=ft.Column([
                    ft.Text("COMISIONES"),
                    ft.Row([ent_p_age, ft.ElevatedButton("AGENCIA", on_click=lambda e: aplicar_comision("AGENCIA"))]),
                    ft.Row([ent_p_cho, ft.ElevatedButton("CHOFER", on_click=lambda e: aplicar_comision("CHOFER"))])
                ]),
                padding=10, bgcolor="#1A1A1A", border_radius=10
            ),
            ft.Container(
                content=ft.Column([
                    ft.Text("KM FINAL DE JORNADA"),
                    ft.Row([ent_km_fin, ent_hora_fin]),
                    ft.Row([ft.TextButton("✓", on_click=lambda e: confirmar_km_fin())])
                ]),
                padding=10, bgcolor="#1A1A1A", border_radius=10
            ),
            ft.Container(content=lbl_resumen, padding=15, bgcolor="#001a33", border_radius=10),
            ft.Container(height=20),
            ft.Container(height=80),
        ]
    )

    pdf_submenu = ft.Column([
        ft.Container(
            padding=ft.padding.only(left=10),
            content=ft.TextButton("Generar", on_click=generar_y_guardar_pdf, style=ft.ButtonStyle(color="cyan"))
        ),
        ft.Container(
            padding=ft.padding.only(left=10),
            content=ft.TextButton("Estadísticas", on_click=_estadisticas, style=ft.ButtonStyle(color="cyan"))
        ),
    ], visible=False)

    tel_submenu = ft.Column([
        ft.Container(
            padding=ft.padding.only(left=10),
            content=ft.TextButton("📞 Emergencias", on_click=abrir_emergencias, style=ft.ButtonStyle(color="red"))
        ),
        ft.Container(
            padding=ft.padding.only(left=10),
            content=ft.TextButton("👤 Cont. por Emerg.", on_click=abrir_contacto_emergencia, style=ft.ButtonStyle(color="cyan"))
        ),
        ft.Container(
            padding=ft.padding.only(left=10),
            content=ft.TextButton("🛡️ Seguro", on_click=abrir_seguro, style=ft.ButtonStyle(color="cyan"))
        ),
    ], visible=False)

    drawer_container = ft.Container(
        width=250,
        height=850,
        bgcolor="#111111",
        visible=False,
        content=ft.Column([
            ft.Container(height=20),
            ft.Text("Menú", size=20, color="white"),
            ft.Divider(),
            ft.TextButton("Inicio", icon=ft.Icons.HOME, on_click=abrir_menu),
            ft.TextButton("Tel. útiles", icon=ft.Icons.PHONE_IN_TALK, on_click=abrir_tel_utiles),
            tel_submenu,
            ft.TextButton("PDF", icon=ft.Icons.PICTURE_AS_PDF, on_click=toggle_pdf_menu),
            pdf_submenu,
            ft.TextButton("Tutorial", icon=ft.Icons.PLAY_CIRCLE,
                on_click=abrir_link("http://tutorial/satr.codice.net.ar")
            ),
            ft.TextButton("Acerca de", icon=ft.Icons.INFO, on_click=abrir_acerca_de),
            ft.Divider(),
            ft.TextButton("Nueva Jornada", icon=ft.Icons.REFRESH, on_click=confirmar_nueva_jornada,
                style=ft.ButtonStyle(color="red")),
        ])
    )

    page.appbar = ft.AppBar(
        title=ft.Text("SATR"),
        leading=ft.IconButton(icon=ft.Icons.MENU, on_click=abrir_menu),
    )

    # ------------------ SPLASH ------------------

    def tocar_splash_aus2(e):
        splash_aus2.visible = False
        contenido.visible = True
        page.update()

    def tocar_splash_aus1(e):
        splash_aus1.visible = False
        if _auspiciante.get("splash2", ""):
            splash_aus2.visible = True
        else:
            contenido.visible = True
        page.update()

    def tocar_splash1(e):
        splash1.visible = False
        if _auspiciante.get("splash1", ""):
            splash_aus1.visible = True
        else:
            contenido.visible = True
        page.update()

    splash_aus1 = ft.Container(
        width=400,
        height=850,
        bgcolor="#000000",
        content=ft.Image(src=_auspiciante.get("splash1", ""), width=400, height=850, fit="cover"),
        visible=False,
        on_click=tocar_splash_aus1,
    )

    splash_aus2 = ft.Container(
        width=400,
        height=850,
        bgcolor="#000000",
        content=ft.Image(src=_auspiciante.get("splash2", ""), width=400, height=850, fit="cover"),
        visible=False,
        on_click=tocar_splash_aus2,
    )

    splash1 = ft.Container(
        width=400,
        height=850,
        bgcolor="#000000",
        content=ft.Image(src="apertura.png", width=400, height=850, fit="cover"),
        visible=True,
        on_click=tocar_splash1
    )

    page.add(
        ft.Stack([
            ft.Image(src="splash.png", width=400, height=850),
            ft.Container(width=400, height=850, padding=10, content=contenido),
            drawer_container,
            splash1,
            splash_aus2,
            splash_aus1,
        ])
    )

    cargar_jornada()
    actualizar_interfaz()

if __name__ == "__main__":
    ft.app(target=main, assets_dir="assets")