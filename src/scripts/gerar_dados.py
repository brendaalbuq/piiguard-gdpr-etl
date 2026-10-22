"""
PiiGuard - Gerador de dados sintéticos "estragados de propósito".

Gera os ficheiros de entrada dos 3 circuitos e um MAPA DE ESTRAGOS
(data/expected/mapa_estragos.csv) que diz, linha a linha, que erro foi
injetado. Esse mapa é a "verdade" usada para verificar se o ETL apanhou tudo.

Todos os dados são FICTÍCIOS. Os NIF são gerados com dígito de controlo válido,
mas não correspondem a pessoas reais.

Uso:  python scripts/gerar_dados.py      (a semente é fixa: gera sempre o mesmo)
"""
import csv
import json
import os
import random
from datetime import date, datetime, timedelta

random.seed(2026)
RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ENTRADA = os.path.join(RAIZ, "data", "input")
ESPERADO = os.path.join(RAIZ, "data", "expected")
os.makedirs(ENTRADA, exist_ok=True)
os.makedirs(ESPERADO, exist_ok=True)

mapa = []  # (ficheiro, registo, campo, tipo_estrago, valor_injetado, resultado_esperado)


def estrago(ficheiro, registo, campo, tipo, valor, esperado):
    mapa.append([ficheiro, registo, campo, tipo, valor, esperado])


# ---------------------------------------------------------------- empresas
EMPRESAS = {
    "A": "Clínica Dentária Sorriso do Minho, Lda",
    "B": "Ginásio Movimento Braga, Lda",
    "C": "TechCávado Informática, Lda",
}

PRIMEIROS = ["Ana", "João", "Maria", "Pedro", "Inês", "Tiago", "Beatriz", "Rui",
             "Sofia", "Miguel", "Carla", "Nuno", "Marta", "Hugo", "Rita", "André",
             "Joana", "Luís", "Catarina", "Diogo", "Teresa", "Bruno", "Filipa",
             "Ricardo", "Leonor", "Gonçalo", "Mariana", "Paulo", "Helena", "Vasco"]
APELIDOS = ["Silva", "Santos", "Ferreira", "Pereira", "Oliveira", "Costa",
            "Rodrigues", "Martins", "Jesus", "Sousa", "Fernandes", "Gonçalves",
            "Gomes", "Lopes", "Marques", "Alves", "Almeida", "Ribeiro", "Pinto",
            "Carvalho", "Teixeira", "Moreira", "Correia", "Mendes", "Nunes"]
CIDADES = [("Braga", "4700"), ("Barcelos", "4750"), ("Guimarães", "4800"),
           ("Esposende", "4740"), ("Vila Nova de Famalicão", "4760"),
           ("Póvoa de Lanhoso", "4830"), ("Viana do Castelo", "4900")]
RUAS = ["Rua do Souto", "Avenida da Liberdade", "Rua de São Vicente",
        "Rua Dom Pedro V", "Largo do Paço", "Rua da Boavista", "Avenida Central",
        "Rua Nova de Santa Cruz", "Rua dos Chãos", "Travessa do Carmo"]


def nif_valido(primeiro="2"):
    d = [int(primeiro)] + [random.randint(0, 9) for _ in range(7)]
    soma = sum(v * (9 - i) for i, v in enumerate(d))
    r = soma % 11
    d.append(0 if r < 2 else 11 - r)
    return "".join(map(str, d))


def telemovel():
    return random.choice(["91", "92", "93", "96"]) + "".join(
        str(random.randint(0, 9)) for _ in range(7))


def sem_acentos(s):
    tabela = str.maketrans("áàâãéêíóôõúçÁÀÂÃÉÊÍÓÔÕÚÇ", "aaaaeeiooouc" + "AAAAEEIOOOUC")
    return s.translate(tabela)


