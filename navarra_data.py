# -*- coding: utf-8 -*-
"""
Datos OPERATIVOS del Proyecto Navarra — CG Constructora S.A.S.
Fuente: Comités de Gerencia Feb–Abr 2026 + Informe Financiero Navarra v2 (30 Abr 2026).

Capa de SEGUIMIENTO (por torre), independiente del modelo financiero auditado (3 etapas, 951 und,
TIR 37.6%/VPN $18.281M). Aquí la estructura es POR TORRE (4 etapas, 951 und — cuadra con lo auditado).
NO altera la factibilidad: alimenta el Monitor de Ejecución (avance real, alertas, crédito, variaciones).

Actualizar mensualmente tras cada comité.
"""

# ------------------------------------------------------------------ avance de obra (Torre 1 / Etapa 1)
NAVARRA_AVANCE_OBRA = {
    "2026-02": {"ejecutado": 7.25, "programado": 6.20, "fuente": "Comité Feb 2026"},
    "2026-03": {"ejecutado": 31.50, "programado": None, "fuente": "Comité Mar 2026"},
    "2026-04": {"ejecutado": 42.01, "programado": None, "fuente": "Comité Abr 2026"},
    # avance según metodología bancaria (Castillo Medina, 27-04-2026) — base para desembolsos
    "2026-04-bancolombia": {"ejecutado": 59.57, "metodologia": "bancaria"},
}

# ------------------------------------------------------------------ estructura por etapa/torre
NAVARRA_ESTRUCTURA = {
    "etapa_1": {"nombre": "Navarra 1 — Torre 1", "torres": ["Torre 1"], "unidades": 158,
                "estado": "En obra", "avance_pct": 42.01, "semaforo": "green",
                "detalle": "Desembolso $2.000 mm autorizado · Avance 42.01%"},
    "etapa_2": {"nombre": "Navarra 2 — Torres 2A/2B", "torres": ["Torre 2A", "Torre 2B"], "unidades": 237,
                "estado": "Crédito en trámite", "avance_pct": 0, "semaforo": "red",
                "detalle": "136+ días en trámite · Crédito puente $1.700 mm requerido"},
    "etapa_3": {"nombre": "Navarra 3 — Torres 3A/3B", "torres": ["Torre 3A", "Torre 3B"], "unidades": 238,
                "estado": "Planificado", "avance_pct": 0, "semaforo": "gray",
                "detalle": "Ejecutar simultáneamente · PE 3B ≤ 3 meses después de 3A"},
    "etapa_4": {"nombre": "Navarra 4 — Torres 4/5", "torres": ["Torre 4", "Torre 5"], "unidades": 318,
                "estado": "Planificado", "avance_pct": 0, "semaforo": "gray",
                "detalle": "Tipologías 27 m² y 36 m² · Oferta SDHT"},
    # Total: 158 + 237 + 238 + 318 = 951 unidades (cuadra con el modelo financiero auditado).
}

# ------------------------------------------------------------------ crédito constructor por torre
NAVARRA_CREDITO_CONSTRUCTOR = {
    "torre_1": {"banco": "Bancolombia", "estado": "En desembolsos", "avance_requerido_pct": 59.57,
                "monto_autorizado_mm": 2000, "fecha_autorizacion": "2026-05-13", "monto_inicial_mm": 630},
    "torre_2a_2b": {"banco": "Bancolombia", "estado": "En trámite", "dias_tramite": 136,
                    "fecha_inicio_tramite": "2026-01-09", "saldo_encargo_preventas_mm": 1260,
                    "credito_puente_requerido_mm": 1700,
                    "tramites_pendientes": [
                        {"actividad": "Estudio jurídico constitución garantías", "fecha_fin": "2026-06-06", "estado": "Pendiente"},
                        {"actividad": "Instrucciones Generales Desembolsos", "fecha_fin": "2026-06-02", "estado": "Pendiente"},
                        {"actividad": "Firma pagaré unificado", "fecha_fin": "2026-06-02", "estado": "Pendiente"},
                        {"actividad": "Formato solicitud desembolso", "fecha_fin": "2026-06-05", "estado": "Pendiente"},
                        {"actividad": "Certificación ventas y recaudo", "fecha_fin": "2026-06-03", "estado": "Pendiente"},
                        {"actividad": "Cert. Existencia y Representación Legal", "fecha_fin": "2026-06-03", "estado": "Pendiente"},
                        {"actividad": "Visto bueno jurídico Bancolombia", "fecha_fin": "2026-06-16", "estado": "Pendiente"},
                    ]},
}

