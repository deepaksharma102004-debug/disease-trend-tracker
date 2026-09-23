function changeRange(val) {
    const url = new URL(window.location.href);
    url.searchParams.set("months", val);
    window.location.href = url.toString();
}

// Render chart for each parameter of each disease
diseaseData.forEach((disease) => {
    const labels = disease.visits.map(v => v.visit_date);

    disease.parameters.forEach((param, pi) => {
        const canvasId = `chart-${pi + 1}-${disease.disease_id}`;
        const canvas   = document.getElementById(canvasId);
        if (!canvas) return;

        const values   = disease.visits.map(v => v[param] ?? null);
        const forecast = disease.forecasts[param] || [];

        renderSingleChart(canvas, labels, values, forecast, param);
    });
});
function escapeHTML(text) {
    return text
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#39;");
}

function formatAIText(text) {
    return escapeHTML(text)
        // Numbered headings 1. **Heading:** → spaced-out heading block
        .replace(/(\d+)\.\s*\*\*(.*?)\*\*/g,
            "<div style='margin-top:22px; margin-bottom:8px;'>" +
            "<span style='font-size:16.5px; color:var(--navy); font-weight:700;'>$1. $2</span></div>")
        // Remaining **bold**
        .replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>")
        // Bullet points * text → each bullet as its own spaced block
        .replace(/\n\s*\*\s(?!\*)(.*)/g,
            "<div style='margin:6px 0 6px 4px; line-height:1.7;'>• $1</div>")
        // Remaining blank-line breaks between paragraphs
        .replace(/\n{2,}/g, "<div style='height:10px'></div>")
        // Regular single newlines
        .replace(/\n/g, "<br>");
}
