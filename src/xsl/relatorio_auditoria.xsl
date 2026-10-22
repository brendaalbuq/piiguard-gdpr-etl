<?xml version="1.0" encoding="UTF-8"?>
<!-- Transforma data/output/resumo_auditoria_loteN.xml (gerado pela c2_03) em HTML; usado pelo Job c2_faturas. -->
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
  <xsl:output method="html" encoding="UTF-8" indent="yes"/>

  <xsl:template match="/Resumo">
    <html lang="pt">
      <head>
        <meta charset="UTF-8"/>
        <title>PiiGuard - Relatório de auditoria RGPD</title>
        <style>
          body { font-family: Segoe UI, Arial, sans-serif; margin: 32px; color: #1f2933; background: #f7f9fb; }
          h1 { color: #0e3a5a; margin-bottom: 4px; }
          h2 { color: #0e3a5a; border-bottom: 2px solid #c9e8fb; padding-bottom: 4px; margin-top: 32px; }
          p.sub { color: #52606d; margin-top: 0; }
          table { border-collapse: collapse; width: 100%; background: #fff; }
          th, td { border: 1px solid #d9e2ec; padding: 6px 10px; text-align: left; }
          th { background: #0e3a5a; color: #fff; }
          tr:nth-child(even) td { background: #f0f4f8; }
          .nota { font-size: 13px; color: #52606d; }
        </style>
      </head>
      <body>
        <h1>PiiGuard - Relatório de auditoria RGPD</h1>
        <p class="sub">Gerado automaticamente pelo Pentaho (XML + XSLT). Nenhum dado pessoal aparece em claro neste relatório.</p>

        <xsl:call-template name="secao">
          <xsl:with-param name="codigo" select="'1_lotes'"/>
          <xsl:with-param name="titulo" select="'Lotes processados e reconciliação'"/>
          <xsl:with-param name="col1" select="'Circuito'"/>
          <xsl:with-param name="col3" select="'Para onde foram os registos'"/>
        </xsl:call-template>

        <xsl:call-template name="secao">
          <xsl:with-param name="codigo" select="'2_quarentena'"/>
          <xsl:with-param name="titulo" select="'Registos em quarentena (nada foi apagado)'"/>
          <xsl:with-param name="col1" select="'Circuito'"/>
          <xsl:with-param name="col3" select="'Registos'"/>
        </xsl:call-template>

        <xsl:call-template name="secao">
          <xsl:with-param name="codigo" select="'3_constatacoes'"/>
          <xsl:with-param name="titulo" select="'Constatações da auditoria por empresa'"/>
          <xsl:with-param name="col1" select="'Empresa'"/>
          <xsl:with-param name="col3" select="'Ocorrências'"/>
        </xsl:call-template>

        <xsl:call-template name="secao">
          <xsl:with-param name="codigo" select="'4_faturas'"/>
          <xsl:with-param name="titulo" select="'Faturas exportadas (pseudonimizadas)'"/>
          <xsl:with-param name="col1" select="'Empresa'"/>
          <xsl:with-param name="col3" select="'Faturas'"/>
        </xsl:call-template>

        <p class="nota">Detalhe completo nas tabelas controlo.lote, quarentena.registo e auditoria.constatacao da base de dados piiguard.</p>
      </body>
    </html>
  </xsl:template>

  <xsl:template name="secao">
    <xsl:param name="codigo"/>
    <xsl:param name="titulo"/>
    <xsl:param name="col1"/>
    <xsl:param name="col3"/>
    <h2><xsl:value-of select="$titulo"/></h2>
    <xsl:choose>
      <xsl:when test="Linha[secao = $codigo]">
        <table>
          <tr><th><xsl:value-of select="$col1"/></th><th>Item</th><th><xsl:value-of select="$col3"/></th></tr>
          <xsl:for-each select="Linha[secao = $codigo]">
            <tr>
              <td><xsl:value-of select="grupo"/></td>
              <td><xsl:value-of select="item"/></td>
              <td><xsl:value-of select="valor"/></td>
            </tr>
          </xsl:for-each>
        </table>
      </xsl:when>
      <xsl:otherwise><p class="nota">Sem registos.</p></xsl:otherwise>
    </xsl:choose>
  </xsl:template>
</xsl:stylesheet>
