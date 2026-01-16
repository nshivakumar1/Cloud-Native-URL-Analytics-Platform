const shortenBtn = document.getElementById('shortenBtn');
const urlInput = document.getElementById('urlInput');
const resultCard = document.getElementById('resultCard');
const shortLink = document.getElementById('shortLink');
const aiBox = document.getElementById('aiBox');
const aiCategory = document.getElementById('aiCategory');
const aiSummary = document.getElementById('aiSummary');

let pollingInterval;

shortenBtn.addEventListener('click', async () => {
    const url = urlInput.value;
    if (!url) return;

    // Reset UI
    resultCard.classList.add('hidden');
    aiBox.classList.add('hidden');
    clearInterval(pollingInterval);

    try {
        const response = await fetch('/shorten', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ url })
        });

        if (!response.ok) throw new Error('Failed');
        const data = await response.json();

        // Show Result
        const shortUrl = `${window.location.origin}/${data.short_code}`;
        shortLink.href = shortUrl;
        shortLink.textContent = shortUrl;
        resultCard.classList.remove('hidden');

        // Start polling for AI insights
        pollStats(data.short_code);

    } catch (e) {
        alert('Error shortening URL');
    }
});

function pollStats(shortCode) {
    aiCategory.textContent = "Analyzing...";
    aiSummary.textContent = "Gemini is reading the website...";
    aiBox.classList.remove('hidden');

    let attempts = 0;
    pollingInterval = setInterval(async () => {
        attempts++;
        if (attempts > 20) { // Timeout after 40s
            clearInterval(pollingInterval);
            aiSummary.textContent = "Analysis timed out (or AI disabled).";
            return;
        }

        try {
            const res = await fetch(`/stats/${shortCode}`);
            const data = await res.json();

            if (data.ai_insights) {
                clearInterval(pollingInterval);
                aiCategory.textContent = data.ai_insights.category || "General";
                aiSummary.textContent = data.ai_insights.summary || "No summary available.";
            }
        } catch (e) {
            console.error("Polling error", e);
        }
    }, 2000); // Check every 2s
}

function resetUI() {
    resultCard.classList.add('hidden');
    urlInput.value = '';
}

function copyLink() {
    navigator.clipboard.writeText(shortLink.href);
    alert('Copied!');
}
