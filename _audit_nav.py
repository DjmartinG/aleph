import json, copy
from engine import modelo

par = json.load(open('proyectos_privados/1_navarra_REAL.json', encoding='utf-8'))
R = modelo.calcular(copy.deepcopy(par))

# P&G
pyg = R['pyg']
print('=== P&G ===')
print('ventas: ' + str(int(pyg['ventas'])))
print('directos: ' + str(int(pyg['directos'])))
print('indirectos: ' + str(int(pyg['indirectos'])))
print('util_oper: ' + str(int(pyg['util_oper'])))
print('margen_oper: ' + str(round(pyg['margen_oper'], 4)))
print('gastos_fijos: ' + str(int(pyg['gastos_fijos'])))
print('indirectos_otros: ' + str(int(pyg['indirectos_otros'])))
print('costo_lote: ' + str(int(pyg['costo_lote'])))
print('honorarios: ' + str(int(pyg['honorarios'])))

# Apalancamiento
apal = R['apalancamiento']
print('=== Apalancamiento ===')
if apal.get('tir_proyecto'):
    print('tir_proyecto: ' + str(round(apal['tir_proyecto'], 4)))
else:
    print('tir_proyecto: ' + str(apal.get('tir_proyecto')))
if apal.get('vpn_proyecto'):
    print('vpn_proyecto: ' + str(int(apal['vpn_proyecto'])))
else:
    print('vpn_proyecto: ' + str(apal.get('vpn_proyecto')))
if apal.get('tir_equity'):
    print('tir_equity: ' + str(round(apal['tir_equity'], 4)))
else:
    print('tir_equity: ' + str(apal.get('tir_equity')))
if apal.get('credito_max'):
    print('credito_max: ' + str(int(apal['credito_max'])))
else:
    print('credito_max: ' + str(apal.get('credito_max')))
if apal.get('intereses_total'):
    print('intereses_total: ' + str(int(apal['intereses_total'])))
else:
    print('intereses_total: ' + str(apal.get('intereses_total')))
print('fiducia_real: ' + str(apal.get('fiducia_real')))

# WACC
wacc_val = modelo.calcular_wacc(par['financiero']['wacc'])
print('=== WACC ===')
print('WACC: ' + str(round(wacc_val, 4)))

