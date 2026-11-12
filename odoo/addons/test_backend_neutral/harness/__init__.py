""" Harness of the backend-neutral suite: the only place of the addon that
knows which database runs behind the ORM. Tests import from here only::

    from odoo.addons.test_backend_neutral.harness import NeutralCase, errors
"""
from . import errors
from .case import NEUTRAL_TAG, NeutralCase, NeutralConcurrencyCase

__all__ = ['NEUTRAL_TAG', 'NeutralCase', 'NeutralConcurrencyCase', 'errors']
