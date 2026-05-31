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
