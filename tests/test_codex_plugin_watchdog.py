import importlib.machinery
import importlib.util
import sys
from pathlib import Path
import tempfile
import unittest

loader = importlib.machinery.SourceFileLoader('watchdog', str(Path(__file__).parents[1] / 'bin/codex-plugin-watchdog'))
spec = importlib.util.spec_from_loader(loader.name, loader)
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)


class WatchdogTests(unittest.TestCase):
    def test_repair_and_noop(self):
        with tempfile.TemporaryDirectory() as root:
            root = Path(root).resolve()
            real = root / 'real'
            real.mkdir()
            home = root / '.codex'
            home.symlink_to(real)
            market = real / '.tmp/bundled-marketplaces/openai-bundled'
            (market / '.agents/plugins').mkdir(parents=True)
            (market / '.agents/plugins/marketplace.json').write_text('{}')
            config = home / 'config.toml'
            before = '# preserved\n[marketplaces.openai-bundled]\nsource_type = "local"\nsource = "' + str(market) + '" # keep\n[other]\nvalue = 42\n'
            config.write_text(before)
            self.assertTrue(module.repair(config, home).startswith('repaired'))
            self.assertEqual(config.read_text(), before.replace(str(market), str(home / '.tmp/bundled-marketplaces/openai-bundled')))
            stamp = config.stat().st_mtime_ns
            self.assertEqual(module.repair(config, home), 'healthy')
            self.assertEqual(stamp, config.stat().st_mtime_ns)
            config.write_text(before.replace(str(market), '/custom/path'))
            self.assertEqual(module.repair(config, home), 'skipped-unrecognized-config')
            config.write_text('invalid = [')
            with self.assertRaises(ValueError):
                module.repair(config, home)


if __name__ == '__main__':
    unittest.main()
