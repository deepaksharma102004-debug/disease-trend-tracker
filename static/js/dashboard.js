// ── Add Patient — Disease Blocks ──────────────────────

let diseaseBlocks = [];

function addDiseaseBlock() {
    const index = diseaseBlocks.length;
    diseaseBlocks.push({ params: [] });

    const container = document.getElementById("diseases_container");
    const block     = document.createElement("div");
    block.className = "border border-border rounded-xl p-4 mb-3";
    block.id        = `disease_block_${index}`;
    block.innerHTML = `
        <div class="flex justify-between items-center mb-3">
            <p class="font-semibold mb-0">Disease ${index + 1}</p>
            ${index > 0 ? `<span style="cursor:pointer; color:var(--destructive);" onclick="removeDiseaseBlock(${index})">✕ Remove</span>` : ""}
        </div>
        <div class="mb-4">
            <label class="block font-semibold text-sm mb-1 text-mutedFg">Disease Name</label>
            <input type="text" class="form-control" id="disease_name_${index}" placeholder="e.g. Type 2 Diabetes">
        </div>
        <div class="mb-4">
            <label class="block font-semibold text-sm mb-1 text-mutedFg">Parameters to Track</label>
            <div class="flex gap-2 mb-2">
                <input type="text" class="form-control" id="param_input_${index}" placeholder="e.g. HbA1c">
                <button class="rounded-full border border-accent text-accent text-xs font-semibold px-4 hover:bg-accent hover:text-primaryFg transition shrink-0" onclick="addParam(${index})">+ Add</button>
            </div>
            <div id="param_tags_${index}" class="flex flex-wrap gap-2 mb-2"></div>
        </div>
        <div class="mb-3">
            <label class="block font-semibold text-sm mb-1 text-mutedFg">First Visit Date</label>
            <input type="date" class="form-control" id="visit_date_${index}">
        </div>
        <div id="param_fields_${index}"></div>
    `;
    container.appendChild(block);
}

function removeDiseaseBlock(index) {
    const block = document.getElementById(`disease_block_${index}`);
    if (block) block.remove();
    diseaseBlocks[index] = null;
}

function addParam(index) {
    const input = document.getElementById(`param_input_${index}`);
    const param = input.value.trim();
    if (!param) return;
    if (!diseaseBlocks[index]) return;
    if (diseaseBlocks[index].params.includes(param)) {
        input.value = "";
        return;
    }
    diseaseBlocks[index].params.push(param);
    input.value = "";
    renderParamTags(index);
    renderParamFields(index);
}

function removeParam(index, param) {
    if (!diseaseBlocks[index]) return;
    diseaseBlocks[index].params = diseaseBlocks[index].params.filter(p => p !== param);
    renderParamTags(index);
    renderParamFields(index);
}

function renderParamTags(index) {
    const container = document.getElementById(`param_tags_${index}`);
    container.innerHTML = diseaseBlocks[index].params.map(p => `
        <span class="inline-flex items-center gap-1.5 rounded-full bg-accent/15 text-accent border border-accent/30 px-3 py-1 text-xs font-semibold">
            ${p}
            <span style="cursor:pointer;" onclick="removeParam(${index}, '${p}')">✕</span>
        </span>
    `).join("");
}

function renderParamFields(index) {
    const container = document.getElementById(`param_fields_${index}`);
    container.innerHTML = diseaseBlocks[index].params.map(p => `
        <div class="mb-4">
            <label class="block font-semibold text-sm mb-1 text-mutedFg">${p}</label>
            <input type="number" step="any" class="form-control"
                id="val_${index}_${p}" placeholder="Enter value">
        </div>
    `).join("");
}


// ── Add Patient — Submit ──────────────────────────────

function submitNewPatient() {
    const patient_id   = document.getElementById("new_patient_id").value.trim();
    const patient_name = document.getElementById("new_patient_name").value.trim();

    if (!patient_id || !patient_name) {
        showError("patientError", "Please enter Patient ID and Name.");
        return;
    }

    const diseases = [];
    diseaseBlocks.forEach((block, index) => {
        if (!block) return;
        const disease_name = document.getElementById(`disease_name_${index}`)?.value.trim();
        const visit_date   = document.getElementById(`visit_date_${index}`)?.value;
        if (!disease_name || !visit_date || block.params.length === 0) return;
        const param_values = {};
        for (const p of block.params) {
            const val = document.getElementById(`val_${index}_${p}`)?.value;
            if (val) param_values[p] = parseFloat(val);
        }
        diseases.push({ disease_name, parameters: block.params, visit_date, param_values });
    });

    if (diseases.length === 0) {
        showError("patientError", "Please add at least one disease with parameters and visit date.");
        return;
    }

    fetch("/api/add-patient", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ patient_id, patient_name, diseases })
    })
    .then(res => res.json())
    .then(data => {
        if (data.status === "success") {
            document.getElementById("patientSuccess").classList.remove("d-none");
            document.getElementById("patientError").classList.add("d-none");
            setTimeout(() => window.location.reload(), 1500);
        } else {
            showError("patientError", data.message || "Something went wrong.");
        }
    })
    .catch(() => showError("patientError", "Network error. Please try again."));
}


