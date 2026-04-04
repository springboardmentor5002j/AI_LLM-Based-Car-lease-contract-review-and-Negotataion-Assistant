// ===== TAB SWITCHING =====
function switchTab(tabName) {
    const tabs = document.querySelectorAll('.tab-content');
    tabs.forEach(tab => tab.classList.remove('active'));
    
    const btns = document.querySelectorAll('.tab-btn');
    btns.forEach(btn => btn.classList.remove('active'));
    
    const selectedTab = document.getElementById(tabName + '-tab');
    if (selectedTab) selectedTab.classList.add('active');
    
    event.target.classList.add('active');
}

// ===== FILE HANDLING =====
function handleFileSelect() {
    const file = document.getElementById('fileInput').files[0];
    const status = document.getElementById('uploadStatus');
    if (file) {
        status.textContent = '📁 Selected: ' + file.name;
        status.className = 'status waiting';
    }
}

// ===== CONTRACT UPLOAD & ANALYSIS =====
async function uploadFile() {
    const file = document.getElementById('fileInput').files[0];
    const status = document.getElementById('uploadStatus');
    
    if (!file) {
        status.textContent = '❌ Please select a PDF file';
        status.className = 'status error';
        return;
    }
    
    if (!file.name.toLowerCase().endsWith('.pdf')) {
        status.textContent = '❌ Only PDF files are supported';
        status.className = 'status error';
        return;
    }
    
    const formData = new FormData();
    formData.append('file', file);
    
    status.textContent = '⏳ Analyzing contract...';
    status.className = 'status uploading';
    
    try {
        const response = await fetch('/upload', {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) throw new Error('Upload failed');
        
        const data = await response.json();
        
        displaySLA(data.sla);
        displaySuggestions(data.suggestions);
        displayFairnessScore(data.fairness_score);
        
        status.textContent = '✅ Contract analyzed successfully!';
        status.className = 'status success';
    } catch (error) {
        console.error(error);
        status.textContent = '❌ Error: ' + error.message;
        status.className = 'status error';
    }
}

// ===== DISPLAY SLA TABLE =====
function displaySLA(slaData) {
    const table = document.querySelector('#slaTable tbody');
    table.innerHTML = '';
    
    for (const key in slaData) {
        const row = `
            <tr>
                <td><strong>${key}</strong></td>
                <td>${slaData[key]}</td>
            </tr>
        `;
        table.innerHTML += row;
    }
    
    document.getElementById('slaCard').style.display = 'block';
}

// ===== DISPLAY SUGGESTIONS =====
function displaySuggestions(suggestions) {
    const list = document.getElementById('negotiationList');
    list.innerHTML = '';
    
    suggestions.forEach(item => {
        const li = document.createElement('li');
        li.textContent = item;
        list.appendChild(li);
    });
    
    document.getElementById('suggestionsCard').style.display = 'block';
}

// ===== DISPLAY FAIRNESS SCORE =====
function displayFairnessScore(scoreData) {
    const scoreCircle = document.getElementById('scoreCircle');
    const grade = document.getElementById('scoreGrade');
    const bonuses = document.getElementById('scoreBonuses');
    const penalties = document.getElementById('scorePenalties');
    
    scoreCircle.textContent = scoreData.score;
    grade.textContent = scoreData.grade;
    
    let bonusText = scoreData.bonuses.length > 0 
        ? '<strong>✅ Favorable Terms:</strong> ' + scoreData.bonuses.join(', ')
        : '';
    let penaltyText = scoreData.penalties.length > 0 
        ? '<strong>⚠️ Areas to Negotiate:</strong> ' + scoreData.penalties.join(', ')
        : '';
    
    bonuses.innerHTML = bonusText;
    penalties.innerHTML = penaltyText;
    
    document.getElementById('fairnessCard').style.display = 'block';
}

// ===== VIN LOOKUP =====
async function lookupVIN() {
    const vin = document.getElementById('vinInput').value.trim().toUpperCase();
    const status = document.getElementById('vinStatus');
    
    if (!vin || vin.length !== 17) {
        status.textContent = '❌ VIN must be exactly 17 characters';
        status.className = 'status error';
        return;
    }
    
    status.textContent = '⏳ Looking up VIN...';
    status.className = 'status uploading';
    
    try {
        const response = await fetch('/api/vin-lookup', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({vin: vin})
        });
        
        if (!response.ok) throw new Error('VIN lookup failed');
        
        const data = await response.json();
        
        if (data.error) {
            status.textContent = '❌ ' + data.error;
            status.className = 'status error';
        } else {
            displayVINInfo(data);
            status.textContent = '✅ VIN lookup successful!';
            status.className = 'status success';
        }
    } catch (error) {
        status.textContent = '❌ Error: ' + error.message;
        status.className = 'status error';
    }
}

// ===== DISPLAY VIN INFO =====
function displayVINInfo(vehicle) {
    const info = document.getElementById('vinInfo');
    let html = '';
    
    for (const key in vehicle) {
        if (key !== 'error') {
            html += `<p><strong>${key}:</strong> ${vehicle[key]}</p>`;
        }
    }
    
    info.innerHTML = html;
    document.getElementById('vinCard').style.display = 'block';
}

// ===== NEGOTIATION TIPS =====
async function getNegotiationTips() {
    try {
        const response = await fetch('/api/negotiation-tips', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({})
        });
        
        if (!response.ok) throw new Error('Failed to fetch tips');
        
        const data = await response.json();
        
        const list = document.getElementById('tipsList');
        list.innerHTML = '';
        
        data.tips.forEach(tip => {
            const li = document.createElement('li');
            li.textContent = tip;
            list.appendChild(li);
        });
        
        document.getElementById('tipsCard').style.display = 'block';
    } catch (error) {
        console.error(error);
        alert('Error fetching tips: ' + error.message);
    }
}