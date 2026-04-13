from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.platypus import (SimpleDocTemplate, Table, TableStyle,
                                 Paragraph, Spacer, HRFlowable, PageBreak)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from datetime import datetime
import os

ORANGE = colors.HexColor('#FF6B35')
DARK   = colors.HexColor('#1A1A2E')
LIGHT  = colors.HexColor('#FFF8F5')
GREY   = colors.HexColor('#F5F5F5')


def _styles():
    s = getSampleStyleSheet()
    title  = ParagraphStyle('HTitle',  fontSize=20, textColor=ORANGE,
                             alignment=TA_CENTER, fontName='Helvetica-Bold', spaceAfter=2)
    sub    = ParagraphStyle('HSub',    fontSize=9,  textColor=colors.grey,
                             alignment=TA_CENTER, spaceAfter=4)
    label  = ParagraphStyle('HLabel',  fontSize=8,  textColor=colors.grey,
                             fontName='Helvetica')
    bold   = ParagraphStyle('HBold',   fontSize=10, textColor=DARK,
                             fontName='Helvetica-Bold')
    normal = ParagraphStyle('HNorm',   fontSize=9,  textColor=DARK)
    head   = ParagraphStyle('HHead',   fontSize=11, textColor=DARK,
                             fontName='Helvetica-Bold', spaceAfter=4)
    footer = ParagraphStyle('HFoot',   fontSize=7,  textColor=colors.grey,
                             alignment=TA_CENTER)
    copy_tag = ParagraphStyle('HCopy', fontSize=13, textColor=ORANGE,
                               fontName='Helvetica-Bold', alignment=TA_RIGHT)
    return s, title, sub, label, bold, normal, head, footer, copy_tag


def _bill_story(order, items, shop, copy_label):
    s, title, sub, label, bold, normal, head, footer, copy_tag = _styles()
    story = []

    story.append(Paragraph("🍦  HANGYO ICE CREAM", title))
    story.append(Paragraph("Distribution Invoice", sub))
    story.append(Paragraph(copy_label, copy_tag))
    story.append(HRFlowable(width="100%", thickness=2, color=ORANGE))
    story.append(Spacer(1, 6))

    pending = order.get('total_amount', 0) - order.get('paid_amount', 0)
    due_date = order.get('due_date', '') or '—'

    info = [
        [Paragraph("BILL TO:", label), Paragraph("BILL DETAILS:", label)],
        [Paragraph(str(shop.get('name', '')), bold),
         Paragraph(f"Bill No: <b>{order.get('bill_no', '')}</b>", normal)],
        [Paragraph(str(shop.get('owner_name', '') or ''), normal),
         Paragraph(f"Date: {order.get('order_date', '')}", normal)],
        [Paragraph(str(shop.get('phone', '') or ''), normal),
         Paragraph(f"Due Date: {due_date}", normal)],
        [Paragraph(str(shop.get('address', '') or ''), normal),
         Paragraph(f"Status: {order.get('status', '')}", normal)],
    ]
    tbl = Table(info, colWidths=[95*mm, 95*mm])
    tbl.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
    ]))
    story.append(tbl)
    story.append(Spacer(1, 8))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.lightgrey))
    story.append(Spacer(1, 6))
    story.append(Paragraph("ORDER ITEMS", head))

    tdata = [['#', 'Item Name', 'Category', 'Qty', 'Unit Price (₹)', 'Total (₹)']]
    for i, item in enumerate(items, 1):
        tdata.append([
            str(i),
            str(item.get('name', '')),
            str(item.get('category', '')),
            str(item.get('quantity', 0)),
            f"{float(item.get('unit_price', 0)):.2f}",
            f"{float(item.get('total_price', 0)):.2f}",
        ])

    total   = float(order.get('total_amount', 0))
    paid    = float(order.get('paid_amount', 0))
    pend    = total - paid

    tdata += [
        ['', '', '', '', 'Sub Total:', f"₹{total:.2f}"],
        ['', '', '', '', 'Paid:', f"₹{paid:.2f}"],
        ['', '', '', '', 'PENDING:', f"₹{pend:.2f}"],
    ]
    n = len(tdata)
    cw = [10*mm, 62*mm, 30*mm, 18*mm, 35*mm, 35*mm]
    t = Table(tdata, colWidths=cw)
    t.setStyle(TableStyle([
        ('BACKGROUND',  (0,0), (-1,0), ORANGE),
        ('TEXTCOLOR',   (0,0), (-1,0), colors.white),
        ('FONTNAME',    (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE',    (0,0), (-1,-1), 8),
        ('ALIGN',       (3,0), (-1,-1), 'RIGHT'),
        ('ALIGN',       (0,0), (2,-1), 'CENTER'),
        ('ROWBACKGROUNDS', (0,1), (-1, n-4), [LIGHT, colors.white]),
        ('GRID',        (0,0), (-1, n-4), 0.4, colors.lightgrey),
        ('LINEABOVE',   (4, n-3), (-1,-1), 1, ORANGE),
        ('FONTNAME',    (4, n-3), (-1,-1), 'Helvetica-Bold'),
        ('BACKGROUND',  (4, n-1), (-1,-1), colors.HexColor('#FFE0D0')),
        ('TEXTCOLOR',   (4, n-1), (-1,-1), ORANGE),
        ('TOPPADDING',  (0,0), (-1,-1), 5),
        ('BOTTOMPADDING',(0,0), (-1,-1), 5),
        ('LEFTPADDING', (0,0), (-1,-1), 5),
    ]))
    story.append(t)
    story.append(Spacer(1, 14))

    # Signature row
    sig = [['Distributor Signature', 'Shop Signature', 'Received By']]
    sig_row = [['________________', '________________', '________________']]
    sig_tbl = Table(sig + sig_row, colWidths=[63*mm, 63*mm, 64*mm])
    sig_tbl.setStyle(TableStyle([
        ('ALIGN',    (0,0), (-1,-1), 'CENTER'),
        ('FONTSIZE', (0,0), (-1,-1), 8),
        ('TOPPADDING', (0,0), (-1,-1), 12),
    ]))
    story.append(sig_tbl)
    story.append(Spacer(1, 8))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.lightgrey))
    story.append(Spacer(1, 4))
    story.append(Paragraph("Thank you for your business!  |  Hangyo Ice Cream Distribution", footer))
    story.append(Paragraph(f"Printed: {datetime.now().strftime('%d %b %Y, %I:%M %p')}", footer))
    return story


