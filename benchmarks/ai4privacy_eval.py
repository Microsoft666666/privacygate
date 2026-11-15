"""Academic-only external benchmark; writes aggregates, never rows or examples."""
from collections import Counter
from pathlib import Path
import argparse
import json
import os
import random
from evaluation import Metrics, score
from detector import detect
from benchmarks.compare import previous_detector

DATASET = 'ai4privacy/pii-masking-300k'
SEED = 20261115
# Observed source labels, not guessed generic PII names. TEL pools both phone
# categories under US_PHONE for scoring only; it does not change app policy.
LABEL_MAP = {'EMAIL':'EMAIL','TEL':'US_PHONE','PASS':'SECRET','BOD':'DATE_OF_BIRTH',
             'GIVENNAME1':'PERSON','GIVENNAME2':'PERSON','LASTNAME1':'PERSON',
             'LASTNAME2':'PERSON','LASTNAME3':'PERSON','IP':'IPV4','CITY':'LOCATION',
             'STATE':'LOCATION','COUNTRY':'LOCATION','STREET':'STREET_ADDRESS',
             'SOCIALNUMBER':'SSN'}
# IDs/passports, generic dates, times, usernames, and address fragments such as
# BUILDING/POSTCODE have no defensible direct equivalent and remain not covered.

def normalize(category):
    return 'US_PHONE' if category == 'INTL_PHONE' else category

def overlap_score(predicted, expected):
    """Maximum one-to-one, same-category span overlap, not double-counted hits."""
    matched={}
    def augment(i,seen):
        p=predicted[i]
        for j,e in enumerate(expected):
            if j in seen or p[0]!=e[0] or max(p[1],e[1])>=min(p[2],e[2]):
                continue
            seen.add(j)
            if j not in matched or augment(matched[j],seen):
                matched[j]=i
                return True
        return False
    tp=sum(augment(i,set()) for i in range(len(predicted)))
    return Metrics(tp,len(predicted)-tp,len(expected)-tp)

def evaluate_rows(rows, detector):
    totals={mode:[0,0,0] for mode in ('exact','overlap')}
    per_category={mode:{} for mode in totals}
    unmapped=Counter(); observed=Counter(); count=0; negatives=0; false_negatives=0
    for row in rows:
        if row['language'] != 'English':
            continue
        count+=1
        text=row['source_text']; expected=[]
        for mask in row['privacy_mask']:
            label=mask['label'];observed[label]+=1
            if label not in LABEL_MAP:
                unmapped[label]+=1
                continue
            start,end=int(mask['start']),int(mask['end'])
            if not 0 <= start < end <= len(text):
                raise ValueError('Invalid benchmark annotation span')
            expected.append((LABEL_MAP[label],start,end))
        predicted=[(normalize(f.category),f.start,f.end) for f in detector(text)]
        if not row['privacy_mask']:
            negatives+=1;false_negatives+=bool(predicted)
        for mode,scorer in [('exact',score),('overlap',overlap_score)]:
            m=scorer(predicted,expected)
            totals[mode]=[a+b for a,b in zip(totals[mode],(m.tp,m.fp,m.fn))]
            for category in {s[0] for s in predicted+expected}:
                m=scorer([s for s in predicted if s[0]==category],[s for s in expected if s[0]==category])
                old=per_category[mode].setdefault(category,[0,0,0])
                per_category[mode][category]=[a+b for a,b in zip(old,(m.tp,m.fp,m.fn))]
    return {'messages':count,'observed_labels':dict(sorted(observed.items())),
            'not_covered':dict(sorted(unmapped.items())),
            'negative_messages':negatives,'false_positive_negative_messages':false_negatives,
            'negative_fpr':false_negatives/negatives if negatives else None,
            **{mode:{**Metrics(*totals[mode]).report(), 'per_category':{c:Metrics(*counts).report() for c,counts in sorted(per_category[mode].items())}} for mode in totals}}

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--n',type=int,default=1000)
    args=parser.parse_args()
    if args.n<=0: parser.error('--n must be positive')
    root=Path(__file__).resolve().parents[1]
    cache=root/'benchmarks/.cache'
    os.environ.setdefault('HF_HOME',str(cache/'hf'))
    from datasets import load_dataset
    from recognizers.ner import ner_status
    try:
        data=load_dataset(DATASET,split='validation',cache_dir=str(cache/'datasets'))
        english=[i for i,language in enumerate(data['language']) if language=='English']
        indices=sorted(random.Random(SEED).sample(english,min(args.n,len(english))))
        rows=[data[i] for i in indices]  # never persist selected rows or annotations
        if not rows: raise ValueError('No English rows')
        modes={'v2':previous_detector,'regex':lambda text:detect(text,ner=False)}
        available=ner_status()[0]=='available'
        if available: modes['ner']=lambda text:detect(text,ner=True)
        report={'dataset':DATASET,'split':'validation','language':'English','seed':SEED,
                'requested_n':args.n,'sample_n':len(rows),'dataset_fingerprint':data._fingerprint,
                'label_map':LABEL_MAP,'ner_available':available,
                'modes':{name:evaluate_rows(rows,fn) for name,fn in modes.items()}}
        if available and ner_status()[0]!='available':
            raise RuntimeError('NER unavailable during benchmark')
        (root/'docs/ai4privacy_metrics.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
        print('Wrote aggregate benchmark metrics; no dataset rows were exported.')
    except Exception:
        print('External benchmark unavailable. No report written; check dataset access and model installation.')
        return 1
    return 0

if __name__=='__main__': raise SystemExit(main())