# ------------------------------------------------------------------ alertas activas
NAVARRA_ALERTAS = [
    {"id": "a1", "severidad": "critica", "titulo": "Crédito puente requerido — $1.700 millones",
     "descripcion": "Se requiere apalancamiento de $1.700 mm mientras se aprueba el crédito constructor Torres 2A/2B. Sin él, la Etapa 2 enfrenta riesgo de liquidez.",
     "modulo_origen": "Flujo de Caja", "fecha_reporte": "2026-04-30", "estado": "Activa", "responsable": "Gerencia Financiera"},
    {"id": "a2", "severidad": "critica", "titulo": "Trámites crédito Torres 2A/2B — fecha crítica 16-jun-2026",
     "descripcion": "La aprobación lleva 136 días (desde 09-ene-2026). El visto bueno jurídico de Bancolombia se estima al 16-jun-2026; cualquier demora previa lo impacta.",
     "modulo_origen": "Crédito Constructor", "fecha_reporte": "2026-05-26", "estado": "Activa", "responsable": "Gerencia Jurídica"},
    {"id": "a3", "severidad": "importante", "titulo": "Otrosíes pendientes con adherentes Torres 2A/2B",
     "descripcion": "Falta suscribir otrosíes al contrato de adhesión con compradores T2A/T2B. Riesgo legal si no se gestionan antes del inicio de obra.",
     "modulo_origen": "Jurídico", "fecha_reporte": "2026-04-30", "estado": "Activa", "responsable": "Gerencia Jurídica"},
    {"id": "a4", "severidad": "importante", "titulo": "Restricción simultaneidad Torres 3A y 3B",
     "descripcion": "Torres 3A y 3B deben ejecutarse simultáneamente: el PE de 3B máximo 3 meses tras el PE de 3A. Afecta cronograma y flujo de caja.",
     "modulo_origen": "Cronograma", "fecha_reporte": "2026-02-27", "estado": "Activa", "responsable": "Gerencia Técnica"},
    {"id": "a5", "severidad": "info", "titulo": "Desembolso Torre 1 desbloqueado — $2.000 millones",
     "descripcion": "Bancolombia autorizó el desembolso de $2.000 mm el 13/05/2026 con base en avance del 59.57% (visita Castillo Medina 27/04/2026).",
     "modulo_origen": "Crédito Constructor", "fecha_reporte": "2026-05-13", "estado": "Resuelta", "responsable": "Gerencia Financiera"},
]