def generate_bill_pdf(order, items, shop, output_path):
    doc = SimpleDocTemplate(output_path, pagesize=A4,
                            rightMargin=15*mm, leftMargin=15*mm,
                            topMargin=12*mm, bottomMargin=12*mm)
    story = []
    story += _bill_story(order, items, shop, "📋  COPY 1 — SHOP COPY")
    story.append(PageBreak())
    story += _bill_story(order, items, shop, "📋  COPY 2 — DISTRIBUTOR COPY")
    doc.build(story)
    return output_path


def generate_company_order_pdf(order, items, output_path):
    doc = SimpleDocTemplate(output_path, pagesize=A4,
                            rightMargin=15*mm, leftMargin=15*mm,
                            topMargin=12*mm, bottomMargin=12*mm)
    s, title, sub, label, bold, normal, head, footer, copy_tag = _styles()
    story = []
    story.append(Paragraph("🍦  HANGYO ICE CREAM", title))
    story.append(Paragraph("Stock Order Request to Company", sub))
    story.append(HRFlowable(width="100%", thickness=2, color=ORANGE))
    story.append(Spacer(1, 10))
    story.append(Paragraph(f"Order Date: <b>{order.get('order_date','')}</b>   |   Order ID: <b>CO-{order.get('id','')}</b>", normal))
    if order.get('notes'):
        story.append(Paragraph(f"Notes: {order.get('notes','')}", normal))
    story.append(Spacer(1, 10))
    story.append(Paragraph("ITEMS REQUIRED", head))

    tdata = [['#', 'Product Name', 'Category', 'Quantity Needed']]
    for i, item in enumerate(items, 1):
        tdata.append([str(i), str(item.get('name','')), str(item.get('category','')), str(item.get('quantity',0))])
    t = Table(tdata, colWidths=[12*mm, 85*mm, 55*mm, 38*mm])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), ORANGE),
        ('TEXTCOLOR',  (0,0), (-1,0), colors.white),
        ('FONTNAME',   (0,0), (-1,0), 'Helvetica-Bold'),
        ('ALIGN',      (0,0), (-1,-1), 'CENTER'),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [LIGHT, colors.white]),
        ('GRID',       (0,0), (-1,-1), 0.4, colors.lightgrey),
        ('FONTSIZE',   (0,0), (-1,-1), 9),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(t)
    story.append(Spacer(1, 14))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.lightgrey))
    story.append(Spacer(1, 4))
    story.append(Paragraph(f"Hangyo Ice Cream Distribution  —  Printed: {datetime.now().strftime('%d %b %Y, %I:%M %p')}", footer))
    doc.build(story)
    return output_path


def generate_delivery_route_pdf(delivery_date, orders, output_path):
    doc = SimpleDocTemplate(output_path, pagesize=A4,
                            rightMargin=15*mm, leftMargin=15*mm,
                            topMargin=12*mm, bottomMargin=12*mm)
    s, title, sub, label, bold, normal, head, footer, copy_tag = _styles()
    story = []
    story.append(Paragraph("🍦  HANGYO ICE CREAM", title))
    story.append(Paragraph(f"Daily Delivery Route — {delivery_date}", sub))
    story.append(HRFlowable(width="100%", thickness=2, color=ORANGE))
    story.append(Spacer(1, 10))

    tdata = [['#', 'Shop', 'Phone', 'Address', 'Bill No', 'Items', 'Total ₹', '✓']]
    for i, o in enumerate(orders, 1):
        tdata.append([
            str(i),
            str(o.get('shop_name', '')),
            str(o.get('phone', '') or ''),
            str(o.get('address', '') or ''),
            str(o.get('bill_no', '')),
            str(o.get('items_count', '')),
            f"₹{float(o.get('total_amount',0)):.0f}",
            '',
        ])
    cw = [8*mm, 42*mm, 27*mm, 45*mm, 22*mm, 12*mm, 20*mm, 10*mm]
    t = Table(tdata, colWidths=cw)
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), ORANGE),
        ('TEXTCOLOR',  (0,0), (-1,0), colors.white),
        ('FONTNAME',   (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE',   (0,0), (-1,-1), 7),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [LIGHT, colors.white]),
        ('GRID',       (0,0), (-1,-1), 0.4, colors.lightgrey),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('ALIGN',      (0,0), (-1,-1), 'CENTER'),
        ('ALIGN',      (1,1), (3,-1), 'LEFT'),
    ]))
    story.append(t)
    story.append(Spacer(1, 14))
    story.append(Paragraph(f"Total Stops: {len(orders)}  |  Printed: {datetime.now().strftime('%d %b %Y, %I:%M %p')}", footer))
    doc.build(story)
    return output_path


