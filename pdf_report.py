from io import BytesIO
import json
from datetime import datetime

from reportlab.lib.pagesizes import A4
from reportlab.lib.colors import HexColor, black, white
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas


PAGE_WIDTH, PAGE_HEIGHT = A4


def _draw_wrapped_text(c, text, x, y, max_width, line_height=14, font_name="Helvetica", font_size=10):
    """
    Escreve texto com quebra automática de linha.
    Retorna o novo y após desenhar o bloco.
    """
    c.setFont(font_name, font_size)

    words = (text or "").split()
    if not words:
        return y

    line = ""
    lines = []

    for word in words:
        test_line = f"{line} {word}".strip()
        if c.stringWidth(test_line, font_name, font_size) <= max_width:
            line = test_line
        else:
            if line:
                lines.append(line)
            line = word

    if line:
        lines.append(line)

    for line in lines:
        c.drawString(x, y, line)
        y -= line_height

    return y


def _draw_label_value(c, label, value, x, y, label_width=120, font_size=10):
    c.setFont("Helvetica-Bold", font_size)
    c.drawString(x, y, f"{label}")
    c.setFont("Helvetica", font_size)
    c.drawString(x + label_width, y, f"{value if value not in [None, ''] else 'N/D'}")
    return y


def _risk_colors(risk: str):
    risk = (risk or "").lower()

    if risk == "baixo":
        return {
            "bg": HexColor("#DCFCE7"),
            "border": HexColor("#22C55E"),
            "text": HexColor("#166534"),
            "title": "Baixo Risco"
        }

    if risk in ("medio", "médio", "medio_baixo"):
        return {
            "bg": HexColor("#FEF3C7"),
            "border": HexColor("#F59E0B"),
            "text": HexColor("#92400E"),
            "title": "Risco Médio"
        }

    return {
        "bg": HexColor("#FEE2E2"),
        "border": HexColor("#EF4444"),
        "text": HexColor("#991B1B"),
        "title": "Alto Risco"
    }


def _safe_observacoes(value):
    if isinstance(value, list):
        return value
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
            if isinstance(parsed, list):
                return parsed
        except Exception:
            return [value]
    return []


