# functions from other files here are for testing purpose. Delete later. Only keep generate()
import time
import statistics
from timeit import default_timer as timer
from multiprocessing import Process, Queue
import os
import datetime
import subprocess
import queue


import utils as utils
import convert as convert
import locate as locate
import report as report

from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.lib import colors
from reportlab.graphics.charts.piecharts import Pie
from reportlab.graphics.shapes import *  # not used?
from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics.charts.textlabels import Label

import energyusage.convert as convert

year = "2016"

styles = getSampleStyleSheet()
TitleStyle = ParagraphStyle(name='Normal', fontSize=16, alignment= TA_CENTER, fontName="Times-Bold")
SubtitleStyle = ParagraphStyle(name='Normal',fontSize=12, alignment= TA_CENTER, fontName="Times-Roman")
# MonospacedSubtitleStyle = ParagraphStyle(name='Normal',fontSize=12, alignment= TA_CENTER, fontName="Courier")
HeaderStyle = ParagraphStyle(name='Normal',fontSize=16)
SubheaderStyle = ParagraphStyle(name='Normal', fontName="Times-Roman")
DescriptorStyle = ParagraphStyle(name='Normal',fontSize=14, alignment= TA_CENTER)
BodyTextStyle = styles["BodyText"]
Elements = []

def bold(text):
    return "<b>"+text+"</b>"

def title(text, style=TitleStyle, klass=Paragraph, sep=0.3):
    """ Creates title of report """
    t = klass(bold(text), style)
    Elements.append(t)

def subtitle(text, style=SubtitleStyle, klass=Paragraph, sep=0.1, spaceBefore=True, spaceAfter = True):
    """ Creates descriptor text for a (sub)section; sp adds space before text """
    s = Spacer(0, 1.5*sep*inch)
    if spaceBefore:
        Elements.append(s)
    d = klass(text, style)
    Elements.append(d)
    if spaceAfter:
        Elements.append(s)