// ── Add Visit — Load Diseases ─────────────────────────

function loadPatientDiseases() {
    const patient_id    = document.getElementById("visit_patient_id").value;
    const diseaseSelect = document.getElementById("visit_disease_id");
    document.getElementById("visit_param_fields").innerHTML = "";
    diseaseSelect.innerHTML = '<option value="">Loading...</option>';

    if (!patient_id) {
        diseaseSelect.innerHTML = '<option value="">-- Select Patient First --</option>';
        return;
    }

    fetch(`/api/patient-diseases/${patient_id}`)
        .then(res => res.json())
        .then(diseases => {
            diseaseSelect.innerHTML = '<option value="">-- Select Disease --</option>';
            diseases.forEach(d => {
                const opt = document.createElement("option");
                opt.value          = d.disease_id;
                opt.text           = d.disease_name;
                opt.dataset.params = JSON.stringify(d.parameters);
                diseaseSelect.appendChild(opt);
            });
        })
        .catch(() => {
            diseaseSelect.innerHTML = '<option value="">Failed to load diseases</option>';
        });
}

function loadDiseaseParams() {
    const diseaseSelect = document.getElementById("visit_disease_id");
    const selected      = diseaseSelect.selectedOptions[0];
    const container     = document.getElementById("visit_param_fields");

    if (!selected || !selected.dataset.params) {
        container.innerHTML = "";
        return;
    }

    const params = JSON.parse(selected.dataset.params);
    container.innerHTML = params.map(p => `
        <div class="mb-4">
            <label class="block font-semibold text-sm mb-1 text-mutedFg">${p}</label>
            <input type="number" step="any" class="form-control" id="visit_val_${p}" placeholder="Enter value">
        </div>
    `).join("");
}


// ── Add Visit — Submit ────────────────────────────────

function submitVisit() {
    const patient_id = document.getElementById("visit_patient_id").value;
    const disease_id = document.getElementById("visit_disease_id").value;
    const visit_date = document.getElementById("visit_date").value;

    if (!patient_id || !disease_id || !visit_date) {
        showError("visitError", "Please select patient, disease and visit date.");
        return;
    }

    const diseaseSelect = document.getElementById("visit_disease_id");
    const params        = JSON.parse(diseaseSelect.selectedOptions[0].dataset.params || "[]");
    const param_values  = {};

    for (const p of params) {
        const val = document.getElementById(`visit_val_${p}`)?.value;
        if (!val) {
            showError("visitError", `Please enter a value for ${p}.`);
            return;
        }
        param_values[p] = parseFloat(val);
    }

    fetch("/api/add-visit", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ patient_id, disease_id, visit_date, param_values })
    })
    .then(res => res.json())
    .then(data => {
        if (data.status === "success") {
            document.getElementById("visitSuccess").classList.remove("d-none");
            document.getElementById("visitError").classList.add("d-none");
            setTimeout(() => window.location.reload(), 1500);
        } else {
            showError("visitError", data.message || "Something went wrong.");
        }
    })
    .catch(() => showError("visitError", "Network error. Please try again."));
}


// ── Utility ───────────────────────────────────────────

function showError(elementId, message) {
    const el = document.getElementById(elementId);
    el.classList.remove("d-none");
    el.innerText = "❌ " + message;
}


// ── Modal Init ────────────────────────────────────────

document.addEventListener("DOMContentLoaded", () => {
    const modal = document.getElementById("addPatientModal");
    if (modal) {
        modal.addEventListener("show.bs.modal", () => {
            diseaseBlocks = [];
            document.getElementById("diseases_container").innerHTML = "";
            document.getElementById("patientSuccess").classList.add("d-none");
            document.getElementById("patientError").classList.add("d-none");
            document.getElementById("new_patient_id").value = "";
            document.getElementById("new_patient_name").value = "";
            addDiseaseBlock();

            fetch("/api/next-patient-id")
                .then(res => res.json())
                .then(data => {
                    if (data.patient_id) {
                        document.getElementById("new_patient_id").value = data.patient_id;
                    }
                });
        });
    }
});

// ── Dashboard Search + Filter ─────────────────────────
let currentFilter = "all";

function setFilter(f) {
    currentFilter = f;
    document.querySelectorAll("[data-filter-btn]").forEach(btn => {
        btn.classList.toggle("active", btn.dataset.filterBtn === f);
    });
    filterPatients();
}

function filterPatients() {
    const q = document.getElementById("patientSearch").value.trim().toLowerCase();
    const cards = document.querySelectorAll(".patient-card");
    let visibleCount = 0;

    cards.forEach(card => {
        const matchesQ = !q || card.dataset.name.includes(q) || card.dataset.id.includes(q);
        const matchesF = currentFilter === "all" || card.dataset.risk === currentFilter;
        const show = matchesQ && matchesF;
        card.classList.toggle("hidden", !show);
        if (show) visibleCount++;
    });

    document.getElementById("noResults").classList.toggle("hidden", visibleCount > 0);
}

document.addEventListener("DOMContentLoaded", () => setFilter("all"));