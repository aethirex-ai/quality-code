from pathlib import Path
import shutil,json,hashlib
judge=Path(__file__).parent
fixture=judge.parent/'error-fixture'
oracle=judge/'oracle'
if oracle.exists(): shutil.rmtree(oracle)
shutil.copytree(fixture,oracle)
seeds=[
('H_PRICE','src/hotel.mjs','quoteStay','Math.floor(subtotal * (100 - discountPercent) / 100)','Math.round(subtotal * (100 - discountPercent) / 100)','Discount calculation truncates fractional cents rather than rounding half upward.',{'checkIn':'2028-06-01','checkOut':'2028-06-02','nightlyCents':105,'discountPercent':10},94,95),
('H_INTERVAL','src/hotel.mjs','staysOverlap','a <= d && c <= b','a < d && c < b','Inclusive overlap comparison treats adjoining exclusive checkout as occupied.',{'first':{'checkIn':'2028-06-01','checkOut':'2028-06-03'},'second':{'checkIn':'2028-06-03','checkOut':'2028-06-05'}},True,False),
('H_HTML','src/hotel.mjs','guestBadge',".replaceAll('\"', '&quot;')",".replaceAll('\"', '&quot;').replaceAll(\"'\", '&#39;')",'Single quote is unescaped in a single-quoted HTML attribute.',"O'Neil","<span data-guest='O'Neil'>O'Neil</span>","<span data-guest='O&#39;Neil'>O&#39;Neil</span>"),
('F_CAPACITY','src/fitness.mjs','canEnroll','confirmed <= capacity','confirmed < capacity','Inclusive capacity comparison allows one enrollment into a full class.',{'confirmed':12,'capacity':12},True,False),
('F_REFUND','src/fitness.mjs','cancellationRefund','startMs - cancelledMs > 86400000','startMs - cancelledMs >= 86400000','Strict cutoff denies the refund at exactly 24 hours.',{'startMs':172800000,'cancelledMs':86400000,'paidCents':3900},0,3900),
('F_PURITY','src/fitness.mjs','chronologicalClasses','return classes.sort','return [...classes].sort','Array.sort mutates caller array and returns it rather than a new array.',[{'id':'late','startMs':30},{'id':'early','startMs':10}],'input reordered and output === input','input retains late/early order; output new early/late array'),
('L_QUANTITY','src/landscape.mjs','estimateCents','total += item.unitCents','total += line','Accumulator ignores quantity despite computing line subtotal.',[{'quantity':3,'unitCents':12500},{'quantity':2,'unitCents':499}],12999,38498),
('L_BUDGET','src/landscape.mjs','withinBudget','estimateCents < budgetCents','estimateCents <= budgetCents','Strict affordability comparison rejects an estimate equal to budget.',{'estimateCents':450000,'budgetCents':450000},False,True),
]
records=[]
for ident,file,fn,old,new,cause,repro,observed,expected in seeds:
    baseline=(fixture/file).read_text()
    assert baseline.count(old)==1,(ident,old)
    p=oracle/file
    p.write_text(p.read_text().replace(old,new))
    line=baseline[:baseline.index(old)].count('\n')+1
    records.append({'id':ident,'file':file,'function':fn,'line':line,'faultyExpression':old,'cause':cause,'repro':repro,'baselineObserved':observed,'requiredBehavior':expected,'oracleReplacement':new})
(judge/'seeds.json').write_text(json.dumps(records,indent=2)+'\n')
(judge/'baseline-manifest.json').write_text(json.dumps({str(p.relative_to(fixture)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(fixture.rglob('*')) if p.is_file()},indent=2)+'\n')
