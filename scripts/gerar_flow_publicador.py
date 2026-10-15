"""Gera nodered/flow_publicador_tickets.json a partir de data/input/tickets_exemplo.json"""
import json, os
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
tickets = json.load(open(os.path.join(R, "data/input/tickets_exemplo.json"), encoding="utf-8"))
func = (
    "// Simula o sistema de suporte das empresas: publica 1 ticket de cada vez no MQTT\n"
    "const tickets = " + json.dumps(tickets, ensure_ascii=False) + ";\n\n"
    "if (msg.payload === 'reiniciar') { context.set('i', 0); node.status({fill:'blue',shape:'ring',text:'reiniciado'}); return null; }\n"
    "let i = context.get('i') || 0;\n"
    "if (i >= tickets.length) { node.status({fill:'grey',shape:'dot',text:'todos enviados (' + tickets.length + ')'}); return null; }\n"
    "const t = Object.assign({}, tickets[i]);\n"
    "t.enviado_em = new Date().toISOString();\n"
    "context.set('i', i + 1);\n"
    "node.status({fill:'green',shape:'dot',text:'enviado ' + (i + 1) + '/' + tickets.length});\n"
    "msg.topic = 'piiguard/tickets';\n"
    "msg.payload = JSON.stringify(t);\n"
    "return msg;"
)
tab = "piiguard_pub_tab"
flow = [
  {"id": tab, "type": "tab", "label": "PiiGuard - Publicador de tickets", "disabled": False,
   "info": "Simula a chegada assíncrona de tickets de suporte das 3 empresas.\nPublica 1 ticket a cada 5 segundos no tópico MQTT piiguard/tickets."},
  {"id": "pg_broker", "type": "mqtt-broker", "name": "Mosquitto local", "broker": "localhost", "port": "1883",
   "clientid": "", "autoConnect": True, "usetls": False, "protocolVersion": "4", "keepalive": "60",
   "cleansession": True, "autoUnsubscribe": True, "birthTopic": "", "birthQos": "0", "birthPayload": "",
   "birthMsg": {}, "closeTopic": "", "closeQos": "0", "closePayload": "", "closeMsg": {},
   "willTopic": "", "willQos": "0", "willPayload": "", "willMsg": {}, "userProps": "", "sessionExpiry": ""},
  {"id": "pg_comment", "type": "comment", "z": tab, "name": "Clique no botão do 'a cada 5 s' para começar; 'reiniciar' volta ao 1.º ticket",
   "info": "", "x": 330, "y": 40, "wires": []},
  {"id": "pg_inject", "type": "inject", "z": tab, "name": "a cada 5 s", "props": [{"p": "payload"}],
   "repeat": "5", "crontab": "", "once": False, "onceDelay": 0.1, "topic": "", "payload": "tick",
   "payloadType": "str", "x": 140, "y": 100, "wires": [["pg_func"]]},
  {"id": "pg_reset", "type": "inject", "z": tab, "name": "reiniciar", "props": [{"p": "payload"}],
   "repeat": "", "crontab": "", "once": False, "onceDelay": 0.1, "topic": "", "payload": "reiniciar",
   "payloadType": "str", "x": 130, "y": 160, "wires": [["pg_func"]]},
  {"id": "pg_func", "type": "function", "z": tab, "name": "próximo ticket", "func": func, "outputs": 1,
   "timeout": 0, "noerr": 0, "initialize": "", "finalize": "", "libs": [], "x": 360, "y": 130,
   "wires": [["pg_mqtt_out", "pg_debug"]]},
  {"id": "pg_mqtt_out", "type": "mqtt out", "z": tab, "name": "piiguard/tickets", "topic": "", "qos": "1",
   "retain": "false", "respTopic": "", "contentType": "", "userProps": "", "correl": "", "expiry": "",
   "broker": "pg_broker", "x": 590, "y": 100, "wires": []},
  {"id": "pg_debug", "type": "debug", "z": tab, "name": "ver ticket enviado", "active": True, "tosidebar": True,
   "console": False, "tostatus": False, "complete": "payload", "targetType": "msg", "statusVal": "",
   "statusType": "auto", "x": 600, "y": 160, "wires": []},
]
json.dump(flow, open(os.path.join(R, "nodered/flow_publicador_tickets.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print("ok", len(tickets))
