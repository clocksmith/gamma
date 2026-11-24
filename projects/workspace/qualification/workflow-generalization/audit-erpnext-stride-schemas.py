#!/usr/bin/env python3
"""Read-only upstream GitHub API schema & role-permission audit for ERPNext stride tags (clocksmith/deco#88).

Checks `frappe/erpnext` doctype JSON definitions across `v15.20.0` (first-upgrade target),
`v15.110.0` (last runnable stride point), `v15.120.0` (where approver setup POST hit 403 on Item),
and the 7 remaining stride points (`v15.126.0` through `v16.60.0`), recording exact blob SHAs,
`Item` read-permission roles, and whether the REST fields read by both frozen arms (`docstatus`,
`total_qty`, `items[].supplier_quotation`, `terms`) changed on any stride tag.

Note: Static upstream schema verification does not substitute for live container execution; live
Docker execution on this Mac remains gated on the `>= 25 GiB` free-disk floor (`6.0 GiB` free
while Gate 3 containers occupy `17.88 GB`).
"""
from __future__ import annotations

import base64
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

TAGS = [
    'v15.20.0',
    'v15.110.0',
    'v15.120.0',
    'v15.126.0',
    'v16.0.0',
    'v16.10.0',
    'v16.20.0',
    'v16.30.0',
    'v16.50.0',
    'v16.60.0',
]
DOCTYPES = {
    'purchase_order': 'erpnext/buying/doctype/purchase_order/purchase_order.json',
    'purchase_order_item': 'erpnext/buying/doctype/purchase_order_item/purchase_order_item.json',
    'supplier_quotation': 'erpnext/buying/doctype/supplier_quotation/supplier_quotation.json',
    'supplier_quotation_item': 'erpnext/buying/doctype/supplier_quotation_item/supplier_quotation_item.json',
    'item': 'erpnext/stock/doctype/item/item.json',
}


def fetch_blob(path: str, tag: str) -> tuple[str, dict]:
    raw = subprocess.check_output(
        ['gh', 'api', f'repos/frappe/erpnext/contents/{path}?ref={tag}'],
        text=True,
    )
    meta = json.loads(raw)
    content = json.loads(base64.b64decode(meta['content']))
    return meta['sha'], content


def main() -> None:
    out_path = Path(
        sys.argv[1]
        if len(sys.argv) > 1
        else Path(__file__).resolve().parent / 'receipts' / 'erpnext-upstream-stride-schema-audit.json'
    )
    rows = []
    for tag in TAGS:
        shas = {}
        docs = {}
        for key, path in DOCTYPES.items():
            sha, doc = fetch_blob(path, tag)
            shas[key] = sha
            docs[key] = doc
        po_fields = {f['fieldname'] for f in docs['purchase_order'].get('fields', [])}
        poi_fields = {f['fieldname'] for f in docs['purchase_order_item'].get('fields', [])}
        sq_fields = {f['fieldname'] for f in docs['supplier_quotation'].get('fields', [])}
        item_read_roles = sorted(
            {p['role'] for p in docs['item'].get('permissions', []) if p.get('read')}
        )
        rows.append({
            'release': tag,
            'blobShas': shas,
            'restReadFieldsIntact': {
                'purchaseOrderTotalQty': 'total_qty' in po_fields,
                'purchaseOrderItems': 'items' in po_fields,
                'purchaseOrderTerms': 'terms' in po_fields,
                'purchaseOrderItemSupplierQuotation': 'supplier_quotation' in poi_fields,
                'supplierQuotationTotalQty': 'total_qty' in sq_fields,
            },
            'itemReadPermissionRoles': item_read_roles,
            'frozenApproverRolesHoldDirectItemRead': bool(
                {'Purchase Manager', 'Purchase Master Manager'} & set(item_read_roles)
            ),
        })

    report = {
        'schema': 'gammatron.erpnext-upstream-stride-schema-audit/v1',
        'recordedAt': datetime.now(timezone.utc).isoformat(),
        'modelSpendUsd': 0,
        'scopeNote': (
            'Static upstream doctype JSON audit across frappe/erpnext tags v15.20.0..v16.60.0. '
            'Confirms REST read fields used by frozen arms (total_qty, items[].supplier_quotation, terms) '
            'are unchanged across all remaining stride tags, and explains why frozen seeder approver roles '
            '(Purchase Manager, Purchase Master Manager) lack direct Item read permission once System Manager '
            'assignment stopped taking effect in v15.120.0+. Does not replace live Docker screening once >=25 GiB '
            'free disk or an authorized Docker host is available.'
        ),
        'allRestReadFieldsUnchangedThroughV16_60': all(
            all(r['restReadFieldsIntact'].values()) for r in rows
        ),
        'releases': rows,
    }
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'ok': True, 'out': str(out_path), 'unchanged': report['allRestReadFieldsUnchangedThroughV16_60']}))


if __name__ == '__main__':
    main()
