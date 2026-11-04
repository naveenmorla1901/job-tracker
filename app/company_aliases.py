"""Company names that were duplicated by two scrapers reading the same board.

The scheduler now maps both scrapers to the canonical name. Existing rows may
still carry the old name, so startup relabels them once and the upsert path
heals any row it meets. Keeping the list here avoids hard-coding aliases in
both the scheduler and the database layer.
"""

COMPANY_ALIASES = {
    "Acxiom": ("Acxiom LLC",),
    "AEP": ("American Electric Power",),
    "Scotts Miracle Gro": ("Scotts Miracle-Gro",),
}
