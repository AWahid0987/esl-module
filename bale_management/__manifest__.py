
{
    'name': 'Bale Management',
    'version': '1.0',
    'summary': 'Manage variable-weight bales sold in KG',
    'author': 'Abdul Wahid',
    'depends': ['sale', 'stock', 'mrp'],
    'data': [
        'security/ir.model.access.csv',
        'views/bale_views.xml',
        'views/sale_order_views.xml',
        'views/manufacturing_views.xml',
    ],
    'installable': True,
}