def pessoa():
    nome = f"{random.choice(PRIMEIROS)} {random.choice(APELIDOS)} {random.choice(APELIDOS)}"
    cidade, cp4 = random.choice(CIDADES)
    nascimento = date(1950, 1, 1) + timedelta(days=random.randint(0, 365 * 55))
    registo = date(2019, 1, 1) + timedelta(days=random.randint(0, 365 * 7))
    email = sem_acentos(nome.split()[0] + "." + nome.split()[-1]).lower() + \
        f"{random.randint(1, 99)}@" + random.choice(["gmail.com", "hotmail.com", "sapo.pt", "outlook.pt"])
    return {
        "nome": nome, "nif": nif_valido(random.choice("123")), "email": email,
        "tel": telemovel(), "cp": f"{cp4}-{random.randint(0, 999):03d}",
        "cidade": cidade, "rua": f"{random.choice(RUAS)}, {random.randint(1, 250)}",
        "nasc": nascimento, "reg": registo,
    }


# ------------------------------------------------- formas de estragar campos
def estragar_nif(n):
    """devolve (valor, tipo, esperado)"""
    op = random.choice(["espacos", "pontos", "prefixo", "curto", "letras", "vazio"])
    if op == "espacos":
        return f"{n[:3]} {n[3:6]} {n[6:]}", "NIF com espaços", "normalizar para " + n
    if op == "pontos":
        return f"{n[:3]}.{n[3:6]}.{n[6:]}", "NIF com pontos", "normalizar para " + n
    if op == "prefixo":
        return "PT" + n, "NIF com prefixo PT", "normalizar para " + n
    if op == "curto":
        return n[:8], "NIF com 8 dígitos", "quarentena NIF_INVALIDO"
    if op == "letras":
        return n[:5] + "O" + n[6:], "NIF com letra O em vez de 0", "quarentena NIF_INVALIDO"
    return "", "NIF vazio", "quarentena CAMPO_OBRIGATORIO_NULO"


def estragar_tel(t):
    op = random.choice(["mais351", "00351", "hifens", "parenteses", "espacos", "curto"])
    if op == "mais351":
        return f"+351 {t[:3]} {t[3:6]} {t[6:]}", "telefone +351 com espaços", "normalizar para +351" + t
    if op == "00351":
        return "00351" + t, "telefone com 00351", "normalizar para +351" + t
    if op == "hifens":
        return f"{t[:3]}-{t[3:6]}-{t[6:]}", "telefone com hífens", "normalizar para +351" + t
    if op == "parenteses":
        return f"(+351){t}", "telefone com (+351)", "normalizar para +351" + t
    if op == "espacos":
        return f"{t[:3]} {t[3:6]} {t[6:]}", "telefone com espaços", "normalizar para +351" + t
    return t[:8], "telefone com 8 dígitos", "quarentena TELEFONE_INVALIDO"


def estragar_email(e):
    op = random.choice(["maiusculas", "espacos", "sem_dominio", "at", "espaco_meio"])
    if op == "maiusculas":
        return e.upper(), "email em maiúsculas", "normalizar para " + e
    if op == "espacos":
        return f"  {e} ", "email com espaços à volta", "normalizar para " + e
    if op == "sem_dominio":
        return e.split(".")[0] + "@" + e.split("@")[1].split(".")[0], "email sem .pt/.com", "quarentena EMAIL_INVALIDO"
    if op == "at":
        return e.replace("@", "(at)"), "email com (at)", "quarentena EMAIL_INVALIDO"
    return e.replace(".", " ", 1), "email com espaço no meio", "quarentena EMAIL_INVALIDO"


def estragar_cp(cp):
    op = random.choice(["sem_hifen", "espaco", "so4", "errado"])
    if op == "sem_hifen":
        return cp.replace("-", ""), "código postal sem hífen", "normalizar para " + cp
    if op == "espaco":
        return cp.replace("-", " "), "código postal com espaço", "normalizar para " + cp
    if op == "so4":
        return cp[:4], "código postal só com 4 dígitos", "quarentena CP_INVALIDO"
    return cp[:4] + cp[5:7], "código postal com 6 dígitos", "quarentena CP_INVALIDO"


