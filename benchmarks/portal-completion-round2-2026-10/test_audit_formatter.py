import json
from pathlib import Path
import unittest


class NativeFormatter(unittest.TestCase):
    def test_every_formatter_constraint_has_explicit_type(self):
        schema = json.loads(Path(__file__).with_name('audit-output-schema.json').read_text())

        def visit(node, path):
            if any(key in node for key in ('const', 'enum', 'properties', 'items')):
                self.assertIn('type', node, path)
            for name, child in node.get('properties', {}).items():
                visit(child, path + '.' + name)
            if 'items' in node:
                visit(node['items'], path + '[]')

        visit(schema, '$')
        self.assertEqual(schema['properties']['schema_version']['type'], 'integer')
        self.assertEqual(schema['properties']['schema_version']['const'], 1)


if __name__ == '__main__':
    unittest.main()
