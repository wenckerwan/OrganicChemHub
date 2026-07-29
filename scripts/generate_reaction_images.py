"""Batch-generate SVG structure images from Reaction SMILES using RDKit.

Output: static/images/reactions/reaction_{slug}_equation.svg
        static/images/reactions/reaction_{slug}_thumbnail.svg
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "organic_chem_hub.settings")

import django
django.setup()

from rdkit import Chem
from rdkit.Chem import AllChem, Draw

from reactions.models import Reaction

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "static" / "images" / "reactions"
EQ_W, EQ_H = 800, 350
TH_W, TH_H = 400, 175


def draw_smiles_to_svg(smiles: str, width: int, height: int) -> str | None:
    """Draw a SMILES string to SVG, handling reaction SMILES (>>)."""
    try:
        if ">>" in smiles:
            parts = smiles.split(">>")
            reactants_smi = parts[0]
            products_smi = parts[1]

            r_mol = Chem.MolFromSmiles(reactants_smi)
            p_mol = Chem.MolFromSmiles(products_smi)
            if r_mol is None or p_mol is None:
                print(f"    Mol parse fail: r={r_mol is None} p={p_mol is None}")
                return None

            # Compute coordinates
            AllChem.Compute2DCoords(r_mol)
            AllChem.Compute2DCoords(p_mol)

            # Draw on a single canvas with padding
            d = Draw.MolDraw2DSVG(width, height)
            opts = d.drawOptions()
            opts.addStereoAnnotation = True
            opts.rotate = 0

            # Draw reactants on left, products on right with arrow in between
            d.DrawMolecule(r_mol)
            # We use the offset mechanism: draw a second molecule
            d.DrawMolecule(p_mol)
            d.FinishDrawing()
            return d.GetDrawingText()
        else:
            mol = Chem.MolFromSmiles(smiles)
            if mol is None:
                return None
            AllChem.Compute2DCoords(mol)
            d = Draw.MolDraw2DSVG(width, height)
            opts = d.drawOptions()
            opts.addStereoAnnotation = True
            opts.rotate = 0
            d.DrawMolecule(mol)
            d.FinishDrawing()
            return d.GetDrawingText()
    except Exception as e:
        print(f"    RDKit error: {e}")
        return None


def generate_images(slug: str, smiles: str) -> bool:
    """Generate equation and thumbnail SVGs."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    eq_path = OUTPUT_DIR / f"reaction_{slug}_equation.svg"
    thumb_path = OUTPUT_DIR / f"reaction_{slug}_thumbnail.svg"

    if eq_path.exists():
        print(f"  [SKIP] {eq_path.name}")
        return True

    svg = draw_smiles_to_svg(smiles, EQ_W, EQ_H)
    if svg is None:
        print(f"  [FAIL] {smiles}")
        return False

    eq_path.write_text(svg, encoding="utf-8")
    print(f"  [OK]   {eq_path.name} ({len(svg)} bytes)")

    # Thumbnail: replace viewBox
    thumb_svg = svg.replace(f'viewBox="0 0 {EQ_W} {EQ_H}"', f'viewBox="0 0 {TH_W} {TH_H}"')
    thumb_path.write_text(thumb_svg, encoding="utf-8")
    print(f"  [OK]   {thumb_path.name} ({len(thumb_svg)} bytes)")

    return True


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    reactions = Reaction.objects.exclude(equation_smiles="").order_by("pk")
    total = reactions.count()
    ok = fail = 0

    print(f"Found {total} reactions with SMILES.\nOutput: {OUTPUT_DIR}\n")

    for rxn in reactions:
        slug = rxn.slug.replace("-", "_").replace(" ", "_")
        print(f"[{rxn.pk:3d}] {rxn.name_en:35s} ({slug})")
        if generate_images(slug, rxn.equation_smiles):
            ok += 1
        else:
            fail += 1

    print(f"\nDone: {ok} OK, {fail} FAIL (total {total})")


if __name__ == "__main__":
    main()
