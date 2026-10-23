"""No-tools version (brief 2.6): the same question as one text prompt, same scoring rule.

Coordinates don't fit in a prompt, so each entry is reduced to what the answer depends
on: every protein entity's sequence (deduplicated across entries) and, per chain, which
sequence positions have a Cα atom. The superposition step is the only thing dropped
(it removes no member in the pilot proteins).

    python gen/no_tools_prompt.py task/environment/data/proteins runs/no_tools/prompt.md
"""
import sys
from pathlib import Path

import gemmi

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "task" / "solution"))
import reference as R  # noqa: E402


def ranges(nums):
    nums = sorted(nums)
    out, start, prev = [], None, None
    for n in nums:
        if start is None:
            start = prev = n
        elif n == prev + 1:
            prev = n
        else:
            out.append(f"{start}-{prev}" if start != prev else f"{start}")
            start = prev = n
    if start is not None:
        out.append(f"{start}-{prev}" if start != prev else f"{start}")
    return ",".join(out)


def protein_block(folder: Path) -> str:
    uniprot = R.read_fasta(folder / "uniprot.fasta")
    seq_ids, lines = {}, []
    for cif in sorted((folder / "structures").glob("*.cif*")):
        st = gemmi.read_structure(str(cif))
        st.setup_entities()
        ent_seq = {}
        for ent in st.entities:
            if ent.entity_type == gemmi.EntityType.Polymer and ent.polymer_type not in R.NUCLEIC:
                s = "".join(R.letter(n) for n in ent.full_sequence)
                ent_seq[ent.name] = seq_ids.setdefault(s, f"S{len(seq_ids) + 1}")
        chains = []
        for chain in st[0]:
            obs = {}
            for res in chain:
                if res.entity_id in ent_seq and R.is_protein_residue(res) and res.label_seq \
                        and any(a.name.strip() == "CA" for a in res):
                    obs.setdefault(ent_seq[res.entity_id], set()).add(res.label_seq)
            for sid, pos in obs.items():
                chains.append(f"{chain.name}:{sid}[{ranges(pos)}]")
        lines.append(f"{cif.name.split('.')[0]} " + " ".join(chains))
    seqs = "\n".join(f"{sid} {s}" for s, sid in seq_ids.items())
    return (f"### {folder.name}\nUniProt sequence:\n{uniprot}\n\nSequences (polymer entities):\n{seqs}\n\n"
            f"Entries (chain:sequence[positions with a CA atom, 1-based in that sequence]):\n"
            + "\n".join(lines) + "\n")


def main(proteins_dir, out_path):
    blocks = [protein_block(f) for f in sorted(Path(proteins_dir).iterdir()) if f.is_dir()]
    head = (Path(__file__).resolve().parents[1] / "task" / "instruction.md").read_text()
    head = head.split("## Tools")[0]
    text = (head + "\n## Data\n\nEach protein's PDB entries, reduced to sequences and observed "
            "positions (no coordinates; skip the superposition step).\n\n" + "\n".join(blocks)
            + "\n## Answer\n\nReply with only the CSV:\nprotein_id,n_members,n_core\n")
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    Path(out_path).write_text(text)
    print(f"{out_path}: {len(text):,} characters (~{len(text) // 4:,} tokens)")
    for b in blocks:
        print(f"  {b.splitlines()[0]}: {len(b):,} chars")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