def generate_monthly_report_pdf(month_label, data, output_path):
    doc = SimpleDocTemplate(output_path, pagesize=A4,
                            rightMargin=15*mm, leftMargin=15*mm,
                            topMargin=12*mm, bottomMargin=12*mm)
    s, title, sub, label, bold, normal, head, footer, copy_tag = _styles()
    story = []
    story.append(Paragraph("🍦  HANGYO ICE CREAM", title))
    story.append(Paragraph(f"Monthly Sales Report — {month_label}", sub))
    story.append(HRFlowable(width="100%", thickness=2, color=ORANGE))
    story.append(Spacer(1, 10))

    summary = data.get('summary', {})
    sdata = [
        ['Total Orders', str(summary.get('total_orders', 0))],
        ['Total Billed', f"₹{float(summary.get('total_billed',0)):.2f}"],
        ['Total Collected', f"₹{float(summary.get('total_collected',0)):.2f}"],
        ['Total Pending', f"₹{float(summary.get('total_pending',0)):.2f}"],
        ['Deliveries Done', str(summary.get('delivered', 0))],
    ]
    st = Table(sdata, colWidths=[80*mm, 60*mm])
    st.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), ORANGE),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('ROWBACKGROUNDS', (0,0), (-1,-1), [LIGHT, colors.white]),
        ('GRID', (0,0), (-1,-1), 0.4, colors.lightgrey),
        ('FONTSIZE', (0,0), (-1,-1), 9),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(Paragraph("Summary", head))
    story.append(st)
    story.append(Spacer(1, 12))

    if data.get('top_products'):
        story.append(Paragraph("Top Selling Products", head))
        pdata = [['Product', 'Category', 'Total Qty Sold', 'Total Revenue']]
        for p in data['top_products']:
            pdata.append([str(p.get('name','')), str(p.get('category','')),
                          str(p.get('total_qty',0)), f"₹{float(p.get('revenue',0)):.2f}"])
        pt = Table(pdata, colWidths=[70*mm, 40*mm, 40*mm, 40*mm])
        pt.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), ORANGE),
            ('TEXTCOLOR',  (0,0), (-1,0), colors.white),
            ('FONTNAME',   (0,0), (-1,0), 'Helvetica-Bold'),
            ('ROWBACKGROUNDS', (0,1), (-1,-1), [LIGHT, colors.white]),
            ('GRID',       (0,0), (-1,-1), 0.4, colors.lightgrey),
            ('FONTSIZE',   (0,0), (-1,-1), 9),
            ('TOPPADDING', (0,0), (-1,-1), 5),
            ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ]))
        story.append(pt)
        story.append(Spacer(1, 12))

    if data.get('top_shops'):
        story.append(Paragraph("Top Shops by Revenue", head))
        shdata = [['Shop Name', 'Orders', 'Total Billed', 'Paid', 'Pending']]
        for sh in data['top_shops']:
            shdata.append([
                str(sh.get('name','')), str(sh.get('orders',0)),
                f"₹{float(sh.get('billed',0)):.2f}",
                f"₹{float(sh.get('paid',0)):.2f}",
                f"₹{float(sh.get('pending',0)):.2f}",
            ])
        sht = Table(shdata, colWidths=[60*mm, 20*mm, 35*mm, 35*mm, 35*mm])
        sht.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), ORANGE),
            ('TEXTCOLOR',  (0,0), (-1,0), colors.white),
            ('FONTNAME',   (0,0), (-1,0), 'Helvetica-Bold'),
            ('ROWBACKGROUNDS', (0,1), (-1,-1), [LIGHT, colors.white]),
            ('GRID',       (0,0), (-1,-1), 0.4, colors.lightgrey),
            ('FONTSIZE',   (0,0), (-1,-1), 9),
            ('TOPPADDING', (0,0), (-1,-1), 5),
            ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ]))
        story.append(sht)

    story.append(Spacer(1, 14))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.lightgrey))
    story.append(Paragraph(f"Hangyo Distribution  |  Printed: {datetime.now().strftime('%d %b %Y, %I:%M %p')}", footer))
    doc.build(story)
    return output_path
