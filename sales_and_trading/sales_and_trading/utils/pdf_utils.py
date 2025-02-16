# sales_and_trading/utils/pdf_utils.py

from io import BytesIO
from django.http import HttpResponse
from django.template.loader import render_to_string
from weasyprint import HTML
from django.conf import settings

def render_pdf(template_src, context_dict=None):
    if context_dict is None:
        context_dict = {}
    html_string = render_to_string(template_src, context_dict)
    html = HTML(string=html_string, base_url=settings.BASE_DIR)
    pdf_io = BytesIO()
    html.write_pdf(target=pdf_io)
    return pdf_io.getvalue()

def pdf_response(pdf_content, filename="document.pdf"):
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    response.write(pdf_content)
    return response
