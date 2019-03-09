"""
Description:
This script takes an Alma XML invoice export file and parses the data into a csv
file that can be imported by Banner.  Variables are normally named after the xml
tag in the Alma export for convenient referencing.
License Info:
Copyright 2019 Eastern Oregon University
Permission is hereby granted, free of charge, to any person obtaining a copy of
this software and associated documentation files (the "Software"), to deal in
the Software without restriction, including without limitation the rights to use,
copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the
Software, and to permit persons to whom the Software is furnished to do so,
subject to the following conditions:
The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.THE SOFTWARE IS PROVIDED "AS IS",
WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO
THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE
FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR
THE USE OR OTHER DEALINGS IN THE SOFTWARE.
"""

# Built-in/Generic Imports
import csv
import datetime

# Libs
import xml.etree.ElementTree as ET

__author__="Jeremiah Kellogg"
__copyright__="Copyright 2019, Eastern Oregon University"
__credits__="Jeremiah Kellogg"
__license__="MIT License"
__version__="0.1.0"
__maintainer__="Jeremiah Kellogg"
__email__="jkellogg@eou.edu"
__status__="Development"

alma_xml_dom = ET.parse('AlmaExport.xml')
root = alma_xml_dom.getroot()
today = datetime.date.today()
Invoice_data = open('alma_invoice_' + today.strftime('%Y%m%d') + '.csv', 'w')
csvwriter = csv.writer(Invoice_data)

## Populate csv column headers
invoice_column_header = []
invoice_number = 'INVOICE_NUMBER'
invoice_column_header.append(invoice_number)
vendor_id = 'VENDOR_ID'
invoice_column_header.append(vendor_id)
payment_address = 'ATYPE_SEQ'
invoice_column_header.append(payment_address)
invoice_date = 'INVOICE_DATE'
invoice_column_header.append(invoice_date)
sum = 'INVOICE_TOTAL'
invoice_column_header.append(sum)
payment_due_date = 'PMT_DUE_DATE'
invoice_column_header.append(payment_due_date)
invoice_line_number = 'PO_SEQ'
invoice_column_header.append(invoice_line_number)
external_id = 'ACCOUNT_INDEX'
invoice_column_header.append(external_id)
price = 'UNIT_PRICE'
invoice_column_header.append(price)
shipment_amount = 'ADDL_CHG'
invoice_column_header.append(shipment_amount)
po_line_number = 'LINE_DESC'
invoice_column_header.append(po_line_number)
csvwriter.writerow(invoice_column_header)
## End csv headers

## Begin adding xml data to csv
namespace = '{http://com/exlibris/repository/acq/invoice/xmlbeans}'  # namespace is declared so it can replace the url in xml data paths
list_of_invoices = root.findall(namespace+'invoice_list/'+namespace+'invoice')
for invoice in list_of_invoices:
    invoice_row = []
    invoice_number = invoice.find(namespace+'invoice_number').text
    sum = invoice.find(namespace+'invoice_amount/'+namespace+'sum').text
    vendor_FinancialSys_Code = invoice.find(namespace+'vendor_FinancialSys_Code').text
    vendor_id, payment_address = vendor_FinancialSys_Code.split('-', 1)
    invoice_date = invoice.find(namespace+'invoice_date').text
    invoice_date_formatted = datetime.datetime.strptime(invoice_date, '%m/%d/%Y').strftime('%Y%m%d')
    creationDate = invoice.find(namespace+'invoice_ownered_entity/'+namespace+'creationDate').text
    creationDate_formatted = datetime.datetime.strptime(creationDate, '%Y%m%d')
    payment_due_date = (creationDate_formatted + datetime.timedelta(days=7)).strftime('%Y%m%d')
    payment_method = invoice.find(namespace+'payment_method').text  #If this has a value other than ACCOUNTINGDEPARTMENT we don't want the row written to csv
    shipment_amount = invoice.find(namespace+'additional_charges/'+namespace+'shipment_amount').text
    invoice_row.append(invoice_number)
    invoice_row.append(vendor_id)
    invoice_row.append(payment_address)
    invoice_row.append(invoice_date_formatted)
    invoice_row.append(sum)
    invoice_row.append(payment_due_date)
    ## Begin parsing individual POLs
    for invoice_line_list in invoice:
        invoice_line = invoice_line_list.findall(namespace+'invoice_line')
        for data in invoice_line:
            line_number = data.find(namespace+'line_number').text
            external_id = data.find(namespace+'fund_info_list/'+namespace+'fund_info/'+namespace+'external_id').text
            price = data.find(namespace+'price').text
            # Only write the value in shipment_amount to the first POL, all others should be zero
            if line_number == '1':
                additional = shipment_amount
            else:
                additional = 0
            po_line_number = data.find(namespace+'po_line_info/'+namespace+'po_line_number').text
            invoice_row.append(line_number)
            invoice_row.append(external_id)
            invoice_row.append(price)
            invoice_row.append(additional)
            invoice_row.append(po_line_number)
            # Only write the row's contents to the csv if the payment_method value is ACCOUNTINGDEPARTMENT.  The other 3 possible
            # values: CORRECTION, CREDITCARD, and DEPOSITACCOUNT shouldn't be sent to Banner
            if payment_method == 'ACCOUNTINGDEPARTMENT':
                csvwriter.writerow(invoice_row )
            #  Pop the last 5 values off the list so if there's more than one POL the list doesn't retain data from previous POLs
            invoice_row.pop()
            invoice_row.pop()
            invoice_row.pop()
            invoice_row.pop()
            invoice_row.pop()
    ## End parsing individual POLs
## End adding xml data to csv
Invoice_data.close()