def estragar_data(d):
    op = random.choice(["barras", "curta", "pontos", "impossivel"])
    if op == "barras":
        return d.strftime("%d/%m/%Y"), "data dd/mm/aaaa", "normalizar para " + d.isoformat()
    if op == "curta":
        return f"{d.day}-{d.month}-{d.strftime('%y')}", "data d-m-aa", "normalizar para " + d.isoformat()
    if op == "pontos":
        return d.strftime("%d.%m.%Y"), "data dd.mm.aaaa", "normalizar para " + d.isoformat()
    return f"31/02/{d.year}", "data impossível (31 de fevereiro)", "quarentena DATA_INVALIDA"


def estragar_nome(n):
    op = random.choice(["espacos", "maiusculas", "minusculas", "mojibake"])
    if op == "espacos":
        return "  " + n.replace(" ", "   ", 1) + " ", "nome com espaços a mais", "normalizar para " + n
    if op == "maiusculas":
        return n.upper(), "nome em maiúsculas", "normalizar para " + n
    if op == "minusculas":
        return n.lower(), "nome em minúsculas", "normalizar para " + n
    estragado = n.encode("utf-8").decode("latin-1")
    if estragado == n:
        return n.upper(), "nome em maiúsculas", "normalizar para " + n
    return estragado, "nome com acentos corrompidos (mojibake)", "corrigir para " + n


OBS_PII = [
    ("Pediu fatura com NIF {nif}", "NIF em campo livre"),
    ("Contactar pelo {tel} depois das 18h", "telefone em campo livre"),
    ("Alergia à penicilina - avisar médico", "DADO DE SAÚDE em campo livre (RGPD art. 9.º)"),
    ("Toma anticoagulantes, ver ficha clínica", "DADO DE SAÚDE em campo livre (RGPD art. 9.º)"),
    ("Pagamento por transferência IBAN PT50 0035 0651 {iban} 05", "IBAN em campo livre"),
    ("Mora na {rua}, perto da farmácia", "morada em campo livre"),
]
OBS_OK = ["", "", "", "Cliente frequente", "Prefere marcações de manhã",
          "Enviar newsletter", "Veio por recomendação"]


def observacao(p, ficheiro, reg):
    if random.random() < 0.25:
        modelo, tipo = random.choice(OBS_PII)
        txt = modelo.format(nif=p["nif"], tel=p["tel"], rua=p["rua"],
                            iban="".join(str(random.randint(0, 9)) for _ in range(11)))
        estrago(ficheiro, reg, "observacoes", "PII escondida: " + tipo, txt, "detetar com regex e mascarar")
        return txt
    return random.choice(OBS_OK)