# ------------------------------------------------------------------ variaciones presupuestales (Torre 1)
NAVARRA_VARIACIONES = {
    "sobrecostos": [
        {"partida": "Red eléctrica (SOLINRED)", "descripcion": "Mayor precio por cambio de año en contratación", "meses": ["2026-02", "2026-03"], "impacto": "Alto"},
        {"partida": "Estructura — acero y concreto", "descripcion": "Mayor consumo concreto, precios otrosí MO, mayor cantidad acero 1/4\"", "meses": ["2026-03", "2026-04"], "impacto": "Alto"},
        {"partida": "Planta eléctrica", "descripcion": "Alquiler por falta de provisional de energía", "meses": ["2026-02"], "impacto": "Medio"},
        {"partida": "Vigilancia", "descripcion": "Doble turno nocturno por condición de zona", "meses": ["2026-02"], "impacto": "Medio"},
        {"partida": "Demoliciones", "descripcion": "Pago Consorcio LEAL y D&W; sub-base granular y recebo", "meses": ["2026-04"], "impacto": "Medio"},
        {"partida": "Prebarreno y PH (pilotaje)", "descripcion": "Mayor costo por uso de prebarreno", "meses": ["2026-02"], "impacto": "Alto"},
        {"partida": "Detección incendio (SOLINRED)", "descripcion": "Mayor precio cambio de año; puertas vidrieras PF no presupuestadas", "meses": ["2026-03"], "impacto": "Medio"},
    ],
    "ahorros": [
        {"partida": "Mampostería → concreto", "descripcion": "Cambio de muros a concreto + cemento Holcim", "meses": ["2026-02", "2026-04"], "impacto": "Alto"},
        {"partida": "Acero 3/8\" y malla electrosoldada", "descripcion": "Menor cantidad (compensa acero 1/4\")", "meses": ["2026-03", "2026-04"], "impacto": "Alto"},
        {"partida": "Carpintería metálica — pasamanos", "descripcion": "Mejores precios en negociación", "meses": ["2026-04"], "impacto": "Bajo"},
        {"partida": "Dovelas, pañete y mampostería", "descripcion": "Menor cantidad por cambio de diseño estructural", "meses": ["2026-02", "2026-03", "2026-04"], "impacto": "Alto"},
        {"partida": "Enchapes (CJR Construcciones)", "descripcion": "Menores cantidades y precios al asegurar el contrato", "meses": ["2026-03"], "impacto": "Medio"},
        {"partida": "Cerramiento y cuarto enfermería", "descripcion": "Menor costo en temporal y enfermería", "meses": ["2026-02"], "impacto": "Bajo"},
        {"partida": "Rejillas de fachada", "descripcion": "Ajuste por ventilación en ventanas — menor cantidad", "meses": ["2026-03"], "impacto": "Bajo"},
    ],
}

