"""Run the builder's actual stdlib regression suite; never accept an empty suite."""
import ast,sys,unittest
from pathlib import Path
root=Path(__file__).resolve().parent
for rel in ['server.py','public/index.html']:
 if not(root/rel).is_file():raise SystemExit('Missing app source: '+rel)
ast.parse((root/'server.py').read_text())
suite=unittest.defaultTestLoader.discover(str(root/'tests'),pattern='test*.py')
if suite.countTestCases()==0:raise SystemExit('No behavioral tests discovered; add actual regression cases')
result=unittest.TextTestRunner(verbosity=2).run(suite)
raise SystemExit(0 if result.wasSuccessful() else 1)