# ---------------------------------------------------- CIRCUITO 1: clientes
def gerar_clientes(empresa, n, ficheiro, colunas, sep, formato_registo, prob=0.35):
    linhas, pessoas = [], []
    for i in range(1, n + 1):
        p = pessoa()
        pessoas.append(p)
        reg = f"{empresa}{i:04d}"
        nome, nif, email, tel = p["nome"], p["nif"], p["email"], p["tel"]
        cp, nasc = p["cp"], p["nasc"].isoformat()
        registo = p["reg"].strftime(formato_registo)
        if random.random() < prob:
            nome, t, e = estragar_nome(nome); estrago(ficheiro, reg, "nome", t, nome, e)
        if random.random() < prob:
            nif, t, e = estragar_nif(nif); estrago(ficheiro, reg, "nif", t, nif, e)
        email_estragado = False
        if random.random() < prob:
            email, t, e = estragar_email(email); estrago(ficheiro, reg, "email", t, email, e)
            email_estragado = True
        if random.random() < prob:
            tel, t, e = estragar_tel(tel); estrago(ficheiro, reg, "telefone", t, tel, e)
        if random.random() < prob * 0.6:
            cp, t, e = estragar_cp(cp); estrago(ficheiro, reg, "codigo_postal", t, cp, e)
        if random.random() < prob * 0.6:
            nasc, t, e = estragar_data(p["nasc"]); estrago(ficheiro, reg, "data_nascimento", t, nasc, e)
        if not email_estragado and random.random() < 0.05:
            email = ""; estrago(ficheiro, reg, "email", "email vazio", "", "aceitar com email nulo (campo opcional)")
        obs = observacao(p, ficheiro, reg)
        linhas.append([reg, nome, nif, email, tel, cp, nasc, registo, obs])

    # duplicados exatos
    for _ in range(3):
        orig = random.choice(linhas[:-5])
        linhas.append(list(orig))
        estrago(ficheiro, orig[0], "(linha inteira)", "duplicado exato", orig[0], "marcar DUPLICADO (fica 1)")
    # duplicado "disfarçado": mesma pessoa, NIF formatado de outra forma, ID novo
    # (só a partir de registos sem erros que os mandem para quarentena)
    rejeitados = {m[1] for m in mapa if m[0] == ficheiro and "quarentena" in m[5]}
    validos = [l for l in linhas[:n] if l[0] not in rejeitados]
    for k in range(2):
        orig = random.choice(validos)
        n_limpo = "".join(ch for ch in orig[2] if ch.isdigit())
        if len(n_limpo) != 9:
            continue
        novo = list(orig)
        novo[0] = f"{empresa}9{k:03d}"
        novo[2] = f"{n_limpo[:3]} {n_limpo[3:6]} {n_limpo[6:]}"
        novo[1] = novo[1].upper()
        linhas.append(novo)
        estrago(ficheiro, novo[0], "(linha inteira)", "duplicado disfarçado do " + orig[0],
                novo[2], "só aparece depois de normalizar o NIF; marcar DUPLICADO")
    random.shuffle(linhas)
    with open(os.path.join(ENTRADA, ficheiro), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, delimiter=sep)
        w.writerow(colunas)
        w.writerows(linhas)
    return pessoas


colsA = ["id_cliente", "nome_completo", "nif", "email", "telemovel", "codigo_postal",
         "data_nascimento", "data_registo", "observacoes"]
colsB = ["customer_id", "name", "tax_id", "mail", "phone", "zip_code",
         "birth_date", "created_at", "notes"]
pessoasA = gerar_clientes("A", 60, "clientes_clinica_sorriso.csv", colsA, ";", "%d/%m/%Y", prob=0.2)
pessoasB = gerar_clientes("B", 40, "clientes_ginasio_movimento.csv", colsB, ",", "%Y-%m-%dT%H:%M:%S", prob=0.2)

