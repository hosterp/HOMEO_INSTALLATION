# -*- coding: utf-8 -*-
##############################################################################


{
    'name': 'Web Menu',
    'version': '1.2',
    'author': 'Hiworth Solutions Pvt Ltd',
    'description': '',
    'category': 'Web',
    'depends': ['web',],
    'data': [
        'views/templates.xml',
    ],
    'qweb' : [
        "static/src/xml/*.xml",
    ],
    'application': True,
    'auto_install': False,
}
