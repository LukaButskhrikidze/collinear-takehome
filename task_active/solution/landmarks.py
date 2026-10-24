"""Find two class A GPCR landmarks from sequence alone (Ballesteros-Weinstein numbering):
  3.50 = arginine of the (D/E)R(Y/W/F/H/C) motif at the cytoplasmic end of TM3;
  6.34 = 16 residues before proline 6.50 of the TM6 'CWxP' motif, whose first two residues vary
         across the family (CWLP, SWIP, CYLP, CFLP, CFAP, MWCP ...). Loop lengths vary a lot, so
         P6.50 is placed relative to TM7's NPxxY motif (N7.49 ~ 34 residues after P6.50)."""
import re


def find_landmarks(seq: str):
    """Return 1-based (pos_3_50, pos_6_34); None where a motif is missing."""
    r350 = [m.start() + 2 for m in re.finditer(r"(?=[DE]R[YWFHC])", seq)]
    if not r350:
        return None, None
    p350 = r350[0]
    n749 = [m.start() + 1 for m in re.finditer(r"(?=[ND]P..[YF])", seq) if m.start() + 1 > p350 + 100]
    cands = [m.start() + 4 for m in re.finditer(r"(?=[CMFS][WYFS].P)", seq) if m.start() + 4 > p350 + 100]
    if not cands:
        return p350, None
    if n749:
        # TM7 NPxxY that has a TM6 proline candidate 28-40 residues before it
        pairs = [(abs((n - p) - 34), p) for n in n749 for p in cands if 28 <= n - p <= 40]
        if pairs:
            return p350, min(pairs)[1] - 16
    return p350, cands[0] - 16