# --------------------------------------------- CIRCUITO 2: faturas SAF-T
PRODUTOS = {
    "A": [("CONS01", "Consulta de medicina dentária", 45.0), ("DEST01", "Destartarização", 60.0),
          ("REST01", "Restauração dentária", 85.0), ("BRAN01", "Branqueamento", 250.0)],
    "C": [("PC001", "Portátil 14\" Ryzen 5", 649.0), ("RAT01", "Rato sem fios", 19.9),
          ("SSD01", "Disco SSD 1TB", 79.9), ("REP01", "Reparação de portátil", 55.0)],
}


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def saft(empresa, nif_empresa, clientes, n_faturas, ficheiro, estragar=False):
    out = ['<?xml version="1.0" encoding="UTF-8"?>', "<AuditFile>", "  <Header>",
           f"    <CompanyID>{nif_empresa}</CompanyID>",
           f"    <TaxRegistrationNumber>{nif_empresa}</TaxRegistrationNumber>",
           f"    <CompanyName>{esc(EMPRESAS[empresa])}</CompanyName>",
           "    <FiscalYear>2026</FiscalYear>", "    <StartDate>2026-01-01</StartDate>",
           "    <EndDate>2026-09-30</EndDate>", "    <CurrencyCode>EUR</CurrencyCode>",
           "  </Header>", "  <MasterFiles>"]
    ids = []
    for i, p in enumerate(clientes, 1):
        cid = f"CLI{i:03d}"
        ids.append(cid)
        out += ["    <Customer>", f"      <CustomerID>{cid}</CustomerID>",
                f"      <CustomerTaxID>{p['nif']}</CustomerTaxID>",
                f"      <CompanyName>{esc(p['nome'])}</CompanyName>",
                "      <BillingAddress>", f"        <AddressDetail>{esc(p['rua'])}</AddressDetail>",
                f"        <City>{esc(p['cidade'])}</City>", f"        <PostalCode>{p['cp']}</PostalCode>",
                "        <Country>PT</Country>", "      </BillingAddress>",
                f"      <Telephone>{p['tel']}</Telephone>", f"      <Email>{p['email']}</Email>",
                "    </Customer>"]
    out += ["  </MasterFiles>", "  <SourceDocuments>", "    <SalesInvoices>"]
    erro_feito = False
    for k in range(1, n_faturas + 1):
        cid = random.choice(ids)
        d = date(2026, 1, 1) + timedelta(days=random.randint(0, 270))
        linhas, liquido = [], 0.0
        for ln in range(1, random.randint(1, 3) + 1):
            cod, desc, preco = random.choice(PRODUTOS[empresa])
            qtd = random.randint(1, 2)
            liquido += qtd * preco
            linhas += ["        <Line>", f"          <LineNumber>{ln}</LineNumber>",
                       f"          <ProductCode>{cod}</ProductCode>",
                       f"          <ProductDescription>{esc(desc)}</ProductDescription>",
                       f"          <Quantity>{qtd}</Quantity>", f"          <UnitPrice>{preco:.2f}</UnitPrice>",
                       f"          <CreditAmount>{qtd * preco:.2f}</CreditAmount>",
                       "          <TaxPercentage>23</TaxPercentage>", "        </Line>"]
        iva = round(liquido * 0.23, 2)
        data_txt = d.isoformat()
        num = f"FT {empresa}2026/{k}"
        if estragar and not erro_feito and k == 4:
            data_txt = d.strftime("%d/%m/%Y")
            erro_feito = True
            estrago(ficheiro, num, "InvoiceDate", "data fora do formato xs:date", data_txt,
                    "XSD falha -> ficheiro inteiro para quarentena XSD_INVALIDO")
        out += ["      <Invoice>", f"        <InvoiceNo>{num}</InvoiceNo>",
                f"        <InvoiceDate>{data_txt}</InvoiceDate>", f"        <CustomerID>{cid}</CustomerID>"]
        out += linhas
        out += ["        <DocumentTotals>", f"          <NetTotal>{liquido:.2f}</NetTotal>",
                f"          <TaxPayable>{iva:.2f}</TaxPayable>",
                f"          <GrossTotal>{liquido + iva:.2f}</GrossTotal>", "        </DocumentTotals>",
                "      </Invoice>"]
    out += ["    </SalesInvoices>", "  </SourceDocuments>", "</AuditFile>"]
    with open(os.path.join(ENTRADA, ficheiro), "w", encoding="utf-8") as f:
        f.write("\n".join(out) + "\n")


# Clínica: os clientes do SAF-T são os mesmos do CRM (CSV) -> o lookup encontra-os
saft("A", "509876543", pessoasA[:25], 30, "saft_clinica_sorriso_2026.xml")
# TechCávado: clientes que não existem no CRM + 1 fatura com data inválida
saft("C", "514567890", [pessoa() for _ in range(15)], 20, "saft_techcavado_2026.xml", estragar=True)
estrago("saft_techcavado_2026.xml", "(ficheiro)", "CustomerTaxID", "clientes sem correspondência no CRM",
        "", "lookup não encontra -> constatação CLIENTE_SEM_CRM")

