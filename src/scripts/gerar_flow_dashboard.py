"""Gera nodered/flow_dashboard_alertas.json: dashboard em tempo real dos alertas de PII (tópico MQTT piiguard/alertas)."""
import json, os
R = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
tab = "piiguard_dash_tab"
contar = """// Conta alertas por empresa e por gravidade (memória do fluxo)
const a = msg.payload;
const nomes = {A: 'Clínica', B: 'Ginásio', C: 'TechCávado'};
let emp = flow.get('porEmpresa') || {};
let grav = flow.get('porGravidade') || {};
let lista = flow.get('ultimos') || [];
const e = nomes[a.empresa] || a.empresa;
emp[e] = (emp[e] || 0) + 1;
grav[a.gravidade] = (grav[a.gravidade] || 0) + 1;
lista.unshift({hora: (a.recebido_em || '').substring(11), ticket: a.ticket_id, empresa: e,
               tipos: a.tipos_pii, gravidade: a.gravidade, mensagem: a.mensagem_mascarada});
lista = lista.slice(0, 12);
flow.set('porEmpresa', emp); flow.set('porGravidade', grav); flow.set('ultimos', lista);
const total = Object.values(emp).reduce((s, v) => s + v, 0);
const empresas = Object.keys(emp);
const gravs = ['ALTA', 'MEDIA', 'BAIXA'];
return [
  {payload: empresas.map(k => ({nome: k, n: emp[k], pct: Math.round(100 * emp[k] / Math.max(...Object.values(emp)))}))},
  {payload: [{series: ['Alertas'], data: [gravs.map(k => grav[k] || 0)], labels: gravs}]},
  {payload: lista},
  {payload: total}
];"""
tabela = """<style>
 .pg-t {width:100%; border-collapse:collapse; font-size:13px}
 .pg-t th {text-align:left; border-bottom:1px solid #888; padding:4px}
 .pg-t td {padding:4px; border-bottom:1px solid #ddd; vertical-align:top}
 .ALTA {color:#c62828; font-weight:bold} .MEDIA {color:#ef6c00; font-weight:bold} .BAIXA {color:#2e7d32}
</style>
<table class="pg-t">
 <tr><th>Hora</th><th>Ticket</th><th>Empresa</th><th>Tipos de PII</th><th>Gravidade</th><th>Mensagem (já mascarada)</th></tr>
 <tr ng-repeat="r in msg.payload">
  <td>{{r.hora}}</td><td>{{r.ticket}}</td><td>{{r.empresa}}</td><td>{{r.tipos}}</td>
  <td class="{{r.gravidade}}">{{r.gravidade}}</td><td>{{r.mensagem}}</td>
 </tr>
</table>"""
barras = """<div style="padding:4px 8px">
 <div ng-repeat="b in msg.payload" style="margin:10px 0">
  <div style="display:flex;justify-content:space-between;font-size:14px"><span>{{b.nome}}</span><b>{{b.n}}</b></div>
  <div style="background:#e3eef7;height:22px;border-radius:4px">
   <div style="background:#1f77b4;height:22px;border-radius:4px;width:{{b.pct}}%"></div>
  </div>
 </div>
 <div ng-if="!msg.payload || msg.payload.length == 0" style="color:#888">À espera de alertas...</div>
</div>"""
reset = """flow.set('porEmpresa', {}); flow.set('porGravidade', {}); flow.set('ultimos', []);
return [{payload: []}, {payload: []}, {payload: []}, {payload: 0}];"""
flow = [
  {"id": tab, "type": "tab", "label": "PiiGuard - Dashboard de alertas", "disabled": False,
   "info": "Recebe os alertas que o Pentaho (c3_01b_processar_ticket) publica no tópico piiguard/alertas e mostra-os em http://localhost:1880/ui"},
  {"id": "pd_broker", "type": "mqtt-broker", "name": "Mosquitto local (dashboard)", "broker": "localhost", "port": "1883",
   "clientid": "", "autoConnect": True, "usetls": False, "protocolVersion": "4", "keepalive": "60", "cleansession": True,
   "birthTopic": "", "birthQos": "0", "birthPayload": "", "birthMsg": {}, "closeTopic": "", "closeQos": "0", "closePayload": "",
   "closeMsg": {}, "willTopic": "", "willQos": "0", "willPayload": "", "willMsg": {}, "userProps": "", "sessionExpiry": ""},
  {"id": "pd_ui_tab", "type": "ui_tab", "name": "PiiGuard", "icon": "dashboard", "order": 1, "disabled": False, "hidden": False},
  {"id": "pd_grp_resumo", "type": "ui_group", "name": "Alertas de dados pessoais (tempo real)", "tab": "pd_ui_tab", "order": 1,
   "disp": True, "width": "12", "collapse": False},
  {"id": "pd_grp_lista", "type": "ui_group", "name": "Últimos tickets com dados pessoais", "tab": "pd_ui_tab", "order": 2,
   "disp": True, "width": "18", "collapse": False},
  {"id": "pd_mqtt_in", "type": "mqtt in", "z": tab, "name": "piiguard/alertas", "topic": "piiguard/alertas", "qos": "1",
   "datatype": "json", "broker": "pd_broker", "nl": False, "rap": True, "rh": 0, "inputs": 0, "x": 130, "y": 120, "wires": [["pd_contar", "pd_debug"]]},
  {"id": "pd_contar", "type": "function", "z": tab, "name": "contar alertas", "func": contar, "outputs": 4, "timeout": 0,
   "noerr": 0, "initialize": "", "finalize": "", "libs": [], "x": 360, "y": 120,
   "wires": [["pd_chart_emp"], ["pd_chart_grav"], ["pd_tabela"], ["pd_total"]]},
  {"id": "pd_chart_emp", "type": "ui_template", "z": tab, "group": "pd_grp_resumo", "name": "Alertas por empresa", "order": 2,
   "width": "6", "height": "5", "format": "<h4 style='text-align:center;margin:4px'>Alertas por empresa</h4>" + barras,
   "storeOutMessages": True, "fwdInMessages": True, "resendOnRefresh": True, "templateScope": "local", "className": "",
   "x": 610, "y": 60, "wires": [[]]},
  {"id": "pd_chart_grav", "type": "ui_chart", "z": tab, "name": "por gravidade", "group": "pd_grp_resumo", "order": 3, "width": "6",
   "height": "5", "label": "Alertas por gravidade", "chartType": "pie", "legend": "true", "xformat": "HH:mm:ss", "interpolate": "linear",
   "nodata": "À espera de alertas...", "dot": False, "ymin": "", "ymax": "", "removeOlder": 1, "removeOlderPoints": "",
   "removeOlderUnit": "3600", "cutout": 0, "useOneColor": False, "useUTC": False,
   "colors": ["#d62728", "#ff7f0e", "#2ca02c", "#2ca02c", "#98df8a", "#d62728", "#ff9896", "#9467bd", "#c5b0d5"],
   "outputs": 1, "useDifferentColor": False, "className": "", "x": 610, "y": 120, "wires": [[]]},
  {"id": "pd_tabela", "type": "ui_template", "z": tab, "group": "pd_grp_lista", "name": "tabela", "order": 1, "width": "18",
   "height": "9", "format": tabela, "storeOutMessages": True, "fwdInMessages": True, "resendOnRefresh": True,
   "templateScope": "local", "className": "", "x": 600, "y": 180, "wires": [[]]},
  {"id": "pd_total", "type": "ui_text", "z": tab, "group": "pd_grp_resumo", "order": 1, "width": "12", "height": "1",
   "name": "total", "label": "Total de alertas recebidos", "format": "{{msg.payload}}", "layout": "row-spread",
   "className": "", "x": 590, "y": 240, "wires": []},
  {"id": "pd_debug", "type": "debug", "z": tab, "name": "ver alerta", "active": False, "tosidebar": True, "console": False,
   "tostatus": False, "complete": "payload", "targetType": "msg", "statusVal": "", "statusType": "auto", "x": 340, "y": 200, "wires": []},
  {"id": "pd_reset_btn", "type": "ui_button", "z": tab, "name": "", "group": "pd_grp_resumo", "order": 4, "width": "12",
   "height": "1", "passthru": False, "label": "Limpar dashboard", "tooltip": "", "color": "", "bgcolor": "", "className": "",
   "icon": "", "payload": "", "payloadType": "str", "topic": "", "topicType": "str", "x": 140, "y": 300, "wires": [["pd_reset"]]},
  {"id": "pd_reset", "type": "function", "z": tab, "name": "limpar contadores", "func": reset, "outputs": 4, "timeout": 0,
   "noerr": 0, "initialize": "", "finalize": "", "libs": [], "x": 360, "y": 300,
   "wires": [["pd_chart_emp"], ["pd_chart_grav"], ["pd_tabela"], ["pd_total"]]},
]
json.dump(flow, open(os.path.join(R, "src", "nodered", "flow_dashboard_alertas.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print("ok")
