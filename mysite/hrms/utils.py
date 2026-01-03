"""
Utility functions for generating PDF salary slips
"""
from io import BytesIO
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
from django.utils import timezone


def generate_salary_slip_pdf(payroll, month=None, year=None):
    """
    Generate a PDF salary slip for the given payroll record
    
    Args:
        payroll: Payroll object
        month: Month number (1-12), defaults to current month
        year: Year, defaults to current year
    
    Returns:
        BytesIO buffer containing the PDF
    """
    buffer = BytesIO()
    
    # Use current month/year if not provided
    if month is None or year is None:
        now = timezone.now()
        month = month or now.month
        year = year or now.year
    
    month_names = ['', 'January', 'February', 'March', 'April', 'May', 'June',
                   'July', 'August', 'September', 'October', 'November', 'December']
    month_name = month_names[month]
    
    # Create the PDF document
    doc = SimpleDocTemplate(buffer, pagesize=A4,
                           rightMargin=72, leftMargin=72,
                           topMargin=72, bottomMargin=18)
    
    # Container for the 'Flowable' objects
    elements = []
    
    # Define styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#6366f1'),
        spaceAfter=30,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#1f2937'),
        spaceAfter=12,
        fontName='Helvetica-Bold'
    )
    
    normal_style = styles['Normal']
    
    # Title
    title = Paragraph("SALARY SLIP", title_style)
    elements.append(title)
    elements.append(Spacer(1, 12))
    
    # Period
    period = Paragraph(f"<b>Period:</b> {month_name} {year}", normal_style)
    elements.append(period)
    elements.append(Spacer(1, 20))
    
    # Employee Details
    employee_heading = Paragraph("Employee Details", heading_style)
    elements.append(employee_heading)
    
    employee_data = [
        ['Employee ID:', payroll.user.employee_id],
        ['Name:', payroll.user.get_full_name()],
        ['Email:', payroll.user.email],
        ['Designation:', getattr(payroll.user.profile, 'designation', 'N/A')],
        ['Department:', getattr(payroll.user.profile, 'department', 'N/A')],
    ]
    
    employee_table = Table(employee_data, colWidths=[2*inch, 4*inch])
    employee_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#374151')),
        ('TEXTCOLOR', (1, 0), (1, -1), colors.HexColor('#6b7280')),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    elements.append(employee_table)
    elements.append(Spacer(1, 20))
    
    # Salary Breakdown
    salary_heading = Paragraph("Salary Breakdown", heading_style)
    elements.append(salary_heading)
    
    # Earnings Table
    earnings_data = [
        ['EARNINGS', 'AMOUNT (₹)'],
        ['Basic Salary', f'{payroll.basic_salary:,.2f}'],
        ['House Rent Allowance', f'{payroll.house_rent_allowance:,.2f}'],
        ['Transport Allowance', f'{payroll.transport_allowance:,.2f}'],
        ['Medical Allowance', f'{payroll.medical_allowance:,.2f}'],
        ['Other Allowances', f'{payroll.other_allowances:,.2f}'],
        ['', ''],
        ['GROSS SALARY', f'{payroll.gross_salary:,.2f}'],
    ]
    
    earnings_table = Table(earnings_data, colWidths=[3*inch, 2*inch])
    earnings_table.setStyle(TableStyle([
        # Header row
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#6366f1')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        
        # Data rows
        ('FONTNAME', (0, 1), (0, -2), 'Helvetica'),
        ('FONTNAME', (1, 1), (1, -2), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -2), 10),
        ('ALIGN', (1, 1), (1, -1), 'RIGHT'),
        
        # Total row
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#f3f4f6')),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, -1), (-1, -1), 11),
        ('TEXTCOLOR', (0, -1), (-1, -1), colors.HexColor('#059669')),
        
        # Grid
        ('GRID', (0, 0), (-1, -2), 0.5, colors.grey),
        ('BOX', (0, 0), (-1, -1), 1, colors.black),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
    ]))
    elements.append(earnings_table)
    elements.append(Spacer(1, 15))
    
    # Deductions Table
    deductions_data = [
        ['DEDUCTIONS', 'AMOUNT (₹)'],
        ['Provident Fund', f'{payroll.provident_fund:,.2f}'],
        ['Professional Tax', f'{payroll.professional_tax:,.2f}'],
        ['Income Tax', f'{payroll.income_tax:,.2f}'],
        ['Other Deductions', f'{payroll.other_deductions:,.2f}'],
        ['', ''],
        ['TOTAL DEDUCTIONS', f'{payroll.total_deductions:,.2f}'],
    ]
    
    deductions_table = Table(deductions_data, colWidths=[3*inch, 2*inch])
    deductions_table.setStyle(TableStyle([
        # Header row
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#ef4444')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        
        # Data rows
        ('FONTNAME', (0, 1), (0, -2), 'Helvetica'),
        ('FONTNAME', (1, 1), (1, -2), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -2), 10),
        ('ALIGN', (1, 1), (1, -1), 'RIGHT'),
        
        # Total row
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#f3f4f6')),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, -1), (-1, -1), 11),
        ('TEXTCOLOR', (0, -1), (-1, -1), colors.HexColor('#dc2626')),
        
        # Grid
        ('GRID', (0, 0), (-1, -2), 0.5, colors.grey),
        ('BOX', (0, 0), (-1, -1), 1, colors.black),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
    ]))
    elements.append(deductions_table)
    elements.append(Spacer(1, 20))
    
    # Net Salary
    net_salary_data = [
        ['NET SALARY (Take Home)', f'₹ {payroll.net_salary:,.2f}'],
    ]
    
    net_salary_table = Table(net_salary_data, colWidths=[3*inch, 2*inch])
    net_salary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#10b981')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 14),
        ('ALIGN', (0, 0), (0, 0), 'LEFT'),
        ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
        ('BOX', (0, 0), (-1, -1), 2, colors.HexColor('#10b981')),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ('TOPPADDING', (0, 0), (-1, -1), 12),
    ]))
    elements.append(net_salary_table)
    elements.append(Spacer(1, 30))
    
    # Footer
    footer_text = f"<i>This is a computer-generated salary slip and does not require a signature.<br/>Generated on: {timezone.now().strftime('%d %B %Y at %I:%M %p')}</i>"
    footer = Paragraph(footer_text, ParagraphStyle('Footer', parent=normal_style, fontSize=8, textColor=colors.grey, alignment=TA_CENTER))
    elements.append(footer)
    
    # Build PDF
    doc.build(elements)
    
    # Get the value of the BytesIO buffer and return it
    pdf = buffer.getvalue()
    buffer.close()
    return pdf
