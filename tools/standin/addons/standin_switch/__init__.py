def postLoad():
    from odoo.addons.account.models.account_account import AccountAccount

    from . import account_route
    account_route.install(AccountAccount)
