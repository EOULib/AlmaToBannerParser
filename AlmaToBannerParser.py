"""
Description:
This program takes an Alma XML invoice export file and parses the data into a csv
file that can be imported by Banner.  Variables are normally named after the xml
tag in the Alma export for convenient referencing.  All default  directory paths
are set to the current directory, so if this script is run in the same directory
as the Alma xml file, then all output (logs, backups and the csv file) will be
saved to that same directory. 
IT IS HIGHLY ADVISABLE TO CHANGE THIS AND MAKE SEPERATE DIRECTORIES FOR EXPORTS 
(LINE 68), LOGS (LINE 62) AND SAVED EXPORTS (LINE 140) TO AVOID CONFUSION BETWEEN 
OLD AND NEW XML FILES.  KEEPING NEW AND SAVED EXPORTS IN THE SAME DIRECTORY WILL 
RESULT IN THE PROGRAM EXITING WITHOUT COMPLETION. THE NEW EXPORT DIRECTORY SHOULD
NEVER HAVE MORE THAN ONE XML FILE IN IT AT ANY GIVEN TIME.   
Variables are provided for setting different file paths as you see fit.  This 
program may need to be modified to fit your institution's needs.  It is advised 
that you work with your Banner analysts and programmers to determine what the csv 
output should look like for importing into Banner.  Logging functionality is built 
into the script for troubleshooting purposes.  An example Alma invoice export file 
can be accessed and used for testing purposes on the Ex Libris Developer Network 
site:
https://developers.exlibrisgroup.com/alma/apis/docs/xsd/invoice_payment.xsd/

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
import os
import logging

# Libs
import xml.etree.ElementTree as ET

__author__="Jeremiah Kellogg"
__copyright__="Copyright 2019, Eastern Oregon University"
__credits__="Jeremiah Kellogg"
__license__="MIT License"
__version__="0.2.1"
__maintainer__="Jeremiah Kellogg"
__email__="jkellogg@eou.edu"
__status__="Development"

today = datetime.date.today()  #Get current date for .xml, .log, & .csv naming conventions

##  Setup basic logging functionality to track errors and output helpful information for troubleshooting
log_directory = './'
logging.basicConfig(filename=log_directory + today.strftime('%Y%m%d') + '.log',  level=logging.DEBUG)

## Begin error checking for entire program using try and except blocks
try:
	## Find the current Alma xml export file in the designated directory
	export_directory = './'  #Directory where the Alma XML file was exported to
	find_current_export = [file for file in os.listdir(export_directory) if file.endswith('.xml')]
	## Begin log info to determine if an xml file was found.  If not, output to the log and exit the program.
	if len(find_current_export) < 1:
		logging.info("No XML file found, exiting program")
		exit()
	elif len(find_current_export) > 1:
		logging.info("More than 1 XML file was found in this directory:")
		for file in find_current_export:
			logging.info(file)
		logging.info("Exiting program")
		exit()
	else:
		current_export = find_current_export[0]
		logging.info("The current export file, " + current_export + ', was found. Continuing with program.')
	##  End info logging on whether an export file was found or not

	## Begin xml to csv parsing
	alma_xml_dom = ET.parse(export_directory + current_export)
	root = alma_xml_dom.getroot()
	Invoice_data = open('alma_invoice_' + today.strftime('%Y%m%d') + '.csv', 'w')
	csvwriter = csv.writer(Invoice_data)

	## Populate csv column headers
	invoice_column_header = [
		'INVOICE_NUMBER', 'VENDOR_ID', 'ATYPE_SEQ', 'INVOICE_DATE', 'INVOICE_TOTAL', 'PMT_DUE_DATE',
		'PO_SEQ', 'ACCOUNT_INDEX', 'UNIT_PRICE', 'ADDL_CHG', 'LINE_DESC'
	]
	csvwriter.writerow(invoice_column_header)
	## End csv headers

	## Begin adding xml data to csv
	namespace = '{http://com/exlibris/repository/acq/invoice/xmlbeans}'  # namespace is declared so it can replace the url in xml data paths
	list_of_invoices = root.findall(namespace+'invoice_list/'+namespace+'invoice')
	for invoice in list_of_invoices:
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
	            # Only write the row's contents to the csv if the payment_method value is ACCOUNTINGDEPARTMENT.  The other 3 possible
	            # values: CORRECTION, CREDITCARD, and DEPOSITACCOUNT shouldn't be sent to Banner
	            if payment_method == 'ACCOUNTINGDEPARTMENT':
					invoice_row = [
					invoice_number, vendor_id, payment_address, invoice_date_formatted, sum, payment_due_date,
					line_number, external_id, price, additional, po_line_number
					]
					csvwriter.writerow(invoice_row)
	    ## End parsing individual POLs
	## End adding xml data to csv
	Invoice_data.close()
	## End xml to csv parsing

	## Store xml import file in designated directory for troubleshooting purposes.  
	store_old_export = './'
	os.rename(export_directory + current_export, store_old_export + today.strftime('%Y%m%d')+'.xml')

	## Find and delete oldest file in the store_old_export directory according to the number of files you want to keep.
	## Set the number of old xml files to hang-on to using the max_xml_files_to_keep variable
	max_xml_files_to_keep = 3
	def sorted_ls(store_old_export):  #function for sorting files in a list according to the date they were created
		mtime = lambda f: os.stat(os.path.join(store_old_export, f)).st_mtime
		return list(sorted(os.listdir(store_old_export), key=mtime))
	del_list = sorted_ls(store_old_export)[0:(len(sorted_ls(store_old_export))-max_xml_files_to_keep)]  #list of old xml files
	if len(del_list) > max_xml_files_to_keep:
		for dfile in del_list:
			os.remove(store_old_export + dfile)
except Exception:
	logging.error("A fatal error occured: ", exc_info=True)
##  End error checking using try and except blocks