# ------------------------------------------ CIRCUITO 3: tickets (MQTT)
MODELOS_PII = [
    ("Bom dia, o meu NIF é {nif_esp} e a fatura veio sem ele.", "NIF"),
    ("Por favor liguem-me para o {tel_fmt}, ninguém atende na loja.", "TELEFONE"),
    ("Enviem a resposta para {email}, obrigado.", "EMAIL"),
    ("Quero o reembolso para o IBAN PT50 0035 0651 {iban} 05.", "IBAN"),
    ("Moro na {rua}, {cp} {cidade} e a encomenda não chegou.", "MORADA"),
    ("Tenho diabetes tipo 2, posso fazer o tratamento na mesma?", "SAUDE"),
    ("O meu cartão de cidadão é {cc} e preciso de alterar os dados.", "CC"),
    ("NIF {nif} / tel {tel} / email {email} - por favor atualizem a minha ficha.", "NIF+TELEFONE+EMAIL"),
]
MODELOS_OK = [
    "A aplicação não abre desde a última atualização.",
    "Qual é o horário de funcionamento no feriado?",
    "Gostaria de saber se têm o modelo em stock.",
    "Excelente atendimento, obrigado!",
    "Posso alterar a marcação de quinta para sexta?",
    "O pagamento por MB Way falhou duas vezes.",
]
ASSUNTOS = ["Faturação", "Marcação", "Reclamação", "Pedido de informação", "Dados pessoais", "Suporte técnico"]
CANAIS = ["email", "formulario_web", "chat", "app"]

tickets = []
for i in range(1, 61):
    emp = random.choice("ABC")
    p = pessoa()
    if random.random() < 0.55:
        modelo, tipos = random.choice(MODELOS_PII)
    else:
        modelo, tipos = random.choice(MODELOS_OK), ""
    t = p["tel"]
    msg = modelo.format(
        nif=p["nif"], nif_esp=f"{p['nif'][:3]} {p['nif'][3:6]} {p['nif'][6:]}",
        tel=t, tel_fmt=random.choice([t, f"+351 {t[:3]} {t[3:6]} {t[6:]}", f"{t[:3]}-{t[3:6]}-{t[6:]}"]),
        email=p["email"], rua=p["rua"], cp=p["cp"], cidade=p["cidade"],
        iban="".join(str(random.randint(0, 9)) for _ in range(11)),
        cc=f"{random.randint(10000000, 39999999)} {random.randint(0, 9)} ZZ{random.randint(0, 9)}")
    tid = f"TK-{i:04d}"
    tickets.append({"ticket_id": tid, "empresa": emp, "empresa_nome": EMPRESAS[emp],
                    "canal": random.choice(CANAIS), "assunto": random.choice(ASSUNTOS),
                    "cliente_nome": p["nome"], "mensagem": msg})
    if tipos:
        estrago("tickets (MQTT)", tid, "mensagem", "PII no texto livre: " + tipos, msg,
                "detetar com regex, mascarar e gerar constatação")
# 2 tickets repetidos (reenvio do mesmo evento) e 1 com JSON incompleto
tickets.append(dict(tickets[5])); estrago("tickets (MQTT)", tickets[5]["ticket_id"], "(evento)", "evento repetido", "", "ignorar repetido (idempotência)")
tickets.append(dict(tickets[17])); estrago("tickets (MQTT)", tickets[17]["ticket_id"], "(evento)", "evento repetido", "", "ignorar repetido (idempotência)")
tickets.append({"ticket_id": "TK-9999", "empresa": "B", "canal": "chat"})
estrago("tickets (MQTT)", "TK-9999", "mensagem", "evento sem mensagem nem assunto", "", "quarentena CAMPO_OBRIGATORIO_NULO")

with open(os.path.join(ENTRADA, "tickets_exemplo.json"), "w", encoding="utf-8") as f:
    json.dump(tickets, f, ensure_ascii=False, indent=2)

# ------------------------------------------------------- mapa de estragos
with open(os.path.join(ESPERADO, "mapa_estragos.csv"), "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f, delimiter=";")
    w.writerow(["ficheiro", "registo", "campo", "estrago", "valor_injetado", "resultado_esperado"])
    w.writerows(mapa)

print(f"{len(mapa)} estragos injetados. Ficheiros em {ENTRADA}")
