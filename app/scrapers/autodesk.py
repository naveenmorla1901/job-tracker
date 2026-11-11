"""Autodesk jobs from its current Eightfold careers site.

The old Workday ``Ext`` board still answers but exposes only a handful of
requisitions; jobs.autodesk.com carries the full catalogue.
"""
from app.scrapers.ats_boards import fetch_eightfold_jobs

BASE_URL = "https://jobs.autodesk.com"
DOMAIN = "autodesk.com"


def get_autodesk_jobs(roles, days=7):
    """Main function to retrieve Autodesk jobs structured by roles"""
    return fetch_eightfold_jobs(BASE_URL, DOMAIN, roles, days=days)