def old_emissions_comparison(process_kwh, year, default_location, printToScreen):
      # Calculates emissions in different locations

    intl_data = utils.get_data("data/json/energy-mix-intl_" + year + ".json")
    global_emissions, europe_emissions, us_emissions = [], [], []
    # Handling international
    for country in intl_data:
           c = intl_data[country]
           total, breakdown = c['total'], [c['coal'], c['petroleum'], \
           c['naturalGas'], c['lowCarbon']]
           if isinstance(total, float) and float(total) > 0:
               breakdown = list(map(lambda x: 100*x/total, breakdown))
               coal, petroleum, natural_gas, low_carbon = breakdown
               breakdown = [convert.coal_to_carbon(process_kwh * coal/100),
                    convert.petroleum_to_carbon(process_kwh * petroleum/100),
                    convert.natural_gas_to_carbon(process_kwh * natural_gas/100), 0]
               emission = sum(breakdown)
               if locate.in_Europe(country):
                   europe_emissions.append((country,emission))
               else:
                   global_emissions.append((country,emission))

    global_emissions.sort(key=lambda x: x[1])
    europe_emissions.sort(key=lambda x: x[1])

    # Handling US
    us_data = utils.get_data("data/json/us-emissions_" + year + ".json")
    for state in us_data:
        if ((state != "United States") and state != "_units"):
            if us_data[state] != "lbs/MWh":
                emission = convert.lbs_to_kgs(us_data[state]*convert.to_MWh(process_kwh))
                us_emissions.append((state, emission))
    us_emissions.sort(key=lambda x: x[1])

    max_global, max_europe, max_us = global_emissions[len(global_emissions)-1], \
        europe_emissions[len(europe_emissions)-1], us_emissions[len(us_emissions)-1]
    median_global, median_europe, median_us = global_emissions[len(global_emissions)//2], \
        europe_emissions[len(europe_emissions)//2], us_emissions[len(us_emissions)//2]
    min_global, min_europe, min_us= global_emissions[0], europe_emissions[0], us_emissions[0]
    if default_location and printToScreen:
        utils.log('Emissions Comparison default', max_global, median_global, min_global, max_europe, \
            median_europe, min_europe, max_us, median_us, min_us)
    default_emissions = [max_global, median_global, min_global, max_europe, \
        median_europe, min_europe, max_us, median_us, min_us]
    return default_emissions

def emissions_comparison(process_kwh, locations, year, default_location, printToScreen):
    # TODO: Disambiguation of states such as Georgia, US and Georgia
    intl_data = utils.get_data("data/json/energy-mix-intl_" + year + ".json")
    us_data = utils.get_data("data/json/us-emissions_" + year + ".json")
    emissions = [] # list of tuples w/ format (location, emission)

    for location in locations:
        if locate.in_US(location):
            emission = convert.lbs_to_kgs(us_data[location]*convert.to_MWh(process_kwh))
            emissions.append((location, emission))
        else:
             c = intl_data[location]
             total, breakdown = c['total'], [c['coal'], c['petroleum'], \
             c['naturalGas'], c['lowCarbon']]
             if isinstance(total, float) and float(total) > 0:
                 breakdown = list(map(lambda x: 100*x/total, breakdown))
                 coal, petroleum, natural_gas, low_carbon = breakdown
                 breakdown = [convert.coal_to_carbon(process_kwh * coal/100),
                      convert.petroleum_to_carbon(process_kwh * petroleum/100),
                      convert.natural_gas_to_carbon(process_kwh * natural_gas/100), 0]
                 emission = sum(breakdown)
                 emissions.append((location,emission))

    if emissions != [] and not default_location and printToScreen:
        utils.log('Emissions Comparison', emissions)
    return emissions

def kwh_and_emissions_table(data):

    s = Spacer(9*inch, .2*inch)
    Elements.append(s)

    no_rows = 1
    no_cols = 2
    col_size = 2

    t = Table(data, [2.75*inch, 2.15*inch],[.25*inch, .29*inch], hAlign="CENTER")
    t.setStyle([('FONT',(0,0),(-1,-1),"Times-Roman"),
                ('FONT',(0,0),(0,-1),"Times-Bold"),
                ('FONTSIZE', (0,0), (-1,-1), 12),
                ('ALIGN', (0,0), (0,-1), "RIGHT"),
                ('ALIGN',(1,1),(1,-1), "LEFT"),
                ('BOX', (0,0), (-1,-1), 1, colors.black),
                ('VALIGN', (0,0), (-1,-1), "TOP")])
    Elements.append(t)

def comparison_graphs(comparison_values, location, emission, default_emissions, default_location):
    s = Spacer(9*inch, .2*inch)
    Elements.append(s)
    drawing = Drawing(0, 0)

    if not default_location:
        bc = gen_bar_graphs(comparison_values, location, emission)
        bc.y = -120
        bc.height = 125
        bc.width = 300
        drawing.add(bc)
    else:
        bc1 = gen_bar_graphs(default_emissions[:3], location, emission)
        bc2 = gen_bar_graphs(default_emissions[3:6], location, emission)
        bc3 = gen_bar_graphs(default_emissions[6:], location, emission)

        offset = -257
        bc1.x = -10 + offset
        bc2.x = 190 + offset
        bc3.x = 390 + offset
        drawing.add(bc1)
        drawing.add(bc2)
        drawing.add(bc3)

        label_offset = offset + 80
        label1, label2, label3 = Label(), Label(), Label()
        label1.setText("Global (excluding Europe and US)")
        label1.x, label1.y = -17 + label_offset, -160
        label1.fontName = "Times-Bold"

        label2.setText("Europe")
        label2.x, label2.y = 185 + label_offset, -160
        label2.fontName = "Times-Bold"

        label3.setText("United States")
        label3.x, label3.y = 385 + label_offset, -160
        label3.fontName = "Times-Bold"

        drawing.add(label1)
        drawing.add(label2)
        drawing.add(label3)





    if_elsewhere_para = Paragraph('<font face="times" size=12>Kilograms of CO<sub rise = -10 size' +
    ' = 8>2 </sub> emissions for the function if the computation had been performed elsewhere</font>', style = styles["Normal"])
    graph_data = [['Emission Comparison'], [if_elsewhere_para], [drawing]]
    graph_table = Table(graph_data, [6.5*inch], [.25*inch, .25*inch, .25*inch], hAlign="CENTER")
    graph_table.setStyle(TableStyle([('FONT', (0,0), (0,0), "Times-Bold"),
                                     ('FONT', (0,1),(0,1),"Times-Roman"),
                                     ('FONTSIZE', (0,0), (0,0), 13),
                                     ('FONTSIZE', (0,1), (0,1), 12),
                                     ('ALIGN', (0,0), (-1,-1), "CENTER")]))


    Elements.append(graph_table)

def equivs_and_emission_equivs(equivs_data, emissions_data):
    '''
    Creates a table with 2 columns, each with their own embedded table
    The embedded tables contain 2 vertically-stacked tables, one for the header
    and the other one for the actual data in order to have better alignment
    The first row of the 2nd vertically-stacked table is smaller than the rest in
    order to remove the extra space and make these tables look cohesive with the
    energy usage readings and energy mix tables
    Setup:
    * Table(data[array of arrays, one for each row], [column widths], [row heights])
    * Spacer(width, height)
    '''
    s = Spacer(9*inch, .2*inch)
    Elements.append(s)

    no_rows = 1
    no_cols = 1
    col_size = 4.5

    equivs_header_data = [["Assumed Carbon Equivalencies"]]

    # Table(data)
    equivs_header_table = Table(equivs_header_data, [3*inch], [.25*inch])
    equivs_header_table.setStyle(TableStyle([('FONT',(0,0),(0,-1),"Times-Bold"),
                                             ('FONTSIZE', (0,0), (-1,-1), 13)]))


    equivs_data_table = Table(equivs_data, [1*inch, 2*inch], [0.17*inch, 0.25*inch, 0.25*inch, 0.25*inch],hAlign="LEFT")
    equivs_data_table.setStyle(TableStyle([('FONT', (0,0), (-1,-1), "Times-Roman"),
                                         ('FONTSIZE', (0,0), (-1,-1), 12),
                                         ('ALIGN', (0,0), (0,-1), "RIGHT"),
                                         ('VALIGN', (-1,-1), (-1,-1), "TOP")]))

    t1_data = [[equivs_header_table],[equivs_data_table]]

    t1 = Table(t1_data, [3*inch])

    emission_equiv_para = Paragraph('<font face="times" size=13><strong>CO<sub rise = -10 size = 8>2</sub>' +
    '  Emissions Equivalents</strong></font>', style = styles["Normal"])
    emissions_header_data = [[emission_equiv_para]]
    emissions_header_table = Table(emissions_header_data, [3*inch], [.25*inch])
    emissions_header_table.setStyle(TableStyle([('FONT',(0,0),(0,-1),"Times-Bold"),
                                             ('FONTSIZE', (0,0), (-1,-1), 13)]))


    emissions_data_table = Table(emissions_data, [2.1*inch, 1.5*inch], [0.17*inch, 0.25*inch, 0.25*inch],hAlign="LEFT")
    emissions_data_table.setStyle(TableStyle([('FONT', (0,0), (-1,-1), "Times-Roman"),
                                         ('FONTSIZE', (0,0), (-1,-1), 12),
                                         ('ALIGN', (0,0), (0,-1), "RIGHT"),
                                         ('VALIGN', (-1,-1), (-1,-1), "TOP")]))

    t2_data = [[emissions_header_table],[emissions_data_table]]

    t2 = Table(t2_data, [3*inch])


    table_data = [(t1, t2)]
    t = Table(table_data, [4.25*inch, 3*inch], hAlign='CENTER')
    t.setStyle(TableStyle([('VALIGN', (-1,-1), (-1,-1), "TOP")]))
    Elements.append(t)

def generate(kwh, emission):
    # TODO: remove state_emission and just use location
    """ Generates pdf report
    Parameters:
        location (str): user's location, locations=["Romania", "Brazil"]
        watt_averages (list): list of baseline, total, process wattage, process duration
        breakdown (list): [% coal, % oil/petroleum, % natural gas, % low carbon]
        kwh_and_emissions (list): [kwh used, emission in kg CO2, state emission > 0 for US states]
        func_info (list): [user func name, user func args (0 or more)]
    """

    # kwh, emission, state_emission = kwh_and_emissions
    # baseline_average, process_average, difference_average, process_duration = watt_averages


    # Initializing document
    doc = SimpleDocTemplate("energy-usage-report.pdf",pagesize=landscape(letter), topMargin=.3*inch)

    title("Energy Usage Report")

    # # Handling header with function name and arguments
    # func_name, *func_args = func_info
    # info_text = " for the function " + func_name
    # if len(func_args) > 0:
    #     if len(func_args) == 1:
    #         info_text += " with the input " + str(func_args[0]) + "."
    #     else:
    #         info_text += " with the inputs "
    #         for arg in func_args:
    #             info_text += arg + ","
    #         info_text = info_text[len(info_text)-1] + "."
    # else:
    #     info_text += "."
    #
    # subtitle("Energy usage and carbon emissions" + info_text, spaceBefore=True)
    #
    # # Energy Usage Readings and Energy Mix Data
    # readings_data = [['Energy Usage Readings', ''],
    #             ['Average baseline wattage:', "{:.2f} watts".format(baseline_average)],
    #             ['Average total wattage:', "{:.2f} watts".format(process_average)],
    #             ['Average process wattage:', "{:.2f} watts".format(difference_average)],
    #             ['Process duration:', process_duration],
    #             ['','']] #hack for the alignment
    #
    # coal_para = Paragraph('<font face="times" size=12>996 kg CO<sub rise = -10 size = 8>2 </sub>/MWh</font>', style = styles["Normal"])
    # oil_para = Paragraph('<font face="times" size=12>817 kg CO<sub rise = -10 size = 8>2 </sub>/MWh</font>', style = styles["Normal"])
    # gas_para = Paragraph('<font face="times" size=12>744 kg CO<sub rise = -10 size = 8>2 </sub>/MWh</font>', style = styles["Normal"])
    # low_para = Paragraph('<font face="times" size=12>0 kg CO<sub rise = -10 size = 8>2 </sub>/MWh</font>', style = styles["Normal"])
    # if state_emission:
    #     coal, oil, natural_gas, low_carbon = breakdown
    #     mix_data = [['Energy Mix Data', ''],
    #                 ['Coal', "{:.2f}%".format(coal)],
    #                 ['Oil', "{:.2f}%".format(oil)],
    #                 ['Natural gas', "{:.2f}%".format(natural_gas)],
    #                 ['Low carbon', "{:.2f}%".format(low_carbon)]]
    #     equivs_data = [['Coal:', coal_para],
    #                    ['Oil:', oil_para],
    #                    ['Natural gas:', gas_para],
    #                    ['Low carbon:', low_para]]
    #
    # else:
    #     coal, petroleum, natural_gas, low_carbon = breakdown
    #     mix_data = [['Energy Mix Data', ''],
    #                 ['Coal',  "{:.2f}%".format(coal)],
    #                 ['Petroleum', "{:.2f}%".format(petroleum)],
    #                 ['Natural gas', "{:.2f}%".format(natural_gas)],
    #                 ['Low carbon', "{:.2f}%".format(low_carbon)]]
    #     equivs_data = [['Coal:', coal_para],
    #                    ['Petroleum:', oil_para],
    #                    ['Natural gas:', gas_para],
    #                    ['Low carbon:', low_para]]
    #
    # readings_and_mix_table(readings_data, mix_data, breakdown, state_emission, location)
    effective_emission = Paragraph('<font face="times" size=12>{:.2e} kg CO<sub rise = -10 size = 8>2 </sub></font>'.format(emission), style = styles["Normal"])
    # Total kWhs used and effective emissions
    kwh_and_emissions_data = [["Total kilowatt hours used:", "{:.2e} kWh".format(kwh)],
                              ["Effective emissions:", effective_emission]]

    kwh_and_emissions_table(kwh_and_emissions_data)

    # Equivalencies and CO2 emission equivalents
    per_house = Paragraph('<font face="times" size=12>% of CO<sub rise = -10 size = 8>2</sub> per US house/day:</font>'.format(emission), style = styles["Normal"])
    emissions_data = [
                 ['Miles driven:', "{:.2e} miles".format(convert.carbon_to_miles(emission))],
                 ['Min. of 32-in. LCD TV:', "{:.2e} minutes".format(convert.carbon_to_tv(emission))],
                 [per_house, \
                   "{:.2e}%".format(convert.carbon_to_home(emission))]]

    coal_para = Paragraph('<font face="times" size=12>996 kg CO<sub rise = -10 size = 8>2 </sub>/MWh</font>', style = styles["Normal"])
    oil_para = Paragraph('<font face="times" size=12>817 kg CO<sub rise = -10 size = 8>2 </sub>/MWh</font>', style = styles["Normal"])
    gas_para = Paragraph('<font face="times" size=12>744 kg CO<sub rise = -10 size = 8>2 </sub>/MWh</font>', style = styles["Normal"])
    low_para = Paragraph('<font face="times" size=12>0 kg CO<sub rise = -10 size = 8>2 </sub>/MWh</font>', style = styles["Normal"])

    equivs_data = [['Coal:', coal_para],
                   ['Petroleum:', oil_para],
                   ['Natural gas:', gas_para],
                   ['Low carbon:', low_para]]

    equivs_and_emission_equivs(equivs_data, emissions_data)


    printToScreen = True
    location = locate.get(printToScreen)
    locations=["Mongolia", "Iceland", "Switzerland"] # why these countries? Shoule we let user input locations?
    default_location = False
    if locations == ["Mongolia", "Iceland", "Switzerland"]:
        default_location = True
    comparison_values = emissions_comparison(kwh, locations, year, default_location, printToScreen)

    default_emissions = old_emissions_comparison(kwh, year, default_location, printToScreen)
    comparison_graphs(comparison_values, location, emission, default_emissions, default_location)
    doc.build(Elements)