# ------------------------------------------------------------------ presupuesto y ejecución Torre 1 (Etapa 1)
# Control de Presupuesto y Ejecución — corte 30/04/2026 (valores en MILLONES COP).
# Columnas: base (BAC) · proy_ant · ejecutado (AC) · asegurado · proy_act (EAC).
NAVARRA_PRESUPUESTO_T1 = {
    "fecha_corte": "2026-04-30",
    "unidad": "millones COP",
    "partidas": [
        {"capitulo": "Preliminares",                              "base": 624,   "proy_ant": 545,   "ejecutado": 319,   "asegurado": 320,   "proy_act": 636},
        {"capitulo": "Cimentaciones",                             "base": 3043,  "proy_ant": 3245,  "ejecutado": 3226,  "asegurado": 3240,  "proy_act": 3244},
        {"capitulo": "Estructura",                                "base": 5259,  "proy_ant": 5609,  "ejecutado": 3270,  "asegurado": 4275,  "proy_act": 5372},
        {"capitulo": "Muros y divisiones",                        "base": 794,   "proy_ant": 561,   "ejecutado": 68,    "asegurado": 361,   "proy_act": 518},
        {"capitulo": "Cubiertas y techos",                        "base": 36,    "proy_ant": 39,    "ejecutado": 0,     "asegurado": 11,    "proy_act": 38},
        {"capitulo": "Instalaciones hidrosanitarias",            "base": 873,   "proy_ant": 907,   "ejecutado": 281,   "asegurado": 671,   "proy_act": 907},
        {"capitulo": "Instalaciones gas",                         "base": 497,   "proy_ant": 488,   "ejecutado": 39,    "asegurado": 382,   "proy_act": 489},
        {"capitulo": "Instalaciones eléctricas e iluminación",   "base": 1194,  "proy_ant": 1365,  "ejecutado": 331,   "asegurado": 1287,  "proy_act": 1365},
        {"capitulo": "Instalaciones telecomunicaciones",         "base": 178,   "proy_ant": 210,   "ejecutado": 17,    "asegurado": 210,   "proy_act": 210},
        {"capitulo": "Sistema seguridad y salud humana",         "base": 402,   "proy_ant": 472,   "ejecutado": 18,    "asegurado": 462,   "proy_act": 458},
        {"capitulo": "Revoque y pintura acabados muros y cielos","base": 540,   "proy_ant": 409,   "ejecutado": 0,     "asegurado": 13,    "proy_act": 408},
        {"capitulo": "Enchape pisos y paredes",                   "base": 371,   "proy_ant": 294,   "ejecutado": 45,    "asegurado": 184,   "proy_act": 282},
        {"capitulo": "Carpintería metálica y aluminio",          "base": 333,   "proy_ant": 333,   "ejecutado": 1,     "asegurado": 0,     "proy_act": 279},
        {"capitulo": "Ventanería",                                "base": 757,   "proy_ant": 545,   "ejecutado": 0,     "asegurado": 525,   "proy_act": 548},
        {"capitulo": "Carpintería madera y mesones",             "base": 173,   "proy_ant": 180,   "ejecutado": 23,    "asegurado": 89,    "proy_act": 180},
        {"capitulo": "Aparatos sanitarios grifería y accesorios","base": 183,   "proy_ant": 183,   "ejecutado": 27,    "asegurado": 151,   "proy_act": 176},
        {"capitulo": "Electrodomésticos y dotaciones internas",  "base": 0,     "proy_ant": 0,     "ejecutado": 0,     "asegurado": 0,     "proy_act": 0},
        {"capitulo": "Sistemas especiales y dotaciones zonas com","base": 348,   "proy_ant": 20,    "ejecutado": 0,     "asegurado": 0,     "proy_act": 20},
        {"capitulo": "Equipos de obra y consumibles",            "base": 239,   "proy_ant": 341,   "ejecutado": 152,   "asegurado": 275,   "proy_act": 354},
        {"capitulo": "Control y mitigación ambiental",           "base": 121,   "proy_ant": 150,   "ejecutado": 46,    "asegurado": 63,    "proy_act": 144},
        {"capitulo": "Control seguridad y salud en el trabajo",  "base": 106,   "proy_ant": 105,   "ejecutado": 34,    "asegurado": 78,    "proy_act": 106},
        {"capitulo": "Urbanismo interno",                         "base": 1845,  "proy_ant": 2439,  "ejecutado": 38,    "asegurado": 1572,  "proy_act": 2457},
        {"capitulo": "Aseo y entregas",                           "base": 100,   "proy_ant": 100,   "ejecutado": 0,     "asegurado": 0,     "proy_act": 100},
        {"capitulo": "Gastos generales obra",                     "base": 1408,  "proy_ant": 1469,  "ejecutado": 507,   "asegurado": 645,   "proy_act": 1474},
        {"capitulo": "Obras de certificación sostenibilidad",    "base": 8,     "proy_ant": 8,     "ejecutado": 0,     "asegurado": 0,     "proy_act": 8},
        {"capitulo": "Edificaciones comunales",                   "base": 2854,  "proy_ant": 3090,  "ejecutado": 655,   "asegurado": 1742,  "proy_act": 3057},
        {"capitulo": "Urbanismo externo",                         "base": 622,   "proy_ant": 622,   "ejecutado": 0,     "asegurado": 0,     "proy_act": 622},
        {"capitulo": "Imprevistos",                               "base": 0,     "proy_ant": 61,    "ejecutado": 21,    "asegurado": 38,    "proy_act": 90},
    ],
    # totales de la imagen (control de transcripción)
    "total_imagen": {"base": 22910, "proy_ant": 23791, "ejecutado": 9115, "asegurado": 16593, "proy_act": 23542},
}

# ------------------------------------------------------------------ factibilidad por etapa (slides 7-10)
# PENDIENTE de transcripción manual desde el Informe Financiero (están como imágenes en el PPTX).
NAVARRA_FACTIBILIDAD_POR_ETAPA = {
    "etapa_1_torre_1":   {},   # ← TRANSCRIBIR slide 7  (ventas/costos/UO/margen/TIR/VPN)
    "etapa_2_torre_2a2b": {},  # ← TRANSCRIBIR slide 8
    "etapa_3_torre_3a3b": {},  # ← TRANSCRIBIR slide 9
    "consolidado":        {},  # ← TRANSCRIBIR slide 10
}

# proyectos con datos operativos disponibles (para que el Monitor sepa cuándo mostrar contenido)
PROYECTOS_CON_MONITOR = {"Navarra Apartamentos"}


def avance_ultimo():
    """(% avance ejecutado real más reciente, % bancolombia) de Torre 1."""
    real = NAVARRA_AVANCE_OBRA["2026-04"]["ejecutado"]
    banco = NAVARRA_AVANCE_OBRA["2026-04-bancolombia"]["ejecutado"]
    return real, banco
