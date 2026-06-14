# -*- coding: utf-8 -*-
"""M6.2 (spec_pyg_dinamico.md) — parser SDMX-ML (XML) de Banrep: defensivo, sin red."""
from datetime import date

from aleph_api.conectores import banrep

DATA_XML = """<?xml version='1.0' encoding='UTF-8'?>
<message:GenericData xmlns:message="http://www.sdmx.org/resources/sdmxml/schemas/v2_1/message"
 xmlns:generic="http://www.sdmx.org/resources/sdmxml/schemas/v2_1/data/generic">
 <message:DataSet>
  <generic:Series>
   <generic:Obs><generic:ObsDimension value="2026-05-20"/><generic:ObsValue value="4100.5"/></generic:Obs>
   <generic:Obs><generic:ObsDimension value="2026-05-22"/><generic:ObsValue value="4125.0"/></generic:Obs>
   <generic:Obs><generic:ObsDimension value="2026-05-21"/><generic:ObsValue value="4110.0"/></generic:Obs>
  </generic:Series>
 </message:DataSet>
</message:GenericData>"""

CAT_XML = """<?xml version='1.0' encoding='UTF-8'?>
<message:Structure xmlns:message="http://www.sdmx.org/resources/sdmxml/schemas/v2_1/message"
 xmlns:str="http://www.sdmx.org/resources/sdmxml/schemas/v2_1/structure"
 xmlns:com="http://www.sdmx.org/resources/sdmxml/schemas/v2_1/common">
 <message:Structures><str:Dataflows>
  <str:Dataflow id="DF_IBR" agencyID="ESTAT" version="1.0"><com:Name>Indicador Bancario de Referencia IBR</com:Name></str:Dataflow>
  <str:Dataflow id="DF_OTRO" agencyID="ESTAT" version="1.0"><com:Name>Algo no relacionado</com:Name></str:Dataflow>
  <str:Dataflow id="DF_TRM_DAILY_HIST" agencyID="ESTAT" version="1.0"><com:Name>TRM diaria</com:Name></str:Dataflow>
 </str:Dataflows></message:Structures>
</message:Structure>"""


def test_parse_xml_toma_la_observacion_mas_reciente():
    p = banrep.parse_sdmx_xml_ultimo(DATA_XML)
    assert p["valor"] == 4125.0 and p["periodo"] == "2026-05-22"


def test_parse_xml_vacio_o_invalido():
    assert banrep.parse_sdmx_xml_ultimo("no es xml") is None
    assert banrep.parse_sdmx_xml_ultimo("<a><b/></a>") is None


def test_fetch_serie_con_get_inyectado():
    v = banrep.fetch_serie("trm", get=lambda url, params=None, **k: DATA_XML)
    assert v is not None and v.valor == 4125.0 and v.unidad == "COP"
    assert v.fecha == date(2026, 5, 22) and v.clave == "banrep:trm"


def test_fetch_serie_dataflow_no_confirmado_es_none():
    assert banrep.fetch_serie("dtf", get=lambda *a, **k: DATA_XML) is None  # DTF aun sin dataflow


def test_descubrir_dataflows_filtra_y_arma_ref():
    flows = banrep.descubrir_dataflows(get=lambda url, params=None, **k: CAT_XML)
    ids = {f[0] for f in flows}
    assert ids == {"DF_IBR", "DF_TRM_DAILY_HIST"}
    refs = {f[0]: f[2] for f in flows}
    assert refs["DF_TRM_DAILY_HIST"] == "ESTAT,DF_TRM_DAILY_HIST,1.0"