def generate_analysis_report_pdf(analysis: dict, user: dict | None = None) -> BytesIO:
    """
    Gera o PDF do relatório da análise e retorna um BytesIO pronto para resposta/download.
    `analysis` deve ser um dicionário com os campos vindos de AnalysisResult.
    `user` é opcional, para exibir nome/e-mail do usuário no relatório.
    """
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    c.setTitle(f"relatorio_analise_{analysis.get('id', 'sem_id')}")

    margin_x = 18 * mm
    y = PAGE_HEIGHT - 20 * mm

    # =========================
    # CABEÇALHO
    # =========================
    c.setFillColor(HexColor("#0F172A"))
    c.rect(0, PAGE_HEIGHT - 35 * mm, PAGE_WIDTH, 35 * mm, stroke=0, fill=1)

    c.setFillColor(white)
    c.setFont("Helvetica-Bold", 20)
    c.drawString(margin_x, PAGE_HEIGHT - 18 * mm, "Boleto Anti-Fraude")

    c.setFont("Helvetica", 11)
    c.drawString(margin_x, PAGE_HEIGHT - 25 * mm, "Relatório técnico de análise automatizada")

    y = PAGE_HEIGHT - 45 * mm

    # =========================
    # CAIXA DE RESULTADO
    # =========================
    risk_info = _risk_colors(analysis.get("risco"))
    c.setFillColor(risk_info["bg"])
    c.setStrokeColor(risk_info["border"])
    c.roundRect(margin_x, y - 18 * mm, PAGE_WIDTH - (2 * margin_x), 16 * mm, 8, stroke=1, fill=1)

    c.setFillColor(risk_info["text"])
    c.setFont("Helvetica-Bold", 16)
    c.drawString(margin_x + 6 * mm, y - 9 * mm, f"Resultado: {risk_info['title']}")

    c.setFont("Helvetica", 11)
    c.drawString(margin_x + 6 * mm, y - 14 * mm, f"Score: {analysis.get('score', 'N/D')}")

    y -= 28 * mm

    # =========================
    # IDENTIFICAÇÃO DA ANÁLISE
    # =========================
    c.setFillColor(black)
    c.setFont("Helvetica-Bold", 13)
    c.drawString(margin_x, y, "1. Identificação da análise")
    y -= 8 * mm

    _draw_label_value(c, "ID da análise:", analysis.get("id"), margin_x, y)
    y -= 6 * mm

    created_at = analysis.get("created_at")
    if created_at:
        try:
            created_at = datetime.fromisoformat(created_at.replace("Z", ""))
            created_at_str = created_at.strftime("%d/%m/%Y %H:%M:%S")
        except Exception:
            created_at_str = str(created_at)
    else:
        created_at_str = "N/D"

    _draw_label_value(c, "Data/Hora:", created_at_str, margin_x, y)
    y -= 6 * mm

    _draw_label_value(c, "Origem:", analysis.get("source_type"), margin_x, y)
    y -= 6 * mm

    _draw_label_value(c, "Arquivo fonte:", analysis.get("source_file_name"), margin_x, y)
    y -= 6 * mm

    _draw_label_value(c, "Método extração:", analysis.get("extraction_method"), margin_x, y)
    y -= 8 * mm

    if user:
        _draw_label_value(c, "Usuário:", user.get("name"), margin_x, y)
        y -= 6 * mm
        _draw_label_value(c, "E-mail:", user.get("email"), margin_x, y)
        y -= 8 * mm

    # =========================
    # DADOS DO DOCUMENTO
    # =========================
    c.setFont("Helvetica-Bold", 13)
    c.drawString(margin_x, y, "2. Dados do documento")
    y -= 8 * mm

    _draw_label_value(c, "Linha digitável:", analysis.get("linha_digitavel"), margin_x, y)
    y -= 6 * mm

    _draw_label_value(c, "Beneficiário:", analysis.get("beneficiario"), margin_x, y)
    y -= 6 * mm

    _draw_label_value(c, "Tipo:", analysis.get("tipo"), margin_x, y)
    y -= 6 * mm

    _draw_label_value(c, "Banco/Emissor:", analysis.get("banco_nome"), margin_x, y)
    y -= 6 * mm

    _draw_label_value(c, "Categoria:", analysis.get("categoria"), margin_x, y)
    y -= 6 * mm

    _draw_label_value(c, "Valor:", analysis.get("valor"), margin_x, y)
    y -= 6 * mm

    _draw_label_value(c, "Vencimento:", analysis.get("vencimento"), margin_x, y)
    y -= 6 * mm

    _draw_label_value(c, "Segmento:", analysis.get("segmento"), margin_x, y)
    y -= 6 * mm

    _draw_label_value(c, "Desc. segmento:", analysis.get("segmento_descricao"), margin_x, y)
    y -= 6 * mm

    _draw_label_value(c, "Cód. empresa/órgão:", analysis.get("empresa_orgao_codigo"), margin_x, y)
    y -= 10 * mm

    # =========================
    # VALIDAÇÕES
    # =========================
    c.setFont("Helvetica-Bold", 13)
    c.drawString(margin_x, y, "3. Validações estruturais")
    y -= 8 * mm

    dv_campos = "Válido" if analysis.get("valido_dv_campos") else "Inválido"
    dv_geral = "Válido" if analysis.get("valido_dv_geral") else "Inválido"

    _draw_label_value(c, "DV dos campos:", dv_campos, margin_x, y)
    y -= 6 * mm

    _draw_label_value(c, "DV geral:", dv_geral, margin_x, y)
    y -= 10 * mm

    # =========================
    # MENSAGEM / CONCLUSÃO
    # =========================
    c.setFont("Helvetica-Bold", 13)
    c.drawString(margin_x, y, "4. Conclusão do sistema")
    y -= 8 * mm

    y = _draw_wrapped_text(
        c,
        analysis.get("mensagem") or "N/D",
        margin_x,
        y,
        PAGE_WIDTH - (2 * margin_x),
        line_height=14,
        font_name="Helvetica",
        font_size=10
    )
    y -= 6 * mm

    # =========================
    # OBSERVAÇÕES
    # =========================
    c.setFont("Helvetica-Bold", 13)
    c.drawString(margin_x, y, "5. Observações técnicas")
    y -= 8 * mm

    observacoes = _safe_observacoes(analysis.get("observacoes"))

    if observacoes:
        for i, obs in enumerate(observacoes, start=1):
            y = _draw_wrapped_text(
                c,
                f"{i}. {obs}",
                margin_x,
                y,
                PAGE_WIDTH - (2 * margin_x),
                line_height=14,
                font_name="Helvetica",
                font_size=10
            )
            y -= 2 * mm
    else:
        y = _draw_wrapped_text(
            c,
            "Nenhuma observação técnica adicional.",
            margin_x,
            y,
            PAGE_WIDTH - (2 * margin_x),
            line_height=14,
            font_name="Helvetica",
            font_size=10
        )

    y -= 8 * mm

    # =========================
    # DISCLAMER
    # =========================
    c.setStrokeColor(HexColor("#CBD5E1"))
    c.line(margin_x, y, PAGE_WIDTH - margin_x, y)
    y -= 8 * mm

    c.setFont("Helvetica-Bold", 11)
    c.drawString(margin_x, y, "Aviso importante")
    y -= 6 * mm

    disclaimer = (
        "Este relatório representa uma análise automatizada de risco com base em estrutura, "
        "campos validáveis, contexto do beneficiário e heurísticas antifraude. "
        "Ele não substitui validação oficial junto ao emissor, banco, órgão arrecadador "
        "ou beneficiário final. Antes de efetuar qualquer pagamento, confirme os dados do recebedor."
    )

    y = _draw_wrapped_text(
        c,
        disclaimer,
        margin_x,
        y,
        PAGE_WIDTH - (2 * margin_x),
        line_height=13,
        font_name="Helvetica",
        font_size=9
    )

    # =========================
    # RODAPÉ
    # =========================
    c.setFont("Helvetica", 8)
    c.setFillColor(HexColor("#64748B"))
    c.drawRightString(PAGE_WIDTH - margin_x, 12 * mm, "Boleto Anti-Fraude • Relatório técnico automatizado")

    c.save()
    buffer.seek(0)
    return buffer