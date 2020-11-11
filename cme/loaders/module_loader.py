import imp
import os
import cme
from cme.context import Context
from cme.logger import CMEAdapter


class module_loader:

    def __init__(self, args, db, logger):
        self.args = args
        self.db = db
        self.logger = logger
        self.cme_path = os.path.expanduser('~/.cme')

    def module_is_sane(self, module, module_path):
        module_error = False

        if not hasattr(module, 'name'):
            self.logger.error('{} missing the name variable'.format(module_path))
            module_error = True

        elif not hasattr(module, 'description'):
            self.logger.error('{} missing the description variable'.format(module_path))
            module_error = True

        elif not hasattr(module, 'opsec_safe'):
            self.logger.error('{} missing the opsec_safe variable'.format(module_path))
            module_error = True

        elif not hasattr(module, 'multiple_hosts'):
            self.logger.error('{} missing the multiple_hosts variable'.format(module_path))
            module_error = True

        elif not hasattr(module, 'options'):
            self.logger.error('{} missing the options function'.format(module_path))
            module_error = True

        elif not hasattr(module, 'on_login') and not (module, 'on_admin_login'):
            self.logger.error('{} missing the on_login/on_admin_login function(s)'.format(module_path))
            module_error = True

        if module_error:
            return False

        return True

    def load_module(self, module_path):
        try:
            module = imp.load_source('payload_module', module_path).CMEModule()
            if self.module_is_sane(module, module_path):
                return module
        except Exception as e:
            self.logger.error('Failed loading module at {}: {}'.format(module_path, e))

        return None

    def get_modules(self):
        modules = {}

        modules_paths = [os.path.join(os.path.dirname(cme.__file__), 'modules'), os.path.join(self.cme_path, 'modules')]

        for path in modules_paths:
            for module_dir in os.listdir(path):
                if self.args.protocol == module_dir:
                    for module in os.listdir(os.path.join(path, module_dir)):
                        if module[-3:] == '.py':
                            module_path = os.path.join(path, module_dir, module)
                            m = self.load_module(module_path)
                            modules[m.name] = {'path': module_path, 'description': m.description, 'options': m.options.__doc__}

        return modules

    def init_module(self, module_path):

        module = None

        module = self.load_module(module_path)

        if module:
            module_logger = CMEAdapter(extra={'module': module.name.upper()})
            context = Context(self.db, module_logger, self.args)

            module_options = {}

            for option in self.args.module_options:
                key, value = option.split('=', 1)
                module_options[str(key).upper()] = value

            module.options(context, module_options)

        return module
