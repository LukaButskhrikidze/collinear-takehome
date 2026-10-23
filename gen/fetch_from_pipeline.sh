#!/bin/bash
# Copy the raw inputs my pipeline used for each accession (read-only, over ssh to the machine that holds its data):
# every PDB entry in the monomer ensemble (aligned + unaligned) + the UniProt FASTA.
#   gen/fetch_from_pipeline.sh <dest_dir> ACC [ACC ...]
set -euo pipefail
DEST=$1; shift
HOST=${PIPELINE_HOST:?set PIPELINE_HOST to the machine that holds my pipeline data}
D=${PIPELINE_DATA:?set PIPELINE_DATA to the pipeline data root on that machine}
for A in "$@"; do
  out="$DEST/$A"; mkdir -p "$out/structures"
  ssh -o BatchMode=yes "$HOST" "cd $D/raw && python3 -c \"
import json; s=json.load(open('$D/products/$A/monomer/sidecar.json'))
ids=sorted({m['pdb_id'] for m in s['models']}|{u['pdb_id'] for u in (s.get('unaligned') or [])})
print('\n'.join('pdb-mmcif/%s/%s.cif.gz' % (p[1:3], p) for p in ids)); print('uniprot/$A.fasta')
\" | tar -cf - -T -" | tar -xf - -C "$out"
  mv "$out"/pdb-mmcif/*/*.cif.gz "$out/structures/"
  mv "$out/uniprot/$A.fasta" "$out/uniprot.fasta"
  rm -rf "$out/pdb-mmcif" "$out/uniprot"
  echo "$A: $(ls "$out/structures" | wc -l | tr -d ' ') entries, $(du -sh "$out" | cut -f1)"
done
