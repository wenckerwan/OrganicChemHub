(function () {
  const viewers = document.querySelectorAll("[data-chem-viewer]");

  function splitMolecules(value) {
    return value
      .split(".")
      .map((item) => item.trim())
      .filter(Boolean);
  }

  function splitReaction(value) {
    const parts = value.split(">");
    return {
      reactants: splitMolecules(parts[0] || ""),
      agents: splitMolecules(parts[1] || ""),
      products: splitMolecules(parts.slice(2).join(">") || ""),
    };
  }

  function setStatus(viewer, text, state) {
    const status = viewer.querySelector("[data-chem-status]");
    if (!status) {
      return;
    }
    status.textContent = text;
    status.dataset.state = state;
  }

  function makeMolecule(smiles, label) {
    const molecule = document.createElement("figure");
    molecule.className = "molecule-tile";

    const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
    svg.setAttribute("role", "img");
    svg.setAttribute("aria-label", label);
    svg.dataset.chemSmiles = smiles;
    molecule.appendChild(svg);

    const caption = document.createElement("figcaption");
    caption.textContent = smiles;
    molecule.appendChild(caption);

    return molecule;
  }

  function appendArrow(stage, label) {
    const arrow = document.createElement("div");
    arrow.className = "reaction-arrow";
    arrow.innerHTML = "<span></span>";
    if (label) {
      const agent = document.createElement("small");
      agent.textContent = label;
      arrow.appendChild(agent);
    }
    stage.appendChild(arrow);
  }

  function drawMolecule(svg, smiles, viewer) {
    if (!window.SmilesDrawer || !window.SmilesDrawer.SvgDrawer) {
      setStatus(viewer, "渲染库未加载，已保留 SMILES", "warning");
      return;
    }

    const drawer = new window.SmilesDrawer.SvgDrawer({
      width: 260,
      height: 170,
      padding: 14,
      experimentalSSSR: true,
    });

    window.SmilesDrawer.parse(
      smiles,
      function (tree) {
        drawer.draw(tree, svg, "light", false);
        setStatus(viewer, "已渲染", "ready");
      },
      function () {
        svg.closest(".molecule-tile").classList.add("is-invalid");
        setStatus(viewer, "部分 SMILES 无法解析", "warning");
      }
    );
  }

  function renderViewer(viewer) {
    const smiles = (viewer.dataset.smiles || "").trim();
    const mode = viewer.dataset.chemViewer;
    const stage = viewer.querySelector("[data-chem-stage]");

    if (!smiles || !stage) {
      return;
    }

    stage.innerHTML = "";

    if (mode === "reaction") {
      const reaction = splitReaction(smiles);
      reaction.reactants.forEach((item, index) => stage.appendChild(makeMolecule(item, "反应物 " + (index + 1))));
      appendArrow(stage, reaction.agents.join(" + "));
      reaction.products.forEach((item, index) => stage.appendChild(makeMolecule(item, "产物 " + (index + 1))));
    } else {
      splitMolecules(smiles).forEach((item, index) => stage.appendChild(makeMolecule(item, "分子 " + (index + 1))));
    }

    viewer.querySelectorAll("[data-chem-smiles]").forEach((svg) => {
      drawMolecule(svg, svg.dataset.chemSmiles, viewer);
    });
  }

  viewers.forEach(renderViewer);
})();
