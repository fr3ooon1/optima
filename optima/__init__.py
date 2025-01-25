
__version__ = '0.0.1'


import frappe
from erpnext.accounts import general_ledger
from erpnext.accounts.general_ledger import merge_similar_entries
# erpnext/erpnext/controllers/accounts_controller.py
from erpnext.controllers.accounts_controller import AccountsController , set_balance_in_account_currency
from erpnext.accounts.utils import get_account_currency, get_fiscal_years
from frappe.utils import formatdate
from erpnext.accounts.doctype.accounting_dimension.accounting_dimension import (
	get_accounting_dimensions,
)

def custom_merge_similar_entries(gl_map, precision=None):
	
	if frappe.get_doc('Optima Setting').get("disable_merage_in_gl_entry") == 0 :
		result =  merge_similar_entries(gl_map , precision=None )
		return result
	else :
		return gl_map
	    




general_ledger.merge_similar_entries = custom_merge_similar_entries




def get_gl_dict(self, args, account_currency=None, item=None):
	"""this method populates the common properties of a gl entry record"""
	if item.get("posting_date") and frappe.get_doc('Optima Setting').get("enable_posting_date_per_row") == 1:

		posting_date = item.posting_date

	else :

		posting_date = args.get("posting_date") or self.get("posting_date")

	fiscal_years = get_fiscal_years(posting_date, company=self.company)
	if len(fiscal_years) > 1:
		frappe.throw(
			_("Multiple fiscal years exist for the date {0}. Please set company in Fiscal Year").format(
				formatdate(posting_date)
			)
		)
	else:
		fiscal_year = fiscal_years[0][0]

	gl_dict = frappe._dict(
		{
			"company": self.company,
			"posting_date": posting_date,
			"fiscal_year": fiscal_year,
			"voucher_type": self.doctype,
			"voucher_no": self.name,
			"remarks": self.get("remarks") or self.get("remark"),
			"debit": 0,
			"credit": 0,
			"debit_in_account_currency": 0,
			"credit_in_account_currency": 0,
			"is_opening": self.get("is_opening") or "No",
			"party_type": None,
			"party": None,
			"project": self.get("project"),
			"post_net_value": args.get("post_net_value"),
		}
	)

	accounting_dimensions = get_accounting_dimensions()
	dimension_dict = frappe._dict()

	for dimension in accounting_dimensions:
		dimension_dict[dimension] = self.get(dimension)
		if item and item.get(dimension):
			dimension_dict[dimension] = item.get(dimension)

	gl_dict.update(dimension_dict)
	gl_dict.update(args)

	if not account_currency:
		account_currency = get_account_currency(gl_dict.account)

	if gl_dict.account and self.doctype not in [
		"Journal Entry",
		"Period Closing Voucher",
		"Payment Entry",
		"Purchase Receipt",
		"Purchase Invoice",
		"Stock Entry",
	]:
		self.validate_account_currency(gl_dict.account, account_currency)

	if gl_dict.account and self.doctype not in [
		"Journal Entry",
		"Period Closing Voucher",
		"Payment Entry",
	]:
		set_balance_in_account_currency(
			gl_dict, account_currency, self.get("conversion_rate"), self.company_currency
		)

	return gl_dict






AccountsController.get_gl_dict = get_gl_dict